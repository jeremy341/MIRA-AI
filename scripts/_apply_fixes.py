import sys
sys.path.insert(0, r'C:\Users\jerem\Documents\JUGEND~1\MIRA-AI\src')

# Fix camera_service.py
with open(r'C:\Users\jerem\Documents\JUGEND~1\MIRA-AI\src\dashboard\backend\camera_service.py', encoding='utf-8') as f:
    c = f.read()

# 1. Add logger import
c = c.replace(
    'from config import CLASS_NAMES, DETECTION_DIR, BYTE_TRACK_CONFIG_PATH, get_tflite_imgsz, setup_camera_properties\nfrom models import WasteClass, Detection, SystemMetrics, Statistics, SystemStatus, ModelConfig',
    'from config import CLASS_NAMES, DETECTION_DIR, BYTE_TRACK_CONFIG_PATH, get_tflite_imgsz, setup_camera_properties\nfrom logger import get_logger\nfrom models import WasteClass, Detection, SystemMetrics, Statistics, SystemStatus, ModelConfig\n\nlogger = get_logger(__name__)'
)

# 2. Split _update_status into locked + public
c = c.replace(
    '    def _update_status(self, status: SystemStatus, message: str):\n        """Update system status"""\n        self.status = status\n        self.status_message = message\n\n        if self.on_status_change and self._loop:\n            asyncio.run_coroutine_threadsafe(self.on_status_change(status, message), self._loop)',
    '    def _update_status_locked(self, status: SystemStatus, message: str):\n        """Update system status (caller MUST hold self._lock)."""\n        self.status = status\n        self.status_message = message\n        self._notify_status_change(status, message)\n\n    def _update_status(self, status: SystemStatus, message: str):\n        """Update system status (thread-safe, acquires lock)."""\n        with self._lock:\n            self.status = status\n            self.status_message = message\n        self._notify_status_change(status, message)\n\n    def _notify_status_change(self, status: SystemStatus, message: str):\n        """Fire status-change callback (lock-free, call from any thread)."""\n        if self.on_status_change and self._loop:\n            asyncio.run_coroutine_threadsafe(self.on_status_change(status, message), self._loop)'
)

# 3. Replace start_streaming + _streaming_loop
start = c.index('    async def start_streaming')
end = c.index('    def _process_results')
old_section = c[start:end]
new_section = '''    async def start_streaming(self):
        """Start the inference streaming loop"""
        with self._lock:
            if self.is_streaming:
                return True

            if not self.camera or not self.model:
                self._update_status_locked(SystemStatus.ERROR, "Camera or model not initialized")
                return False

            self.is_streaming = True
            self._update_status_locked(SystemStatus.RUNNING, "Streaming started")

            threading.Thread(target=self._streaming_loop, daemon=True).start()

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
                        frame, imgsz=local_img_size, conf=local_conf, iou=local_iou, verbose=False,
                    )
                elif local_enable_tracking:
                    results = mod.track(
                        frame, imgsz=local_img_size, conf=local_conf, iou=local_iou,
                        persist=True, verbose=False, tracker=str(BYTE_TRACK_CONFIG_PATH),
                    )
                else:
                    results = mod.predict(
                        frame, imgsz=local_img_size, conf=local_conf, iou=local_iou, verbose=False,
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

                if self.on_frame:
                    try:
                        self.on_frame(frame, detections)
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

'''
c = c[:start] + new_section + c[end:]

# 4. Fix _process_results signature
c = c.replace(
    '    def _process_results(self, results):',
    '    def _process_results(self, results, conf_threshold: float = 0.5):'
)
c = c.replace(
    '            if conf < self.model_config.conf_threshold:',
    '            if conf < conf_threshold:'
)

# 5. Fix _update_performance_metrics
c = c.replace(
    '    def _update_performance_metrics(self, inference_time: float, detections: list[Detection]):\n        """Update performance tracking metrics"""\n        self.latency_history.append(inference_time)\n\n        # Update frame times for FPS calculation\n        self.frame_times.append(time.perf_counter())\n        if len(self.frame_times) > 1:\n            # Keep only recent times for accurate FPS\n            while len(self.frame_times) > 1 and self.frame_times[-1] - self.frame_times[0] > 2.0:\n                self.frame_times.popleft()',
    '    def _update_performance_metrics(self, inference_time: float):\n        """Update performance tracking metrics (thread-safe via lock)."""\n        with self._lock:\n            self.latency_history.append(inference_time)\n            self.frame_times.append(time.perf_counter())\n            while len(self.frame_times) > 1 and self.frame_times[-1] - self.frame_times[0] > 2.0:\n                self.frame_times.popleft()'
)

