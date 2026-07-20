"""Tests for MIRA deployment utilities — hardware detection and environment checks."""

import sys
import pathlib
from unittest.mock import patch, MagicMock

import pytest

_project_root = str(pathlib.Path(__file__).resolve().parent.parent)
_src_dir = str(pathlib.Path(__file__).resolve().parent.parent / "src")
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)
if _src_dir not in sys.path:
    sys.path.insert(0, _src_dir)


# ── HardwareInfo dataclass ───────────────────────────────────────────


def test_hardware_info_defaults():
    from src.deploy import HardwareInfo

    info = HardwareInfo(platform="linux", arch="x86_64")
    assert info.platform == "linux"
    assert info.arch == "x86_64"
    assert info.is_raspberry_pi is False
    assert info.is_jetson is False
    assert info.has_cuda is False
    assert info.cuda_version == ""
    assert info.has_tflite_runtime is False
    assert info.has_tensorflow is False
    assert info.has_torch is False
    assert info.has_opencv is False
    assert info.memory_mb == 0
    assert info.cpu_count == 0
    assert info.python_version == ""
    assert info.details == {}


def test_hardware_info_with_values():
    from src.deploy import HardwareInfo

    info = HardwareInfo(
        platform="linux",
        arch="aarch64",
        is_raspberry_pi=True,
        has_cuda=True,
        cuda_version="12.1",
        memory_mb=4096,
        cpu_count=4,
    )
    assert info.is_raspberry_pi is True
    assert info.has_cuda is True
    assert info.memory_mb == 4096


# ── detect_hardware ──────────────────────────────────────────────────


@patch("src.deploy._detect_cuda", return_value=(False, ""))
@patch("src.deploy._detect_jetson", return_value=False)
@patch("src.deploy._detect_raspberry_pi", return_value=False)
@patch("src.deploy._safe_memory_mb", return_value=16384)
@patch("src.deploy._safe_cpu_count", return_value=8)
@patch("src.deploy._module_available", return_value=True)
def test_detect_hardware_returns_hardware_info(mock_mod, mock_cpu, mock_mem, mock_pi, mock_jet, mock_cuda):
    from src.deploy import detect_hardware

    info = detect_hardware()
    assert hasattr(info, "platform")
    assert hasattr(info, "arch")
    assert isinstance(info.cpu_count, int)
    assert isinstance(info.memory_mb, int)


@patch("src.deploy._detect_cuda", return_value=(True, "535.129.03"))
@patch("src.deploy._detect_jetson", return_value=False)
@patch("src.deploy._detect_raspberry_pi", return_value=False)
@patch("src.deploy._safe_memory_mb", return_value=8192)
@patch("src.deploy._safe_cpu_count", return_value=16)
@patch("src.deploy._module_available", return_value=True)
def test_detect_hardware_cuda_detected(mock_mod, mock_cpu, mock_mem, mock_pi, mock_jet, mock_cuda):
    from src.deploy import detect_hardware

    info = detect_hardware()
    assert info.has_cuda is True
    assert info.cuda_version == "535.129.03"


@patch("src.deploy._detect_cuda", return_value=(False, ""))
@patch("src.deploy._detect_jetson", return_value=False)
@patch("src.deploy._detect_raspberry_pi", return_value=True)
@patch("src.deploy._safe_memory_mb", return_value=2048)
@patch("src.deploy._safe_cpu_count", return_value=4)
@patch("src.deploy._module_available", return_value=False)
def test_detect_hardware_raspberry_pi(mock_mod, mock_cpu, mock_mem, mock_pi, mock_jet, mock_cuda):
    from src.deploy import detect_hardware

    info = detect_hardware()
    assert info.is_raspberry_pi is True


# ── suggest_model ────────────────────────────────────────────────────


def test_suggest_model_raspberry_pi():
    from src.deploy import HardwareInfo, suggest_model

    info = HardwareInfo(platform="linux", arch="aarch64", is_raspberry_pi=True)
    assert suggest_model(info) == "tflite_int8"


def test_suggest_model_jetson():
    from src.deploy import HardwareInfo, suggest_model

    info = HardwareInfo(platform="linux", arch="aarch64", is_jetson=True)
    assert suggest_model(info) == "tensorrt"


def test_suggest_model_cuda_torch():
    from src.deploy import HardwareInfo, suggest_model

    info = HardwareInfo(platform="linux", arch="x86_64", has_cuda=True, has_torch=True)
    assert suggest_model(info) == "pt"


def test_suggest_model_cuda_no_torch():
    from src.deploy import HardwareInfo, suggest_model

    info = HardwareInfo(platform="linux", arch="x86_64", has_cuda=True, has_torch=False)
    assert suggest_model(info) == "pt"


def test_suggest_model_no_cuda():
    from src.deploy import HardwareInfo, suggest_model

    info = HardwareInfo(platform="linux", arch="x86_64", has_cuda=False, has_torch=False)
    assert suggest_model(info) == "tflite_fp32"


# ── check_environment ────────────────────────────────────────────────


@patch("src.deploy.detect_hardware")
def test_check_environment_no_warnings(mock_detect):
    from src.deploy import HardwareInfo, check_environment

    mock_detect.return_value = HardwareInfo(
        platform="linux",
        arch="x86_64",
        has_opencv=True,
        has_torch=True,
    )
    warnings = check_environment()
    assert isinstance(warnings, list)
    assert len(warnings) == 0


@patch("src.deploy.detect_hardware")
def test_check_environment_missing_opencv(mock_detect):
    from src.deploy import HardwareInfo, check_environment

    mock_detect.return_value = HardwareInfo(
        platform="linux",
        arch="x86_64",
        has_opencv=False,
        has_torch=True,
    )
    warnings = check_environment()
    assert any("OpenCV" in w for w in warnings)


@patch("src.deploy.detect_hardware")
def test_check_environment_no_frameworks(mock_detect):
    from src.deploy import HardwareInfo, check_environment

    mock_detect.return_value = HardwareInfo(
        platform="linux",
        arch="x86_64",
        has_opencv=True,
        has_torch=False,
        has_tensorflow=False,
    )
    warnings = check_environment()
    assert any("deep learning framework" in w for w in warnings)


@patch("src.deploy.detect_hardware")
def test_check_environment_pi_no_tflite(mock_detect):
    from src.deploy import HardwareInfo, check_environment

    mock_detect.return_value = HardwareInfo(
        platform="linux",
        arch="aarch64",
        is_raspberry_pi=True,
        has_opencv=True,
        has_torch=False,
        has_tensorflow=False,
        has_tflite_runtime=False,
    )
    warnings = check_environment()
    assert any("Raspberry Pi" in w for w in warnings)
