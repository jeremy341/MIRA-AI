import argparse
import pathlib
import subprocess
import sys
from model_picker import pick_model

from config import ROOT_DIR, SCRIPT_DIR, REF_DIR, DETECTION_DIR, DETECTION_MODEL_LABELS as MODEL_LABELS, get_detection_models, get_tflite_imgsz


def run_script(script_path, args_list=None):
    if not script_path.exists():
        raise FileNotFoundError(f"Script not found at {script_path}")
    cmd = [sys.executable, str(script_path)]
    if args_list:
        cmd.extend(args_list)
    subprocess.run(cmd, check=True)


def resolve_detection_data_yaml(explicit_path=None):
    candidates = []
    if explicit_path:
        candidate = pathlib.Path(explicit_path).expanduser()
        if not candidate.is_absolute():
            candidate = (ROOT_DIR / candidate).resolve()
        candidates.append(candidate)
    candidates.extend([
        ROOT_DIR / "datasets" / "mira_v2" / "dataset.yaml",
        ROOT_DIR / "datasets" / "mira_v1" / "dataset.yaml",
    ])
    for candidate in candidates:
        if candidate.exists():
            return candidate
    raise FileNotFoundError(
        "Could not find a YOLO dataset YAML. Looked for datasets/mira_v2/dataset.yaml "
        "and datasets/mira_v1/dataset.yaml."
    )


def _pick_model_interactive(title="Available models"):
    """Show interactive picker for detection models. Returns model name or None."""
    models = get_detection_models()
    return pick_model(models, labels=MODEL_LABELS, title=title)


def main():
    parser = argparse.ArgumentParser(
        description="MIRA - Machine Intelligence for Recycling Automation Developer CLI"
    )
    subparsers = parser.add_subparsers(dest="command", help="Available subcommands")

    subparsers.add_parser("data-build", help="Build YOLO detection dataset from classification folder")
    subparsers.add_parser("data-viz", help="Visualize dataset distribution and sample grids")

    subparsers.add_parser("train-baseline", help="Train baseline CNN classification model (EXP-001)")
    subparsers.add_parser("train-transfer", help="Train frozen MobileNetV2 classification model (EXP-002)")
    subparsers.add_parser("train-tune", help="Train fine-tuned MobileNetV2 classification model (EXP-003)")
    subparsers.add_parser("train-detection", help="Initiate local YOLOv8 training pipeline (legacy)")

    subparsers.add_parser("quant-class", help="Execute Keras post-training quantization (EXP-004)")
    subparsers.add_parser("quant-yolo", help="Execute YOLOv8 quantization")

    eval_class_parser = subparsers.add_parser("eval-class", help="Evaluate classification models (EXP-001 - EXP-004)")
    eval_class_parser.add_argument("--model", type=str, required=True, help="Model filename in /models")
    eval_class_parser.add_argument("--exp", type=str, required=True, help="Experiment folder name")

    eval_yolo_parser = subparsers.add_parser("eval-yolo", help="Evaluate YOLOv8 detection models")
    eval_yolo_parser.add_argument("--model", type=str, default=None, nargs="?", help="Model filename. Omit to use interactive picker.")
    eval_yolo_parser.add_argument("--data", type=str, default=None, help="Optional dataset YAML path.")

    subparsers.add_parser("field-bench", help="Field benchmark: capture real images, test all models, compare accuracy")

    live_parser = subparsers.add_parser("live", help="Start real-time YOLOv8 webcam tracking stream")
    live_parser.add_argument("--model", type=str, default=None, nargs="?", help="Model filename. Omit to use interactive picker.")
    live_parser.add_argument("--camera", type=int, default=0, help="Camera device index (default: 0).")
    live_parser.add_argument("--resolution", type=str, default="640x360", choices=["640x360", "1280x720", "1920x1080"],
                             help="Camera capture resolution (default: 640x360).")
    live_parser.add_argument("--target-latency", type=int, default=50, help="Target latency in ms (default: 50).")
    live_parser.add_argument("--conf", type=float, default=0.5, help="Confidence threshold (default: 0.5).")
    subparsers.add_parser("dashboard", help="Launch Streamlit web control center")

    args = parser.parse_args()

    if args.command == "data-build":
        run_script(REF_DIR / "build_detector_dataset.py")
    elif args.command == "data-viz":
        run_script(SCRIPT_DIR / "visualize_classifier_dataset.py")
    elif args.command == "train-baseline":
        run_script(REF_DIR / "train_classifier_baseline.py")
    elif args.command == "train-transfer":
        run_script(REF_DIR / "train_classifier_transfer.py")
    elif args.command == "train-tune":
        run_script(REF_DIR / "train_classifier_finetune.py")
    elif args.command == "train-detection":
        run_script(REF_DIR / "train_detector.py")
    elif args.command == "quant-class":
        run_script(REF_DIR / "quantize_classifier.py")
    elif args.command == "quant-yolo":
        run_script(REF_DIR / "quantize_detector.py")
    elif args.command == "field-bench":
        run_script(SCRIPT_DIR / "field_benchmark.py")
    elif args.command == "live":
        model = args.model
        if model is None:
            model = _pick_model_interactive("Available detection models")
            if model is None:
                sys.exit(0)
        if "classifier" in model.lower():
            print(f"ERROR: '{model}' is a classifier model, not a detector.")
            sys.exit(1)
        run_script(SCRIPT_DIR / "live_detector.py", [
            "--model", model,
            "--camera", str(args.camera),
            "--resolution", args.resolution,
            "--target-latency", str(args.target_latency),
            "--conf", str(args.conf),
        ])
    elif args.command == "dashboard":
        print("Launching Streamlit web server...")
        subprocess.run(["streamlit", "run", str(SCRIPT_DIR / "dashboard.py")], check=True)
    elif args.command == "eval-class":
        run_script(REF_DIR / "evaluate_classifier.py", ["--model", args.model, "--exp", args.exp])
    elif args.command == "eval-yolo":
        model = args.model
        if model is None:
            model = _pick_model_interactive("Available detection models")
            if model is None:
                sys.exit(0)
        model_path = DETECTION_DIR / model
        if not model_path.exists():
            raise FileNotFoundError(f"Model file not found at {model_path}")
        from ultralytics import YOLO
        data_path = resolve_detection_data_yaml(args.data)
        task_type = "detect" if model_path.suffix == ".tflite" else None
        model = YOLO(str(model_path), task=task_type)
        val_imgsz = get_tflite_imgsz(model_path) if model_path.suffix == ".tflite" else 640
        model.val(data=str(data_path), imgsz=val_imgsz)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()

