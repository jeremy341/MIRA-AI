"""
WebSocket handlers for real-time video streaming
"""

import asyncio
import base64
import logging
import threading
from datetime import datetime
import cv2
import numpy as np
from starlette.websockets import WebSocketDisconnect

from models import Detection, SystemMetrics

logger = logging.getLogger(__name__)


class WebSocketHandler:
    """Handle WebSocket connections for video streaming"""

    def __init__(self, camera_service):
        self.camera_service = camera_service
        self._lock = threading.Lock()
        self.connections = set()
        self.frame_buffer = None
        self.latest_detections = []
        self._frame_id = 0
        # A live view needs the newest frame, not a backlog of old frames.
        self._broadcast_queue = asyncio.Queue(maxsize=32)
        self._broadcast_task = None
        self._loop = None  # Will be set by main.py

        camera_service.on_detection = self._on_detections
        camera_service.on_metrics = self._on_metrics
        camera_service.on_status_change = self._on_status_change
        camera_service.on_frame = self.update_frame

    async def start(self):
        """Start the background broadcast task"""
        self._broadcast_task = asyncio.create_task(self._broadcast_consumer())

    async def stop(self):
        """Stop the background broadcast task"""
        if self._broadcast_task:
            self._broadcast_task.cancel()
            try:
                await self._broadcast_task
            except asyncio.CancelledError:
                pass

    async def _broadcast_consumer(self):
        """Consume messages from the broadcast queue and send to all connections"""
        while True:
            try:
                message = await self._broadcast_queue.get()
                if not self.connections:
                    continue

                connections = list(self.connections)
                tasks = [websocket.send_json(message) for websocket in connections]

                if tasks:
                    results = await asyncio.gather(*tasks, return_exceptions=True)
                    for websocket, result in zip(connections, results, strict=True):
                        if isinstance(result, Exception):
                            self.connections.discard(websocket)
            except asyncio.CancelledError:
                break
            except Exception:
                logger.exception("Broadcast consumer failed")

    def _enqueue_message(self, message: dict):
        """Queue an event without allowing frames to build an unbounded backlog."""
        message_type = message.get("type")
        if self._broadcast_queue.full():
            if message_type == "frame":
                # Remove an old frame so the newest frame can be shown.
                retained = []
                while self._broadcast_queue.full():
                    try:
                        old = self._broadcast_queue.get_nowait()
                    except asyncio.QueueEmpty:
                        break
                    if old.get("type") != "frame":
                        retained.append(old)
                for old in retained:
                    try:
                        self._broadcast_queue.put_nowait(old)
                    except asyncio.QueueFull:
                        break
            else:
                # Preserve control/status events by making room only from frames.
                retained = []
                while self._broadcast_queue.full():
                    try:
                        old = self._broadcast_queue.get_nowait()
                    except asyncio.QueueEmpty:
                        break
                    if old.get("type") != "frame":
                        retained.append(old)
                for old in retained:
                    try:
                        self._broadcast_queue.put_nowait(old)
                    except asyncio.QueueFull:
                        break

        try:
            self._broadcast_queue.put_nowait(message)
        except asyncio.QueueFull:
            logger.warning("Dropping full dashboard event: %s", message_type)

    def _publish_from_thread(self, message: dict):
        """Publish an event from the camera thread onto the FastAPI loop."""
        if self._loop and self._loop.is_running():
            self._loop.call_soon_threadsafe(self._enqueue_message, message)
        else:
            self._enqueue_message(message)

    async def handle_video_stream(self, websocket):
        """Handle video streaming WebSocket connection"""
        self.connections.add(websocket)
        try:
            await websocket.send_json({"type": "status", "status": "connected", "message": "Video stream connected"})

            with self._lock:
                initial_frame = self.frame_buffer.copy() if self.frame_buffer is not None else None
                initial_detections = list(self.latest_detections)
                initial_frame_id = self._frame_id
            if initial_frame is not None:
                await self._send_frame(websocket, initial_frame, initial_detections, initial_frame_id)

            async for message in websocket.iter_text():
                if message == "ping":
                    await websocket.send_text("pong")

        except WebSocketDisconnect:
            logger.info("Video WebSocket disconnected")
        except Exception:
            logger.exception("Video WebSocket handler failed")
        finally:
            self.connections.discard(websocket)

    async def _on_detections(self, detections: list[Detection]):
        """Callback when new detections are available"""
        with self._lock:
            self.latest_detections = list(detections)

    async def _on_metrics(self, metrics: SystemMetrics):
        """Callback when system metrics are updated"""
        message = {
            "type": "metrics",
            "fps": round(metrics.fps, 1),
            "inference_latency_ms": round(metrics.inference_latency_ms, 1),
            "avg_latency_ms": round(metrics.avg_latency_ms, 1),
            "cpu_percent": round(metrics.cpu_percent, 1),
            "memory_percent": round(metrics.memory_percent, 1),
            "temperature_celsius": round(metrics.temperature_celsius, 1) if metrics.temperature_celsius else None,
            "detections_per_second": round(metrics.detections_per_second, 1),
            "skip_frames": metrics.skip_frames,
            "timestamp": metrics.timestamp.isoformat(),
        }

        self._enqueue_message(message)

    async def _on_status_change(self, status, message):
        """Callback when system status changes"""
        self._enqueue_message(
            {"type": "status", "status": status.value, "message": message, "timestamp": datetime.now().isoformat()}
        )

    def update_frame(self, frame: np.ndarray, detections: list[Detection] | None = None):
        """Publish one frame together with the detections from that frame."""
        if frame is None:
            return

        to_store = frame.copy()
        detections = list(detections or [])
        serialized_detections = [
            {
                "class": det.class_name.value,
                "confidence": det.confidence,
                "bbox": det.bbox,
                "track_id": det.track_id,
                "timestamp": det.timestamp.isoformat(),
            }
            for det in detections
        ]

        with self._lock:
            self.frame_buffer = to_store
            self.latest_detections = detections
            self._frame_id += 1
            frame_id = self._frame_id

        success, buffer = cv2.imencode(".jpg", to_store, [cv2.IMWRITE_JPEG_QUALITY, 85])
        if not success:
            return

        frame_data = base64.b64encode(buffer).decode("utf-8")

        message = {
            "type": "frame",
            "frame_id": frame_id,
            "frame": frame_data,
            "detections": serialized_detections,
            "timestamp": datetime.now().isoformat(),
        }

        self._publish_from_thread(message)

    async def _send_frame(self, websocket, frame: np.ndarray, detections=None, frame_id=0):
        """Send a single frame to a websocket"""
        if frame is None:
            return

        _, buffer = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 85])

        frame_data = base64.b64encode(buffer).decode("utf-8")

        await websocket.send_json(
            {
                "type": "frame",
                "frame_id": frame_id,
                "frame": frame_data,
                "detections": [
                    {
                        "class": det.class_name.value,
                        "confidence": det.confidence,
                        "bbox": det.bbox,
                        "track_id": det.track_id,
                        "timestamp": det.timestamp.isoformat(),
                    }
                    for det in (detections or [])
                ],
                "timestamp": datetime.now().isoformat(),
            }
        )
