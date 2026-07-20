"""MIRA — Machine Intelligence for Recycling Automation."""

from exceptions import MiraError, ConfigError, ModelError, DatasetError, CameraError, PipelineError
from deploy import detect_hardware, check_environment, suggest_model, HardwareInfo
from serialization import (
    serialize_result,
    load_result,
    serialize_config,
    experiment_metadata,
)
from version import __version__

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
    "serialize_result",
    "load_result",
    "serialize_config",
    "experiment_metadata",
    "__version__",
]
