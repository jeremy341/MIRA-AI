"""Structured benchmarking module for MIRA detection models."""

from __future__ import annotations

import json
import math
import time
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

from ..config import CLASS_NAMES
from .models import Detection, DetectionModel, ModelRegistry


IMAGE_EXTENSIONS = (".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tiff")


@dataclass
class PerClassMetrics:
    """Per-class detection evaluation metrics."""
    tp: int = 0
    fp: int = 0
    fn: int = 0

    @property
    def precision(self) -> float:
        predicted_positive = self.tp + self.fp
        if predicted_positive == 0:
            return 0.0
        return self.tp / predicted_positive

    @property
    def recall(self) -> float:
        actual_positive = self.tp + self.fn
        if actual_positive == 0:
            return 0.0
        return self.tp / actual_positive

    @property
    def f1(self) -> float:
        precision = self.precision
        recall = self.recall
        combined_score = precision + recall
        if combined_score == 0:
            return 0.0
        return 2 * precision * recall / combined_score

    def to_dict(self) -> dict:
        return {
            "tp": self.tp,
            "fp": self.fp,
            "fn": self.fn,
            "precision": self.precision,
            "recall": self.recall,
            "f1": self.f1,
        }

@dataclass(frozen=True)
class MatchResult:
    true_positives: int
    false_positives: int
    false_negatives: int


def match_predictions(
    predictions: list[Detection],
    ground_truth: list[Detection],
    iou_threshold: float,
) -> MatchResult:
    if not 0 <= iou_threshold <= 1:
        raise ValueError("iou_threshold must be between 0 and 1")
    used_ground_truth_indices: set[int] = set()
    true_positives = 0
    confidence_ordered_predictions = sorted(
        predictions,
        key=lambda prediction: prediction.confidence,
        reverse=True,
    )
    for prediction in confidence_ordered_predictions:
        best_ground_truth_index = None
        best_overlap = iou_threshold
        for ground_truth_index, truth in enumerate(ground_truth):
            if ground_truth_index in used_ground_truth_indices:
                continue
            if truth.class_id != prediction.class_id:
                continue
            overlap = compute_iou(prediction.bbox, truth.bbox)
            if overlap >= best_overlap:
                best_overlap = overlap
                best_ground_truth_index = ground_truth_index
        if best_ground_truth_index is not None:
            used_ground_truth_indices.add(best_ground_truth_index)
            true_positives += 1
    return MatchResult(
        true_positives=true_positives,
        false_positives=len(predictions) - true_positives,
        false_negatives=len(ground_truth) - true_positives,
    )






def compute_iou(box_a: list[float], box_b: list[float]) -> float:
    """Compute IoU between two bounding boxes in xyxy format."""
    intersection_left = max(box_a[0], box_b[0])
    intersection_top = max(box_a[1], box_b[1])
    intersection_right = min(box_a[2], box_b[2])
    intersection_bottom = min(box_a[3], box_b[3])
    intersection_width = max(0, intersection_right - intersection_left)
    intersection_height = max(0, intersection_bottom - intersection_top)
    intersection_area = intersection_width * intersection_height

    area_a = max(0, box_a[2] - box_a[0]) * max(0, box_a[3] - box_a[1])
    area_b = max(0, box_b[2] - box_b[0]) * max(0, box_b[3] - box_b[1])
    union_area = area_a + area_b - intersection_area
    if union_area == 0:
        return 0.0
    return intersection_area / union_area


@dataclass
class BenchmarkResult:
    model_name: str
    model_path: str
    model_type: str
    total_images: int = 0
    per_class: dict[str, PerClassMetrics] = field(default_factory=dict)
    overall_f1: float = 0.0
    overall_precision: float = 0.0
    overall_recall: float = 0.0
    avg_latency_ms: float = 0.0
    total_detections: int = 0
    map50: float = 0.0
    map50_95: float = 0.0
    errors: list[str] = field(default_factory=list)
    evaluated_on_train: bool = False

    def to_dict(self) -> dict:
        return {
            "model_name": self.model_name,
            "model_path": self.model_path,
            "model_type": self.model_type,
            "total_images": self.total_images,
            "per_class": {k: v.to_dict() for k, v in self.per_class.items()},
            "overall_f1": self.overall_f1,
            "overall_precision": self.overall_precision,
            "overall_recall": self.overall_recall,
            "avg_latency_ms": self.avg_latency_ms,
            "total_detections": self.total_detections,
            "map50": self.map50,
            "map50_95": self.map50_95,
            "errors": self.errors,
            "evaluated_on_train": self.evaluated_on_train,
        }


