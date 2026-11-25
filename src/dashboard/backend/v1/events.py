"""In-process pub/sub. `publish` is thread-safe and never blocks."""

from __future__ import annotations

import asyncio
import threading
from datetime import datetime, timezone
from typing import Any

EVENT_TYPES = (
    "session_started",
    "session_stopped",
    "job_progress",
    "job_finished",
    "arm_event",
    "hardware_sample",
    "detection_batch",
)


class EventBus:
    def __init__(self, queue_size: int = 200):
        self._queue_size = queue_size
        self._subscribers: list[tuple[asyncio.AbstractEventLoop, asyncio.Queue]] = []
        self._lock = threading.Lock()

    def subscribe(self) -> asyncio.Queue:
        """Call from inside the event loop. Returns a queue of event dicts."""
        queue: asyncio.Queue = asyncio.Queue(maxsize=self._queue_size)
        with self._lock:
            self._subscribers.append((asyncio.get_running_loop(), queue))
        return queue

    def unsubscribe(self, queue: asyncio.Queue) -> None:
        with self._lock:
            self._subscribers = [(loop, q) for loop, q in self._subscribers if q is not queue]

    def publish(self, event_type: str, data: dict[str, Any] | None = None) -> None:
        event = {"type": event_type, "ts": datetime.now(timezone.utc).isoformat(), "data": data or {}}
        with self._lock:
            subscribers = list(self._subscribers)
        for loop, queue in subscribers:
            try:
                loop.call_soon_threadsafe(self._offer, queue, event)
            except RuntimeError:
                self.unsubscribe(queue)

    @staticmethod
    def _offer(queue: asyncio.Queue, event: dict[str, Any]) -> None:
        if queue.full():
            try:
                queue.get_nowait()  # drop the oldest event for a slow client
            except asyncio.QueueEmpty:
                pass
        try:
            queue.put_nowait(event)
        except asyncio.QueueFull:
            pass
