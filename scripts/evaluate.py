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
    intersection_left = max(box_a[0], box_b[0])
    intersection_top = max(box_a[1], box_b[1])
    intersection_right = min(box_a[2], box_b[2])
    intersection_bottom = min(box_a[3], box_b[3])
    intersection_width = max(0, intersection_right - intersection_left)
    intersection_height = max(0, intersection_bottom - intersection_top)
    intersection_area = intersection_width * intersection_height
    area_a = max(0, box_a[2] - box_a[0]) * max(0, box_a[3] - box_a[1])
    area_b = max(0, box_b[2] - box_b[0]) * max(0, box_b[3] - box_b[1])
    union = area_a + area_b - intersection_area
    if union == 0:
        return 0.0
    return intersection_area / union


def build_confusion_matrix(
    model: DetectionModel,
    samples: list[tuple[Path, list[dict]]],
    conf: float,
) -> np.ndarray:
    # Build and return a proper confusion matrix (GT rows, Pred cols)
    class_count = len(CLASS_NAMES)
    background_class_id = class_count
    matrix = np.zeros((class_count + 1, class_count + 1), dtype=int)

    for img_path, gt_objects in samples:
        try:
            result = model.predict(str(img_path), conf=conf, iou=0.5)
        except Exception as exc:
            logger.warning("Prediction failed for %s: %s", img_path.name, exc)
            for ground_truth in gt_objects:
                ground_truth_class = int(ground_truth["class_id"])
                if 0 <= ground_truth_class < class_count:
                    matrix[ground_truth_class, background_class_id] += 1
            continue

        prediction_boxes = [list(detection.bbox) for detection in result.detections]
        prediction_classes = [detection.class_id for detection in result.detections]
        prediction_was_matched = [False] * len(prediction_boxes)

        for ground_truth in gt_objects:
            ground_truth_box = ground_truth["bbox"]
            ground_truth_class = int(ground_truth["class_id"])
            if not (0 <= ground_truth_class < class_count):
                continue
            best_overlap = 0.5
            best_prediction_index = -1

            for prediction_index, prediction_box in enumerate(prediction_boxes):
                if prediction_was_matched[prediction_index]:
                    continue
                overlap = _iou(ground_truth_box, prediction_box)
                if overlap >= best_overlap:
                    best_overlap = overlap
                    best_prediction_index = prediction_index

            if best_prediction_index >= 0:
                prediction_was_matched[best_prediction_index] = True
                prediction_class = int(prediction_classes[best_prediction_index])
                if 0 <= prediction_class < class_count:
                    matrix[ground_truth_class, prediction_class] += 1
                else:
                    matrix[ground_truth_class, background_class_id] += 1
            else:
                matrix[ground_truth_class, background_class_id] += 1

        for prediction_index, was_matched in enumerate(prediction_was_matched):
            if was_matched:
                continue
            prediction_class = int(prediction_classes[prediction_index])
            if 0 <= prediction_class < class_count:
                matrix[background_class_id, prediction_class] += 1
            else:
                matrix[background_class_id, background_class_id] += 1

    return matrix


def plot_confusion_matrix(matrix: np.ndarray, output_dir: Path) -> None:
    # Save a formatted confusion matrix as PNG
    figure, axes = plt.subplots(figsize=(7, 6))
    image = axes.imshow(matrix, cmap="Blues", aspect="auto")

    colorbar = figure.colorbar(image, ax=axes, shrink=0.85)
    colorbar.ax.set_ylabel("Count", rotation=-90, va="bottom", fontweight="bold")

    axis_count = len(CLASS_NAMES) + 1
    tick_positions = np.arange(axis_count)
    axes.set_xticks(tick_positions)
    axes.set_yticks(tick_positions)
    labels = [*CLASS_NAMES, "background"]
    axes.set_xticklabels(labels, fontsize=9, fontweight="bold")
    axes.set_yticklabels(labels, fontsize=9, fontweight="bold")

    half_maximum_count = matrix.max() / 2
    for row_index in range(axis_count):
        for column_index in range(axis_count):
            cell_count = matrix[row_index, column_index]
            if cell_count > half_maximum_count:
                text_color = "white"
            else:
                text_color = "black"
            axes.text(
                column_index,
                row_index,
                str(cell_count),
                ha="center",
                va="center",
                color=text_color,
                fontsize=10,
                fontweight="bold",
            )

    axes.set_xlabel("Prediction", fontsize=10, fontweight="bold")
    axes.set_ylabel("Ground Truth", fontsize=10, fontweight="bold")
    plt.title("Confusion Matrix", fontsize=12, fontweight="bold", pad=12)
    plt.tight_layout()
    output_path = output_dir / "confusion_matrix.png"
    plt.savefig(output_path, dpi=300)
    plt.close()
    logger.info("Confusion matrix saved to %s", output_path)


