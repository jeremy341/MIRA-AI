"""Tests for MIRA hardware abstraction layer."""

from __future__ import annotations

import time
from unittest.mock import MagicMock, patch

import pytest

from src.exceptions import CameraError
from src.hardware import (
    AbstractCamera,
    USBCamera,
    IPCamera,
    _FrameBuffer,
)




def test_frame_buffer_update_and_get():
    buf = _FrameBuffer()
    fake_frame = MagicMock()
    buf.update(True, fake_frame)
    ret, frame = buf.get()
    assert ret is True
    assert frame is not None


def test_frame_buffer_get_returns_copy():
    buf = _FrameBuffer()
    import numpy as np

    arr = np.array([1, 2, 3])
    buf.update(True, arr)
    _, frame = buf.get()
    assert frame is not arr  # should be a copy


def test_frame_buffer_not_frozen_initially():
    buf = _FrameBuffer()
    assert not buf.is_frozen


def test_frame_buffer_frozen_after_timeout():
    buf = _FrameBuffer()
    buf.update(True, object())
    # Manually set last_update to way in the past
    with buf._lock:
        buf._last_update = time.perf_counter() - 10.0
    assert buf.is_frozen


def test_frame_buffer_stop():
    buf = _FrameBuffer()
    assert buf.running
    buf.stop()
    assert not buf.running




def test_usbcamera_init_success():
    with patch("src.hardware.cv2.VideoCapture") as mock_cap:
        mock_instance = MagicMock()
        mock_instance.isOpened.return_value = True
        mock_instance.read.return_value = (True, object())
        mock_cap.return_value = mock_instance
        cam = USBCamera(0, 640, 360)
        assert cam.width() == 640
        assert cam.height() == 360
        cam.release()


def test_usbcamera_init_failure():
    with patch("src.hardware.cv2.VideoCapture") as mock_cap:
        mock_instance = MagicMock()
        mock_instance.isOpened.return_value = False
        mock_cap.return_value = mock_instance
        with pytest.raises(CameraError):
            USBCamera(0)


def test_usbcamera_is_alive():
    with patch("src.hardware.cv2.VideoCapture") as mock_cap:
        mock_instance = MagicMock()
        mock_instance.isOpened.return_value = True
        mock_instance.read.return_value = (True, object())
        mock_cap.return_value = mock_instance
        cam = USBCamera(0)
        assert cam.is_alive()
        cam.release()
        assert not cam.is_alive()


def test_usbcamera_release_idempotent():
    with patch("src.hardware.cv2.VideoCapture") as mock_cap:
        mock_instance = MagicMock()
        mock_instance.isOpened.return_value = True
        mock_instance.read.return_value = (True, object())
        mock_cap.return_value = mock_instance
        cam = USBCamera(0)
        cam.release()
        cam.release()  # should not raise
        assert cam._released


def test_usbcamera_context_manager():
    with patch("src.hardware.cv2.VideoCapture") as mock_cap:
        mock_instance = MagicMock()
        mock_instance.isOpened.return_value = True
        mock_instance.read.return_value = (True, object())
        mock_cap.return_value = mock_instance
        with USBCamera(0) as cam:
            assert isinstance(cam, USBCamera)




def test_ipcamera_init_success():
    with patch("src.hardware.cv2.VideoCapture") as mock_cap:
        mock_instance = MagicMock()
        mock_instance.isOpened.return_value = True
        mock_cap.return_value = mock_instance
        cam = IPCamera("rtsp://test", 640, 360)
        assert cam.width() == 640
        cam.release()


def test_ipcamera_reconnection():
    with patch("src.hardware.cv2.VideoCapture") as mock_cap:
        mock_instance = MagicMock()
        mock_instance.isOpened.return_value = True
        # First read succeeds, subsequent reads fail to trigger reconnection
        mock_instance.read.side_effect = [
            (True, object()),
            (False, None),
            (False, None),
            (False, None),
            (False, None),
        ]
        mock_cap.return_value = mock_instance
        cam = IPCamera("rtsp://test")
        # Let reader thread run briefly
        time.sleep(0.1)
        cam.release()




def test_abstract_camera_constants():
    assert AbstractCamera.WARMUP_FRAMES == 10
    assert AbstractCamera.FREEZE_TIMEOUT_SECONDS == 2.0
