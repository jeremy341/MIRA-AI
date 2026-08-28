# Camera service managing inference pipeline
import asyncio
import threading
import time
from typing import Any
from collections import deque, defaultdict
from datetime import datetime, timedelta, timezone
import psutil

from ultralytics import YOLO
from src.config import CLASS_NAMES, DETECTION_DIR, BYTE_TRACK_CONFIG_PATH, get_tflite_imgsz
from src.hardware import USBCamera
from src.logger import get_logger
from src.dashboard.backend.models import WasteClass, Detection, SystemMetrics, Statistics, SystemStatus, ModelConfig

logger = get_logger(__name__)


class CameraService:
    _STOP_JOIN_TIMEOUT_SECONDS = 1.0

    def __init__(self, loop=None):
        self._lock = threading.Lock()
        self._operation_lock = asyncio.Lock()
        self.status = SystemStatus.IDLE
        self.status_message = "System ready"

        self._loop = loop

        self.camera = None
        self.camera_config = None
        self.is_streaming = False
        self._disconnect_count = 0
        self._streaming_thread = None

        self.model = None
        self.model_config = None
        self.is_tflite_int8 = False
        self.img_size = 640

        self.detection_history = deque(maxlen=1000)
        self.class_history = defaultdict(list)
        self.metrics_history = deque(maxlen=100)

        self.latency_history = deque(maxlen=30)
        self.frame_times = deque(maxlen=30)
        self.skip_frame = False

        self.on_detection = None
        self.on_metrics = None
        self.on_status_change = None
        self.on_frame = None

    def _update_status_locked(self, status: SystemStatus, message: str):
        self.status = status
        self.status_message = message

    def _notify_status_change(self):
        with self._lock:
            callback = self.on_status_change
            loop = self._loop
            status = self.status
            message = self.status_message
        if callback and loop:
            notification = self._run_status_callback(callback, status, message)
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
        async with self._operation_lock:
            return await self._initialize_camera(config)

    async def _initialize_camera(self, config):
        if self.get_status_snapshot()["streaming"]:
            self._update_status(SystemStatus.ERROR, "Stop the stream before changing camera settings")
            return False

        self._update_status(SystemStatus.INITIALIZING, "Initializing camera...")

        try:
            camera = await asyncio.to_thread(self._open_camera, config)
        except Exception as exc:
            self._update_status(SystemStatus.ERROR, f"Camera error: {exc}")
            return False

        with self._lock:
            previous_camera = self.camera
            self.camera = camera
            self.camera_config = config

        if previous_camera is not None and previous_camera is not camera:
            try:
                previous_camera.release()
            except Exception as exc:
                logger.warning("Exception releasing previous camera: %s", exc)

        self._update_status(SystemStatus.IDLE, "Camera ready")
        return True

    @staticmethod
    def _open_camera(config):
        return USBCamera(
            config.index,
            config.width,
            config.height,
            config.fps,
            config.autofocus,
            config.auto_exposure,
        )

    async def load_model(self, model_name: str, config):
        async with self._operation_lock:
            return await self._load_model_for_service(model_name, config)

    async def _load_model_for_service(self, model_name: str, config):
        with self._lock:
            was_streaming = self.is_streaming
        if was_streaming:
            self._update_status(SystemStatus.ERROR, "Stop the stream before changing models")
            return False

        self._update_status(SystemStatus.INITIALIZING, f"Loading model {model_name}...")

        try:
            model, model_config, is_tflite_int8, img_size = await asyncio.to_thread(
                self._load_model, model_name, config
            )
        except Exception as exc:
            self._update_status(SystemStatus.ERROR, f"Model load error: {exc}")
            return False

        with self._lock:
            self.model = model
            self.model_config = model_config
            self.is_tflite_int8 = is_tflite_int8
            self.img_size = img_size

        self._update_status(SystemStatus.IDLE, f"Model {model_name} loaded")
        return True

    @staticmethod
    def _load_model(model_name: str, config):
        if any(sep in model_name for sep in ("/", "\\", "..")):
            raise ValueError(f"Invalid model name: {model_name}")

        model_path = (DETECTION_DIR / model_name).resolve()
        detection_root = DETECTION_DIR.resolve()
        if model_path.parent != detection_root or not model_path.exists():
            raise FileNotFoundError(f"Model not found: {model_name}")

        is_tflite = model_path.suffix.lower() == ".tflite"
        is_tflite_int8 = is_tflite and "int8" in model_name.lower()
        img_size = get_tflite_imgsz(model_path) if is_tflite else 640
        model = YOLO(str(model_path), task="detect")
        model_config = ModelConfig(
            name=config.name,
            conf_threshold=min(config.conf_threshold, 0.25) if is_tflite_int8 else config.conf_threshold,
            reject_threshold=config.reject_threshold,
            iou_threshold=config.iou_threshold,
            enable_tracking=config.enable_tracking if not is_tflite else False,
            target_latency_ms=config.target_latency_ms,
        )
        return model, model_config, is_tflite_int8, img_size

    async def start_streaming(self):
        with self._lock:
            if self.is_streaming:
                return True

            if self._streaming_thread and self._streaming_thread.is_alive():
                self._update_status_locked(SystemStatus.ERROR, "Previous streaming thread is still shutting down")
                should_start = False
            elif not self.camera or not self.model:
                self._update_status_locked(SystemStatus.ERROR, "Camera or model not initialized")
                should_start = False
            else:
                self.is_streaming = True
                self._update_status_locked(SystemStatus.RUNNING, "Streaming started")
                self._streaming_thread = threading.Thread(target=self._streaming_loop, daemon=True)
                self._streaming_thread.start()
                should_start = True

        self._notify_status_change()
        return should_start

    def _streaming_loop(self):
        last_metrics_time = time.time()
        metrics_interval = 0.5
        consecutive_read_failures = 0

        with self._lock:
            local_conf = self.model_config.conf_threshold if self.model_config else 0.5
            local_reject = self.model_config.reject_threshold if self.model_config else local_conf
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
                    consecutive_read_failures += 1
                    if consecutive_read_failures >= 30:
                        self._update_status(SystemStatus.ERROR, "Camera disconnected")
                        with self._lock:
                            self.is_streaming = False
                        break
                    time.sleep(0.01)
                    continue
                consecutive_read_failures = 0
                if hasattr(cam, "is_alive") and not cam.is_alive():
                    self._update_status(SystemStatus.ERROR, "Camera stream is frozen")
                    with self._lock:
                        self.is_streaming = False
                    break

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
                detections = self._process_results(results, local_conf, local_reject)
                self._update_performance_metrics(inference_time, results)

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
                    if not results:
                        self.skip_frame = False
                    elif self.latency_history:
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

    def _process_results(self, results, conf_threshold: float = 0.5, reject_threshold: float | None = None):
        detections = []
        effective_threshold = max(conf_threshold, reject_threshold or conf_threshold)

        if not results or len(results) == 0:
            return detections

        boxes = results[0].boxes
        if boxes is None or len(boxes) == 0:
            return detections

        for box in boxes:
            if box.conf is None or len(box.conf) == 0 or box.cls is None or len(box.cls) == 0:
                continue
            conf = float(box.conf[0])
            if conf < effective_threshold:
                continue

            cls_id = int(box.cls[0])
            class_name = self._class_id_to_name(cls_id)

            # Convert to WasteClass enum
            try:
                waste_class = WasteClass(class_name)
            except ValueError:
                continue  # Skip unknown classes

            x1, y1, x2, y2 = box.xyxy[0].cpu().numpy().astype(int).tolist()
            track_id = int(box.id[0]) if box.id is not None and len(box.id) > 0 else None

            detection = Detection(class_name=waste_class, confidence=conf, bbox=[x1, y1, x2, y2], track_id=track_id)

            detections.append(detection)

        return detections

    def _class_id_to_name(self, class_id: int) -> str:
        from src.visualize import class_id_to_name

        return class_id_to_name(class_id, CLASS_NAMES)

    def _update_performance_metrics(self, inference_time: float, results=None):
        with self._lock:
            latency = inference_time
            if results:
                speed = getattr(results[0], "speed", None) or {}
                if isinstance(speed, dict):
                    latency = speed.get("inference", inference_time)
            self.latency_history.append(latency)

            # Update frame times for FPS calculation
            self.frame_times.append(time.perf_counter())
            if len(self.frame_times) > 1:
                # Keep only recent times for accurate FPS
                while len(self.frame_times) > 1 and self.frame_times[-1] - self.frame_times[0] > 2.0:
                    self.frame_times.popleft()

    def _calculate_system_metrics(self) -> SystemMetrics:
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
        with self._lock:
            for detection in detections:
                if self.detection_history:
                    last = self.detection_history[-1]
                    if last.class_name == detection.class_name and last.bbox == detection.bbox:
                        continue
                self.detection_history.append(detection)
                self.class_history[detection.class_name].append(detection)

    def _update_status(self, status: SystemStatus, message: str):
        with self._lock:
            self._update_status_locked(status, message)
        self._notify_status_change()

    def get_status_snapshot(self) -> dict:
        with self._lock:
            return {
                "status": self.status.value,
                "message": self.status_message,
                "camera_initialized": self.camera is not None,
                "model_loaded": self.model is not None,
                "streaming": self.is_streaming,
            }

    async def stop_streaming(self, release_camera: bool = False) -> bool:
        with self._lock:
            self.is_streaming = False
            cam = self.camera
            streaming_thread = self._streaming_thread

        thread_alive = False
        camera_released = False
        if streaming_thread and streaming_thread is not threading.current_thread():
            await asyncio.to_thread(streaming_thread.join, self._STOP_JOIN_TIMEOUT_SECONDS)
            thread_alive = streaming_thread.is_alive()
            if thread_alive:
                logger.warning(
                    "Streaming thread did not stop within %.2f seconds; releasing camera to unblock it",
                    self._STOP_JOIN_TIMEOUT_SECONDS,
                )

        if thread_alive and cam:
            with self._lock:
                self.camera = None
            try:
                cam.release()
                camera_released = True
            except Exception as exc:
                logger.warning("Exception releasing camera: %s", exc)

        if thread_alive:
            await asyncio.to_thread(streaming_thread.join, self._STOP_JOIN_TIMEOUT_SECONDS)
            thread_alive = streaming_thread.is_alive()
            if thread_alive:
                logger.error("Streaming thread remains blocked after camera release; retaining daemon for tracking")

        if release_camera and cam and not camera_released:
            with self._lock:
                self.camera = None
            try:
                cam.release()
                camera_released = True
            except Exception as exc:
                logger.warning("Exception releasing camera: %s", exc)

        with self._lock:
            if self._streaming_thread is streaming_thread and not thread_alive:
                self._streaming_thread = None

        with self._lock:
            final_status = SystemStatus.ERROR if thread_alive else SystemStatus.IDLE
            final_message = "Streaming worker did not stop" if thread_alive else "System stopped"
            self._update_status_locked(final_status, final_message)
        self._notify_status_change()
        return not thread_alive

    async def stop(self):
        return await self.stop_streaming(release_camera=False)

    async def shutdown(self):
        return await self.stop_streaming(release_camera=True)

    def get_statistics(self, period_seconds: int = 60) -> Statistics:
        cutoff_time = datetime.now(timezone.utc) - timedelta(seconds=period_seconds)

        with self._lock:
            snapshot = list(self.detection_history)

        recent_detections = [
            d
            for d in snapshot
            if (d.timestamp if d.timestamp.tzinfo else d.timestamp.replace(tzinfo=timezone.utc)) >= cutoff_time
        ]

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
        models = []

        for model_file in DETECTION_DIR.glob("*"):
            if model_file.suffix.lower() in (".pt", ".tflite"):
                is_int8 = "int8" in model_file.name.lower()
                is_tflite = model_file.suffix.lower() == ".tflite"

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
