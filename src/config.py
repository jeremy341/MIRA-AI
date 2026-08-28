# config for MIRA - paths, mira.yaml loading, defaults

from __future__ import annotations

import os
import pathlib
from copy import deepcopy
from types import MappingProxyType
from typing import Any

import yaml

from .exceptions import CameraError, ConfigError
from .logger import get_logger

logger = get_logger(__name__)

SRC_DIR = pathlib.Path(__file__).resolve().parent
ASSETS_DIR = SRC_DIR / "assets"


def _discover_project_root() -> pathlib.Path:
    # Find project root via MIRA_HOME or nearest mira.yaml.
    env_home = os.environ.get("MIRA_HOME")
    if env_home:
        return pathlib.Path(env_home).expanduser().resolve()
    cwd = pathlib.Path.cwd()
    for candidate in [cwd, *cwd.parents]:
        if (candidate / "mira.yaml").exists():
            return candidate
    return cwd


ROOT_DIR = _discover_project_root()


def _load_project_config(root: pathlib.Path) -> tuple[dict[str, Any], pathlib.Path | None]:
    config_path = root / "mira.yaml"
    if config_path.exists():
        try:
            with open(config_path, encoding="utf-8") as f:
                return yaml.safe_load(f), config_path
        except yaml.YAMLError as e:
            raise ConfigError(f"Invalid YAML in {config_path}: {e}") from None
    default_path = ASSETS_DIR / "mira.yaml"
    if default_path.exists():
        with open(default_path, encoding="utf-8") as f:
            return yaml.safe_load(f), None
    raise ConfigError(
        f"Config file not found: {config_path}. Run MIRA from a directory containing mira.yaml or set MIRA_HOME."
    )


PROJECT_CONFIG, _CONFIG_PATH = _load_project_config(ROOT_DIR)
_PROJECT_CONFIG_FROZEN: MappingProxyType = MappingProxyType(PROJECT_CONFIG)


def _validate_project_config(cfg: dict[str, Any]) -> list[str]:
    # Validate mira.yaml and return errors.
    errors: list[str] = []
    if not isinstance(cfg, dict):
        errors.append("mira.yaml must contain a YAML mapping (key-value pairs)")
        return errors
    for section in ("classes", "training", "inference"):
        if section not in cfg:
            errors.append(f"Missing required section: '{section}'")
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
    training = cfg.get("training", {})
    if isinstance(training, dict):
        for key, min_val in (("default_epochs", 1), ("default_batch_size", 1), ("default_imgsz", 1)):
            val = training.get(key)
            if val is not None and (not isinstance(val, int) or val < min_val):
                errors.append(f"'training.{key}' must be an integer >= {min_val}")
        lr = training.get("default_lr")
        if lr is not None and (not isinstance(lr, (int, float)) or lr <= 0):
            errors.append("'training.default_lr' must be a positive number")
        patience = training.get("early_stopping_patience")
        if patience is not None and (not isinstance(patience, int) or patience < 1):
            errors.append("'training.early_stopping_patience' must be a positive integer")
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


_CONFIG_ERRORS = _validate_project_config(PROJECT_CONFIG)
if _CONFIG_ERRORS:
    for err in _CONFIG_ERRORS:
        logger.error(f"Config validation error: {err}")
    raise ConfigError(f"mira.yaml validation failed with {_CONFIG_ERRORS} error(s). See above for details.")

MODELS_DIR = ROOT_DIR / PROJECT_CONFIG.get("paths", {}).get("models", "models")
PROJECT_DETECTION_DIR = MODELS_DIR / "detection"
PACKAGED_DETECTION_DIR = ASSETS_DIR / "models" / "detection"
if PROJECT_DETECTION_DIR.exists() and any(
    p.suffix.lower() in {".pt", ".pth", ".tflite", ".onnx"} for p in PROJECT_DETECTION_DIR.iterdir()
):
    DETECTION_DIR = PROJECT_DETECTION_DIR
else:
    DETECTION_DIR = PACKAGED_DETECTION_DIR
DATA_CLASSES_DIR = ROOT_DIR / "data" / "classes"
BYTE_TRACK_CONFIG_PATH = ROOT_DIR / "bytetrack.yaml"
if not BYTE_TRACK_CONFIG_PATH.exists():
    BYTE_TRACK_CONFIG_PATH = ASSETS_DIR / "bytetrack.yaml"

