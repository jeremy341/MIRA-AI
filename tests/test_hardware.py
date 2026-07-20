"""Tests for MIRA hardware abstraction layer."""

import sys
import pathlib
from unittest.mock import MagicMock, patch, PropertyMock

import pytest

_project_root = str(pathlib.Path(__file__).resolve().parent.parent)
_src_dir = str(pathlib.Path(__file__).resolve().parent.parent / "src")
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)
if _src_dir not in sys.path:
    sys.path.insert(0, _src_dir)


# ── AbstractCamera interface ─────────────────────────────────────────


def test_abstract_camera_cannot_be_instantiated():
    from src.hardware import AbstractCamera

    with pytest.raises(TypeError):
        AbstractCamera()


def test_abstract_camera_read_raises():
    from src.hardware import AbstractCamera

    class _Dummy(AbstractCamera):
        def read(self):
            return super().read()

        def release(self):
            pass

        def width(self):
            return 0

        def height(self):
            return 0

    with pytest.raises(TypeError):
        _Dummy().read()


# ── USBCamera ────────────────────────────────────────────────────────


@patch("src.hardware.setup_camera_properties")
@patch("src.hardware.cv2")
def test_usb_camera_read_returns_none_when_not_connected(mock_cv2, mock_setup):
    mock_cap = MagicMock()
    mock_cap.isOpened.return_value = True
    mock_cap.read.return_value = (False, None)
    mock_cv2.VideoCapture.return_value = mock_cap
    mock_cv2.CAP_DSHOW = 0x700

    from src.hardware import USBCamera

    cam = USBCamera(index=0, width=640, height=360)
    ret, frame = cam.read()
    assert ret is False
    assert frame is None
    cam.release()


@patch("src.hardware.setup_camera_properties")
@patch("src.hardware.cv2")
def test_usb_camera_constructor_stores_dimensions(mock_cv2, mock_setup):
    mock_cap = MagicMock()
    mock_cap.isOpened.return_value = True
    mock_cap.read.return_value = (False, None)
    mock_cv2.VideoCapture.return_value = mock_cap
    mock_cv2.CAP_DSHOW = 0x700

    from src.hardware import USBCamera

    cam = USBCamera(index=2, width=800, height=600)
    assert cam.width() == 800
    assert cam.height() == 600
    assert cam._index == 2
    cam.release()


@patch("src.hardware.setup_camera_properties")
@patch("src.hardware.cv2")
def test_usb_camera_release_idempotent(mock_cv2, mock_setup):
    mock_cap = MagicMock()
    mock_cap.isOpened.return_value = True
    mock_cap.read.return_value = (False, None)
    mock_cv2.VideoCapture.return_value = mock_cap
    mock_cv2.CAP_DSHOW = 0x700

    from src.hardware import USBCamera

    cam = USBCamera(index=0)
    cam.release()
    cam.release()
    mock_cap.release.assert_called()


@patch("src.hardware.setup_camera_properties")
@patch("src.hardware.cv2")
def test_usb_camera_raises_on_failed_open(mock_cv2, mock_setup):
    from src.exceptions import CameraError

    mock_cap = MagicMock()
    mock_cap.isOpened.return_value = False
    mock_cv2.VideoCapture.return_value = mock_cap
    mock_cv2.CAP_DSHOW = 0x700

    from src.hardware import USBCamera

    with pytest.raises(CameraError, match="Failed to open USB camera"):
        USBCamera(index=99)


# ── IPCamera ─────────────────────────────────────────────────────────


@patch("src.hardware.cv2")
def test_ip_camera_constructor(mock_cv2):
    mock_cap = MagicMock()
    mock_cap.isOpened.return_value = True
    mock_cap.read.return_value = (False, None)
    mock_cv2.VideoCapture.return_value = mock_cap

    from src.hardware import IPCamera

    url = "rtsp://192.168.1.100:554/stream"
    cam = IPCamera(rtsp_url=url, width=1280, height=720)
    assert cam._rtsp_url == url
    assert cam.width() == 1280
    assert cam.height() == 720
    cam.release()


@patch("src.hardware.cv2")
def test_ip_camera_raises_on_failed_open(mock_cv2):
    from src.exceptions import CameraError

    mock_cap = MagicMock()
    mock_cap.isOpened.return_value = False
    mock_cv2.VideoCapture.return_value = mock_cap

    from src.hardware import IPCamera

    with pytest.raises(CameraError, match="Failed to open IP camera"):
        IPCamera(rtsp_url="rtsp://unreachable/stream")


@patch("src.hardware.cv2")
def test_ip_camera_read_returns_none_when_no_frame(mock_cv2):
    mock_cap = MagicMock()
    mock_cap.isOpened.return_value = True
    mock_cap.read.return_value = (False, None)
    mock_cv2.VideoCapture.return_value = mock_cap

    from src.hardware import IPCamera

    cam = IPCamera(rtsp_url="rtsp://test/stream")
    ret, frame = cam.read()
    assert ret is False
    assert frame is None
    cam.release()


# ── create_camera factory ────────────────────────────────────────────


@patch("src.hardware.setup_camera_properties")
@patch("src.hardware.cv2")
def test_create_camera_int_returns_usb(mock_cv2, mock_setup):
    mock_cap = MagicMock()
    mock_cap.isOpened.return_value = True
    mock_cap.read.return_value = (False, None)
    mock_cv2.VideoCapture.return_value = mock_cap
    mock_cv2.CAP_DSHOW = 0x700

    from src.hardware import USBCamera, create_camera

    cam = create_camera(source=0)
    assert isinstance(cam, USBCamera)
    cam.release()


@patch("src.hardware.setup_camera_properties")
@patch("src.hardware.cv2")
def test_create_camera_digit_string_returns_usb(mock_cv2, mock_setup):
    mock_cap = MagicMock()
    mock_cap.isOpened.return_value = True
    mock_cap.read.return_value = (False, None)
    mock_cv2.VideoCapture.return_value = mock_cap
    mock_cv2.CAP_DSHOW = 0x700

    from src.hardware import USBCamera, create_camera

    cam = create_camera(source="1")
    assert isinstance(cam, USBCamera)
    cam.release()


@patch("src.hardware.cv2")
def test_create_camera_rtsp_returns_ip(mock_cv2):
    mock_cap = MagicMock()
    mock_cap.isOpened.return_value = True
    mock_cap.read.return_value = (False, None)
    mock_cv2.VideoCapture.return_value = mock_cap

    from src.hardware import IPCamera, create_camera

    cam = create_camera(source="rtsp://192.168.1.1:554/stream")
    assert isinstance(cam, IPCamera)
    cam.release()


@patch("src.hardware.cv2")
def test_create_camera_http_returns_ip(mock_cv2):
    mock_cap = MagicMock()
    mock_cap.isOpened.return_value = True
    mock_cap.read.return_value = (False, None)
    mock_cv2.VideoCapture.return_value = mock_cap

    from src.hardware import IPCamera, create_camera

    cam = create_camera(source="http://192.168.1.1:8080/video")
    assert isinstance(cam, IPCamera)
    cam.release()


def test_create_camera_invalid_source_raises():
    from src.exceptions import CameraError
    from src.hardware import create_camera

    with pytest.raises(CameraError, match="Unknown camera source"):
        create_camera(source="invalid_source_string")
