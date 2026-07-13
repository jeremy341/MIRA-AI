"""Shared configuration, constants, and utility functions for MIRA."""
import pathlib

SCRIPT_DIR = pathlib.Path(__file__).resolve().parent
ROOT_DIR = SCRIPT_DIR.parent
REF_DIR = ROOT_DIR / "reference"
MODELS_DIR = ROOT_DIR / "models"
CLASSIFIER_DIR = MODELS_DIR / "classifier"
DETECTION_DIR = MODELS_DIR / "detection"
DATA_CLASSES_DIR = ROOT_DIR / "data" / "classes"

CLASS_NAMES: list[str] = ["glass", "metal", "paper", "plastic", "trash"]

CLASSIFIER_MODELS: list[str] = [
    "mira_classifier_baseline.keras",
    "mira_classifier_transfer.keras",
    "mira_classifier_tuned.keras",
    "mira_classifier_fp32.tflite",
    "mira_classifier_int8.tflite",
]

DETECTION_MODEL_LABELS: dict[str, str] = {
    "mira_exp006.pt": "EXP-006 (YOLOv8n, multi-dataset)",
    "mira_exp006_int8.tflite": "EXP-006 INT8 (YOLOv8n, multi-dataset)",
    "mira_exp009_int8.tflite": "EXP-009 INT8 (inflated mAP)",
    "mira_exp011.pt": "EXP-011 (YOLOv8n, TACO-only)",
    "mira_exp011_int8.tflite": "EXP-011 INT8 (YOLOv8n, TACO-only)",
    "mira_exp013.pt": "EXP-013 (YOLO11n, TACO+TrashNet)",
    "mira_exp013_int8.tflite": "EXP-013 INT8 (YOLO11n, TACO+TrashNet)",
    "mira_exp014.pt": "EXP-014 (YOLO11n, +Roboflow)",
    "mira_exp014_int8.tflite": "EXP-014 INT8 (YOLO11n, +Roboflow)",
    "mira_exp015.pt": "EXP-015 (YOLO11n, +WaRP)",
    "mira_exp015_int8.tflite": "EXP-015 INT8 (YOLO11n, +WaRP)",
}


def get_detection_models() -> list[str]:
    """Return sorted list of detection model filenames."""
    return sorted(
        p.name for p in DETECTION_DIR.glob("*")
        if p.suffix in (".pt", ".tflite") and "classifier" not in p.name.lower()
    )


def get_tflite_imgsz(model_path: pathlib.Path) -> int:
    """Read input image size from a TFLite model's tensor shape."""
    from ai_edge_litert.interpreter import Interpreter as LiteRTInterpreter
    tmp = LiteRTInterpreter(model_path=str(model_path))
    shape = tmp.get_input_details()[0]["shape"]
    del tmp
    return int(max(shape))
