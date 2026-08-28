# CLI commands for model evaluation, live webcam inference, and model downloads.

import sys
from pathlib import Path

from src.config import (
    CAMERA_DEFAULT_CONF,
    CAMERA_DEFAULT_REJECT,
    CAMERA_DEFAULT_TARGET_LATENCY_MS,
    DEFAULT_IMGSZ,
    DETECTION_DIR,
    ROOT_DIR,
    get_tflite_imgsz,
    resolve_safe_path,
)
from src.exceptions import ConfigError
from src.model_picker import pick_model
from src.pipeline.models import ModelRegistry
from src.pipeline.registry import register_command

AVAILABLE_MODELS = {
    "mira_exp014.pt": {
        "description": "EXP-014 (YOLO11n, +Roboflow)",
        "category": "detection",
    },
    "mira_exp014_int8.tflite": {
        "description": "EXP-014 INT8 (YOLO11n, +Roboflow)",
        "category": "detection",
    },
    "mira_exp015.pt": {
        "description": "EXP-015 (YOLO11n, +WaRP+TrashNet)",
        "category": "detection",
    },
    "mira_exp015_int8.tflite": {
        "description": "EXP-015 INT8 (YOLO11n, +WaRP+TrashNet)",
        "category": "detection",
    },
    "mira_exp016.pt": {
        "description": "EXP-016 (YOLO11n, +WaRP)",
        "category": "detection",
    },
    "mira_exp016_int8.tflite": {
        "description": "EXP-016 INT8 (YOLO11n, +WaRP)",
        "category": "detection",
    },
    "mira_exp013.pt": {
        "description": "EXP-013 (YOLO11n, TACO+TrashNet)",
        "category": "detection",
    },
    "mira_exp013_int8.tflite": {
        "description": "EXP-013 INT8 (YOLO11n, TACO+TrashNet)",
        "category": "detection",
    },
    "mira_exp018.pt": {
        "description": "EXP-018 (YOLO11n, clean balanced dataset)",
        "category": "detection",
    },
    "mira_exp018_int8.tflite": {
        "description": "EXP-018 INT8 TFLite export",
        "category": "detection",
    },
    "mira_exp018.onnx": {
        "description": "EXP-018 ONNX export",
        "category": "detection",
    },
    "mira_exp019.pt": {
        "description": "EXP-019 (YOLO11n, clean balanced repeatability run)",
        "category": "detection",
    },
    "mira_exp019_int8_320.tflite": {
        "description": "EXP-019 INT8 TFLite export at 320px",
        "category": "detection",
    },
    "mira_exp019_int8_640.tflite": {
        "description": "EXP-019 INT8 TFLite export at 640px",
        "category": "detection",
    },
    "mira_exp019.onnx": {
        "description": "EXP-019 ONNX export",
        "category": "detection",
    },
}


def _resolve_model_filename(model_name: str) -> str:
    raw_path = Path(model_name)
    candidate = (
        (DETECTION_DIR / raw_path).resolve()
        if raw_path.parent == Path(".")
        else resolve_safe_path(raw_path, base_dir=ROOT_DIR)
    )
    try:
        candidate.relative_to(DETECTION_DIR.resolve())
    except ValueError:
        raise ConfigError(f"Model path must be inside {DETECTION_DIR}: {model_name}") from None
    if not candidate.is_file():
        raise FileNotFoundError(candidate)
    return candidate.name


def resolve_detection_data_yaml(explicit_path=None):
    candidates = []
    if explicit_path:
        try:
            candidate = resolve_safe_path(explicit_path, base_dir=ROOT_DIR)
        except ConfigError as e:
            print(f"Error: {e}")
            sys.exit(2)
        if candidate.is_file():
            return candidate
        print(f"Warning: {explicit_path} is not a valid file, searching defaults...")

    # Scan datasets/ for any existing dataset.yaml
    datasets_dir = ROOT_DIR / "datasets"
    if datasets_dir.exists():
        for subdir in sorted(datasets_dir.iterdir()):
            if subdir.is_dir() and not subdir.name.startswith("."):
                yaml_candidate = subdir / "dataset.yaml"
                if yaml_candidate.exists():
                    candidates.append(yaml_candidate)

    for candidate in candidates:
        if candidate.exists():
            return candidate
    raise FileNotFoundError(
        "Could not find a YOLO dataset YAML. Please specify one with --data or generate a dataset using `mira merge`."
    )


def _pick_model_interactive(title="Available models"):
    registry = ModelRegistry()
    registry.discover()
    models = registry.list_models()
    labels = {m["name"]: m["label"] for m in models}
    return pick_model([m["name"] for m in models], labels=labels, title=title)


