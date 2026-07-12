import argparse
import pathlib
import subprocess
import sys

# PATH RESOLUTION
SCRIPT_DIR = pathlib.Path(__file__).resolve().parent
ROOT_DIR = SCRIPT_DIR.parent
REF_DIR = ROOT_DIR / "reference"


def run_script(script_path, args_list=None):
    """Run a Python helper script and fail loudly if it exits with an error."""
    if not script_path.exists():
        raise FileNotFoundError(f"Script not found at {script_path}")

    cmd = [sys.executable, str(script_path)]
    if args_list:
        cmd.extend(args_list)

    subprocess.run(cmd, check=True)


def resolve_detection_data_yaml(explicit_path=None):
    """Find the YOLO dataset YAML from the current repo layout."""
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


def main():
    parser = argparse.ArgumentParser(
        description="MIRA - Machine Intelligence for Recycling Automation Developer CLI"
    )
    subparsers = parser.add_subparsers(dest="command", help="Available subcommands")

    # --- DATA COMMANDS ---
    subparsers.add_parser("data-build", help="Build the pristine tabletop YOLO dataset")
    subparsers.add_parser("data-viz", help="Visualize dataset distribution and sample grids")

    # --- TRAINING COMMANDS (STAGE A) ---
    subparsers.add_parser("train-baseline", help="Train baseline CNN classification model (EXP-001)")
    subparsers.add_parser("train-transfer", help="Train frozen MobileNetV2 classification model (EXP-002)")
    subparsers.add_parser("train-tune", help="Train fine-tuned MobileNetV2 classification model (EXP-003)")

    # --- TRAINING COMMANDS (STAGE B) ---
    subparsers.add_parser("train-detection", help="Initiate local YOLOv8 training pipeline")

    # --- QUANTIZATION COMMANDS ---
    subparsers.add_parser("quant-class", help="Execute Keras post-training quantization (EXP-004)")
    subparsers.add_parser("quant-yolo", help="Execute YOLOv8 quantization")

    # --- EVALUATION COMMANDS ---
    eval_class_parser = subparsers.add_parser("eval-class", help="Evaluate classification models (EXP-001 - EXP-004)")
    eval_class_parser.add_argument("--model", type=str, required=True, help="Model filename in /models")
    eval_class_parser.add_argument("--exp", type=str, required=True, help="Experiment folder name")

    eval_yolo_parser = subparsers.add_parser("eval-yolo", help="Evaluate YOLOv8 detection models")
    eval_yolo_parser.add_argument("--model", type=str, required=True, help="Model filename in /models")
    eval_yolo_parser.add_argument(
        "--data",
        type=str,
        default=None,
        help="Optional dataset YAML path. Defaults to the first matching YOLO dataset in the repo.",
    )

    # --- DEPLOYMENT COMMANDS ---
    live_parser = subparsers.add_parser("live", help="Start real-time YOLOv8 webcam tracking stream")
    live_parser.add_argument(
        "--model", type=str, default="mira_detector_wild.pt",
        help="Model filename inside models/ (default: mira_detector_wild.pt)."
    )
    live_parser.add_argument(
        "--camera", type=int, default=0,
        help="Camera device index (default: 0). Use --camera 1 for a second camera."
    )
    live_parser.add_argument(
        "--resolution", type=str, default="640x360",
        choices=["640x360", "1280x720", "1920x1080"],
        help="Camera capture resolution (default: 640x360). Model inference resolution "
             "is fixed at imgsz=640 regardless of this setting."
    )
    live_parser.add_argument(
        "--target-latency", type=int, default=50,
        help="Target latency in ms (default: 50). Frames are skipped to meet target."
    )
    live_parser.add_argument(
        "--conf", type=float, default=0.5,
        help="Confidence threshold (default: 0.5). Higher = fewer false positives."
    )
    subparsers.add_parser("dashboard", help="Launch Streamlit web control center")

    args = parser.parse_args()

    # COMMAND ROUTING
    if args.command == "data-build":
        run_script(REF_DIR / "build_detection_dataset.py")
    elif args.command == "data-viz":
        run_script(SCRIPT_DIR / "visualize_dataset.py")
    elif args.command == "train-baseline":
        run_script(REF_DIR / "train_baseline.py")
    elif args.command == "train-transfer":
        run_script(REF_DIR / "train_transfer.py")
    elif args.command == "train-tune":
        run_script(REF_DIR / "train_fine_tune.py")
    elif args.command == "train-detection":
        run_script(REF_DIR / "train_detection.py")
    elif args.command == "quant-class":
        run_script(REF_DIR / "quantize.py")
    elif args.command == "quant-yolo":
        run_script(REF_DIR / "quantize_yolo.py")
    elif args.command == "live":
        if "classifier" in args.model.lower():
            print(f"ERROR: '{args.model}' is a classifier model, not a detector.")
            print("Live detection requires a detection model (.pt or detection .tflite).")
            print(f"Use: mira eval-class --model {args.model} --exp <folder>")
            sys.exit(1)
        run_script(SCRIPT_DIR / "live_detection.py", [
            "--model",          args.model,
            "--camera",         str(args.camera),
            "--resolution",     args.resolution,
            "--target-latency", str(args.target_latency),
            "--conf",           str(args.conf),
        ])
    elif args.command == "dashboard":
        print("Launching Streamlit web server...")
        subprocess.run(["streamlit", "run", str(SCRIPT_DIR / "dashboard.py")], check=True)
    elif args.command == "eval-class":
        run_script(REF_DIR / "evaluate.py", ["--model", args.model, "--exp", args.exp])
    elif args.command == "eval-yolo":
        model_path = ROOT_DIR / "models" / args.model
        if not model_path.exists():
            raise FileNotFoundError(f"Model file not found at {model_path}")

        from ultralytics import YOLO

        data_path = resolve_detection_data_yaml(args.data)
        task_type = "detect" if model_path.suffix == ".tflite" else None
        model = YOLO(str(model_path), task=task_type)
        if model_path.suffix == ".tflite":
            from ai_edge_litert.interpreter import Interpreter as LiteRTInterpreter
            _tmp = LiteRTInterpreter(model_path=str(model_path))
            val_imgsz = int(max(_tmp.get_input_details()[0]["shape"]))
            del _tmp
        else:
            val_imgsz = 640
        model.val(data=str(data_path), imgsz=val_imgsz)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