# 6. Fix _calculate_system_metrics
start = c.index('    def _calculate_system_metrics')
end = c.index('    def _update_history')
old_calc = c[start:end]
new_calc = '''    def _calculate_system_metrics(self) -> SystemMetrics:
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

'''
c = c[:start] + new_calc + c[end:]

# 7. Fix _update_history with dedup
c = c.replace(
    '    def _update_history(self, detections: list[Detection]):\n        """Update detection history"""\n        for detection in detections:\n            self.detection_history.append(detection)\n            if detection.class_name not in self.class_history:\n                self.class_history[detection.class_name] = []\n            self.class_history[detection.class_name].append(detection)\n            if len(self.class_history[detection.class_name]) > 200:\n                self.class_history[detection.class_name] = self.class_history[detection.class_name][-200:]',
    '    def _update_history(self, detections: list[Detection]):\n        """Update detection history with deduplication (thread-safe via lock)."""\n        with self._lock:\n            for detection in detections:\n                if self.detection_history:\n                    last = self.detection_history[-1]\n                    if (last.class_name == detection.class_name\n                            and last.bbox == detection.bbox\n                            and abs((detection.timestamp - last.timestamp).total_seconds()) < 0.5):\n                        continue\n                self.detection_history.append(detection)\n                if detection.class_name not in self.class_history:\n                    self.class_history[detection.class_name] = []\n                self.class_history[detection.class_name].append(detection)\n                if len(self.class_history[detection.class_name]) > 200:\n                    self.class_history[detection.class_name] = self.class_history[detection.class_name][-200:]'
)

# 8. Fix stop()
start = c.index('    async def stop(')
end = c.index('    def get_statistics')
old_stop = c[start:end]
new_stop = '''    async def stop(self):
        """Stop streaming and cleanup. Signals thread first, then releases camera."""
        with self._lock:
            self.is_streaming = False
            cam = self.camera
            self.camera = None

        if cam:
            try:
                cam.release()
            except Exception as exc:
                logger.warning("Exception releasing camera: %s", exc)

        with self._lock:
            self._update_status_locked(SystemStatus.IDLE, "System stopped")

'''
c = c[:start] + new_stop + c[end:]

# 9. Fix get_statistics
start = c.index('    def get_statistics')
end = c.index('    def get_available_models')
old_stats = c[start:end]
new_stats = '''    def get_statistics(self, period_seconds: int = 60) -> Statistics:
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

'''
c = c[:start] + new_stats + c[end:]

# 10. Strengthen path validation in load_model
c = c.replace(
    '            model_path = (DETECTION_DIR / model_name).resolve()\n            try:\n                model_path.relative_to(DETECTION_DIR.resolve())\n            except ValueError:\n                raise ValueError(f"Model path escapes detection directory: {model_name}") from None',
    '            if "/" in model_name or "\\\\" in model_name or ".." in model_name:\n                raise ValueError(f"Invalid model name (path traversal blocked): {model_name}")\n\n            model_path = (DETECTION_DIR / model_name).resolve()\n            try:\n                model_path.relative_to(DETECTION_DIR.resolve())\n            except ValueError:\n                raise ValueError(f"Model path escapes detection directory: {model_name}") from None'
)

with open(r'C:\Users\jerem\Documents\JUGEND~1\MIRA-AI\src\dashboard\backend\camera_service.py', 'w', encoding='utf-8') as f:
    f.write(c)
print(f'camera_service.py: {len(c)} bytes')

# Fix websocket_handler.py
with open(r'C:\Users\jerem\Documents\JUGEND~1\MIRA-AI\src\dashboard\backend\websocket_handler.py', encoding='utf-8') as f:
    w = f.read()

