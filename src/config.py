"""Shared configuration, constants, and utility functions for MIRA."""

from __future__ import annotations

import pathlib
from types import MappingProxyType
from typing import Any

import yaml

from .exceptions import CameraError, ConfigError
from .logger import get_logger

logger = get_logger(__name__)

SRC_DIR = pathlib.Path(__file__).resolve().parent
ROOT_DIR = SRC_DIR.parent
SCRIPT_DIR = SRC_DIR  # backward compatibility — SRC_DIR is preferred

# Load project config
_CONFIG_PATH = ROOT_DIR / "mira.yaml"
try:
    with open(_CONFIG_PATH, encoding="utf-8") as f:
        PROJECT_CONFIG = yaml.safe_load(f)
except FileNotFoundError:
    raise ConfigError(f"Config file not found: {_CONFIG_PATH}") from None
except yaml.YAMLError as e:
    raise ConfigError(f"Invalid YAML in {_CONFIG_PATH}: {e}") from None


def _validate_project_config(cfg: dict[str, Any]) -> list[str]:
    """Validate the loaded project configuration and return a list of errors."""
    errors: list[str] = []

    if not isinstance(cfg, dict):
        errors.append("mira.yaml must contain a YAML mapping (key-value pairs)")
        return errors

    # Required sections
    for section in ("classes", "training", "inference"):
        if section not in cfg:
            errors.append(f"Missing required section: '{section}'")

    # Classes validation
    classes = cfg.get("classes", {})
    if not isinstance(classes, dict):
        errors.append("'classes' must be a mapping")
    else:
        names = classes.get("names")
        if not names:
            errors.append("'classes.names' must be a non-empty list of class names")
        elif not isinstance(names, list) or not all(isinstance(n, str) for n in names):
            errors.append("'classes.names' must be a list of strings")
        count = classes.get("count")
        if count is not None and (not isinstance(count, int) or count < 1):
            errors.append("'classes.count' must be a positive integer")
        if names and count is not None and len(names) != count:
            errors.append(f"'classes.count' ({count}) does not match number of names ({len(names)})")

    # Training validation
    training = cfg.get("training", {})
    if isinstance(training, dict):
        for key, min_val in (
            ("default_epochs", 1),
            ("default_batch_size", 1),
            ("default_imgsz", 1),
        ):
            val = training.get(key)
            if val is not None and (not isinstance(val, int) or val < min_val):
                errors.append(f"'training.{key}' must be an integer >= {min_val}")
        lr = training.get("default_lr")
        if lr is not None and (not isinstance(lr, (int, float)) or lr <= 0):
            errors.append("'training.default_lr' must be a positive number")
        patience = training.get("early_stopping_patience")
        if patience is not None and (not isinstance(patience, int) or patience < 1):
            errors.append("'training.early_stopping_patience' must be a positive integer")

    # Inference validation
    inference = cfg.get("inference", {})
    if isinstance(inference, dict):
        reject = inference.get("reject_threshold")
        if reject is not None and (not isinstance(reject, (int, float)) or not 0 < reject < 1):
            errors.append("'inference.reject_threshold' must be a float in (0, 1)")
        conf = inference.get("default_conf")
        if conf is not None and (not isinstance(conf, (int, float)) or not 0 < conf < 1):
            errors.append("'inference.default_conf' must be a float in (0, 1)")
        iou = inference.get("default_iou")
        if iou is not None and (not isinstance(iou, (int, float)) or not 0 < iou < 1):
            errors.append("'inference.default_iou' must be a float in (0, 1)")

    return errors


# Validate on import
_CONFIG_ERRORS = _validate_project_config(PROJECT_CONFIG)
if _CONFIG_ERRORS:
    for err in _CONFIG_ERRORS:
        logger.error(f"Config validation error: {err}")
    raise ConfigError(f"mira.yaml validation failed with {_CONFIG_ERRORS} error(s). See above for details.")

# Directory paths (derived from config)
MODELS_DIR = ROOT_DIR / PROJECT_CONFIG.get("paths", {}).get("models", "models")
DETECTION_DIR = MODELS_DIR / "detection"
DATA_CLASSES_DIR = ROOT_DIR / "data" / "classes"
BYTE_TRACK_CONFIG_PATH = ROOT_DIR / "bytetrack.yaml"

