"""Centralized exception hierarchy for MIRA."""


class MiraError(Exception):
    """Base exception for all MIRA errors."""


class ConfigError(MiraError):
    """Configuration loading or validation error."""


class ModelError(MiraError):
    """Model loading or inference error."""


class DatasetError(MiraError):
    """Dataset loading or merge error."""


class CameraError(MiraError):
    """Camera initialization or streaming error."""


class PipelineError(MiraError):
    """Pipeline execution error."""
