"""Inference loop for camera-backed live detection."""

from __future__ import annotations

import asyncio
import time
from typing import Any

from src.config import BYTE_TRACK_CONFIG_PATH
from src.dashboard.backend.models import SystemStatus
from src.logger import get_logger

logger = get_logger(__name__)


class StreamingWorker:
    """Run the existing CameraService stream loop against its stable service interface."""

    def __init__(self, service: Any):
        self.service = service

    def run(self) -> None:
        service = self.service
        last_metrics_time = time.time()
        metrics_interval = 0.5
        consecutive_read_failures = 0

        with service._lock:
            config = service.model_config
            confidence_threshold = config.conf_threshold if config else 0.5
            reject_threshold = config.reject_threshold if config else confidence_threshold
            iou_threshold = config.iou_threshold if config else 0.45
            image_size = service.img_size
            use_int8_tflite = service.is_tflite_int8
            enable_tracking = config.enable_tracking if config else False
            target_latency_ms = config.target_latency_ms if config else 50

        while True:
            try:
                with service._lock:
                    if not service.is_streaming:
                        break
                    camera = service.camera
                    model = service.model
                    if service.skip_frame:
                        service.skip_frame = False
                        continue

                if camera is None or model is None:
                    break

                frame_received, frame = camera.read()
                with service._lock:
                    if not service.is_streaming:
                        break
                if not frame_received:
                    consecutive_read_failures += 1
                    if consecutive_read_failures >= 30:
                        service._update_status(SystemStatus.ERROR, "Camera disconnected")
                        with service._lock:
                            service.is_streaming = False
                        break
                    time.sleep(0.01)
                    continue
                consecutive_read_failures = 0
                if hasattr(camera, "is_alive") and not camera.is_alive():
                    service._update_status(SystemStatus.ERROR, "Camera stream is frozen")
                    with service._lock:
                        service.is_streaming = False
                    break

                frame_start = time.perf_counter()

                if enable_tracking and not use_int8_tflite:
                    results = model.track(
                        frame,
                        imgsz=image_size,
                        conf=confidence_threshold,
                        iou=iou_threshold,
                        persist=True,
                        verbose=False,
                        tracker=str(BYTE_TRACK_CONFIG_PATH),
                    )
                else:
                    results = model.predict(
                        frame,
                        imgsz=image_size,
                        conf=confidence_threshold,
                        iou=iou_threshold,
                        verbose=False,
                    )

                inference_time = (time.perf_counter() - frame_start) * 1000
                detections = service._process_results(results, confidence_threshold, reject_threshold)
                service._update_performance_metrics(inference_time, results)

                current_time = time.time()
                if current_time - last_metrics_time >= metrics_interval:
                    metrics = service._calculate_system_metrics()
                    with service._lock:
                        service.metrics_history.append(metrics)
                    if service.on_metrics and service._loop:
                        asyncio.run_coroutine_threadsafe(service.on_metrics(metrics), service._loop)
                    last_metrics_time = current_time

                if detections and service.on_detection and service._loop:
                    asyncio.run_coroutine_threadsafe(service.on_detection(detections), service._loop)

                service._update_history(detections)

                frame_callback = service.on_frame
                if frame_callback:
                    try:
                        frame_callback(frame, detections)
                    except Exception as exc:
                        logger.warning("Frame send error: %s", exc)

                with service._lock:
                    if not results:
                        service.skip_frame = False
                    elif service.latency_history:
                        avg_latency = sum(service.latency_history) / len(service.latency_history)
                        service.skip_frame = avg_latency > target_latency_ms
                    else:
                        service.skip_frame = False

            except Exception as exc:
                service._update_status(SystemStatus.ERROR, f"Streaming error: {exc}")
                logger.error("Streaming error: %s", exc)
                with service._lock:
                    service.is_streaming = False
                break