# Class configuration (single source of truth)
_RAW_CLASSES = PROJECT_CONFIG.get("classes", {})
CLASS_NAMES: list[str] = _RAW_CLASSES.get("names", ["glass", "metal", "paper", "plastic", "trash"])
NUM_CLASSES: int = _RAW_CLASSES.get("count", len(CLASS_NAMES))

# Training defaults
_TRAINING = PROJECT_CONFIG.get("training", {})

# Inference defaults
_INFERENCE = PROJECT_CONFIG.get("inference", {})
REJECT_THRESHOLD: float = _INFERENCE.get("reject_threshold", 0.55)

# Centralized numeric defaults
DEFAULT_CONF: float = _INFERENCE.get("default_conf", 0.5)
DEFAULT_IOU: float = _INFERENCE.get("default_iou", 0.45)
DEFAULT_IMGSZ: int = _TRAINING.get("default_imgsz", 640)
DEFAULT_MODEL: str = _TRAINING.get("default_model", "yolo11n.pt")
TFLITE_INT8_CONF: float = 0.25

# Legacy model labels — kept for backward compatibility.
# New models are discovered dynamically by ModelRegistry.
# To add a label for a model, create a YAML sidecar file in models/detection/.
DETECTION_MODEL_LABELS: dict[str, str] = {}

_PROJECT_CONFIG_FROZEN: MappingProxyType = MappingProxyType(PROJECT_CONFIG)


def get_project_config() -> dict:
    """Return the full project configuration loaded from mira.yaml."""
    return _PROJECT_CONFIG_FROZEN


def validate_config() -> list[str]:
    """Re-validate the current project configuration and return any errors."""
    return _validate_project_config(PROJECT_CONFIG)


def get_detection_models() -> list[str]:
    """Return sorted list of detection model filenames."""
    return sorted(
        p.name for p in DETECTION_DIR.glob("*") if p.suffix in (".pt", ".tflite") and "classifier" not in p.name.lower()
    )


def get_tflite_imgsz(model_path: pathlib.Path) -> int:
    """Read input image size from a TFLite model's tensor shape."""
    interp = None
    for import_path, cls_name in [
        ("ai_edge_litert.interpreter", "Interpreter"),
        ("tflite_runtime.interpreter", "Interpreter"),
        ("tensorflow.lite.python.interpreter", "Interpreter"),
    ]:
        try:
            mod = __import__(import_path, fromlist=[cls_name])
            interp = getattr(mod, cls_name)(model_path=str(model_path))
            break
        except Exception:
            continue
    if interp is None:
        raise ImportError("No TFLite interpreter found (install tflite_runtime or tensorflow).")
    try:
        input_details = interp.get_input_details()[0]
        shape_raw = input_details.get("shape")
        if shape_raw is None:
            shape_raw = input_details.get("shape_signature", [])
        shape = list(map(int, shape_raw))
        if len(shape) == 4:
            if shape[1] in (1, 3):
                h, w = shape[2], shape[3]
            elif shape[3] in (1, 3):
                h, w = shape[1], shape[2]
            else:
                h, w = shape[1], shape[2]
            return int(max(h, w))
        elif len(shape) == 3:
            return int(max(shape[1], shape[2]))
        return int(max(shape))
    finally:
        try:
            del interp
        except Exception:
            pass


def setup_camera_properties(cap, width: int, height: int, fps: int = 30):
    import cv2

    if not cap.isOpened():
        raise CameraError("Camera is not opened before setting properties.")
    cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*"MJPG"))
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
    cap.set(cv2.CAP_PROP_FPS, fps)
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
    cap.set(cv2.CAP_PROP_AUTOFOCUS, 0)
    cap.set(cv2.CAP_PROP_AUTO_EXPOSURE, 1)


def resolve_safe_path(user_path: str | pathlib.Path, base_dir: pathlib.Path | None = None) -> pathlib.Path:
    """Resolve a user-provided path safely, preventing path traversal.

    Args:
        user_path: The path string provided by the user.
        base_dir: The directory that the resolved path must be within.
                  Defaults to ROOT_DIR.

    Returns:
        The resolved Path.

    Raises:
        ConfigError: If the path escapes the base directory.
    """
    base = base_dir or ROOT_DIR
    path = pathlib.Path(user_path).expanduser()
    if not path.is_absolute():
        path = (base / path).resolve()
    else:
        path = path.resolve()

    # Ensure the resolved path is within the base directory
    try:
        path.relative_to(base.resolve())
    except ValueError:
        raise ConfigError(f"Path traversal detected: '{user_path}' resolves outside the project directory.") from None
    return path
