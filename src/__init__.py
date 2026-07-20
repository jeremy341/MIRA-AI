"""MIRA — Machine Intelligence for Recycling Automation."""

from exceptions import MiraError, ConfigError, ModelError, DatasetError, CameraError, PipelineError
from deploy import detect_hardware, check_environment, suggest_model, HardwareInfo

__all__ = [
    "MiraError",
    "ConfigError",
    "ModelError",
    "DatasetError",
    "CameraError",
    "PipelineError",
    "detect_hardware",
    "check_environment",
    "suggest_model",
    "HardwareInfo",
]
