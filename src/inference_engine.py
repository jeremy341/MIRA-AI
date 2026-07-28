"""Shared inference engine: camera setup, model loading, inference loop."""

from __future__ import annotations

import time
import warnings
from collections import deque
from types import TracebackType
from typing import Self

import cv2
from ultralytics import YOLO

from .config import (
    BYTE_TRACK_CONFIG_PATH,
    CLASS_NAMES,
    DEFAULT_CONF,
    DEFAULT_IMGSZ,
    DEFAULT_IOU,
    DETECTION_DIR,
    REJECT_THRESHOLD,
    get_tflite_imgsz,
)
from .exceptions import CameraError, ConfigError
from .hardware import USBCamera
from .logger import logger
from .visualize import draw_boxes


class InferenceEngine:
    """Unified inference engine for MIRA detection models.

    Handles camera initialization, model loading, TFLite/INT8 configuration,
    and the main real-time inference loop.

    Usage as context manager (recommended):
        with InferenceEngine(...) as engine:
            engine.run()
    """

    def __init__(
        self,
        model_name: str,
        camera_index: int = 0,
        cam_width: int = 640,
        cam_height: int = 360,
        target_latency_ms: int = 50,
        conf_threshold: float | None = None,
        reject_threshold: float = REJECT_THRESHOLD,
        imgsz: int | None = None,
        enable_tracking: bool = True,
        iou_threshold: float | None = None,
    ):
        if conf_threshold is None:
            conf_threshold = DEFAULT_CONF
        if iou_threshold is None:
            iou_threshold = DEFAULT_IOU
        self.model_name = model_name
        self.camera_index = camera_index
        self.cam_width = cam_width
        self.cam_height = cam_height
        self.target_latency_ms = target_latency_ms
        self.conf_threshold = conf_threshold
        self.reject_threshold = reject_threshold
        self.enable_tracking = enable_tracking
        self.iou_threshold = iou_threshold

        # Lifecycle flags
        self._stopped = False
        self._released = False

        # Resolve and load model (guard against path traversal)
        self.model_path = (DETECTION_DIR / model_name).resolve()
        try:
            self.model_path.relative_to(DETECTION_DIR.resolve())
        except ValueError:
            raise ConfigError(f"Model path escapes detection directory: {model_name}") from None
        self._load_model(imgsz)

        # Initialize camera
        try:
            self.stream = USBCamera(camera_index, cam_width, cam_height)
        except Exception:
            self._cleanup()
            raise

        # Tracking state
        self.prev_time = time.perf_counter()
        self.latency_history = deque(maxlen=30)
        self.skip_frame = False
        self._current_fps = 0.0

    def _load_model(self, imgsz: int | None):
        """Load YOLO model with TFLite/INT8-specific configuration."""
        available = sorted(p.name for p in DETECTION_DIR.glob("*") if p.suffix in (".pt", ".tflite", ".keras"))

        logger.info("\nAvailable models in models/:")
        for name in available:
            marker = "  <-- selected" if name == self.model_name else ""
            int8_marker = " [INT8 - Recommended for speed]" if "int8" in name.lower() else ""
            logger.info(f"  {name}{marker}{int8_marker}")
        logger.info("")

        if not self.model_path.exists():
            logger.error(
                f"Model '{self.model_name}' not found in {DETECTION_DIR}.\nAvailable models: {', '.join(available)}"
            )
            raise FileNotFoundError(
                f"Model '{self.model_name}' not found in {DETECTION_DIR}.\nAvailable models: {', '.join(available)}"
            )

        if "classifier" in self.model_name.lower():
            logger.error(f"\nERROR: '{self.model_name}' is a CLASSIFIER model, not a detector.")
            logger.error("Live detection requires a detection model (.pt or detection .tflite).")
            raise ValueError(
                f"Model '{self.model_name}' is a classifier, not a detector. Use a detection model for live detection."
            )

        task_type = "detect"
        try:
            self.model = YOLO(str(self.model_path), task=task_type)
        except Exception as e:
            raise RuntimeError(f"Failed to load model {self.model_name}: {e}") from e

        self.is_tflite_int8 = self.model_path.suffix == ".tflite" and "int8" in self.model_name.lower()

        if self.model_path.suffix == ".tflite":
            self.img_size = imgsz or get_tflite_imgsz(self.model_path)
            if self.is_tflite_int8:
                logger.info(f"TFLite INT8 model: input {self.img_size}x{self.img_size}, auto-setting conf=0.25")
            else:
                logger.info(f"TFLite model: input {self.img_size}x{self.img_size}")
        else:
            self.img_size = imgsz or DEFAULT_IMGSZ
            logger.info(f"PyTorch model: input {self.img_size}x{self.img_size}")

        if self.is_tflite_int8:
            # INT8 quantization compresses confidence scores toward 0.5;
            # use 0.25 so low-confidence detections are still visible.
            self.conf_threshold = 0.25
            logger.info(f"Confidence threshold overridden to {self.conf_threshold} for INT8 model.")

        # TFLite models don't support ByteTrack; disable tracking
        if self.model_path.suffix == ".tflite" and self.enable_tracking:
            self.enable_tracking = False
            logger.info("Tracking disabled — not supported for TFLite models.")

    def __enter__(self) -> Self:
        """Context manager entry."""
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        """Context manager exit — always release resources."""
        self._cleanup()

    def stop(self) -> None:
        """Signal the inference loop to stop on the next iteration."""
        self._stopped = True

    def _cleanup(self) -> None:
        """Release all held resources. Safe to call multiple times (idempotent)."""
        if self._released:
            return
        self._released = True
        self._stopped = True
        try:
            if hasattr(self, "model") and self.model is not None:
                del self.model
                self.model = None
            import gc

            gc.collect()
            try:
                import torch

                if torch.cuda.is_available():
                    torch.cuda.empty_cache()
            except (ImportError, AttributeError):
                pass
        except Exception as exc:
            logger.warning("Exception while releasing model: %s", exc)
        try:
            if hasattr(self, "stream") and self.stream is not None:
                self.stream.release()
        except Exception as exc:
            logger.warning("Exception while releasing camera: %s", exc)
        finally:
            try:
                cv2.destroyAllWindows()
            except Exception as exc:
                logger.warning("Exception while destroying cv2 windows: %s", exc)

    def run(self):
        """Start the real-time inference loop."""
        self.prev_time = time.perf_counter()
        logger.info(
            f"MIRA Live Detection active (camera {self.camera_index}, "
            f"{self.cam_width}x{self.cam_height}, "
            f"target latency: {self.target_latency_ms}ms). "
            f"Press 'q' to exit."
        )

        consecutive_errors = 0
        consecutive_read_failures = 0
        try:
            while not self._stopped:
                ret, frame = self.stream.read()
                if not ret or frame is None:
                    consecutive_read_failures += 1
                    if consecutive_read_failures >= 30:
                        raise CameraError(
                            f"Camera {self.camera_index} disconnected or frozen "
                            f"({consecutive_read_failures} consecutive read failures)"
                        )
                    time.sleep(0.01)
                    continue
                consecutive_read_failures = 0

                if self.skip_frame:
                    self.skip_frame = False
                    continue

                try:
                    results = self._infer(frame)
                    annotated = draw_boxes(frame, results, self.conf_threshold, self.reject_threshold, CLASS_NAMES)
                    self._update_metrics(results)
                    self._draw_status(annotated, results)
                except Exception as exc:
                    consecutive_errors += 1
                    logger.warning("Inference error (%d consecutive): %s", consecutive_errors, exc)
                    if consecutive_errors >= 30:
                        logger.error("Too many consecutive inference errors, stopping")
                        break
                    continue
                consecutive_errors = 0
                cv2.imshow("MIRA Real-Time Multi-Object Detection", annotated)

                if cv2.waitKey(1) & 0xFF == ord("q"):
                    break
        finally:
            self._cleanup()

    def _infer(self, frame):
        """Run model inference or tracking on a single frame."""
        if self.is_tflite_int8:
            return self.model.predict(
                frame,
                imgsz=self.img_size,
                conf=self.conf_threshold,
                iou=self.iou_threshold,
                verbose=False,
                quantize=False,
            )
        elif self.enable_tracking:
            return self.model.track(
                frame,
                imgsz=self.img_size,
                conf=self.conf_threshold,
                iou=self.iou_threshold,
                persist=True,
                verbose=False,
                tracker=str(BYTE_TRACK_CONFIG_PATH),
                quantize=False,
            )
        else:
            return self.model.predict(
                frame,
                imgsz=self.img_size,
                conf=self.conf_threshold,
                iou=self.iou_threshold,
                verbose=False,
                quantize=False,
            )

    def _update_metrics(self, results):
        """Track latency history and decide whether to skip the next frame."""
        curr_time = time.perf_counter()
        frame_time = curr_time - self.prev_time
        self.prev_time = curr_time

        self._current_fps = 1.0 / max(frame_time, 1e-6)
        if not results or len(results) == 0:
            self.skip_frame = False
            return
        speed = getattr(results[0], "speed", None) or {}
        latency_ms = speed.get("inference", 0) if isinstance(speed, dict) else 0
        self.latency_history.append(latency_ms)
        avg_latency = sum(self.latency_history) / len(self.latency_history)

        self.skip_frame = avg_latency > self.target_latency_ms

    def _draw_status(self, frame, results):
        """Draw status overlay on the annotated frame."""
        speed = getattr(results[0], "speed", None) or {}
        latency_ms = speed.get("inference", 0) if isinstance(speed, dict) else 0
        avg_latency = sum(self.latency_history) / len(self.latency_history)
        fps = self._current_fps

        status_text = (
            f"Cam: {self.camera_index} | {self.cam_width}x{self.cam_height} | "
            f"Latency: {latency_ms:.1f}ms (avg: {avg_latency:.1f}ms) | FPS: {fps:.1f} | "
            f"Skip: {'ON' if self.skip_frame else 'OFF'}"
        )
        cv2.putText(
            frame,
            status_text,
            (20, 40),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (0, 255, 255),
            2,
        )

    def __del__(self):
        """Safety-net finalizer. Warns if resources were not explicitly released."""
        if getattr(self, "_released", False):
            return
        warnings.warn(
            "InferenceEngine was not explicitly released. "
            "Use it as a context manager (with-statement) for guaranteed cleanup.",
            ResourceWarning,
            stacklevel=2,
        )
        try:
            self._cleanup()
        except Exception:
            pass
