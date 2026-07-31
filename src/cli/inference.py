"""CLI commands for model evaluation, live webcam inference, and model downloads."""

import os
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
        "url": "https://huggingface.co/Jeremy341/MIRA-AI/resolve/main/models/detection/mira_exp014.pt",
        "category": "detection",
    },
    "mira_exp014_int8.tflite": {
        "description": "EXP-014 INT8 (YOLO11n, +Roboflow)",
        "url": "https://huggingface.co/Jeremy341/MIRA-AI/resolve/main/models/detection/mira_exp014_int8.tflite",
        "category": "detection",
    },
    "mira_exp015.pt": {
        "description": "EXP-015 (YOLO11n, +WaRP+TrashNet)",
        "url": "https://huggingface.co/Jeremy341/MIRA-AI/resolve/main/models/detection/mira_exp015.pt",
        "category": "detection",
    },
    "mira_exp015_int8.tflite": {
        "description": "EXP-015 INT8 (YOLO11n, +WaRP+TrashNet)",
        "url": "https://huggingface.co/Jeremy341/MIRA-AI/resolve/main/models/detection/mira_exp015_int8.tflite",
        "category": "detection",
    },
    "mira_exp016.pt": {
        "description": "EXP-016 (YOLO11n, +WaRP)",
        "url": "https://huggingface.co/Jeremy341/MIRA-AI/resolve/main/models/detection/mira_exp016.pt",
        "category": "detection",
    },
    "mira_exp016_int8.tflite": {
        "description": "EXP-016 INT8 (YOLO11n, +WaRP)",
        "url": "https://huggingface.co/Jeremy341/MIRA-AI/resolve/main/models/detection/mira_exp016_int8.tflite",
        "category": "detection",
    },
    "mira_exp013.pt": {
        "description": "EXP-013 (YOLO11n, TACO+TrashNet)",
        "url": "https://huggingface.co/Jeremy341/MIRA-AI/resolve/main/models/detection/mira_exp013.pt",
        "category": "detection",
    },
    "mira_exp013_int8.tflite": {
        "description": "EXP-013 INT8 (YOLO11n, TACO+TrashNet)",
        "url": "https://huggingface.co/Jeremy341/MIRA-AI/resolve/main/models/detection/mira_exp013_int8.tflite",
        "category": "detection",
    },
    "mira_exp018.pt": {
        "description": "EXP-018 (YOLO11n, clean balanced dataset)",
        "url": "https://huggingface.co/Jeremy341/MIRA-AI/resolve/main/models/detection/mira_exp018.pt",
        "category": "detection",
    },
    "mira_exp018_int8.tflite": {
        "description": "EXP-018 INT8 TFLite export",
        "url": "https://huggingface.co/Jeremy341/MIRA-AI/resolve/main/models/detection/mira_exp018_int8.tflite",
        "category": "detection",
    },
    "mira_exp018.onnx": {
        "description": "EXP-018 ONNX export",
        "url": "https://huggingface.co/Jeremy341/MIRA-AI/resolve/main/models/detection/mira_exp018.onnx",
        "category": "detection",
    },
    "mira_exp019.pt": {
        "description": "EXP-019 (YOLO11n, clean balanced repeatability run)",
        "url": "https://huggingface.co/Jeremy341/MIRA-AI/resolve/main/models/detection/mira_exp019.pt",
        "category": "detection",
    },
    "mira_exp019_int8_320.tflite": {
        "description": "EXP-019 INT8 TFLite export at 320px",
        "url": "https://huggingface.co/Jeremy341/MIRA-AI/resolve/main/models/detection/mira_exp019_int8_320.tflite",
        "category": "detection",
    },
    "mira_exp019_int8_640.tflite": {
        "description": "EXP-019 INT8 TFLite export at 640px",
        "url": "https://huggingface.co/Jeremy341/MIRA-AI/resolve/main/models/detection/mira_exp019_int8_640.tflite",
        "category": "detection",
    },
    "mira_exp019.onnx": {
        "description": "EXP-019 ONNX export",
        "url": "https://huggingface.co/Jeremy341/MIRA-AI/resolve/main/models/detection/mira_exp019.onnx",
        "category": "detection",
    },
}


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
    """Show interactive picker for detection models. Returns model name or None."""
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
    if os.sep in model or "/" in model or "\\" in model or ".." in model:
        print(f"Error: Invalid model name '{model}'. Use a simple filename, not a path.")
        sys.exit(1)
    model_path = DETECTION_DIR / model
    if not model_path.exists():
        from src.logger import get_logger

        logger = get_logger(__name__)
        logger.error(f"Model file not found at {model_path}")
        print(f"Error: Model file not found at {model_path}")
        sys.exit(1)
    from ultralytics import YOLO

    data_path = resolve_detection_data_yaml(args.data)
    task_type = "detect"  # Always detect for both .pt and .tflite models
    model = YOLO(str(model_path), task=task_type)
    val_imgsz = get_tflite_imgsz(model_path) if model_path.suffix == ".tflite" else 640
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
        help="Reject threshold: uncertain detections below this are labeled 'unsicher' (default: 0.25).",
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
    parser.add_argument("model_name", nargs="?", default=None, help="Model filename to download (e.g. mira_exp014.pt).")
    parser.add_argument("--all", action="store_true", help="Download all available models.")
    parser.add_argument(
        "--list", action="store_true", dest="list_only", help="List available models without downloading."
    )


