# Evaluate a detection model and write plots

from __future__ import annotations

import argparse
import json
import logging
import sys
import time
from datetime import datetime
from pathlib import Path

import matplotlib
import numpy as np

_ROOT_DIR = Path(__file__).resolve().parent.parent
if str(_ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(_ROOT_DIR))

from src.config import CLASS_NAMES, DETECTION_DIR, ROOT_DIR, resolve_safe_path
from src.exceptions import ConfigError
from src.pipeline.benchmark import ModelBenchmark, PerClassMetrics, load_yolo_dataset
from src.pipeline.models import DetectionModel, ModelRegistry

matplotlib.use("Agg")
import matplotlib.pyplot as plt

logger = logging.getLogger("evaluate")

plt.rcParams["font.family"] = "sans-serif"
plt.rcParams["font.sans-serif"] = ["DejaVu Sans", "Arial", "Helvetica"]
plt.rcParams["axes.edgecolor"] = "#cccccc"
plt.rcParams["axes.linewidth"] = 0.8
plt.rcParams["xtick.color"] = "#333333"
plt.rcParams["ytick.color"] = "#333333"
plt.rcParams["grid.color"] = "#eeeeee"
plt.rcParams["grid.linewidth"] = 0.5

PALETTE = ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd"]


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


def discover_default_dataset() -> Path | None:
    for yaml_path in sorted((ROOT_DIR / "datasets").rglob("dataset.yaml")):
        if yaml_path.exists():
            return yaml_path

    return None


def _validate_dataset_path(dataset_path):
    if not dataset_path.exists():
        logger.error("Dataset not found: %s", dataset_path)
        sys.exit(1)


def _iou(box_a: list[float], box_b: list[float]) -> float:
    x1 = max(box_a[0], box_b[0])
    y1 = max(box_a[1], box_b[1])
    x2 = min(box_a[2], box_b[2])
    y2 = min(box_a[3], box_b[3])
    inter_width = max(0, x2 - x1)
    inter_height = max(0, y2 - y1)
    inter = inter_width * inter_height
    area_a = max(0, box_a[2] - box_a[0]) * max(0, box_a[3] - box_a[1])
    area_b = max(0, box_b[2] - box_b[0]) * max(0, box_b[3] - box_b[1])
    union = area_a + area_b - inter
    return inter / union if union > 0 else 0.0


def build_confusion_matrix(
    model: DetectionModel,
    samples: list[tuple[Path, list[dict]]],
    conf: float,
) -> np.ndarray:
    # Build and return a proper confusion matrix (GT rows, Pred cols)
    n = len(CLASS_NAMES)
    background = n
    matrix = np.zeros((n + 1, n + 1), dtype=int)

    for img_path, gt_objects in samples:
        try:
            result = model.predict(str(img_path), conf=conf, iou=0.5)
        except Exception as exc:
            logger.warning("Prediction failed for %s: %s", img_path.name, exc)
            for gt in gt_objects:
                gt_cls = int(gt["class_id"])
                if 0 <= gt_cls < n:
                    matrix[gt_cls, background] += 1
            continue

        pred_boxes = [list(d.bbox) for d in result.detections]
        pred_cls = [d.class_id for d in result.detections]
        pred_used = [False] * len(pred_boxes)

        for gt in gt_objects:
            gt_box = gt["bbox"]
            gt_cls = int(gt["class_id"])
            if not (0 <= gt_cls < len(CLASS_NAMES)):
                continue
            best_iou = 0.5
            best_pi = -1

            for pi in range(len(pred_boxes)):
                if pred_used[pi]:
                    continue
                iou_val = _iou(gt_box, pred_boxes[pi])
                if iou_val >= best_iou:
                    best_iou = iou_val
                    best_pi = pi

            if best_pi >= 0:
                pred_used[best_pi] = True
                pc = int(pred_cls[best_pi])
                matrix[gt_cls, pc if 0 <= pc < n else background] += 1
            else:
                matrix[gt_cls, background] += 1

        for pi, used in enumerate(pred_used):
            if not used:
                pc = int(pred_cls[pi])
                matrix[background, pc if 0 <= pc < n else background] += 1

    return matrix