def _add_eval_yolo_args(parser):
    parser.add_argument(
        "--model", type=str, default=None, nargs="?", help="Model filename. Omit to use interactive picker."
    )
    parser.add_argument("--data", type=str, default=None, help="Optional dataset YAML path.")


@register_command("eval-yolo", "Evaluate YOLO detection models", add_args=_add_eval_yolo_args)
def cmd_eval_yolo(args):
    model = args.model
    if model is None:
        model = _pick_model_interactive("Available detection models")
        if model is None:
            sys.exit(0)
    try:
        model = _resolve_model_filename(model)
    except (ConfigError, FileNotFoundError) as exc:
        print(f"Error: Model file not found: {exc}")
        sys.exit(1)
    model_path = DETECTION_DIR / model
    if not model_path.is_file():
        from src.logger import get_logger

        logger = get_logger(__name__)
        logger.error(f"Model file not found at {model_path}")
        print(f"Error: Model file not found at {model_path}")
        sys.exit(1)
    from ultralytics import YOLO

    data_path = resolve_detection_data_yaml(args.data)
    task_type = "detect"  # Always detect for both .pt and .tflite models
    model = YOLO(str(model_path), task=task_type)
    val_imgsz = get_tflite_imgsz(model_path) if model_path.suffix.lower() == ".tflite" else 640
    model.val(data=str(data_path), imgsz=val_imgsz)


def _add_live_args(parser):
    parser.add_argument(
        "--model", type=str, default=None, nargs="?", help="Model filename. Omit to use interactive picker."
    )
    parser.add_argument("--camera", type=int, default=0, help="Camera device index (default: 0).")
    parser.add_argument(
        "--resolution",
        type=str,
        default="640x360",
        choices=["640x360", "1280x720", "1920x1080"],
        help="Camera capture resolution (default: 640x360).",
    )
    parser.add_argument(
        "--target-latency",
        type=int,
        default=CAMERA_DEFAULT_TARGET_LATENCY_MS,
        help="Target latency in ms (default: 1000; prevents frame skipping).",
    )
    parser.add_argument(
        "--conf",
        type=float,
        default=CAMERA_DEFAULT_CONF,
        help="Confidence threshold (default: 0.25).",
    )
    parser.add_argument(
        "--imgsz",
        type=int,
        default=DEFAULT_IMGSZ,
        help="Inference image size for PyTorch models (default: 640; fixed for TFLite models).",
    )
    parser.add_argument(
        "--reject",
        type=float,
        default=CAMERA_DEFAULT_REJECT,
        help="Reject threshold: uncertain detections below this are labeled 'uncertain' (default: 0.25).",
    )


@register_command("live", "Start real-time webcam detection stream", add_args=_add_live_args)
def cmd_live(args):
    model = args.model
    if model is None:
        model = _pick_model_interactive("Available detection models")
        if model is None:
            sys.exit(0)
    if "classifier" in model.lower():
        print(f"ERROR: '{model}' is a classifier model, not a detector.")
        sys.exit(1)
    from src.inference_engine import InferenceEngine

    try:
        w, h = map(int, args.resolution.split("x"))
    except (ValueError, AttributeError):
        print(f"Error: Invalid resolution format '{args.resolution}'. Use WIDTHxHEIGHT (e.g., 640x480)")
        sys.exit(1)
    engine = InferenceEngine(
        model_name=model,
        camera_index=args.camera,
        cam_width=w,
        cam_height=h,
        target_latency_ms=args.target_latency,
        conf_threshold=args.conf,
        reject_threshold=args.reject,
        imgsz=args.imgsz,
    )
    engine.run()


def _add_download_args(parser):
    parser.add_argument("model_name", nargs="?", default=None, help="Bundled model filename (e.g. mira_exp014.pt).")
    parser.add_argument("--all", action="store_true", help="List all bundled models.")
    parser.add_argument("--list", action="store_true", dest="list_only", help="List bundled models.")


@register_command("download", "List models bundled with the installation", add_args=_add_download_args)
def cmd_download(args):
    registry = ModelRegistry()
    registry.discover()
    bundled = {model["name"]: model for model in registry.list_models()}

    if args.model_name and not args.all and not args.list_only:
        if args.model_name not in bundled:
            print(f"Model '{args.model_name}' is not bundled. Run 'mira models' to see available models.")
            sys.exit(1)
        print(f"{args.model_name} is already bundled at {bundled[args.model_name]['path']}")
        return

    print("\n  Models bundled with mira-ai:")
    for name, model in bundled.items():
        print(f"  {name:<30} {model['label']}")
    print("\n  No model download is required.")
    return
