"""MIRA — Machine Intelligence for Recycling Automation."""

from .exceptions import MiraError, ConfigError, ModelError, DatasetError, CameraError, PipelineError
from .version import __version__

__all__ = [
    "__version__",
    "MiraError",
    "ConfigError",
    "ModelError",
    "DatasetError",
    "CameraError",
    "PipelineError",
]
