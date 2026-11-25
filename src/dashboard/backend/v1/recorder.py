"""Asynchronous SQLite recorder for live camera sessions."""

from __future__ import annotations

import inspect
import logging
import queue
import threading
import time
from datetime import datetime, timezone
from typing import Any

from .state import get_db, get_events

logger = logging.getLogger(__name__)


class SessionRecorder:
    """Queue camera callbacks and batch their writes away from the inference thread."""

    FLUSH_INTERVAL_SECONDS = 0.5
    DETECTION_EVENT_INTERVAL_SECONDS = 0.2

    def __init__(self) -> None:
        self._queue: queue.Queue[tuple[str, Any]] = queue.Queue()
        self._lock = threading.RLock()
        self._active_session_id: str | None = None
        self._frame_index = 0
        self._camera_service: Any | None = None
        self._previous_detection_callback = None
        self._previous_metrics_callback = None
        self._worker: threading.Thread | None = None
        self._pending_detections: list[tuple[Any, ...]] = []
        self._pending_metrics: list[tuple[Any, ...]] = []
        self._pending_event_detections: list[dict[str, Any]] = []
        self._last_detection_event_at = 0.0

    @property
    def active_session_id(self) -> str | None:
        with self._lock:
            return self._active_session_id

    def attach(self, camera_service: Any) -> None:
        with self._lock:
            if self._camera_service is camera_service:
                self._ensure_worker_locked()
                return
            self._detach_locked()
            self._camera_service = camera_service
            self._previous_detection_callback = camera_service.on_detection
            self._previous_metrics_callback = camera_service.on_metrics
            previous_detection_callback = self._previous_detection_callback
            previous_metrics_callback = self._previous_metrics_callback

            async def detection_callback(detections: list[Any]) -> None:
                try:
                    await self._call_previous(previous_detection_callback, detections)
                finally:
                    self._queue_detections(detections)

            async def metrics_callback(metrics: Any) -> None:
                try:
                    await self._call_previous(previous_metrics_callback, metrics)
                finally:
                    self._queue_metrics(metrics)

            self._detection_callback = detection_callback
            self._metrics_callback = metrics_callback
            camera_service.on_detection = detection_callback
            camera_service.on_metrics = metrics_callback
            self._ensure_worker_locked()

    @staticmethod
    async def _call_previous(callback: Any, value: Any) -> None:
        if callback is None:
            return
        result = callback(value)
        if inspect.isawaitable(result):
            await result

    def start_session(self, session: dict[str, Any]) -> None:
        session_id = session["id"]
        with self._lock:
            self._ensure_worker_locked()
            self._active_session_id = session_id
            self._frame_index = 0
        get_events().publish(
            "session_started",
            {
                "id": session_id,
                "name": session["name"],
                "source": session["source"],
                "model_name": session.get("model_name"),
                "started_at": session.get("started_at"),
            },
        )

    def stop_session(self, session_id: str, *, ended_at: str | None = None) -> bool:
        flush_signal = threading.Event()
        with self._lock:
            if self._active_session_id != session_id:
                return False
            self._active_session_id = None
            self._queue.put_nowait(("flush", flush_signal))
        flush_signal.wait(5.0)
        get_events().publish("session_stopped", {"id": session_id, "ended_at": ended_at})
        return True

    def flush(self, timeout: float = 5.0) -> bool:
        signal = threading.Event()
        self._queue.put_nowait(("flush", signal))
        return signal.wait(timeout)

    def shutdown(self) -> None:
        with self._lock:
            worker = self._worker
            if worker is None:
                self._detach_locked()
                return
            signal = threading.Event()
            self._queue.put_nowait(("shutdown", signal))
        signal.wait(5.0)
        worker.join(timeout=1.0)
        with self._lock:
            self._worker = None
            self._active_session_id = None
            self._detach_locked()

    def _queue_detections(self, detections: list[Any]) -> None:
        with self._lock:
            session_id = self._active_session_id
            if session_id is None:
                return
            frame_index = self._frame_index
            self._frame_index += 1
            for detection in detections:
                ts = self._timestamp_seconds(getattr(detection, "timestamp", None))
                bbox = list(detection.bbox)
                class_name = getattr(detection.class_name, "value", detection.class_name)
                row = (
                    session_id,
                    ts,
                    frame_index,
                    str(class_name),
                    float(detection.confidence),
                    int(bbox[0]),
                    int(bbox[1]),
                    int(bbox[2]),
                    int(bbox[3]),
                    int(detection.track_id) if detection.track_id is not None else None,
                )
                self._queue.put_nowait(("detection", row))

    def _queue_metrics(self, metrics: Any) -> None:
        with self._lock:
            session_id = self._active_session_id
            if session_id is None:
                return
            ts = self._timestamp_seconds(getattr(metrics, "timestamp", None))
            row = (
                session_id,
                ts,
                float(metrics.fps),
                float(metrics.inference_latency_ms),
                float(metrics.cpu_percent),
                float(metrics.memory_percent),
                float(metrics.temperature_celsius) if metrics.temperature_celsius is not None else None,
            )
            self._queue.put_nowait(("metric", row))

    @staticmethod
    def _timestamp_seconds(value: Any) -> float:
        if isinstance(value, datetime):
            if value.tzinfo is None:
                value = value.replace(tzinfo=timezone.utc)
            return value.timestamp()
        return time.time()

    def _ensure_worker_locked(self) -> None:
        if self._worker is None or not self._worker.is_alive():
            self._worker = threading.Thread(target=self._worker_loop, name="mira-session-recorder", daemon=True)
            self._worker.start()

    def _detach_locked(self) -> None:
        service = self._camera_service
        if service is not None:
            if getattr(service, "on_detection", None) is getattr(self, "_detection_callback", None):
                service.on_detection = self._previous_detection_callback
            if getattr(service, "on_metrics", None) is getattr(self, "_metrics_callback", None):
                service.on_metrics = self._previous_metrics_callback
        self._camera_service = None
        self._previous_detection_callback = None
        self._previous_metrics_callback = None

    def _worker_loop(self) -> None:
        last_flush = time.monotonic()
        while True:
            try:
                message = self._queue.get(timeout=self.FLUSH_INTERVAL_SECONDS)
            except queue.Empty:
                message = None

            should_stop = False
            signal = None
            if message is not None:
                kind, value = message
                if kind == "detection":
                    self._pending_detections.append(value)
                    self._pending_event_detections.append(self._event_detection(value))
                elif kind == "metric":
                    self._pending_metrics.append(value)
                elif kind in {"flush", "shutdown"}:
                    signal = value
                    should_stop = kind == "shutdown"

            if message is None or (time.monotonic() - last_flush >= self.FLUSH_INTERVAL_SECONDS) or signal is not None:
                self._flush_pending(wait_for_detection_event=signal is not None)
                last_flush = time.monotonic()
            if signal is not None:
                signal.set()
            if should_stop:
                break

    @staticmethod
    def _event_detection(row: tuple[Any, ...]) -> dict[str, Any]:
        return {
            "session_id": row[0],
            "ts": datetime.fromtimestamp(row[1], timezone.utc).isoformat(),
            "frame_index": row[2],
            "class_name": row[3],
            "confidence": row[4],
            "bbox": [row[5], row[6], row[7], row[8]],
            "track_id": row[9],
        }

    def _flush_pending(self, *, wait_for_detection_event: bool = False) -> None:
        if self._pending_detections or self._pending_metrics:
            try:
                with get_db().transaction():
                    if self._pending_detections:
                        get_db().executemany(
                            "INSERT INTO detections (session_id, ts, frame_index, class_name, confidence,"
                            " x1, y1, x2, y2, track_id) VALUES (?,?,?,?,?,?,?,?,?,?)",
                            self._pending_detections,
                        )
                    if self._pending_metrics:
                        get_db().executemany(
                            "INSERT INTO metrics (session_id, ts, fps, latency_ms, cpu_percent, memory_percent,"
                            " temperature_c) VALUES (?,?,?,?,?,?,?)",
                            self._pending_metrics,
                        )
            except Exception:
                logger.exception("Could not flush camera session samples to SQLite")
                return
            self._pending_detections.clear()
            self._pending_metrics.clear()

        now = time.monotonic()
        time_until_event = self.DETECTION_EVENT_INTERVAL_SECONDS - (now - self._last_detection_event_at)
        if self._pending_event_detections and wait_for_detection_event and time_until_event > 0:
            time.sleep(time_until_event)
            now = time.monotonic()
        if (
            self._pending_event_detections
            and now - self._last_detection_event_at >= self.DETECTION_EVENT_INTERVAL_SECONDS
        ):
            events = self._pending_event_detections
            self._pending_event_detections = []
            self._last_detection_event_at = now
            get_events().publish(
                "detection_batch",
                {"session_id": events[0]["session_id"], "detections": events},
            )


recorder = SessionRecorder()


def set_camera_service(camera_service: Any) -> None:
    """Attach the process-wide recorder to the dashboard's shared CameraService."""
    recorder.attach(camera_service)