def load_yolo_dataset(dataset_path: Path | str) -> tuple[list[tuple[Path, list[dict]]], bool]:
    from PIL import Image

    dataset_path = Path(dataset_path)
    dataset_config: dict = {}
    is_yaml_file = dataset_path.suffix.lower() in (".yaml", ".yml")
    if dataset_path.is_file() and is_yaml_file:
        import yaml

        dataset_config = yaml.safe_load(dataset_path.read_text(encoding="utf-8")) or {}
        dataset_root = dataset_path.parent
        configured_root = dataset_config.get("path")
        if configured_root:
            configured_root_path = Path(configured_root)
            if configured_root_path.is_absolute():
                dataset_root = configured_root_path
            else:
                dataset_root = dataset_root / configured_root_path
    else:
        dataset_root = dataset_path

    def split_directories(split_name: str) -> tuple[Path, Path]:
        configured_split = dataset_config.get(split_name)
        if isinstance(configured_split, list):
            configured_split = configured_split[0] if configured_split else None
        if configured_split:
            image_dir = Path(configured_split)
            if not image_dir.is_absolute():
                image_dir = dataset_root / image_dir
            image_parts = list(image_dir.parts)
            if "images" in image_parts:
                images_index = image_parts.index("images")
                image_parts[images_index] = "labels"
                label_dir = Path(*image_parts)
            else:
                label_dir = dataset_root / "labels" / split_name
            return image_dir, label_dir
        return dataset_root / "images" / split_name, dataset_root / "labels" / split_name

    split_name = "val"
    evaluated_on_train = False
    image_dir, label_dir = split_directories(split_name)
    if not image_dir.exists():
        from ..logger import get_logger as _get_logger

        _get_logger(__name__).warning(
            "Validation split not found in %s - falling back to train split. "
            "Metrics may be inflated because the model is evaluated on training data.",
            dataset_root,
        )
        split_name = "train"
        evaluated_on_train = True
        image_dir, label_dir = split_directories(split_name)
        if not image_dir.exists():
            raise FileNotFoundError(f"No images/val (or train) directory found in {dataset_root}")

    samples: list[tuple[Path, list[dict]]] = []
    skipped = 0
    image_paths = sorted(
        path
        for path in image_dir.iterdir()
        if path.is_file() and path.suffix.lower() in IMAGE_EXTENSIONS
    )
    for img_path in image_paths:
        label_path = label_dir / f"{img_path.stem}.txt"

        try:
            with Image.open(img_path) as img:
                image_width, image_height = img.size
        except (OSError, ValueError):
            skipped += 1
            continue

        objects_for_image: list[dict] = []
        if label_path.exists():
            try:
                label_lines = label_path.read_text(encoding="utf-8").splitlines()
            except OSError:
                label_lines = []
            for label_line in label_lines:
                fields = label_line.strip().split()
                if len(fields) < 5:
                    continue
                try:
                    class_id = int(fields[0])
                    coordinates = [float(value) for value in fields[1:]]
                except ValueError:
                    continue
                if class_id < 0 or not all(math.isfinite(value) for value in coordinates):
                    continue
                if len(coordinates) == 4:
                    center_x, center_y, box_width, box_height = coordinates
                    left = (center_x - box_width / 2) * image_width
                    top = (center_y - box_height / 2) * image_height
                    right = (center_x + box_width / 2) * image_width
                    bottom = (center_y + box_height / 2) * image_height
                elif len(coordinates) >= 6 and len(coordinates) % 2 == 0:
                    x_coordinates = coordinates[0::2]
                    y_coordinates = coordinates[1::2]
                    left = min(x_coordinates) * image_width
                    top = min(y_coordinates) * image_height
                    right = max(x_coordinates) * image_width
                    bottom = max(y_coordinates) * image_height
                else:
                    continue
                objects_for_image.append(
                    {"class_id": class_id, "bbox": [left, top, right, bottom]}
                )
        samples.append((img_path, objects_for_image))

    print(
        f"  Loaded {len(samples)} images from {dataset_root.name}/{split_name}"
        + (f" (skipped {skipped})" if skipped else "")
    )
    return samples, evaluated_on_train


