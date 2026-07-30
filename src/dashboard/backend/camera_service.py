"""
Camera service managing inference pipeline
"""

import asyncio
import threading
import time
import cv2
from typing import Any
from collections import deque, defaultdict
from datetime import datetime, timedelta
import psutil

from ultralytics import YOLO
from config import CLASS_NAMES, DETECTION_DIR, BYTE_TRACK_CONFIG_PATH, get_tflite_imgsz, setup_camera_properties
from logger import get_logger
from models import WasteClass, Detection, SystemMetrics, Statistics, SystemStatus, ModelConfig

logger = get_logger(__name__)


class CameraService:
    """Main service handling camera, inference, and statistics"""

    _STOP_JOIN_TIMEOUT_SECONDS = 1.0

    def __init__(self, loop=None):
        self._lock = threading.Lock()
        self.status = SystemStatus.IDLE
        self.status_message = "System ready"

        # Store event loop for thread-safe coroutine scheduling
        self._loop = loop

        # Camera state
        self.camera = None
        self.camera_config = None
        self.is_streaming = False
        self._disconnect_count = 0
        self._streaming_thread = None

        # Model state
        self.model = None
        self.model_config = None
        self.is_tflite_int8 = False
        self.img_size = 640

        # Statistics
        self.detection_history = deque(maxlen=1000)
        self.class_history = defaultdict(list)
        self.metrics_history = deque(maxlen=100)

        # Performance tracking
        self.latency_history = deque(maxlen=30)
        self.frame_times = deque(maxlen=30)
        self.skip_frame = False

        # Callbacks for UI updates
        self.on_detection = None
        self.on_metrics = None
        self.on_status_change = None
        self.on_frame = None

    def _update_status_locked(self, status: SystemStatus, message: str):
        """Caller must hold self._lock"""
        self.status = status
        self.status_message = message

    def _notify_status_change(self):
        callback = self.on_status_change
        loop = self._loop
        if callback and loop:
            notification = self._run_status_callback(callback, self.status, self.status_message)
            try:
                asyncio.run_coroutine_threadsafe(notification, loop)
            except Exception as exc:
                notification.close()
                logger.warning("Status callback scheduling failed: %s", exc)

    @staticmethod
    async def _run_status_callback(callback, status, message):
        try:
            result = callback(status, message)
            if result is not None:
                await result
        except Exception as exc:
            logger.warning("Status callback failed: %s", exc)

    async def initialize_camera(self, config):
        """Initialize camera with configuration"""
        if self.status == SystemStatus.RUNNING:
            await self.stop()

        self._update_status(SystemStatus.INITIALIZING, "Initializing camera...")

        with self._lock:
            try:
                self.camera = cv2.VideoCapture(config.index, cv2.CAP_DSHOW if hasattr(cv2, "CAP_DSHOW") else 0)

                if not self.camera.isOpened():
                    raise RuntimeError(f"Failed to open camera index {config.index}")

                setup_camera_properties(self.camera, config.width, config.height, config.fps)

                # Warmup camera
                for _ in range(10):
                    self.camera.read()

                self.camera_config = config
                self._update_status(SystemStatus.IDLE, "Camera ready")
                return True

            except Exception as e:
                self._update_status(SystemStatus.ERROR, f"Camera error: {str(e)}")
                return False

    async def load_model(self, model_name: str, config):
        """Load detection model"""
        self._update_status(SystemStatus.INITIALIZING, f"Loading model {model_name}...")

        with self._lock:
            try:
                # Basic validation to prevent path traversal
                if any(sep in model_name for sep in ("/", "\\", "..")):
                    raise ValueError(f"Invalid model name: {model_name}")
                model_path = DETECTION_DIR / model_name
                model_path = model_path.resolve()
                if not str(model_path).startswith(str(DETECTION_DIR.resolve())):
                    raise ValueError(f"Invalid model path: {model_name}")
                if not model_path.exists():
                    raise FileNotFoundError(f"Model not found: {model_name}")

                # Load model
                if model_path.suffix == ".tflite":
                    task_type = "detect"
                    self.is_tflite_int8 = "int8" in model_name.lower()
                    self.img_size = get_tflite_imgsz(model_path)
                else:
                    task_type = "detect"
                    self.is_tflite_int8 = False
                    self.img_size = 640

                self.model = YOLO(str(model_path), task=task_type)

                # Adjust confidence for INT8 models
                self.model_config = ModelConfig(
                    name=config.name,
                    conf_threshold=min(config.conf_threshold, 0.25) if self.is_tflite_int8 else config.conf_threshold,
                    reject_threshold=config.reject_threshold,
                    iou_threshold=config.iou_threshold,
                    enable_tracking=config.enable_tracking if model_path.suffix != ".tflite" else False,
                    target_latency_ms=config.target_latency_ms,
                )
                self._update_status(SystemStatus.IDLE, f"Model {model_name} loaded")
                return True

            except Exception as e:
                self._update_status(SystemStatus.ERROR, f"Model load error: {str(e)}")
                return False

    async def start_streaming(self):
        """Start the inference streaming loop"""
        with self._lock:
            if self.is_streaming:
                return True

            if self._streaming_thread and self._streaming_thread.is_alive():
                self._update_status_locked(SystemStatus.ERROR, "Previous streaming thread is still shutting down")
                return False

            if not self.camera or not self.model:
                self._update_status_locked(SystemStatus.ERROR, "Camera or model not initialized")
                return False

            self.is_streaming = True
            self._update_status_locked(SystemStatus.RUNNING, "Streaming started")

            self._streaming_thread = threading.Thread(target=self._streaming_loop, daemon=True)
            self._streaming_thread.start()

            return True

    def _streaming_loop(self):
        """Main streaming and inference loop (runs in daemon thread)."""
        last_metrics_time = time.time()
        metrics_interval = 0.5

        with self._lock:
            local_conf = self.model_config.conf_threshold if self.model_config else 0.5
            local_iou = self.model_config.iou_threshold if self.model_config else 0.45
            local_img_size = self.img_size
            local_is_tflite_int8 = self.is_tflite_int8
            local_enable_tracking = self.model_config.enable_tracking if self.model_config else False
            local_target_latency = self.model_config.target_latency_ms if self.model_config else 50

        while True:
            try:
                with self._lock:
                    if not self.is_streaming:
                        break
                    cam = self.camera
                    mod = self.model
                    if self.skip_frame:
                        self.skip_frame = False
                        continue

                if cam is None or mod is None:
                    break

                ret, frame = cam.read()
                with self._lock:
                    if not self.is_streaming:
                        break
                if not ret:
                    with self._lock:
                        self._disconnect_count += 1
                        dc = self._disconnect_count > 100
                    if dc:
                        self._update_status(SystemStatus.ERROR, "Camera disconnected")
                        with self._lock:
                            self.is_streaming = False
                        break
                    time.sleep(0.01)
                    continue
                with self._lock:
                    self._disconnect_count = 0

                frame_start = time.perf_counter()

                if local_is_tflite_int8:
                    results = mod.predict(
                        frame,
                        imgsz=local_img_size,
                        conf=local_conf,
                        iou=local_iou,
                        verbose=False,
                    )
                elif local_enable_tracking:
                    results = mod.track(
                        frame,
                        imgsz=local_img_size,
                        conf=local_conf,
                        iou=local_iou,
                        persist=True,
                        verbose=False,
                        tracker=str(BYTE_TRACK_CONFIG_PATH),
                    )
                else:
                    results = mod.predict(
                        frame,
                        imgsz=local_img_size,
                        conf=local_conf,
                        iou=local_iou,
                        verbose=False,
                    )

                inference_time = (time.perf_counter() - frame_start) * 1000
                detections = self._process_results(results, local_conf)
                self._update_performance_metrics(inference_time)

                current_time = time.time()
                if current_time - last_metrics_time >= metrics_interval:
                    metrics = self._calculate_system_metrics()
                    with self._lock:
                        self.metrics_history.append(metrics)
                    if self.on_metrics and self._loop:
                        asyncio.run_coroutine_threadsafe(self.on_metrics(metrics), self._loop)
                    last_metrics_time = current_time

                if detections and self.on_detection and self._loop:
                    asyncio.run_coroutine_threadsafe(self.on_detection(detections), self._loop)

                self._update_history(detections)

                _callback = self.on_frame  # Capture under lock
                if _callback:
                    try:
                        _callback(frame, detections)
                    except Exception as e:
                        logger.warning("Frame send error: %s", e)

                with self._lock:
                    if self.latency_history:
                        avg_latency = sum(self.latency_history) / len(self.latency_history)
                        self.skip_frame = avg_latency > local_target_latency
                    else:
                        self.skip_frame = False

            except Exception as e:
                self._update_status(SystemStatus.ERROR, f"Streaming error: {e}")
                logger.error("Streaming error: %s", e)
                with self._lock:
                    self.is_streaming = False
                break

    def _process_results(self, results, conf_threshold: float = 0.5):
        """Process YOLO results into Detection objects"""
        detections = []

        if not results or len(results) == 0:
            return detections

        boxes = results[0].boxes
        if boxes is None or len(boxes) == 0:
            return detections

        for box in boxes:
            conf = float(box.conf[0])
            if conf < conf_threshold:
                continue

            cls_id = int(box.cls[0])
            class_name = self._class_id_to_name(cls_id)

            # Convert to WasteClass enum
            try:
                waste_class = WasteClass(class_name)
            except ValueError:
                continue  # Skip unknown classes

            x1, y1, x2, y2 = box.xyxy[0].cpu().numpy().astype(int).tolist()
            track_id = int(box.id[0]) if box.id is not None else None

            detection = Detection(class_name=waste_class, confidence=conf, bbox=[x1, y1, x2, y2], track_id=track_id)

            detections.append(detection)

        return detections

    def _class_id_to_name(self, class_id: int) -> str:
        """Map class ID to name"""
        return CLASS_NAMES[class_id] if class_id < len(CLASS_NAMES) else "unknown"

    def _update_performance_metrics(self, inference_time: float):
        """Update performance tracking metrics"""
        with self._lock:
            self.latency_history.append(inference_time)

            # Update frame times for FPS calculation
            self.frame_times.append(time.perf_counter())
            if len(self.frame_times) > 1:
                # Keep only recent times for accurate FPS
                while len(self.frame_times) > 1 and self.frame_times[-1] - self.frame_times[0] > 2.0:
                    self.frame_times.popleft()

    def _calculate_system_metrics(self) -> SystemMetrics:
        """Calculate current system metrics (snapshot shared state under lock)."""
        with self._lock:
            frame_times_snapshot = list(self.frame_times)
            latency_history_snapshot = list(self.latency_history)
            detection_history_snapshot = list(self.detection_history)
            skip = self.skip_frame

        fps = 0.0
        if len(frame_times_snapshot) > 1:
            time_span = frame_times_snapshot[-1] - frame_times_snapshot[0]
            if time_span > 0:
                fps = (len(frame_times_snapshot) - 1) / time_span

        inference_latency = 0.0
        avg_latency = 0.0
        if latency_history_snapshot:
            inference_latency = latency_history_snapshot[-1]
            avg_latency = sum(latency_history_snapshot) / len(latency_history_snapshot)

        cpu_percent = psutil.cpu_percent()
        memory_percent = psutil.virtual_memory().percent

        temperature = None
        try:
            with open("/sys/class/thermal/thermal_zone0/temp") as f:
                temp_millic = int(f.read().strip())
                temperature = temp_millic / 1000.0
        except Exception:
            pass

        detections_per_second = 0.0
        if len(detection_history_snapshot) >= 2:
            recent_detections = detection_history_snapshot[-10:]
            if len(recent_detections) >= 2:
                time_diff = (recent_detections[-1].timestamp - recent_detections[0].timestamp).total_seconds()
                if time_diff > 0.001:
                    detections_per_second = (len(recent_detections) - 1) / time_diff

        return SystemMetrics(
            fps=fps,
            inference_latency_ms=inference_latency,
            avg_latency_ms=avg_latency,
            cpu_percent=cpu_percent,
            memory_percent=memory_percent,
            temperature_celsius=temperature,
            detections_per_second=detections_per_second,
            skip_frames=skip,
        )

    def _update_history(self, detections: list[Detection]):
        """Update detection history, avoiding immediate duplicates"""
        with self._lock:
            for detection in detections:
                if self.detection_history:
                    last = self.detection_history[-1]
                    if last.class_name == detection.class_name and last.bbox == detection.bbox:
                        continue
                self.detection_history.append(detection)
                self.class_history[detection.class_name].append(detection)

    def _update_status(self, status: SystemStatus, message: str):
        """Update system status"""
        self._update_status_locked(status, message)
        self._notify_status_change()

    async def stop(self):
        """Stop streaming and cleanup. Signals thread first, then releases camera."""
        with self._lock:
            self.is_streaming = False
            cam = self.camera
            self.camera = None
            streaming_thread = self._streaming_thread

        thread_alive = False
        if streaming_thread and streaming_thread is not threading.current_thread():
            await asyncio.to_thread(streaming_thread.join, self._STOP_JOIN_TIMEOUT_SECONDS)
            thread_alive = streaming_thread.is_alive()
            if thread_alive:
                logger.warning(
                    "Streaming thread did not stop within %.2f seconds; releasing camera to unblock it",
                    self._STOP_JOIN_TIMEOUT_SECONDS,
                )

        if cam:
            try:
                cam.release()
            except Exception as exc:
                logger.warning("Exception releasing camera: %s", exc)

        if thread_alive:
            await asyncio.to_thread(streaming_thread.join, self._STOP_JOIN_TIMEOUT_SECONDS)
            thread_alive = streaming_thread.is_alive()
            if thread_alive:
                logger.error("Streaming thread remains blocked after camera release; retaining daemon for tracking")

        with self._lock:
            if self._streaming_thread is streaming_thread and not thread_alive:
                self._streaming_thread = None

        with self._lock:
            self._update_status_locked(SystemStatus.IDLE, "System stopped")

    def get_statistics(self, period_seconds: int = 60) -> Statistics:
        """Get statistics for the given time period (thread-safe via lock + UTC)."""
        from datetime import timezone

        cutoff_time = datetime.now(timezone.utc) - timedelta(seconds=period_seconds)

        with self._lock:
            snapshot = list(self.detection_history)

        recent_detections = [d for d in snapshot if d.timestamp.replace(tzinfo=timezone.utc) >= cutoff_time]

        class_counts = defaultdict(int)
        confidence_sums = defaultdict(float)

        for detection in recent_detections:
            class_counts[detection.class_name] += 1
            confidence_sums[detection.class_name] += detection.confidence

        avg_confidence = {}
        for cls_name, count in class_counts.items():
            avg_confidence[cls_name] = confidence_sums[cls_name] / count

        return Statistics(
            period_start=cutoff_time,
            period_end=datetime.now(timezone.utc),
            total_detections=len(recent_detections),
            class_counts=dict(class_counts),
            avg_confidence=dict(avg_confidence),
        )

    def get_available_models(self) -> list[dict[str, Any]]:
        """Get list of available models"""
        models = []

        for model_file in DETECTION_DIR.glob("*"):
            if model_file.suffix.lower() in (".pt", ".tflite"):
                is_int8 = "int8" in model_file.name.lower()
                is_tflite = model_file.suffix == ".tflite"

                try:
                    if is_tflite:
                        input_size = get_tflite_imgsz(model_file)
                    else:
                        input_size = 640
                except Exception:
                    input_size = 640

                models.append(
                    {
                        "name": model_file.name,
                        "label": model_file.name.replace("_", " ").title(),
                        "path": str(model_file),
                        "model_type": "yolo_tflite" if is_tflite else "yolo_pt",
                        "size_mb": round(model_file.stat().st_size / 1024 / 1024, 2),
                        "is_tflite_int8": is_int8,
                        "input_size": input_size,
                        "recommended": is_int8,  # INT8 models recommended for Raspberry Pi
                    }
                )

        return sorted(models, key=lambda x: x["name"])
