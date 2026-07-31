"""Comprehensive model evaluation script for MIRA detection models.

Usage:
    python scripts/evaluate.py --model mira_exp014.pt
    python scripts/evaluate.py --model mira_exp013.pt --data datasets/roboflow_raw/dataset.yaml
    python scripts/evaluate.py --model mira_exp014.pt --conf 0.3 --output results/eval_exp014/
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
import time
from datetime import datetime
from pathlib import Path

_src_dir = str(Path(__file__).resolve().parent.parent / "src")
if _src_dir not in sys.path:
    sys.path.insert(0, _src_dir)

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np

from config import CLASS_NAMES, DETECTION_DIR, ROOT_DIR
from pipeline.benchmark import (
    ModelBenchmark,
    PerClassMetrics,
    load_yolo_dataset,
)
from pipeline.models import DetectionModel, ModelRegistry

logger = logging.getLogger("evaluate")

# ---------------------------------------------------------------------------
# Plotting style shared by the evaluation outputs.
# ---------------------------------------------------------------------------
plt.rcParams["font.family"] = "sans-serif"
plt.rcParams["font.sans-serif"] = ["DejaVu Sans", "Arial", "Helvetica"]
plt.rcParams["axes.edgecolor"] = "#cccccc"
plt.rcParams["axes.linewidth"] = 0.8
plt.rcParams["xtick.color"] = "#333333"
plt.rcParams["ytick.color"] = "#333333"
plt.rcParams["grid.color"] = "#eeeeee"
plt.rcParams["grid.linewidth"] = 0.5

PALETTE = ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd"]


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Evaluate a MIRA detection model on a YOLO validation set",
    )
    p.add_argument(
        "--model",
        type=str,
        required=True,
        help="Model filename inside models/detection/ (e.g. mira_exp014.pt)",
    )
    p.add_argument(
        "--data",
        type=str,
        default=None,
        help="Path to dataset YAML (auto-discovers first available if omitted)",
    )
    p.add_argument(
        "--conf",
        type=float,
        default=0.25,
        help="Confidence threshold (default: 0.25)",
    )
    p.add_argument(
        "--output",
        type=str,
        default=None,
        help="Output directory (default: results/eval_<timestamp>/)",
    )
    return p.parse_args()


# ---------------------------------------------------------------------------
# Auto-discover default dataset
# ---------------------------------------------------------------------------
def discover_default_dataset() -> Path | None:
    """Return the first dataset YAML found in datasets/ with a val split."""
    for yaml_path in sorted((ROOT_DIR / "datasets").rglob("dataset.yaml")):
        if yaml_path.exists():
            return yaml_path

    return None


# ---------------------------------------------------------------------------
# Confusion matrix
# ---------------------------------------------------------------------------
def _iou(box_a: list[float], box_b: list[float]) -> float:
    x1 = max(box_a[0], box_b[0])
    y1 = max(box_a[1], box_b[1])
    x2 = min(box_a[2], box_b[2])
    y2 = min(box_a[3], box_b[3])
    inter = max(0, x2 - x1) * max(0, y2 - y1)
    area_a = (box_a[2] - box_a[0]) * (box_a[3] - box_a[1])
    area_b = (box_b[2] - box_b[0]) * (box_b[3] - box_b[1])
    union = area_a + area_b - inter
    return inter / union if union > 0 else 0.0


def build_confusion_matrix(
    model: DetectionModel,
    samples: list[tuple[Path, list[dict]]],
    conf: float,
) -> np.ndarray:
    """Build and return a proper confusion matrix (GT rows, Pred cols)."""
    n = len(CLASS_NAMES)
    matrix = np.zeros((n, n), dtype=int)

    for img_path, gt_objects in samples:
        try:
            result = model.predict(str(img_path), conf=conf, iou=0.5)
        except Exception:
            continue

        pred_boxes = [list(d.bbox) for d in result.detections]
        pred_cls = [d.class_id for d in result.detections]
        pred_used = [False] * len(pred_boxes)

        for gt in gt_objects:
            gt_box = gt["bbox"]
            gt_cls = gt["class_id"]
            best_iou = 0.5
            best_pi = -1

            for pi in range(len(pred_boxes)):
                if pred_used[pi]:
                    continue
                if gt_cls != pred_cls[pi]:
                    continue
                iou_val = _iou(gt_box, pred_boxes[pi])
                if iou_val >= best_iou:
                    best_iou = iou_val
                    best_pi = pi

            if best_pi >= 0:
                pred_used[best_pi] = True
                matrix[gt_cls, pred_cls[best_pi]] += 1
            # else: FN — not added to matrix (implicitly counted)

    return matrix


def plot_confusion_matrix(matrix: np.ndarray, output_dir: Path) -> None:
    """Save a formatted confusion matrix as PNG."""
    fig, ax = plt.subplots(figsize=(7, 6))
    im = ax.imshow(matrix, cmap="Blues", aspect="auto")

    cbar = fig.colorbar(im, ax=ax, shrink=0.85)
    cbar.ax.set_ylabel("Count", rotation=-90, va="bottom", fontweight="bold")

    n = len(CLASS_NAMES)
    ax.set_xticks(np.arange(n))
    ax.set_yticks(np.arange(n))
    ax.set_xticklabels(CLASS_NAMES, fontsize=9, fontweight="bold")
    ax.set_yticklabels(CLASS_NAMES, fontsize=9, fontweight="bold")

    for i in range(n):
        for j in range(n):
            val = matrix[i, j]
            color = "white" if val > matrix.max() / 2 else "black"
            ax.text(j, i, str(val), ha="center", va="center", color=color, fontsize=10, fontweight="bold")

    ax.set_xlabel("Prediction", fontsize=10, fontweight="bold")
    ax.set_ylabel("Ground Truth", fontsize=10, fontweight="bold")
    plt.title("Confusion Matrix", fontsize=12, fontweight="bold", pad=12)
    plt.tight_layout()
    path = output_dir / "confusion_matrix.png"
    plt.savefig(path, dpi=300)
    plt.close()
    logger.info("Confusion matrix saved to %s", path)


# ---------------------------------------------------------------------------
# Per-class PR curve
# ---------------------------------------------------------------------------
def compute_per_class_ap(
    model: DetectionModel,
    samples: list[tuple[Path, list[dict]]],
    conf_thresh: float,
    class_id: int,
    iou_thresh: float = 0.5,
) -> tuple[np.ndarray, np.ndarray, float]:
    """Compute precision, recall arrays and AP for a single class.

    Returns (precision, recall, ap) where arrays are sorted by descending
    confidence with an interpolated precision envelope.
    """
    all_dets: list[dict] = []

    for img_idx, (img_path, gt_objects) in enumerate(samples):
        try:
            result = model.predict(str(img_path), conf=0.0, iou=iou_thresh)
        except Exception:
            continue

        for det in result.detections:
            if det.class_id != class_id:
                continue
            if det.confidence < conf_thresh:
                continue
            # Find best IoU with GT of same class in same image
            gt_matches = [gt for gt in gt_objects if gt["class_id"] == class_id]
            best_iou = 0.0
            best_gt_idx = -1
            for gi, gt in enumerate(gt_matches):
                iou_val = _iou(list(det.bbox), gt["bbox"])
                if iou_val > best_iou:
                    best_iou = iou_val
                    best_gt_idx = gi

            all_dets.append(
                {
                    "img_idx": img_idx,
                    "confidence": det.confidence,
                    "best_iou": best_iou,
                    "matched_gt": best_gt_idx,
                    "gt_total": len(gt_matches),
                }
            )

    all_dets.sort(key=lambda x: x["confidence"], reverse=True)

    num_gt = sum(1 for _, gts in samples for gt in gts if gt["class_id"] == class_id)
    if num_gt == 0:
        return np.array([0.0]), np.array([0.0]), 0.0

    tp = np.zeros(len(all_dets))
    fp = np.zeros(len(all_dets))
    used_gt: dict[int, set[int]] = {}

    for i, d in enumerate(all_dets):
        img = d["img_idx"]
        if d["best_iou"] >= iou_thresh:
            used = used_gt.setdefault(img, set())
            if d["matched_gt"] not in used:
                tp[i] = 1.0
                used.add(d["matched_gt"])
            else:
                fp[i] = 1.0
        else:
            fp[i] = 1.0

    tp_cum = np.cumsum(tp)
    fp_cum = np.cumsum(fp)
    precision = tp_cum / (tp_cum + fp_cum)
    recall = tp_cum / num_gt

    # Append endpoints
    precision = np.concatenate([[1.0], precision])
    recall = np.concatenate([[0.0], recall])

    # Interpolated AP (COCO style)
    ap = 0.0
    for t in np.arange(0, 1.01, 0.01):
        mask = recall >= t
        if np.any(mask):
            ap += np.max(precision[mask]) / 101

    return precision, recall, float(ap)


def plot_pr_curves(
    model: DetectionModel,
    samples: list[tuple[Path, list[dict]]],
    conf: float,
    output_dir: Path,
) -> dict[str, float]:
    """Plot per-class precision-recall curves and return per-class AP values."""
    per_class_ap: dict[str, float] = {}

    fig, ax = plt.subplots(figsize=(8, 6))

    for cls_id, cls_name in enumerate(CLASS_NAMES):
        precision, recall, ap = compute_per_class_ap(model, samples, conf, cls_id)
        per_class_ap[cls_name] = ap
        color = PALETTE[cls_id % len(PALETTE)]
        ax.plot(recall, precision, color=color, linewidth=1.8, label=f"{cls_name} (AP={ap:.3f})")

    ax.set_xlabel("Recall", fontsize=10, fontweight="bold")
    ax.set_ylabel("Precision", fontsize=10, fontweight="bold")
    ax.set_xlim(0, 1.05)
    ax.set_ylim(0, 1.05)
    ax.grid(True, linestyle=":")
    ax.legend(loc="lower left", fontsize=8, framealpha=0.9)
    plt.title("Precision-Recall Curves (per class)", fontsize=12, fontweight="bold", pad=12)
    plt.tight_layout()

    path = output_dir / "pr_curves.png"
    plt.savefig(path, dpi=300)
    plt.close()
    logger.info("PR curves saved to %s", path)

    return per_class_ap


# ---------------------------------------------------------------------------
# Per-class metrics bar chart
# ---------------------------------------------------------------------------
def plot_class_metrics(per_class: dict[str, PerClassMetrics], output_dir: Path) -> None:
    """Bar chart of per-class precision, recall, F1."""
    names = list(per_class.keys())
    precisions = [m.precision for m in per_class.values()]
    recalls = [m.recall for m in per_class.values()]
    f1s = [m.f1 for m in per_class.values()]

    x = np.arange(len(names))
    width = 0.25

    fig, ax = plt.subplots(figsize=(9, 5))
    ax.bar(x - width, precisions, width, label="Precision", color="#1f77b4", edgecolor="#333333", linewidth=0.7)
    ax.bar(x, recalls, width, label="Recall", color="#ff7f0e", edgecolor="#333333", linewidth=0.7)
    ax.bar(x + width, f1s, width, label="F1", color="#2ca02c", edgecolor="#333333", linewidth=0.7)

    ax.set_xticks(x)
    ax.set_xticklabels(names, fontsize=9, fontweight="bold")
    ax.set_ylim(0, 1.1)
    ax.set_ylabel("Score", fontsize=10, fontweight="bold")
    ax.grid(axis="y", linestyle="--")
    ax.legend(fontsize=9)
    plt.title("Per-Class Metrics", fontsize=12, fontweight="bold", pad=12)
    plt.tight_layout()

    path = output_dir / "class_metrics.png"
    plt.savefig(path, dpi=300)
    plt.close()
    logger.info("Class metrics chart saved to %s", path)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%H:%M:%S",
    )

    args = parse_args()

    # Resolve model path
    model_path = DETECTION_DIR / args.model
    if not model_path.exists():
        logger.error("Model not found: %s", model_path)
        available = sorted(p.name for p in DETECTION_DIR.glob("*") if p.suffix in (".pt", ".tflite"))
        logger.info("Available models: %s", available)
        sys.exit(1)

    # Resolve dataset
    if args.data:
        data_path = Path(args.data)
        if not data_path.is_absolute():
            data_path = ROOT_DIR / data_path
    else:
        data_path = discover_default_dataset()
        if data_path is None:
            logger.error("No dataset found. Specify --data path explicitly.")
            sys.exit(1)
    logger.info("Dataset: %s", data_path)

    # Output directory
    if args.output:
        output_dir = Path(args.output)
        if not output_dir.is_absolute():
            output_dir = ROOT_DIR / output_dir
    else:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        model_stem = Path(args.model).stem
        output_dir = ROOT_DIR / "results" / f"eval_{model_stem}_{timestamp}"
    output_dir.mkdir(parents=True, exist_ok=True)
    logger.info("Output dir: %s", output_dir)

    # Load model
    logger.info("Loading model %s ...", args.model)
    registry = ModelRegistry()
    registry.discover()
    model = registry.load_model(args.model)
    logger.info("Model loaded: %s", model.name)

    # Load validation samples
    logger.info("Loading validation dataset ...")
    samples, evaluated_on_train = load_yolo_dataset(data_path)
    logger.info("Loaded %d images", len(samples))

    # Run benchmark via ModelBenchmark
    logger.info("Running benchmark (conf=%.2f) ...", args.conf)
    benchmark = ModelBenchmark(models=[model], dataset=data_path, conf=args.conf)
    benchmark.samples = samples
    t0 = time.perf_counter()
    results = benchmark.run()
    elapsed = time.perf_counter() - t0
    logger.info("Benchmark completed in %.1fs", elapsed)

    result = results[0]

    # Generate charts
    logger.info("Generating confusion matrix ...")
    matrix = build_confusion_matrix(model, samples, args.conf)
    plot_confusion_matrix(matrix, output_dir)

    logger.info("Generating PR curves ...")
    per_class_ap = plot_pr_curves(model, samples, args.conf, output_dir)

    logger.info("Generating per-class metrics chart ...")
    plot_class_metrics(result.per_class, output_dir)

    # Print summary
    print("\n" + "=" * 60)
    print(f"  Model:    {result.model_name}")
    print(f"  Images:   {result.total_images}")
    print(f"  mAP50:    {result.map50:.4f}")
    print(f"  mAP50-95: {result.map50_95:.4f}")
    print(f"  Precision: {result.overall_precision:.4f}")
    print(f"  Recall:    {result.overall_recall:.4f}")
    print(f"  F1:        {result.overall_f1:.4f}")
    print(f"  Latency:   {result.avg_latency_ms:.1f} ms")
    print("-" * 60)
    print("  Per-class breakdown:")
    for cls_name, m in result.per_class.items():
        ap = per_class_ap.get(cls_name, 0.0)
        print(f"    {cls_name:<10s}  P={m.precision:.3f}  R={m.recall:.3f}  F1={m.f1:.3f}  AP={ap:.3f}")
    print("=" * 60 + "\n")

    # Save JSON results
    export_data = result.to_dict()
    export_data["per_class_ap"] = per_class_ap
    export_data["confusion_matrix"] = matrix.tolist()
    export_data["eval_args"] = {
        "conf": args.conf,
        "data": str(data_path),
        "model": args.model,
    }

    json_path = output_dir / "metrics.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(export_data, f, indent=2)
    logger.info("Metrics saved to %s", json_path)

    # Also save a comparison table
    table_path = output_dir / "comparison_table.txt"
    with open(table_path, "w", encoding="utf-8") as f:
        f.write(ModelBenchmark.comparison_table(results))
    logger.info("Comparison table saved to %s", table_path)

    print(f"All outputs saved to {output_dir}/")


if __name__ == "__main__":
    main()