def compute_per_class_ap(
    model: DetectionModel,
    samples: list[tuple[Path, list[dict]]],
    conf_thresh: float,
    class_id: int,
    iou_thresh: float = 0.5,
) -> tuple[np.ndarray, np.ndarray, float]:
    # Compute precision, recall and AP for a single class.
    all_detections: list[dict] = []
    ground_truth_by_image: dict[int, list[dict]] = {}
    failed_images: list[str] = []

    for image_index, (image_path, ground_truth_objects) in enumerate(samples):
        class_ground_truth = [
            ground_truth
            for ground_truth in ground_truth_objects
            if ground_truth["class_id"] == class_id
        ]
        ground_truth_by_image[image_index] = class_ground_truth
        try:
            result = model.predict(str(image_path), conf=0.0, iou=iou_thresh)
        except Exception as exc:
            logger.warning(
                "Prediction failed for %s (class_id=%s): %s — counting as no detections for AP",
                image_path.name,
                class_id,
                exc,
            )
            failed_images.append(str(image_path))
            continue

        for detection in result.detections:
            if detection.class_id != class_id:
                continue
            all_detections.append(
                {
                    "img_idx": image_index,
                    "confidence": float(detection.confidence),
                    "bbox": list(detection.bbox),
                }
            )

    if failed_images:
        logger.warning(
            "Per-class AP class_id=%s: %d/%d images had prediction failures and were counted as missed detections",
            class_id,
            len(failed_images),
            len(samples),
        )

    all_detections.sort(
        key=lambda detection: detection["confidence"],
        reverse=True,
    )

    ground_truth_count = sum(len(objects) for objects in ground_truth_by_image.values())
    if ground_truth_count == 0:
        logger.warning("Per-class AP class_id=%s: no ground-truth boxes for this class (AP=0.0)", class_id)
        return np.array([0.0]), np.array([0.0]), 0.0

    true_positive_flags = np.zeros(len(all_detections))
    false_positive_flags = np.zeros(len(all_detections))
    used_ground_truth_by_image: dict[int, set[int]] = {}

    for detection_index, detection in enumerate(all_detections):
        image_index = detection["img_idx"]
        image_ground_truth = ground_truth_by_image.get(image_index, [])
        if not image_ground_truth:
            false_positive_flags[detection_index] = 1.0
            continue
        used_ground_truth = used_ground_truth_by_image.setdefault(image_index, set())
        best_overlap = 0.0
        best_ground_truth_index = -1
        for ground_truth_index, ground_truth in enumerate(image_ground_truth):
            if ground_truth_index in used_ground_truth:
                continue
            overlap = _iou(detection["bbox"], ground_truth["bbox"])
            if overlap > best_overlap:
                best_overlap = overlap
                best_ground_truth_index = ground_truth_index
        if best_overlap >= iou_thresh and best_ground_truth_index >= 0:
            true_positive_flags[detection_index] = 1.0
            used_ground_truth.add(best_ground_truth_index)
        else:
            false_positive_flags[detection_index] = 1.0

    cumulative_true_positives = np.cumsum(true_positive_flags)
    cumulative_false_positives = np.cumsum(false_positive_flags)
    precision_denominators = cumulative_true_positives + cumulative_false_positives
    precision = np.divide(
        cumulative_true_positives,
        precision_denominators,
        out=np.zeros_like(cumulative_true_positives, dtype=float),
        where=precision_denominators != 0,
    )
    precision = np.nan_to_num(precision, nan=0.0)
    if ground_truth_count > 0:
        recall = cumulative_true_positives / ground_truth_count
    else:
        recall = np.zeros_like(cumulative_true_positives, dtype=float)

    # Append endpoints
    precision = np.concatenate([[1.0], precision])
    recall = np.concatenate([[0.0], recall])

    # Interpolated AP (COCO style)
    ap = 0.0
    for recall_sample in np.arange(0, 1.01, 0.01):
        eligible_precisions = precision[recall >= recall_sample]
        if len(eligible_precisions) > 0:
            ap += np.max(eligible_precisions) / 101

    return precision, recall, float(ap)


