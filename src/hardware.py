"""Hardware abstraction layer for MIRA.

Provides an abstract camera interface and concrete implementations
for different camera types (USB, IP, Raspberry Pi).
"""

from __future__ import annotations

import sys
import time
from abc import ABC, abstractmethod
from threading import Lock, Thread
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


class USBCamera(AbstractCamera):
    """USB camera implementation using OpenCV VideoCapture."""

    def __init__(self, index: int = 0, width: int = 640, height: int = 360):
        self._index = index
        self._cam_width = width
        self._cam_height = height
        cap_flags = cv2.CAP_DSHOW if sys.platform == "win32" else 0
        self.cap = cv2.VideoCapture(index, cap_flags)
        if not self.cap.isOpened():
            raise CameraError(f"Failed to open USB camera index {index}.")

        setup_camera_properties(self.cap, width, height)

        self._lock = Lock()
        self._running = True
        self._ret = False
        self._frame = None

        for _ in range(self.WARMUP_FRAMES):
            self.cap.read()

        self._ret, self._frame = self.cap.read()
        self._thread = Thread(target=self._reader, daemon=True)
        self._thread.start()

    def _reader(self) -> None:
        while self._running:
            ret, frame = self.cap.read()
            with self._lock:
                self._ret = ret
                self._frame = frame
            time.sleep(0.001)

    def read(self) -> tuple[bool, object | None]:
        with self._lock:
            if not self._ret or self._frame is None:
                return False, None
            return True, self._frame.copy()

    def release(self) -> None:
        self._running = False
        self._thread.join(timeout=2)
        self.cap.release()

    def width(self) -> int:
        return self._cam_width

    def height(self) -> int:
        return self._cam_height


class IPCamera(AbstractCamera):
    """IP/RTSP camera implementation."""

    def __init__(self, rtsp_url: str, width: int = 640, height: int = 360):
        self._rtsp_url = rtsp_url
        self._cam_width = width
        self._cam_height = height
        self.cap = cv2.VideoCapture(rtsp_url)
        if not self.cap.isOpened():
            raise CameraError(f"Failed to open IP camera at {rtsp_url}.")

        self._lock = Lock()
        self._running = True
        self._ret = False
        self._frame = None
        self._thread = Thread(target=self._reader, daemon=True)
        self._thread.start()

    def _reader(self) -> None:
        while self._running:
            ret, frame = self.cap.read()
            if not ret:
                time.sleep(0.05)
                continue
            with self._lock:
                self._ret = True
                self._frame = frame
            time.sleep(0.001)

    def read(self) -> tuple[bool, object | None]:
        with self._lock:
            if not self._ret or self._frame is None:
                return False, None
            return True, self._frame.copy()

    def release(self) -> None:
        self._running = False
        self._thread.join(timeout=2)
        self.cap.release()

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
