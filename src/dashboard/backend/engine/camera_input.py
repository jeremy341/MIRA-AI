"""Camera and model input construction for the dashboard inference service."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Any


class CameraInputSource:
    """Build camera and YOLO inputs while keeping hardware imports at the service boundary."""

    @staticmethod
    def open_camera(config: Any, camera_factory: Callable[..., Any]) -> Any:
        return camera_factory(
            config.index,
            config.width,
            config.height,
            config.fps,
            config.autofocus,
            config.auto_exposure,
        )

    @staticmethod
    def load_model(
        model_name: str,
        config: Any,
        *,
        detection_dir: Path,
        model_factory: Callable[..., Any],
        imgsz_resolver: Callable[[Path], int],
        model_config_factory: Callable[..., Any],
    ) -> tuple[Any, Any, bool, int]:
        if any(sep in model_name for sep in ("/", "\\", "..")):
            raise ValueError(f"Invalid model name: {model_name}")

        model_path = (detection_dir / model_name).resolve()
        detection_root = detection_dir.resolve()
        if model_path.parent != detection_root or not model_path.exists():
            raise FileNotFoundError(f"Model not found: {model_name}")

        is_tflite = model_path.suffix.lower() == ".tflite"
        is_tflite_int8 = is_tflite and "int8" in model_name.lower()
        img_size = imgsz_resolver(model_path) if is_tflite else 640
        model = model_factory(str(model_path), task="detect")
        model_config = model_config_factory(
            name=config.name,
            conf_threshold=min(config.conf_threshold, 0.25) if is_tflite_int8 else config.conf_threshold,
            reject_threshold=config.reject_threshold,
            iou_threshold=config.iou_threshold,
            enable_tracking=config.enable_tracking if not is_tflite else False,
            target_latency_ms=config.target_latency_ms,
        )
        return model, model_config, is_tflite_int8, img_size
