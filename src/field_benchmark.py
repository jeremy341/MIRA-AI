"""Benchmark: compare all detection models on a YOLO-format validation set.

Usage:
    py src/field_benchmark.py --dataset datasets/mira_tnr
    py src/field_benchmark.py --dataset datasets/mira_warp_only
"""
import argparse
import json
import pathlib
import sys
import time
from ultralytics import YOLO

from config import ROOT_DIR, DETECTION_DIR, CLASS_NAMES

RESULTS_DIR = ROOT_DIR / "results"


def load_dataset(dataset_path):
    """Load val split from a YOLO-format dataset.
    Returns dict: {filename: set_of_class_ids}
    """
    dataset_path = pathlib.Path(dataset_path)
    img_dir = dataset_path / "images" / "val"
    lbl_dir = dataset_path / "labels" / "val"

    if not img_dir.exists():
        raise FileNotFoundError(f"Validation images not found: {img_dir}")
    if not lbl_dir.exists():
        raise FileNotFoundError(f"Validation labels not found: {lbl_dir}")

    annotations = {}
    skipped = 0
    for lbl_path in sorted(lbl_dir.glob("*.txt")):
        stem = lbl_path.stem
        img_path = None
        for ext in [".jpg", ".png", ".jpeg"]:
            candidate = img_dir / f"{stem}{ext}"
            if candidate.exists():
                img_path = candidate
                break
        if img_path is None:
            skipped += 1
            continue
        with open(lbl_path) as f:
            classes = set()
            for line in f:
                parts = line.strip().split()
                if parts:
                    classes.add(int(parts[0]))
        if classes:
            annotations[img_path.name] = classes

    print(f"  Loaded {len(annotations)} validation images from {dataset_path.name}")
    if skipped:
        print(f"  Skipped {skipped} labels with no matching image")
    return annotations, img_dir


def get_detection_models():
    """Return list of (name, path) tuples for detection models."""
    from config import get_detection_models as _get_names
    return [(name, DETECTION_DIR / name) for name in _get_names()]


def run_models(models, annotations, img_dir, conf=0.5):
    results = {}
    for name, path in models:
        is_int8 = "int8" in name.lower() and path.suffix == ".tflite"
        effective_conf = min(conf, 0.25) if is_int8 else conf
        thresh_note = f" (INT8: conf capped at {effective_conf:.2f})" if is_int8 else ""
        print(f"  Running {name}...{thresh_note}", end=" ", flush=True)
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
            preds = model(str(img_path), conf=effective_conf, verbose=False)
            detections = preds[0].boxes
            detected = set()
            if detections is not None:
                for cls_id in detections.cls.int().tolist():
                    detected.add(int(cls_id))
            model_results[fname] = {"true": true_classes, "pred": detected}
        results[name] = model_results
        print("done")
    return results


def compute_metrics(results):
    model_metrics = {}
    for model_name, images in results.items():
        per_class = {}
        for cls_id in range(5):
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
            per_class[CLASS_NAMES[cls_id]] = {
                "tp": tp, "fp": fp, "fn": fn,
                "precision": prec, "recall": rec, "f1": f1,
            }
        model_metrics[model_name] = per_class
    return model_metrics


def print_results(model_metrics, dataset_name):
    print(f"\n  {'='*70}")
    print(f"  Benchmark on: {dataset_name}")
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


def find_datasets():
    datasets_dir = ROOT_DIR / "datasets"
    candidates = []
    for d in sorted(datasets_dir.iterdir()):
        if d.is_dir() and (d / "images" / "val").exists():
            candidates.append(d)
    return candidates


def main():
    p = argparse.ArgumentParser(description="MIRA Model Benchmark on real validation data")
    p.add_argument("--dataset", type=str, default=None,
                   help="Path to dataset with images/val and labels/val. Omit to pick from list.")
    p.add_argument("--conf", type=float, default=0.5, help="Confidence threshold")
    args = p.parse_args()

    if args.dataset:
        dataset_path = pathlib.Path(args.dataset)
        if not dataset_path.is_absolute():
            dataset_path = (ROOT_DIR / dataset_path).resolve()
    else:
        candidates = find_datasets()
        if not candidates:
            print("No datasets with val splits found in datasets/")
            sys.exit(1)
        print("\n  Available datasets:")
        for i, d in enumerate(candidates):
            n_imgs = len(list((d / "images" / "val").glob("*")))
            print(f"  [{i}] {d.name} ({n_imgs} val images)")
        try:
            idx = int(input("\n  Select dataset [0]: ").strip() or "0")
            dataset_path = candidates[idx]
        except (ValueError, IndexError):
            print("Invalid selection.")
            sys.exit(1)

    annotations, img_dir = load_dataset(dataset_path)
    if len(annotations) < 3:
        print(f"  Need at least 3 labeled images, found {len(annotations)}")
        sys.exit(1)

    models = get_detection_models()
    if not models:
        print("  No detection models found")
        sys.exit(1)

    print(f"\n  Running {len(models)} models on {len(annotations)} images...\n")
    results = run_models(models, annotations, img_dir, args.conf)
    model_metrics = compute_metrics(results)
    print_results(model_metrics, dataset_path.name)

    run_id = time.strftime("bench_%Y%m%d_%H%M%S")
    out_dir = RESULTS_DIR / run_id
    out_dir.mkdir(parents=True, exist_ok=True)
    with open(out_dir / "benchmark_results.json", "w") as f:
        json.dump(model_metrics, f, indent=2, default=str)
    print(f"  Results saved to: {out_dir / 'benchmark_results.json'}")


if __name__ == "__main__":
    main()
