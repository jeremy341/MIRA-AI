"""Field benchmark: compare all detection models on real webcam images.

Usage:
    py src/field_benchmark.py

Workflow:
    1. Collect ~20-50 webcam images with manual labels
    2. Runs all .pt and .tflite detection models on every image
    3. Prints per-model, per-class precision/recall table
"""
import argparse
import json
import pathlib
import sys
import time
import cv2
from ultralytics import YOLO

SCRIPT_DIR = pathlib.Path(__file__).resolve().parent
ROOT_DIR = SCRIPT_DIR.parent
MODELS_DIR = ROOT_DIR / "models"
RESULTS_DIR = ROOT_DIR / "results"

CLASS_NAMES = ["glass", "metal", "paper", "plastic", "trash"]
CLASS_IDS = {n: i for i, n in enumerate(CLASS_NAMES)}


def collect_images(output_dir, camera=0, resolution="640x360"):
    """Capture webcam images with manual class labels."""
    cap = cv2.VideoCapture(camera, cv2.CAP_DSHOW)
    cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*"MJPG"))
    W, H = (int(v) for v in resolution.split("x"))
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, W)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, H)
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
    cap.set(cv2.CAP_PROP_FPS, 30)

    for _ in range(10):
        cap.read()

    img_dir = output_dir / "images"
    img_dir.mkdir(parents=True, exist_ok=True)
    annotations = {}
    count = 0

    print(f"\n  Field Benchmark \u2014 Image Collection")
    print(f"  {'='*40}")
    print(f"  Press SPACE to capture a frame")
    print(f"  Enter class labels: {' '.join(CLASS_NAMES)}")
    print(f"  Multiple labels: space-separated (e.g. 'plastic metal')")
    print(f"  Press Q to finish collection")
    print(f"  {'='*40}\n")

    while True:
        ret, frame = cap.read()
        if not ret:
            break
        display = frame.copy()
        cv2.putText(display, "SPACE: capture | Q: finish", (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        cv2.imshow("MIRA Field Benchmark", display)
        key = cv2.waitKey(1) & 0xFF

        if key == ord('q') or key == ord('Q'):
            break
        elif key == ord(' '):
            fname = f"frame_{count:03d}.jpg"
            path = str(img_dir / fname)
            cv2.imwrite(path, frame)
            print(f"\n  Captured: {fname}")

            labels = input(f"    Classes (space-separated): ").strip().lower()
            if labels:
                parsed = []
                for lbl in labels.split():
                    if lbl in CLASS_IDS:
                        parsed.append(CLASS_IDS[lbl])
                    else:
                        print(f"    Unknown class '{lbl}', skipping")
                if parsed:
                    annotations[fname] = parsed
                    count += 1
                else:
                    (img_dir / fname).unlink(missing_ok=True)
                    print(f"    Discarded (no valid labels)")
            else:
                (img_dir / fname).unlink(missing_ok=True)
                print(f"    Discarded (no labels)")

    cap.release()
    cv2.destroyAllWindows()

    with open(output_dir / "annotations.json", "w") as f:
        json.dump(annotations, f, indent=2)
    print(f"\n  Collected {len(annotations)} labeled images.")
    print(f"  Annotations saved to: {output_dir / 'annotations.json'}\n")
    return annotations


def get_detection_models():
    models = []
    for p in sorted(MODELS_DIR.glob("*")):
        if p.suffix in (".pt", ".tflite") and "classifier" not in p.name.lower():
            models.append((p.name, p))
    return models


def run_models(models, annotations, img_dir, conf=0.5):
    results = {}
    for name, path in models:
        print(f"  Running {name}...", end=" ", flush=True)
        task_type = "detect" if path.suffix == ".tflite" else None
        try:
            model = YOLO(str(path), task=task_type)
        except Exception as e:
            print(f"ERROR: {e}")
            continue
        model_results = {}
        for fname, true_classes in annotations.items():
            img_path = img_dir / fname
            if not img_path.exists():
                continue
            preds = model(str(img_path), conf=conf, verbose=False)
            detections = preds[0].boxes
            detected = set()
            if detections is not None:
                for cls_id in detections.cls.int().tolist():
                    detected.add(int(cls_id))
            model_results[fname] = {"true": set(true_classes), "pred": detected}
        results[name] = model_results
        print("done")
    return results


def compute_metrics(results):
    model_metrics = {}
    for model_name, images in results.items():
        per_class = {}
        for cls_name, cls_id in CLASS_IDS.items():
            tp = fp = fn = 0
            for img_data in images.values():
                if cls_id in img_data["true"] and cls_id in img_data["pred"]:
                    tp += 1
                elif cls_id not in img_data["true"] and cls_id in img_data["pred"]:
                    fp += 1
                elif cls_id in img_data["true"] and cls_id not in img_data["pred"]:
                    fn += 1
            prec = tp / (tp + fp) if (tp + fp) > 0 else 0.0
            rec = tp / (tp + fn) if (tp + fn) > 0 else 0.0
            f1 = 2 * prec * rec / (prec + rec) if (prec + rec) > 0 else 0.0
            per_class[cls_name] = {"tp": tp, "fp": fp, "fn": fn,
                                   "precision": prec, "recall": rec, "f1": f1}
        model_metrics[model_name] = per_class
    return model_metrics


def print_results(model_metrics):
    print(f"\n  {'='*70}")
    print(f"  Field Benchmark Results")
    print(f"  {'='*70}")

    for model_name, per_class in model_metrics.items():
        print(f"\n  {model_name}")
        print(f"  {'-'*60}")
        print(f"  {'Class':<10} {'TP':>4} {'FP':>4} {'FN':>4} {'Prec':>6} {'Recall':>6} {'F1':>6}")
        print(f"  {'-'*60}")
        totals = {"tp": 0, "fp": 0, "fn": 0}
        for cls_name in CLASS_NAMES:
            m = per_class[cls_name]
            for k in totals:
                totals[k] += m[k]
            print(f"  {cls_name:<10} {m['tp']:>4} {m['fp']:>4} {m['fn']:>4} "
                  f"{m['precision']:>5.1%} {m['recall']:>5.1%} {m['f1']:>5.1%}")
        total_prec = totals["tp"] / (totals["tp"] + totals["fp"]) if (totals["tp"] + totals["fp"]) > 0 else 0.0
        total_rec = totals["tp"] / (totals["tp"] + totals["fn"]) if (totals["tp"] + totals["fn"]) > 0 else 0.0
        total_f1 = 2 * total_prec * total_rec / (total_prec + total_rec) if (total_prec + total_rec) > 0 else 0.0
        print(f"  {'-'*60}")
        print(f"  {'Total':<10} {totals['tp']:>4} {totals['fp']:>4} {totals['fn']:>4} "
              f"{total_prec:>5.1%} {total_rec:>5.1%} {total_f1:>5.1%}")

    print(f"\n  {'='*70}\n")


def main():
    p = argparse.ArgumentParser(description="MIRA Field Benchmark")
    p.add_argument("--camera", type=int, default=0)
    p.add_argument("--resolution", type=str, default="640x360")
    p.add_argument("--conf", type=float, default=0.5)
    args = p.parse_args()

    run_id = time.strftime("field_bench_%Y%m%d_%H%M%S")
    output_dir = RESULTS_DIR / run_id

    annotations = collect_images(output_dir, args.camera, args.resolution)
    if len(annotations) < 3:
        print("  Too few labeled images. Need at least 3.")
        sys.exit(1)

    models = get_detection_models()
    if not models:
        print("  No detection models found in models/")
        sys.exit(1)

    print(f"  Running {len(models)} models on {len(annotations)} images...\n")
    results = run_models(models, annotations, output_dir / "images", args.conf)

    model_metrics = compute_metrics(results)
    print_results(model_metrics)

    results_path = output_dir / "benchmark_results.json"
    with open(results_path, "w") as f:
        json.dump(model_metrics, f, indent=2, default=str)
    print(f"  Full results saved to: {results_path}")


if __name__ == "__main__":
    main()