w = w.replace(
    'import asyncio\nimport base64\nfrom datetime import datetime\nimport cv2\nimport numpy as np\nfrom starlette.websockets import WebSocketDisconnect',
    'import asyncio\nimport base64\nimport threading\nfrom datetime import datetime\nimport cv2\nimport numpy as np\nfrom starlette.websockets import WebSocketDisconnect'
)
w = w.replace(
    '    def __init__(self, camera_service):\n        self.camera_service = camera_service\n        self.connections = set()',
    '    def __init__(self, camera_service):\n        self.camera_service = camera_service\n        self._lock = threading.Lock()\n        self.connections = set()'
)
w = w.replace(
    '        self.latest_detections = detections',
    '        with self._lock:\n            self.latest_detections = list(detections)'
)
w = w.replace(
    '        # Store raw frame for new connections (no annotation)\n        self.frame_buffer = frame',
    '        with self._lock:\n            self.frame_buffer = frame.copy() if frame is not None else None'
)
w = w.replace(
    '            # Send initial frame if available\n            if self.frame_buffer is not None:\n                await self._send_frame(websocket, self.frame_buffer)',
    '            with self._lock:\n                initial_frame = self.frame_buffer.copy() if self.frame_buffer is not None else None\n            if initial_frame is not None:\n                await self._send_frame(websocket, initial_frame)'
)
w = w.replace(
    '        _, buffer = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 85])\n\n        # Encode as base64\n        frame_data = base64.b64encode(buffer).decode("utf-8")',
    '        success, buffer = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 85])\n        if not success:\n            return\n\n        frame_data = base64.b64encode(buffer).decode("utf-8")'
)
w = w.replace(
    '        _, buffer = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 85])\n\n        frame_data = base64.b64encode(buffer).decode("utf-8")\n\n        await websocket.send_json({"type": "frame", "frame": frame_data, "timestamp": datetime.now().isoformat()})',
    '        success, buffer = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 85])\n        if not success:\n            return\n\n        frame_data = base64.b64encode(buffer).decode("utf-8")\n\n        await websocket.send_json({"type": "frame", "frame": frame_data, "timestamp": datetime.now().isoformat()})'
)

with open(r'C:\Users\jerem\Documents\JUGEND~1\MIRA-AI\src\dashboard\backend\websocket_handler.py', 'w', encoding='utf-8') as f:
    f.write(w)
print(f'websocket_handler.py: {len(w)} bytes')

# Fix models.py
with open(r'C:\Users\jerem\Documents\JUGEND~1\MIRA-AI\src\dashboard\backend\models.py', encoding='utf-8') as f:
    m = f.read()

m = m.replace(
    'class CameraConfig(BaseModel):\n    """Camera configuration"""\n    index: int = 0\n    width: int = 640\n    height: int = 360\n    fps: int = 30\n    autofocus: bool = False\n    auto_exposure: bool = True\n\n\nclass ModelConfig(BaseModel):\n    """Model inference configuration"""\n    name: str\n    conf_threshold: float = 0.5\n    reject_threshold: float = 0.55\n    iou_threshold: float = 0.45\n    enable_tracking: bool = True\n    target_latency_ms: int = 50',
    'class CameraConfig(BaseModel):\n    """Camera configuration"""\n    index: int = Field(default=0, ge=0)\n    width: int = Field(default=640, ge=64, le=3840)\n    height: int = Field(default=360, ge=64, le=2160)\n    fps: int = Field(default=30, ge=1, le=120)\n    autofocus: bool = False\n    auto_exposure: bool = True\n\n\nclass ModelConfig(BaseModel):\n    """Model inference configuration"""\n    name: str\n    conf_threshold: float = Field(default=0.5, ge=0.01, le=1.0)\n    reject_threshold: float = Field(default=0.55, ge=0.0, le=1.0)\n    iou_threshold: float = Field(default=0.45, ge=0.01, le=1.0)\n    enable_tracking: bool = True\n    target_latency_ms: int = Field(default=50, ge=10, le=5000)'
)

with open(r'C:\Users\jerem\Documents\JUGEND~1\MIRA-AI\src\dashboard\backend\models.py', 'w', encoding='utf-8') as f:
    f.write(m)
print(f'models.py: {len(m)} bytes')

print('\\nAll fixes applied successfully!')
