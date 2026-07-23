"""Hardware abstraction layer for MIRA.

Provides an abstract camera interface and concrete implementations
for different camera types (USB, IP, Raspberry Pi).
"""

from __future__ import annotations

import sys
import threading
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Self

import cv2
import numpy as np

from .config import setup_camera_properties
from .exceptions import CameraError
from .logger import get_logger

logger = get_logger(__name__)


class AbstractCamera(ABC):
    """Abstract interface for camera hardware."""

    WARMUP_FRAMES = 10
    FREEZE_TIMEOUT_SECONDS = 2.0

    @abstractmethod
    def read(self) -> tuple[bool, object | None]: ...

    @abstractmethod
    def release(self) -> None: ...

    @abstractmethod
    def width(self) -> int: ...

    @abstractmethod
    def height(self) -> int: ...

    @abstractmethod
    def is_alive(self) -> bool: ...

    def __enter__(self) -> Self:
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.release()


@dataclass
class _FrameBuffer:
    """Thread-safe single-frame buffer with freeze detection."""

    _lock: threading.Lock = field(default_factory=threading.Lock)
    _ret: bool = False
    _frame: np.ndarray | None = None
    _last_update: float = 0.0
    _running: bool = True

    def update(self, ret: bool, frame: object | None) -> None:
        with self._lock:
            self._ret = ret
            self._frame = frame
            self._last_update = time.perf_counter()

    def get(self) -> tuple[bool, object | None]:
        with self._lock:
            return self._ret, self._frame.copy() if self._frame is not None else None

    @property
    def is_frozen(self) -> bool:
        with self._lock:
            if not self._last_update:
                return False
            return (time.perf_counter() - self._last_update) > AbstractCamera.FREEZE_TIMEOUT_SECONDS

    def stop(self) -> None:
        with self._lock:
            self._running = False

    @property
    def running(self) -> bool:
        with self._lock:
            return self._running


class USBCamera(AbstractCamera):
    """USB camera implementation using OpenCV VideoCapture."""

    def __init__(self, index: int = 0, width: int = 640, height: int = 360):
        self._index = index
        self._cam_width = width
        self._cam_height = height
        self._released = False

        cap_flags = cv2.CAP_DSHOW if sys.platform == "win32" else 0
        self.cap = cv2.VideoCapture(index, cap_flags)
        if not self.cap.isOpened():
            raise CameraError(f"Failed to open USB camera index {index}.")

        setup_camera_properties(self.cap, width, height)

        self._buffer = _FrameBuffer()

        # Warmup
        for _ in range(self.WARMUP_FRAMES):
            self.cap.read()

        # Prime the buffer with the first frame
        ret, frame = self.cap.read()
        self._buffer.update(ret, frame)

        self._thread = threading.Thread(target=self._reader, daemon=True, name=f"USBCamera-{index}")
        self._thread.start()
        logger.debug(f"USBCamera {index} initialized at {width}x{height}")

    def _reader(self) -> None:
        while self._buffer.running:
            try:
                ret, frame = self.cap.read()
            except Exception as e:
                logger.warning(f"Frame read error: {type(e).__name__}: {e}")
                time.sleep(0.01)
                continue
            if not ret:
                time.sleep(0.01)
                continue
            self._buffer.update(ret, frame)
            time.sleep(0.01)

    def read(self) -> tuple[bool, object | None]:
        return self._buffer.get()

    def release(self) -> None:
        """Release camera resources. Idempotent."""
        if self._released:
            return
        self._released = True
        self._buffer.stop()
        self._thread.join(timeout=5.0)
        if self._thread.is_alive():
            logger.warning(f"Camera {self._index} reader thread did not terminate within 5s")
        try:
            self.cap.release()
        except Exception as exc:
            logger.warning(f"Exception releasing camera {self._index}: {exc}")
        logger.debug(f"USBCamera {self._index} released")

    def width(self) -> int:
        return self._cam_width

    def height(self) -> int:
        return self._cam_height

    def is_alive(self) -> bool:
        return self._buffer.running and not self._buffer.is_frozen

    @property
    def is_frozen(self) -> bool:
        return self._buffer.is_frozen


class IPCamera(AbstractCamera):
    """IP/RTSP camera implementation."""

    RECONNECT_ATTEMPTS = 3
    RECONNECT_DELAY_SECONDS = 2.0

    def __init__(self, rtsp_url: str, width: int = 640, height: int = 360):
        self._rtsp_url = rtsp_url
        self._cam_width = width
        self._cam_height = height
        self._released = False

        self.cap = cv2.VideoCapture(rtsp_url)
        if not self.cap.isOpened():
            safe_url = rtsp_url.split("@")[-1] if "@" in rtsp_url else rtsp_url
            raise CameraError(f"Failed to open IP camera at rtsp://<redacted>@{safe_url}.")

        self._buffer = _FrameBuffer()
        self._thread = threading.Thread(target=self._reader, daemon=True, name=f"IPCamera-{rtsp_url}")
        self._thread.start()
        logger.debug(f"IPCamera initialized at {rtsp_url}")

    def _reader(self) -> None:
        while self._buffer.running:
            try:
                ret, frame = self.cap.read()
            except Exception as exc:
                logger.warning(f"IP camera read error: {exc}")
                time.sleep(0.05)
                continue
            if not ret:
                # Attempt reconnection
                logger.warning("IP camera stream lost, attempting reconnection...")
                for attempt in range(self.RECONNECT_ATTEMPTS):
                    time.sleep(self.RECONNECT_DELAY_SECONDS)
                    old_cap = self.cap
                    if old_cap is not None:
                        try:
                            old_cap.release()
                        except Exception:
                            pass
                    self.cap = cv2.VideoCapture(self._rtsp_url)
                    if self.cap.isOpened():
                        logger.info(f"IP camera reconnected after {attempt + 1} attempt(s)")
                        break
                else:
                    logger.error(f"IP camera reconnection failed after {self.RECONNECT_ATTEMPTS} attempts")
                    self._buffer.stop()
                continue
            self._buffer.update(ret, frame)
            time.sleep(0.01)

    def read(self) -> tuple[bool, object | None]:
        return self._buffer.get()

    def release(self) -> None:
        if self._released:
            return
        self._released = True
        self._buffer.stop()
        self._thread.join(timeout=5.0)
        try:
            self.cap.release()
        except Exception as exc:
            logger.warning(f"Exception releasing IP camera: {exc}")

    def width(self) -> int:
        return self._cam_width

    def height(self) -> int:
        return self._cam_height

    def is_alive(self) -> bool:
        return self._buffer.running and not self._buffer.is_frozen

    @property
    def is_frozen(self) -> bool:
        return self._buffer.is_frozen
