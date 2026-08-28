# Centralized exception hierarchy for MIRA.


class MiraError(Exception):
    # Base exception for all MIRA errors.
    pass


class ConfigError(MiraError):
    pass


class ModelError(MiraError):
    # Model loading or inference error.
    pass


class DatasetError(MiraError):
    pass


class CameraError(MiraError):
    pass


class PipelineError(MiraError):
    # Pipeline execution error.
    pass