@register_command("download", "Download pretrained models from Hugging Face", add_args=_add_download_args)
def cmd_download(args):
    if args.list_only:
        print("\n  Available models:")
        print(f"  {'Name':<30} {'Description'}")
        print("  " + "-" * 60)
        for name, info in AVAILABLE_MODELS.items():
            exists = (DETECTION_DIR / name).exists()
            status = " (already downloaded)" if exists else ""
            print(f"  {name:<30} {info['description']}{status}")
        print()
        return

    if args.all:
        models_to_download = list(AVAILABLE_MODELS.items())
    elif args.model_name:
        if args.model_name not in AVAILABLE_MODELS:
            print(f"Unknown model '{args.model_name}'. Run 'mira download --list' to see available models.")
            sys.exit(1)
        models_to_download = [(args.model_name, AVAILABLE_MODELS[args.model_name])]
    else:
        print("\n  Available models:")
        names = list(AVAILABLE_MODELS.keys())
        for i, name in enumerate(names, 1):
            exists = (DETECTION_DIR / name).exists()
            status = " (downloaded)" if exists else ""
            print(f"  [{i}] {name}{status} — {AVAILABLE_MODELS[name]['description']}")
        print()
        choice = input("  Enter model name or number: ").strip()
        if choice.isdigit() and 1 <= int(choice) <= len(names):
            choice = names[int(choice) - 1]
        if choice not in AVAILABLE_MODELS:
            print(f"  Invalid choice '{choice}'.")
            sys.exit(1)
        models_to_download = [(choice, AVAILABLE_MODELS[choice])]

    failed = []
    for name, info in models_to_download:
        dest_dir = DETECTION_DIR
        dest_path = dest_dir / name

        if dest_path.exists():
            print(f"  {name} already exists at {dest_path}")
            continue

        dest_dir.mkdir(parents=True, exist_ok=True)
        url = info["url"]
        print(f"  Downloading {name}...")
        print(f"    URL: {url}")

        try:
            _download_with_progress(url, dest_path)
            print(f"    Saved to {dest_path}")
        except Exception as e:
            print(f"    Download failed: {e}")
            if dest_path.exists():
                dest_path.unlink()
            failed.append(name)
            continue

    if failed:
        print(f"\nFailed to download: {', '.join(failed)}")
        sys.exit(1)

    print("\nDone.")


def _download_with_progress(url: str, dest: Path):
    """Download a file with a progress indicator."""
    import hashlib
    import urllib.request

    req = urllib.request.Request(url, headers={"User-Agent": "MIRA-AI/1.0"})
    with urllib.request.urlopen(req, timeout=120) as resp:
        total = resp.headers.get("Content-Length")
        total = int(total) if total else None
        downloaded = 0
        block_size = 8192
        sha256 = hashlib.sha256()

        with open(dest, "wb") as f:
            while True:
                chunk = resp.read(block_size)
                if not chunk:
                    break
                f.write(chunk)
                sha256.update(chunk)
                downloaded += len(chunk)
                if total:
                    pct = downloaded * 100 / total
                    bar_len = 30
                    filled = int(bar_len * downloaded // total)
                    bar = "=" * filled + "-" * (bar_len - filled)
                    print(f"\r    [{bar}] {pct:.0f}% ({downloaded}/{total})", end="", flush=True)
                else:
                    print(f"\r    Downloaded {downloaded} bytes", end="", flush=True)
        print()
        print(f"    SHA-256: {sha256.hexdigest()}")
