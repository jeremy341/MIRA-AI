"""Quantize a YOLO detection model to INT8 TFLite.

Usage:
    py quantize_detector.py --model mira_exp014.pt
    py quantize_detector.py  (interactive picker)
"""
import argparse
import pathlib
import sys

ROOT_DIR = pathlib.Path(__file__).resolve().parent.parent
DETECTION_DIR = ROOT_DIR / "models" / "detection"

# Add src/ to path for config imports
sys.path.insert(0, str(ROOT_DIR / "src"))
from config import get_detection_models, DETECTION_MODEL_LABELS


def main():
    parser = argparse.ArgumentParser(description="Quantize YOLO model to INT8 TFLite")
    parser.add_argument("--model", type=str, default=None,
                        help="Model filename to quantize. Omit for interactive picker.")
    parser.add_argument("--data", type=str, default=None,
                        help="Dataset YAML for INT8 calibration. Defaults to first available dataset.")
    args = parser.parse_args()

    if args.model:
        model_name = args.model
    else:
        models = get_detection_models()
        pt_models = [m for m in models if m.endswith(".pt")]
        if not pt_models:
            print("No .pt models found for quantization.")
            sys.exit(1)
        print("\nAvailable .pt models for quantization:")
        for i, m in enumerate(pt_models):
            label = DETECTION_MODEL_LABELS.get(m, m)
            print(f"  [{i}] {m} -- {label}")
        try:
            idx = int(input("\nSelect model [0]: ").strip() or "0")
            model_name = pt_models[idx]
        except (ValueError, IndexError):
            print("Invalid selection.")
            sys.exit(1)

    model_path = DETECTION_DIR / model_name
    if not model_path.exists():
        print(f"Model not found: {model_path}")
        sys.exit(1)

    from ultralytics import YOLO
    model = YOLO(str(model_path))

    print(f"\nQuantizing {model_name} to INT8 TFLite...")
    if args.data:
        data_yaml = pathlib.Path(args.data)
        if not data_yaml.is_absolute():
            data_yaml = ROOT_DIR / data_yaml
    else:
        # Scan datasets/ for first available dataset.yaml
        data_yaml = None
        datasets_dir = ROOT_DIR / "datasets"
        if datasets_dir.exists():
            for subdir in sorted(datasets_dir.iterdir()):
                if subdir.is_dir() and not subdir.name.startswith("."):
                    candidate = subdir / "dataset.yaml"
                    if candidate.exists():
                        data_yaml = candidate
                        break
        if data_yaml is None:
            print("ERROR: No dataset.yaml found. Use --data to specify one.")
            sys.exit(1)
    print(f"  Using dataset: {data_yaml}")
    model.export(format="tflite", int8=True, data=str(data_yaml))

    print(f"\nDone! Exported to: {DETECTION_DIR / model_name.replace('.pt', '_int8.tflite')}")


if __name__ == "__main__":
    main()