def plot_confusion_matrix(matrix: np.ndarray, output_dir: Path) -> None:
    # Save a formatted confusion matrix as PNG
    fig, ax = plt.subplots(figsize=(7, 6))
    im = ax.imshow(matrix, cmap="Blues", aspect="auto")

    cbar = fig.colorbar(im, ax=ax, shrink=0.85)
    cbar.ax.set_ylabel("Count", rotation=-90, va="bottom", fontweight="bold")

    n = len(CLASS_NAMES) + 1
    ax.set_xticks(np.arange(n))
    ax.set_yticks(np.arange(n))
    labels = [*CLASS_NAMES, "background"]
    ax.set_xticklabels(labels, fontsize=9, fontweight="bold")
    ax.set_yticklabels(labels, fontsize=9, fontweight="bold")

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


def compute_per_class_ap(
    model: DetectionModel,
    samples: list[tuple[Path, list[dict]]],
    conf_thresh: float,
    class_id: int,
    iou_thresh: float = 0.5,
) -> tuple[np.ndarray, np.ndarray, float]:
    # Compute precision, recall and AP for a single class.
    all_dets: list[dict] = []
    gt_by_img: dict[int, list[dict]] = {}
    failed_images: list[str] = []

    for img_idx, (img_path, gt_objects) in enumerate(samples):
        gt_matches = [gt for gt in gt_objects if gt["class_id"] == class_id]
        gt_by_img[img_idx] = gt_matches
        try:
            result = model.predict(str(img_path), conf=0.0, iou=iou_thresh)
        except Exception as exc:
            logger.warning(
                "Prediction failed for %s (class_id=%s): %s — counting as no detections for AP",
                img_path.name,
                class_id,
                exc,
            )
            failed_images.append(str(img_path))
            continue

        for det in result.detections:
            if det.class_id != class_id:
                continue
            all_dets.append(
                {
                    "img_idx": img_idx,
                    "confidence": float(det.confidence),
                    "bbox": list(det.bbox),
                }
            )

    if failed_images:
        logger.warning(
            "Per-class AP class_id=%s: %d/%d images had prediction failures and were counted as missed detections",
            class_id,
            len(failed_images),
            len(samples),
        )

    all_dets.sort(key=lambda x: x["confidence"], reverse=True)

    num_gt = sum(len(v) for v in gt_by_img.values())
    if num_gt == 0:
        logger.warning("Per-class AP class_id=%s: no ground-truth boxes for this class (AP=0.0)", class_id)
    if num_gt == 0:
        return np.array([0.0]), np.array([0.0]), 0.0

    tp = np.zeros(len(all_dets))
    fp = np.zeros(len(all_dets))
    used_gt: dict[int, set[int]] = {}

    for i, d in enumerate(all_dets):
        img = d["img_idx"]
        gt_list = gt_by_img.get(img, [])
        if not gt_list:
            fp[i] = 1.0
            continue
        used = used_gt.setdefault(img, set())
        best_iou = 0.0
        best_gt_idx = -1
        for gi, gt in enumerate(gt_list):
            if gi in used:
                continue
            iou_val = _iou(d["bbox"], gt["bbox"])
            if iou_val > best_iou:
                best_iou = iou_val
                best_gt_idx = gi
        if best_iou >= iou_thresh and best_gt_idx >= 0:
            tp[i] = 1.0
            used.add(best_gt_idx)
        else:
            fp[i] = 1.0

    tp_cum = np.cumsum(tp)
    fp_cum = np.cumsum(fp)
    denom = tp_cum + fp_cum
    precision = np.divide(tp_cum, denom, out=np.zeros_like(tp_cum, dtype=float), where=denom != 0)
    precision = np.nan_to_num(precision, nan=0.0)
    recall = tp_cum / num_gt if num_gt > 0 else np.zeros_like(tp_cum, dtype=float)

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
    # Plot per-class precision-recall curves and return per-class AP values
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