def _compute_ap_for_class(
    all_detections_for_class: list[dict],
    all_gts_for_class: list[dict],
    iou_thresh: float,
) -> float:
    # Compute AP for a single class using 101-point interpolation.
    num_gt = len(all_gts_for_class)
    if num_gt == 0:
        return float("nan")

    all_detections_for_class.sort(
        key=lambda detection: detection["confidence"],
        reverse=True,
    )

    true_positive_flags = np.zeros(len(all_detections_for_class))
    false_positive_flags = np.zeros(len(all_detections_for_class))
    used_ground_truth_indices = set()

    for detection_index, detection in enumerate(all_detections_for_class):
        best_overlap = iou_thresh
        best_ground_truth_index = -1
        for ground_truth_index, ground_truth in enumerate(all_gts_for_class):
            if ground_truth_index in used_ground_truth_indices:
                continue
            if ground_truth["img_idx"] != detection["img_idx"]:
                continue
            overlap = compute_iou(detection["bbox_pixel"], ground_truth["bbox"])
            if overlap >= best_overlap:
                best_overlap = overlap
                best_ground_truth_index = ground_truth_index
        if best_ground_truth_index >= 0:
            true_positive_flags[detection_index] = 1
            used_ground_truth_indices.add(best_ground_truth_index)
        else:
            false_positive_flags[detection_index] = 1

    cumulative_true_positives = np.cumsum(true_positive_flags)
    cumulative_false_positives = np.cumsum(false_positive_flags)
    recall_values = cumulative_true_positives / num_gt
    precision_denominators = cumulative_true_positives + cumulative_false_positives
    precision_values = cumulative_true_positives / np.maximum(precision_denominators, 1e-6)

    ap = 0.0
    recall_samples = np.linspace(0, 1, 101)
    for recall_sample in recall_samples:
        eligible_precisions = precision_values[recall_values >= recall_sample]
        if len(eligible_precisions) > 0:
            ap += np.max(eligible_precisions) / 101
    return ap


def compute_map(preds: list[list[dict]], gts: list[list[dict]], iou_thresh: float = 0.5) -> float:
    # Compute mAP at given IoU threshold using 101-point interpolation. Averages per-class AP (COCO-style macro-averaged mAP).
    class_ids: set[int] = set()
    for image_ground_truth in gts:
        for ground_truth in image_ground_truth:
            if ground_truth["class_id"] >= 0:
                class_ids.add(ground_truth["class_id"])
    for image_predictions in preds:
        for prediction in image_predictions:
            if prediction["class_id"] >= 0:
                class_ids.add(prediction["class_id"])

    if not class_ids:
        return 0.0

    per_class_aps: list[float] = []
    for class_id in class_ids:
        class_predictions = []
        class_ground_truth = []
        if len(preds) != len(gts):
            raise ValueError("preds and gts must contain the same number of images")
        for image_index, (image_predictions, image_ground_truth) in enumerate(zip(preds, gts)):
            for prediction in image_predictions:
                if prediction["class_id"] == class_id:
                    prediction_for_ap = {**prediction, "img_idx": image_index}
                    class_predictions.append(prediction_for_ap)
            for ground_truth in image_ground_truth:
                if ground_truth["class_id"] == class_id:
                    ground_truth_for_ap = {**ground_truth, "img_idx": image_index}
                    class_ground_truth.append(ground_truth_for_ap)
        average_precision = _compute_ap_for_class(
            class_predictions,
            class_ground_truth,
            iou_thresh,
        )
        if not np.isnan(average_precision):
            per_class_aps.append(average_precision)

    if not per_class_aps:
        return 0.0
    return float(np.mean(per_class_aps))