_CLASSES = PROJECT_CONFIG.get("classes", {})
CLASS_NAMES: list[str] = _CLASSES.get("names", ["glass", "metal", "paper", "plastic", "trash"])
NUM_CLASSES: int = _CLASSES.get("count", len(CLASS_NAMES))


def get_project_config() -> dict:
    # Return loaded mira.yaml as dict.
    return deepcopy(dict(_PROJECT_CONFIG_FROZEN))


def get_tflite_imgsz(model_path: pathlib.Path) -> int:
    # Get imgsize from TFLite tensor shape.
    interp = None
    for import_path, cls_name in [
        ("ai_edge_litert.interpreter", "Interpreter"),
        ("tflite_runtime.interpreter", "Interpreter"),
        ("tensorflow.lite.python.interpreter", "Interpreter"),
    ]:
        try:
            mod = __import__(import_path, fromlist=[cls_name])
            interp = getattr(mod, cls_name)(model_path=str(model_path))
            interp.allocate_tensors()
            break
        except (ImportError, AttributeError, RuntimeError, OSError):
            continue
    if interp is None:
        raise ImportError("No TFLite interpreter found (install tflite_runtime or tensorflow).")
    try:
        input_details = interp.get_input_details()[0]
        shape_raw = input_details.get("shape")
        if shape_raw is None:
            shape_raw = input_details.get("shape_signature", [])
        shape = list(map(int, shape_raw))
        if any(d <= 0 for d in shape):
            signature = input_details.get("shape_signature")
            if signature is not None:
                signature_shape = list(map(int, signature))
                if all(d > 0 for d in signature_shape):
                    shape = signature_shape
            if any(d <= 0 for d in shape):
                raise ValueError(f"Dynamic or invalid tensor shape in TFLite model: {shape}")
        if not shape:
            raise ValueError("Empty tensor shape in TFLite model")
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


def setup_camera_properties(
    cap,
    width: int,
    height: int,
    fps: int = 30,
    autofocus: bool = False,
    auto_exposure: bool = True,
):
    import cv2

    if not cap.isOpened():
        raise CameraError("Camera is not opened before setting properties.")
    properties = (
        (cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*"MJPG")),
        (cv2.CAP_PROP_FRAME_WIDTH, width),
        (cv2.CAP_PROP_FRAME_HEIGHT, height),
        (cv2.CAP_PROP_FPS, fps),
        (cv2.CAP_PROP_BUFFERSIZE, 1),
        (cv2.CAP_PROP_AUTOFOCUS, int(autofocus)),
        (cv2.CAP_PROP_AUTO_EXPOSURE, int(auto_exposure)),
    )
    for property_id, value in properties:
        cap.set(property_id, value)


_TRAINING = PROJECT_CONFIG.get("training", {})
_INFERENCE = PROJECT_CONFIG.get("inference", {})
REJECT_THRESHOLD: float = _INFERENCE.get("reject_threshold", 0.55)
DEFAULT_CONF: float = _INFERENCE.get("default_conf", 0.5)
DEFAULT_IOU: float = _INFERENCE.get("default_iou", 0.45)
DEFAULT_IMGSZ: int = _TRAINING.get("default_imgsz", 640)
DEFAULT_MODEL: str = _TRAINING.get("default_model", "mira_exp014.pt")
TFLITE_INT8_CONF: float = 0.25
CAMERA_DEFAULT_CONF: float = 0.25
CAMERA_DEFAULT_REJECT: float = 0.25
CAMERA_DEFAULT_TARGET_LATENCY_MS: int = 1000


def validate_config() -> list[str]:
    # Re-validate mira.yaml.
    return _validate_project_config(PROJECT_CONFIG)


def resolve_safe_path(user_path: str | pathlib.Path, base_dir: pathlib.Path | None = None) -> pathlib.Path:
    # Resolve user path inside base_dir, block traversal.
    base = base_dir or ROOT_DIR
    path = pathlib.Path(user_path).expanduser()
    if not path.is_absolute():
        path = (base / path).resolve()
    else:
        path = path.resolve()
    try:
        path.relative_to(base.resolve())
    except ValueError:
        raise ConfigError(f"Path traversal detected: '{user_path}' resolves outside the project directory.") from None
    return path