def plot_class_metrics(per_class: dict[str, PerClassMetrics], output_dir: Path) -> None:
    # Bar chart of per-class precision, recall, F1
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


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%H:%M:%S",
    )

    args = parse_args()

    raw_model_path = Path(args.model)
    try:
        model_path = (
            (DETECTION_DIR / raw_model_path).resolve()
            if raw_model_path.parent == Path(".")
            else resolve_safe_path(raw_model_path, ROOT_DIR)
        )
        model_path.relative_to(DETECTION_DIR.resolve())
    except (ConfigError, ValueError):
        model_path = None
    if model_path is None or not model_path.is_file():
        logger.error("Model not found: %s", model_path)
        available = sorted(p.name for p in DETECTION_DIR.glob("*") if p.suffix in (".pt", ".tflite"))
        logger.info("Available models: %s", available)
        sys.exit(1)

    if args.data:
        data_path = Path(args.data)
        if not data_path.is_absolute():
            data_path = ROOT_DIR / data_path
        _validate_dataset_path(data_path)
    else:
        data_path = discover_default_dataset()
        if data_path is None:
            logger.error("No dataset found. Specify --data path explicitly.")
            sys.exit(1)
        _validate_dataset_path(data_path)
    logger.info("Dataset: %s", data_path)

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

    logger.info("Loading model %s ...", args.model)
    registry = ModelRegistry()
    registry.discover()
    model = registry.load_model(model_path.name)
    logger.info("Model loaded: %s", model.name)

    logger.info("Loading validation dataset ...")
    samples, evaluated_on_train = load_yolo_dataset(data_path)
    logger.info("Loaded %d images", len(samples))

    logger.info("Running benchmark (conf=%.2f) ...", args.conf)
    benchmark = ModelBenchmark(models=[model], dataset=data_path, conf=args.conf)
    benchmark.samples = samples
    benchmark.evaluated_on_train = evaluated_on_train
    t0 = time.perf_counter()
    results = benchmark.run()
    elapsed = time.perf_counter() - t0
    throughput_fps = len(samples) / elapsed if elapsed > 0 else 0.0
    logger.info("Benchmark completed in %.1fs (throughput: %.1f images/sec)", elapsed, throughput_fps)

    result = results[0]

    logger.info("Generating confusion matrix ...")
    matrix = build_confusion_matrix(model, samples, args.conf)
    plot_confusion_matrix(matrix, output_dir)

    logger.info("Generating PR curves ...")
    per_class_ap = plot_pr_curves(model, samples, args.conf, output_dir)

    logger.info("Generating per-class metrics chart ...")
    plot_class_metrics(result.per_class, output_dir)

    print("\n" + "=" * 60)
    print(f"  Model:    {result.model_name}")
    print(f"  Images:   {result.total_images}")
    print(f"  mAP50:    {result.map50:.4f}")
    print(f"  mAP50-95: {result.map50_95:.4f}")
    print(f"  Precision: {result.overall_precision:.4f}")
    print(f"  Recall:    {result.overall_recall:.4f}")
    print(f"  F1:        {result.overall_f1:.4f}")
    print(f"  Latency:   {result.avg_latency_ms:.1f} ms (throughput: {throughput_fps:.1f} FPS)")
    print("-" * 60)
    print("  Per-class breakdown:")
    for cls_name, m in result.per_class.items():
        ap = per_class_ap.get(cls_name, 0.0)
        print(f"    {cls_name:<10s}  P={m.precision:.3f}  R={m.recall:.3f}  F1={m.f1:.3f}  AP={ap:.3f}")
    print("=" * 60 + "\n")

    export_data = result.to_dict()
    export_data["per_class_ap"] = per_class_ap
    export_data["confusion_matrix"] = matrix.tolist()
    export_data["throughput_fps"] = throughput_fps
    export_data["eval_args"] = {
        "conf": args.conf,
        "data": str(data_path),
        "model": args.model,
    }

    json_path = output_dir / "metrics.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(export_data, f, indent=2)
    logger.info("Metrics saved to %s", json_path)

    table_path = output_dir / "comparison_table.txt"
    with open(table_path, "w", encoding="utf-8") as f:
        f.write(ModelBenchmark.comparison_table(results))
    logger.info("Comparison table saved to %s", table_path)

    print(f"All outputs saved to {output_dir}/")


if __name__ == "__main__":
    main()
