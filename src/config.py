"""Shared configuration, constants, and utility functions for MIRA."""

import pathlib

import yaml

SCRIPT_DIR = pathlib.Path(__file__).resolve().parent
ROOT_DIR = SCRIPT_DIR.parent

# Load project config
_CONFIG_PATH = ROOT_DIR / "mira.yaml"
try:
    with open(_CONFIG_PATH) as f:
        PROJECT_CONFIG = yaml.safe_load(f)
except FileNotFoundError:
    raise RuntimeError(f"Config file not found: {_CONFIG_PATH}") from None
except yaml.YAMLError as e:
    raise RuntimeError(f"Invalid YAML in {_CONFIG_PATH}: {e}") from None

# Directory paths (derived from config)
REF_DIR = ROOT_DIR / PROJECT_CONFIG["paths"]["reference"]
MODELS_DIR = ROOT_DIR / PROJECT_CONFIG["paths"]["models"]
CLASSIFIER_DIR = MODELS_DIR / "classifier"
DETECTION_DIR = MODELS_DIR / "detection"
DATA_CLASSES_DIR = ROOT_DIR / "data" / "classes"
BYTE_TRACK_CONFIG_PATH = ROOT_DIR / "bytetrack.yaml"

# Class configuration (single source of truth)
CLASS_NAMES: list[str] = PROJECT_CONFIG["classes"]["names"]
NUM_CLASSES: int = PROJECT_CONFIG["classes"]["count"]

# Inference defaults
REJECT_THRESHOLD: float = PROJECT_CONFIG["inference"]["reject_threshold"]

DETECTION_MODEL_LABELS: dict[str, str] = {
    "mira_exp006.pt": "EXP-006 (YOLOv8n, multi-dataset)",
    "mira_exp006_int8.tflite": "EXP-006 INT8 (YOLOv8n, multi-dataset)",
    "mira_exp009_int8.tflite": "EXP-009 INT8 (YOLOv8n, multi-dataset)",
    "mira_exp011.pt": "EXP-011 (YOLOv8n, TACO-only)",
    "mira_exp011_int8.tflite": "EXP-011 INT8 (YOLOv8n, TACO-only)",
    "mira_exp013.pt": "EXP-013 (YOLO11n, TACO+TrashNet)",
    "mira_exp013_int8.tflite": "EXP-013 INT8 (YOLO11n, TACO+TrashNet)",
    "mira_exp014.pt": "EXP-014 (YOLO11n, +Roboflow)",
    "mira_exp014_int8.tflite": "EXP-014 INT8 (YOLO11n, +Roboflow)",
    "mira_exp015.pt": "EXP-015 (YOLO11n, +WaRP+TrashNet)",
    "mira_exp015_int8.tflite": "EXP-015 INT8 (YOLO11n, +WaRP+TrashNet)",
    "mira_exp016.pt": "EXP-016 (YOLO11n, +WaRP)",
    "mira_exp016_int8.tflite": "EXP-016 INT8 (YOLO11n, +WaRP)",
}


def get_project_config() -> dict:
    """Return the full project configuration loaded from mira.yaml."""
    return PROJECT_CONFIG


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
        shape = list(map(int, input_details.get("shape") or input_details.get("shape_signature", [])))
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
        raise RuntimeError("Camera is not opened before setting properties.")
    cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*"MJPG"))
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
    cap.set(cv2.CAP_PROP_FPS, fps)
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
    cap.set(cv2.CAP_PROP_AUTOFOCUS, 0)
    cap.set(cv2.CAP_PROP_AUTO_EXPOSURE, 1)
