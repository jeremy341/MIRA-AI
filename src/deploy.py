"""Deployment utilities for MIRA — hardware detection and environment checks."""

from __future__ import annotations

import platform
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class HardwareInfo:
    platform: str
    arch: str
    is_raspberry_pi: bool = False
    is_jetson: bool = False
    has_cuda: bool = False
    cuda_version: str = ""
    has_tflite_runtime: bool = False
    has_tensorflow: bool = False
    has_torch: bool = False
    has_opencv: bool = False
    pi_model: str = ""
    memory_mb: int = 0
    cpu_count: int = 0
    python_version: str = ""
    details: dict[str, Any] = field(default_factory=dict)


def detect_hardware() -> HardwareInfo:
    """Detect the current hardware platform and available capabilities."""
    info = HardwareInfo(
        platform=sys.platform,
        arch=platform.machine(),
        python_version=sys.version,
    )

    # CPU info
    info.cpu_count = _safe_cpu_count()

    # Memory
    info.memory_mb = _safe_memory_mb()

    # Raspberry Pi detection
    info.is_raspberry_pi = _detect_raspberry_pi()
    if info.is_raspberry_pi:
        info.pi_model = _get_pi_model()

    # Jetson detection
    info.is_jetson = _detect_jetson()

    # CUDA detection
    info.has_cuda, info.cuda_version = _detect_cuda()

    # Library availability
    info.has_torch = _module_available("torch")
    info.has_tensorflow = _module_available("tensorflow")
    info.has_tflite_runtime = _module_available("tflite_runtime")
    info.has_opencv = _module_available("cv2")

    return info


def suggest_model(info: HardwareInfo | None = None) -> str:
    """Suggest the best model type for the current hardware."""
    if info is None:
        info = detect_hardware()

    if info.is_raspberry_pi:
        return "tflite_int8"
    if info.is_jetson:
        return "tensorrt"
    if info.has_cuda and info.has_torch:
        return "pt"
    if info.has_cuda:
        return "pt"
    return "tflite_fp32"


def check_environment() -> list[str]:
    """Run environment checks and return a list of warnings."""
    warnings: list[str] = []
    info = detect_hardware()

    if not info.has_opencv:
        warnings.append("OpenCV (cv2) is not installed. Camera and visualization will not work.")

    if info.is_raspberry_pi and not info.has_tflite_runtime and not info.has_tensorflow:
        warnings.append(
            "Raspberry Pi detected but no TFLite runtime found. Install tflite-runtime for edge deployment."
        )

    if not info.has_torch and not info.has_tensorflow:
        warnings.append("No deep learning framework (torch/tensorflow) found.")

    return warnings


def _module_available(name: str) -> bool:
    try:
        __import__(name)
        return True
    except ImportError:
        return False


def _safe_cpu_count() -> int:
    try:
        return (
            len(open("/proc/stat").readlines())
            if sys.platform != "win32"
            else int(subprocess.check_output("wmic cpu get NumberOfCores", shell=True).decode().strip().split("\n")[1])
        )
    except Exception:
        import os

        return os.cpu_count() or 1


def _safe_memory_mb() -> int:
    try:
        if sys.platform == "win32":
            import ctypes

            kernel32 = ctypes.windll.kernel32
            mem = ctypes.c_ulonglong()
            kernel32.GetPhysicallyInstalledSystemMemory(ctypes.byref(mem))
            return int(mem.value // 1024)
        with open("/proc/meminfo") as f:
            for line in f:
                if line.startswith("MemTotal:"):
                    return int(line.split()[1]) // 1024
    except Exception:
        pass
    return 0


def _detect_raspberry_pi() -> bool:
    try:
        if sys.platform == "linux":
            with open("/proc/cpuinfo") as f:
                return "Raspberry Pi" in f.read() or "BCM" in f.read()
    except Exception:
        pass
    return False


def _get_pi_model() -> str:
    try:
        if sys.platform == "linux":
            result = subprocess.run(
                ["cat", "/sys/firmware/devicetree/base/model"], capture_output=True, text=True, timeout=2
            )
            return result.stdout.strip().rstrip("\x00") if result.stdout else ""
    except Exception:
        pass
    return ""


def _detect_jetson() -> bool:
    try:
        if sys.platform == "linux":
            return Path("/etc/nv_tegra_release").exists()
    except Exception:
        pass
    return False


def _detect_cuda() -> tuple[bool, str]:
    try:
        result = subprocess.run(
            ["nvidia-smi", "--query-gpu=driver_version", "--format=csv,noheader"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0 and result.stdout.strip():
            return True, result.stdout.strip().split("\n")[0]
    except Exception:
        try:
            import torch

            if torch.cuda.is_available():
                return True, torch.version.cuda or ""
        except Exception:
            pass
    return False, ""
