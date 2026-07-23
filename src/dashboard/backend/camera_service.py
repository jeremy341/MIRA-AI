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
from models import WasteClass, Detection, SystemMetrics, Statistics, SystemStatus, ModelConfig


class CameraService:
    """Main service handling camera, inference, and statistics"""

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

    async def initialize_camera(self, config):
        """Initialize camera with configuration"""
        if self.status == SystemStatus.RUNNING:
            await self.stop()

        with self._lock:
            self._update_status(SystemStatus.INITIALIZING, "Initializing camera...")

            try:
                self.camera = cv2.VideoCapture(
                    config.index,
                    cv2.CAP_DSHOW if hasattr(cv2, 'CAP_DSHOW') else 0
                )

                if not self.camera.isOpened():
                    raise RuntimeError(f"Failed to open camera index {config.index}")

                setup_camera_properties(
                    self.camera,
                    config.width,
                    config.height,
                    config.fps
                )

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
        with self._lock:
            self._update_status(SystemStatus.INITIALIZING, f"Loading model {model_name}...")

            try:
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
                    enable_tracking=config.enable_tracking,
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
            if not self.camera or not self.model:
                self._update_status(
                    SystemStatus.ERROR,
                    "Camera or model not initialized"
                )
                return False

            self.is_streaming = True
            self._update_status(SystemStatus.RUNNING, "Streaming started")

            # Start background thread
            threading.Thread(
                target=self._streaming_loop,
                daemon=True
            ).start()

            return True

    def _streaming_loop(self):
        """Main streaming and inference loop"""
        last_metrics_time = time.time()
        metrics_interval = .5  # Update metrics twice per second

        while self.is_streaming:
            try:
                if not self.camera or not self.model:
                    break

                # Skip frame if latency is too high
                if self.skip_frame:
                    self.skip_frame = False
                    continue

                # Read frame
                ret, frame = self.camera.read()
                if not ret:
                    self._disconnect_count = getattr(self, '_disconnect_count', 0) + 1
                    if self._disconnect_count > 100:  # ~1 second at 10ms sleep
                        self._update_status(SystemStatus.ERROR, "Camera disconnected")
                        self.is_streaming = False
                        break
                    time.sleep(0.01)
                    continue
                self._disconnect_count = 0

                frame_start = time.perf_counter()

                # Run inference
                if self.is_tflite_int8:
                    results = self.model.predict(
                        frame,
                        imgsz=self.img_size,
                        conf=self.model_config.conf_threshold,
                        iou=self.model_config.iou_threshold,
                        verbose=False,
                        quantize=False,
                    )
                elif self.model_config.enable_tracking:
                    results = self.model.track(
                        frame,
                        imgsz=self.img_size,
                        conf=self.model_config.conf_threshold,
                        iou=self.model_config.iou_threshold,
                        persist=True,
                        verbose=False,
                        tracker=str(BYTE_TRACK_CONFIG_PATH),
                        quantize=False,
                    )
                else:
                    results = self.model.predict(
                        frame,
                        imgsz=self.img_size,
                        conf=self.model_config.conf_threshold,
                        iou=self.model_config.iou_threshold,
                        verbose=False,
                        quantize=False,
                    )

                inference_time = (time.perf_counter() - frame_start) * 1000

                # Process detections
                detections = self._process_results(results)

                # Update performance metrics
                self._update_performance_metrics(inference_time, detections)

                # Calculate system metrics periodically
                current_time = time.time()
                if current_time - last_metrics_time >= metrics_interval:
                    metrics = self._calculate_system_metrics()
                    if self.on_metrics and self._loop:
                        asyncio.run_coroutine_threadsafe(
                            self.on_metrics(metrics),
                            self._loop
                        )
                    last_metrics_time = current_time

                # Notify about detections
                if detections and self.on_detection and self._loop:
                    asyncio.run_coroutine_threadsafe(
                        self.on_detection(detections),
                        self._loop
                    )

                # Store in history
                self._update_history(detections)

                # Control frame skipping based on latency
                if self.model_config and self.latency_history:
                    avg_latency = sum(self.latency_history) / len(self.latency_history)
                    self.skip_frame = avg_latency > self.model_config.target_latency_ms

            except Exception as e:
                print(f"Streaming error: {e}")
                time.sleep(0.1)

    def _process_results(self, results):
        """Process YOLO results into Detection objects"""
        detections = []

        if not results or len(results) == 0:
            return detections

        boxes = results[0].boxes
        if boxes is None or len(boxes) == 0:
            return detections

        for box in boxes:
            conf = float(box.conf[0])
            if conf < self.model_config.conf_threshold:
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

            detection = Detection(
                class_name=waste_class,
                confidence=conf,
                bbox=[x1, y1, x2, y2],
                track_id=track_id
            )

            detections.append(detection)

        return detections

    def _class_id_to_name(self, class_id: int) -> str:
        """Map class ID to name"""
        return CLASS_NAMES[class_id] if class_id < len(CLASS_NAMES) else "unknown"

    def _update_performance_metrics(self, inference_time: float, detections: list[Detection]):
        """Update performance tracking metrics"""
        self.latency_history.append(inference_time)

        # Update frame times for FPS calculation
        self.frame_times.append(time.perf_counter())
        if len(self.frame_times) > 1:
            # Keep only recent times for accurate FPS
            while len(self.frame_times) > 1 and \
                  self.frame_times[-1] - self.frame_times[0] > 2.0:
                self.frame_times.popleft()

    def _calculate_system_metrics(self) -> SystemMetrics:
        """Calculate current system metrics"""
        # Calculate FPS
        fps = 0.0
        if len(self.frame_times) > 1:
            time_span = self.frame_times[-1] - self.frame_times[0]
            if time_span > 0:
                fps = (len(self.frame_times) - 1) / time_span

        # Calculate latency
        inference_latency = 0.0
        avg_latency = 0.0
        if self.latency_history:
            inference_latency = self.latency_history[-1]
            avg_latency = sum(self.latency_history) / len(self.latency_history)

        # Get system resources
        cpu_percent = psutil.cpu_percent()
        memory_percent = psutil.virtual_memory().percent

        # Try to get temperature (Raspberry Pi specific)
        temperature = None
        try:
            with open("/sys/class/thermal/thermal_zone0/temp") as f:
                temp_millic = int(f.read().strip())
                temperature = temp_millic / 1000.0
        except Exception:
            pass

        # Calculate detections per second
        detections_per_second = 0.0
        if len(self.detection_history) >= 2:
            recent_detections = list(self.detection_history)[-10:]
            if len(recent_detections) >= 2:
                time_diff = (recent_detections[-1].timestamp -
                           recent_detections[0].timestamp).total_seconds()
                if time_diff > 0:
                    detections_per_second = len(recent_detections) / time_diff

        return SystemMetrics(
            fps=fps,
            inference_latency_ms=inference_latency,
            avg_latency_ms=avg_latency,
            cpu_percent=cpu_percent,
            memory_percent=memory_percent,
            temperature_celsius=temperature,
            detections_per_second=detections_per_second,
            skip_frames=self.skip_frame
        )

    def _update_history(self, detections: list[Detection]):
        """Update detection history"""
        for detection in detections:
            self.detection_history.append(detection)
            self.class_history[detection.class_name].append(detection)

    def _update_status(self, status: SystemStatus, message: str):
        """Update system status"""
        self.status = status
        self.status_message = message

        if self.on_status_change and self._loop:
            asyncio.run_coroutine_threadsafe(
                self.on_status_change(status, message),
                self._loop
            )

    async def stop(self):
        """Stop streaming and cleanup"""
        with self._lock:
            self.is_streaming = False

            if self.camera:
                self.camera.release()
                self.camera = None

            self._update_status(SystemStatus.IDLE, "System stopped")

    def get_statistics(self, period_seconds: int = 60) -> Statistics:
        """Get statistics for the given time period"""
        cutoff_time = datetime.now() - timedelta(seconds=period_seconds)

        recent_detections = [
            d for d in self.detection_history
            if d.timestamp >= cutoff_time
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
            period_end=datetime.now(),
            total_detections=len(recent_detections),
            class_counts=dict(class_counts),
            avg_confidence=dict(avg_confidence)
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

                models.append({
                    "name": model_file.name,
                    "label": model_file.name.replace("_", " ").title(),
                    "path": str(model_file),
                    "model_type": "yolo_tflite" if is_tflite else "yolo_pt",
                    "size_mb": round(model_file.stat().st_size / 1024 / 1024, 2),
                    "is_tflite_int8": is_int8,
                    "input_size": input_size,
                    "recommended": is_int8  # INT8 models recommended for Raspberry Pi
                })

        return sorted(models, key=lambda x: x["name"])