class ModelBenchmark:
    # Run one or more detection models against a validation dataset.

    def __init__(
        self,
        models: list[DetectionModel] | None = None,
        dataset: Path | str | None = None,
        conf: float = 0.5,
        inference_iou: float = 0.7,
        evaluation_iou: float = 0.5,
        max_images: int | None = None,
    ):
        if models:
            self.models = models
        else:
            self.models = []
        if isinstance(dataset, (Path, str)):
            self.dataset = Path(dataset)
        else:
            self.dataset = None
        self.conf = conf
        self.inference_iou = inference_iou
        self.evaluation_iou = evaluation_iou
        self.max_images = max_images
        self.evaluated_on_train = False
        if self.dataset is not None:
            self.samples, self.evaluated_on_train = load_yolo_dataset(self.dataset)

    @classmethod
    def from_registry(
        cls,
        model_names: list[str],
        dataset_path: Path | str,
        conf: float = 0.5,
        inference_iou: float = 0.7,
        evaluation_iou: float = 0.5,
        max_images: int | None = None,
    ) -> ModelBenchmark:
        # Create benchmark from model names using ModelRegistry.
        model_registry = ModelRegistry()
        model_registry.discover()
        models = []
        for model_name in model_names:
            model = model_registry.load_model(model_name)
            models.append(model)
        return cls(
            models=models,
            dataset=dataset_path,
            conf=conf,
            inference_iou=inference_iou,
            evaluation_iou=evaluation_iou,
            max_images=max_images,
        )

    def run(self) -> list[BenchmarkResult]:
        # Evaluate every model and return structured results.

        samples = self.samples[: self.max_images] if self.max_images else self.samples
        results: list[BenchmarkResult] = []

        for model in self.models:
            print(f"  Running {model.name}... ", end="", flush=True)

            per_class: dict[str, PerClassMetrics] = {name: PerClassMetrics() for name in CLASS_NAMES}
            total_detections = 0
            total_latency_ms = 0.0
            successful_predictions = 0
            errors: list[str] = []
            all_preds: list[list[dict]] = []
            all_gts: list[list[dict]] = []

            for img_path, gt_objects in samples:
                try:
                    start_time = time.perf_counter()
                    result = model.predict(str(img_path), conf=0.0, iou=self.inference_iou)
                    elapsed_seconds = time.perf_counter() - start_time
                    total_latency_ms += elapsed_seconds * 1000
                    successful_predictions += 1

                    image_predictions: list[dict] = []
                    for det in result.detections:
                        prediction = {
                            "class_id": det.class_id,
                            "confidence": det.confidence,
                            "bbox_pixel": list(det.bbox),
                        }
                        image_predictions.append(prediction)

                    predictions_for_metrics = [
                        prediction
                        for prediction in image_predictions
                        if prediction["confidence"] >= self.conf
                    ]
                    total_detections += len(predictions_for_metrics)

                    prediction_objects: list[Detection] = []
                    for prediction in predictions_for_metrics:
                        class_id = prediction["class_id"]
                        if 0 <= class_id < len(CLASS_NAMES):
                            class_name = CLASS_NAMES[class_id]
                        else:
                            class_name = f"class_{class_id}"
                        prediction_objects.append(
                            Detection(
                                class_id=class_id,
                                class_name=class_name,
                                confidence=prediction["confidence"],
                                bbox=tuple(prediction["bbox_pixel"]),
                            )
                        )

                    ground_truth_objects: list[Detection] = []
                    for ground_truth in gt_objects:
                        class_id = ground_truth["class_id"]
                        if 0 <= class_id < len(CLASS_NAMES):
                            class_name = CLASS_NAMES[class_id]
                        else:
                            class_name = f"class_{class_id}"
                        ground_truth_objects.append(
                            Detection(
                                class_id=class_id,
                                class_name=class_name,
                                confidence=1.0,
                                bbox=tuple(ground_truth["bbox"]),
                            )
                        )

                    class_ids = {
                        detection.class_id
                        for detection in prediction_objects + ground_truth_objects
                    }
                    for class_id in class_ids:
                        class_predictions = [
                            detection
                            for detection in prediction_objects
                            if detection.class_id == class_id
                        ]
                        class_ground_truth = [
                            detection
                            for detection in ground_truth_objects
                            if detection.class_id == class_id
                        ]
                        match_result = match_predictions(
                            class_predictions,
                            class_ground_truth,
                            self.evaluation_iou,
                        )
                        if 0 <= class_id < len(CLASS_NAMES):
                            class_name = CLASS_NAMES[class_id]
                        else:
                            class_name = f"class_{class_id}"
                        if class_name not in per_class:
                            per_class[class_name] = PerClassMetrics()
                        metrics = per_class[class_name]
                        metrics.tp += match_result.true_positives
                        metrics.fp += match_result.false_positives
                        metrics.fn += match_result.false_negatives

                    all_preds.append(image_predictions)
                    all_gts.append(gt_objects)

                except (
                    RuntimeError,
                    ValueError,
                    OSError,
                    FileNotFoundError,
                    ImportError,
                    AttributeError,
                    KeyError,
                ) as exc:
                    errors.append(f"{img_path.name}: {exc}")
                    all_preds.append([])
                    all_gts.append(gt_objects)

            total_images = len(samples)
            if successful_predictions > 0:
                average_latency_ms = total_latency_ms / successful_predictions
            else:
                average_latency_ms = 0.0

            total_true_positives = sum(metrics.tp for metrics in per_class.values())
            total_false_positives = sum(metrics.fp for metrics in per_class.values())
            total_false_negatives = sum(metrics.fn for metrics in per_class.values())

            precision_denominator = total_true_positives + total_false_positives
            if precision_denominator > 0:
                overall_precision = total_true_positives / precision_denominator
            else:
                overall_precision = 0.0

            recall_denominator = total_true_positives + total_false_negatives
            if recall_denominator > 0:
                overall_recall = total_true_positives / recall_denominator
            else:
                overall_recall = 0.0

            combined_score = overall_precision + overall_recall
            if combined_score > 0:
                overall_f1 = 2 * overall_precision * overall_recall / combined_score
            else:
                overall_f1 = 0.0

            map_thresholds = np.linspace(0.5, 0.95, 10)
            map_scores = np.array(
                [compute_map(all_preds, all_gts, iou_thresh=threshold) for threshold in map_thresholds]
            )
            map50 = float(map_scores[0])
            map50_95 = float(np.mean(map_scores))

            model_type = getattr(model, "model_type", str(model.path.suffix))
            benchmark_result = BenchmarkResult(
                model_name=model.name,
                model_path=str(model.path),
                model_type=model_type,
                total_images=total_images,
                per_class=per_class,
                overall_f1=overall_f1,
                overall_precision=overall_precision,
                overall_recall=overall_recall,
                avg_latency_ms=average_latency_ms,
                total_detections=total_detections,
                map50=map50,
                map50_95=map50_95,
                errors=errors,
                evaluated_on_train=self.evaluated_on_train,
            )
            results.append(benchmark_result)
            print("done")

        return results

    @staticmethod
    def export(results: list[BenchmarkResult], output_path: Path | str) -> None:
        # Save benchmark results to a JSON file.
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        serialized_results = []
        for result in results:
            serialized_results.append(result.to_dict())
        with open(output_path, "w", encoding="utf-8") as results_file:
            json.dump(serialized_results, results_file, indent=2)
        print(f"  Results exported to {output_path}")

    @staticmethod
    def comparison_table(results: list[BenchmarkResult]) -> str:
        # Return a markdown table comparing models, sorted by F1 descending.
        sorted_results = sorted(
            results,
            key=lambda result: result.overall_f1,
            reverse=True,
        )

        header = "| Model | Images | Precision | Recall | F1 | mAP50 | Latency (ms) |"
        sep = "|---|---:|---:|---:|---:|---:|---:|"
        rows = [header, sep]

        for result in sorted_results:
            rows.append(
                f"| {result.model_name} "
                f"| {result.total_images} "
                f"| {result.overall_precision:.1%} "
                f"| {result.overall_recall:.1%} "
                f"| {result.overall_f1:.1%} "
                f"| {result.map50:.1%} "
                f"| {result.avg_latency_ms:.1f} |"
            )

        table = "\n".join(rows)
        return table
