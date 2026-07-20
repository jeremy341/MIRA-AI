"""Hardware abstraction layer for MIRA.

Provides an abstract camera interface and concrete implementations
for different camera types (USB, IP, Raspberry Pi).
"""

from __future__ import annotations

import sys
import time
import warnings
from abc import ABC, abstractmethod
from threading import Lock, Thread
from types import TracebackType
from typing import Self

import cv2

from config import setup_camera_properties
from exceptions import CameraError


class AbstractCamera(ABC):
    """Abstract interface for camera hardware."""

    WARMUP_FRAMES = 10

    @abstractmethod
    def read(self) -> tuple[bool, object | None]: ...

    @abstractmethod
    def release(self) -> None: ...

    @abstractmethod
    def width(self) -> int: ...

    @abstractmethod
    def height(self) -> int: ...

    @property
    @abstractmethod
    def is_alive(self) -> bool: ...

    def __enter__(self) -> Self:
        """Context manager entry."""
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        """Context manager exit — always release the camera."""
        self.release()


class _BaseThreadedCamera(AbstractCamera):
    """Shared logic for threaded camera implementations."""

    def __init__(self) -> None:
        self._lock = Lock()
        self._running = False
        self._released = False
        self._ret = False
        self._frame = None
        self._thread: Thread | None = None

    def _reader(self) -> None:
        """Background frame reader. Must be overridden by subclasses."""
        raise NotImplementedError

    def read(self) -> tuple[bool, object | None]:
        with self._lock:
            if not self._ret or self._frame is None:
                return False, None
            return True, self._frame.copy()

    @property
    def is_alive(self) -> bool:
        """Return True if the camera thread is running and resources are held."""
        with self._lock:
            return self._running and self._thread is not None and self._thread.is_alive()

    def _stop_thread(self, timeout: float = 2.0) -> None:
        """Signal the reader thread to stop and wait for it."""
        with self._lock:
            self._running = False
            thread = self._thread
        if thread is not None and thread.is_alive():
            thread.join(timeout=timeout)

    def release(self) -> None:
        """Release camera resources. Safe to call multiple times (idempotent)."""
        with self._lock:
            if self._released:
                return
            self._released = True
            self._running = False
            thread = self._thread
            cap = getattr(self, "cap", None)
        # Perform joins/releases outside the lock to avoid deadlocks.
        if thread is not None and thread.is_alive():
            thread.join(timeout=2)
        if cap is not None:
            cap.release()

    def __del__(self) -> None:
        """Safety-net finalizer. Log a warning if context-manager use wasn't employed."""
        if hasattr(self, "_released") and not self._released:
            warnings.warn(
                f"{type(self).__name__} was not explicitly released. "
                "Use the camera as a context manager (with-statement) for guaranteed cleanup.",
                ResourceWarning,
                stacklevel=2,
            )
            try:
                self.release()
            except Exception:
                pass


class USBCamera(_BaseThreadedCamera):
    """USB camera implementation using OpenCV VideoCapture."""

    def __init__(self, index: int = 0, width: int = 640, height: int = 360):
        super().__init__()
        self._index = index
        self._cam_width = width
        self._cam_height = height
        cap_flags = cv2.CAP_DSHOW if sys.platform == "win32" else 0
        self.cap = cv2.VideoCapture(index, cap_flags)
        if not self.cap.isOpened():
            raise CameraError(f"Failed to open USB camera index {index}.")

        setup_camera_properties(self.cap, width, height)

        for _ in range(self.WARMUP_FRAMES):
            self.cap.read()

        self._ret, self._frame = self.cap.read()
        with self._lock:
            self._running = True
            self._released = False
        self._thread = Thread(target=self._reader, daemon=True)
        self._thread.start()

    def _reader(self) -> None:
        """Read frames in a background thread."""
        while True:
            with self._lock:
                if not self._running:
                    break
            ret, frame = self.cap.read()
            with self._lock:
                self._ret = ret
                self._frame = frame
            time.sleep(0.001)

    def width(self) -> int:
        return self._cam_width

    def height(self) -> int:
        return self._cam_height


class IPCamera(_BaseThreadedCamera):
    """IP/RTSP camera implementation."""

    def __init__(self, rtsp_url: str, width: int = 640, height: int = 360):
        super().__init__()
        self._rtsp_url = rtsp_url
        self._cam_width = width
        self._cam_height = height
        self.cap = cv2.VideoCapture(rtsp_url)
        if not self.cap.isOpened():
            raise CameraError(f"Failed to open IP camera at {rtsp_url}.")

        with self._lock:
            self._running = True
            self._released = False
        self._thread = Thread(target=self._reader, daemon=True)
        self._thread.start()

    def _reader(self) -> None:
        """Read frames in a background thread."""
        while True:
            with self._lock:
                if not self._running:
                    break
            ret, frame = self.cap.read()
            if not ret:
                time.sleep(0.05)
                continue
            with self._lock:
                self._ret = True
                self._frame = frame
            time.sleep(0.001)

    def width(self) -> int:
        return self._cam_width

    def height(self) -> int:
        return self._cam_height


def create_camera(source: str | int = 0, width: int = 640, height: int = 360) -> AbstractCamera:
    """Factory to create the appropriate camera type.

    Args:
        source: Camera index (int) for USB, or RTSP URL (str) for IP.
        width: Desired capture width.
        height: Desired capture height.

    Returns:
        A configured AbstractCamera implementation.
    """
    if isinstance(source, int) or (isinstance(source, str) and source.isdigit()):
        return USBCamera(int(source) if isinstance(source, str) else source, width, height)
    if source.startswith("rtsp://") or source.startswith("http://"):
        return IPCamera(source, width, height)
    raise CameraError(f"Unknown camera source: {source}")