def plot_pr_curves(
    model: DetectionModel,
    samples: list[tuple[Path, list[dict]]],
    conf: float,
    output_dir: Path,
) -> dict[str, float]:
    # Plot per-class precision-recall curves and return per-class AP values
    per_class_ap: dict[str, float] = {}

    figure, axes = plt.subplots(figsize=(8, 6))

    for class_id, class_name in enumerate(CLASS_NAMES):
        precision_values, recall_values, average_precision = compute_per_class_ap(
            model,
            samples,
            conf,
            class_id,
        )
        per_class_ap[class_name] = average_precision
        color_index = class_id % len(PALETTE)
        line_color = PALETTE[color_index]
        legend_label = f"{class_name} (AP={average_precision:.3f})"
        axes.plot(
            recall_values,
            precision_values,
            color=line_color,
            linewidth=1.8,
            label=legend_label,
        )

    axes.set_xlabel("Recall", fontsize=10, fontweight="bold")
    axes.set_ylabel("Precision", fontsize=10, fontweight="bold")
    axes.set_xlim(0, 1.05)
    axes.set_ylim(0, 1.05)
    axes.grid(True, linestyle=":")
    axes.legend(loc="lower left", fontsize=8, framealpha=0.9)
    plt.title("Precision-Recall Curves (per class)", fontsize=12, fontweight="bold", pad=12)
    plt.tight_layout()

    output_path = output_dir / "pr_curves.png"
    plt.savefig(output_path, dpi=300)
    plt.close()
    logger.info("PR curves saved to %s", output_path)

    return per_class_ap


def plot_class_metrics(per_class: dict[str, PerClassMetrics], output_dir: Path) -> None:
    # Bar chart of per-class precision, recall, F1
    class_names = list(per_class.keys())
    precision_values = [metrics.precision for metrics in per_class.values()]
    recall_values = [metrics.recall for metrics in per_class.values()]
    f1_values = [metrics.f1 for metrics in per_class.values()]

    class_positions = np.arange(len(class_names))
    bar_width = 0.25

    figure, axes = plt.subplots(figsize=(9, 5))
    axes.bar(
        class_positions - bar_width,
        precision_values,
        bar_width,
        label="Precision",
        color="#1f77b4",
        edgecolor="#333333",
        linewidth=0.7,
    )
    axes.bar(
        class_positions,
        recall_values,
        bar_width,
        label="Recall",
        color="#ff7f0e",
        edgecolor="#333333",
        linewidth=0.7,
    )
    axes.bar(
        class_positions + bar_width,
        f1_values,
        bar_width,
        label="F1",
        color="#2ca02c",
        edgecolor="#333333",
        linewidth=0.7,
    )

    axes.set_xticks(class_positions)
    axes.set_xticklabels(class_names, fontsize=9, fontweight="bold")
    axes.set_ylim(0, 1.1)
    axes.set_ylabel("Score", fontsize=10, fontweight="bold")
    axes.grid(axis="y", linestyle="--")
    axes.legend(fontsize=9)
    plt.title("Per-Class Metrics", fontsize=12, fontweight="bold", pad=12)
    plt.tight_layout()

    output_path = output_dir / "class_metrics.png"
    plt.savefig(output_path, dpi=300)
    plt.close()
    logger.info("Class metrics chart saved to %s", output_path)


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%H:%M:%S",
    )

    args = parse_args()

    raw_model_path = Path(args.model)
    model_path = None
    try:
        if raw_model_path.parent == Path("."):
            resolved_model_path = (DETECTION_DIR / raw_model_path).resolve()
        else:
            resolved_model_path = resolve_safe_path(raw_model_path, ROOT_DIR)
        resolved_model_path.relative_to(DETECTION_DIR.resolve())
        model_path = resolved_model_path
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
    benchmark_start_time = time.perf_counter()
    results = benchmark.run()
    benchmark_elapsed_seconds = time.perf_counter() - benchmark_start_time
    if benchmark_elapsed_seconds > 0:
        throughput_fps = len(samples) / benchmark_elapsed_seconds
    else:
        throughput_fps = 0.0
    logger.info(
        "Benchmark completed in %.1fs (throughput: %.1f images/sec)",
        benchmark_elapsed_seconds,
        throughput_fps,
    )

    result = results[0]

    logger.info("Generating confusion matrix ...")
    confusion_matrix = build_confusion_matrix(model, samples, args.conf)
    plot_confusion_matrix(confusion_matrix, output_dir)

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
    export_data["confusion_matrix"] = confusion_matrix.tolist()
    export_data["throughput_fps"] = throughput_fps
    export_data["eval_args"] = {
        "conf": args.conf,
        "data": str(data_path),
        "model": args.model,
    }

    metrics_path = output_dir / "metrics.json"
    with open(metrics_path, "w", encoding="utf-8") as metrics_file:
        json.dump(export_data, metrics_file, indent=2)
    logger.info("Metrics saved to %s", metrics_path)

    comparison_path = output_dir / "comparison_table.txt"
    with open(comparison_path, "w", encoding="utf-8") as comparison_file:
        comparison_file.write(ModelBenchmark.comparison_table(results))
    logger.info("Comparison table saved to %s", comparison_path)

    print(f"All outputs saved to {output_dir}/")


if __name__ == "__main__":
    main()
