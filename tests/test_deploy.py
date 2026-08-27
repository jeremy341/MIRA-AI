"""Tests for MIRA deployment and hardware detection utilities."""

from __future__ import annotations

import sys
from unittest.mock import MagicMock, mock_open, patch


from src.deploy import (
    HardwareInfo,
    detect_hardware,
    suggest_model,
    check_environment,
    _module_available,
    _safe_cpu_count,
    _detect_raspberry_pi,
    _detect_jetson,
    _detect_cuda,
)


def test_hardware_info_defaults():
    info = HardwareInfo(platform="linux", arch="x86_64")
    assert info.platform == "linux"
    assert info.arch == "x86_64"
    assert not info.is_raspberry_pi
    assert not info.is_jetson
    assert info.memory_mb >= 0


def test_detect_hardware_returns_info():
    info = detect_hardware()
    assert isinstance(info, HardwareInfo)
    assert info.platform == sys.platform
    assert info.cpu_count > 0
    assert info.python_version != ""


def test_detect_hardware_detects_cuda():
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0, stdout="525.85.12\n")
        has_cuda, version = _detect_cuda()
        assert has_cuda
        assert version == "525.85.12"


def test_detect_cuda_fallback_torch():
    with patch("subprocess.run") as mock_run:
        mock_run.side_effect = FileNotFoundError()
        mock_torch = MagicMock()
        mock_torch.cuda.is_available.return_value = True
        mock_torch.version.cuda = "11.8"
        with patch.dict("sys.modules", {"torch": mock_torch}):
            has_cuda, version = _detect_cuda()
            assert has_cuda
            assert version == "11.8"


def test_detect_cuda_no_cuda():
    with patch("subprocess.run") as mock_run:
        mock_run.side_effect = FileNotFoundError()
        mock_torch = MagicMock()
        mock_torch.cuda.is_available.return_value = False
        with patch.dict("sys.modules", {"torch": mock_torch}):
            has_cuda, version = _detect_cuda()
        assert not has_cuda
        assert version == ""


def test_suggest_model_raspberry_pi():
    info = HardwareInfo(platform="linux", arch="armv7l", is_raspberry_pi=True, has_tflite_runtime=True)
    assert suggest_model(info) == "tflite_int8"


def test_suggest_model_jetson():
    info = HardwareInfo(platform="linux", arch="aarch64", is_jetson=True)
    assert suggest_model(info) == "tensorrt"


def test_suggest_model_cuda():
    info = HardwareInfo(platform="linux", arch="x86_64", has_cuda=True, has_torch=True)
    assert suggest_model(info) == "pt"


def test_suggest_model_cpu_only():
    info = HardwareInfo(platform="linux", arch="x86_64")
    # No torch/tflite/onnx: suggest_model now returns "onnx" as safest CPU fallback
    # instead of "pt" which would fail without torch.
    assert suggest_model(info) == "pt"


def test_suggest_model_none_calls_detect():
    with patch("src.deploy.detect_hardware") as mock_detect:
        mock_detect.return_value = HardwareInfo(platform="linux", arch="x86_64")
        result = suggest_model()
        assert result == "pt"
        mock_detect.assert_called_once()


def test_check_environment_no_opencv():
    with patch("src.deploy.detect_hardware") as mock_detect:
        mock_detect.return_value = HardwareInfo(platform="linux", arch="x86_64", has_opencv=False)
        warnings = check_environment()
        assert any("OpenCV" in w for w in warnings)


def test_check_environment_no_frameworks():
    with patch("src.deploy.detect_hardware") as mock_detect:
        mock_detect.return_value = HardwareInfo(
            platform="linux", arch="x86_64", has_opencv=True, has_torch=False, has_tensorflow=False
        )
        warnings = check_environment()
        assert any("deep learning framework" in w for w in warnings)


def test_check_environment_healthy():
    with patch("src.deploy.detect_hardware") as mock_detect:
        mock_detect.return_value = HardwareInfo(platform="linux", arch="x86_64", has_opencv=True, has_torch=True)
        warnings = check_environment()
        assert warnings == []


def test_module_available_existing():
    assert _module_available("sys")


def test_module_available_missing():
    assert not _module_available("nonexistent_module_12345")


def test_detect_raspberry_pi_true():
    m = mock_open(read_data="Hardware\t: Raspberry Pi 4")
    with patch("builtins.open", m):
        with patch("sys.platform", "linux"):
            assert _detect_raspberry_pi()


def test_detect_raspberry_pi_false():
    m = mock_open(read_data="Intel CPU")
    with patch("builtins.open", m):
        with patch("sys.platform", "linux"):
            assert not _detect_raspberry_pi()


def test_detect_jetson_true():
    with patch("pathlib.Path.exists", return_value=True):
        with patch("sys.platform", "linux"):
            assert _detect_jetson()


def test_detect_jetson_false():
    with patch("pathlib.Path.exists", return_value=False):
        with patch("sys.platform", "linux"):
            assert not _detect_jetson()


def test_safe_cpu_count_returns_positive():
    count = _safe_cpu_count()
    assert isinstance(count, int)
    assert count >= 1
