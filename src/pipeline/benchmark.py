# Structured benchmarking module for MIRA detection models.

from __future__ import annotations

import json
import math
import time
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

from ..config import CLASS_NAMES
from .models import DetectionModel, ModelRegistry

IMAGE_EXTENSIONS = (".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tiff")


# keep simple dataclass - no fancy options
@dataclass
class PerClassMetrics:
    tp: int = 0
    fp: int = 0
    fn: int = 0

    @property
    def precision(self) -> float:
        denom = self.tp + self.fp
        return self.tp / denom if denom > 0 else 0.0

    @property
    def recall(self) -> float:
        denom = self.tp + self.fn
        return self.tp / denom if denom > 0 else 0.0

    @property
    def f1(self) -> float:
        p, r = self.precision, self.recall
        return 2 * p * r / (p + r) if (p + r) > 0 else 0.0

    def to_dict(self) -> dict:
        return {
            "tp": self.tp,
            "fp": self.fp,
            "fn": self.fn,
            "precision": self.precision,
            "recall": self.recall,
            "f1": self.f1,
        }


def compute_iou(box_a: list[float], box_b: list[float]) -> float:
    # Compute IoU between two boxes in xyxy format.
    x1 = max(box_a[0], box_b[0])
    y1 = max(box_a[1], box_b[1])
    x2 = min(box_a[2], box_b[2])
    y2 = min(box_a[3], box_b[3])
    inter = max(0, x2 - x1) * max(0, y2 - y1)
    area_a = max(0, box_a[2] - box_a[0]) * max(0, box_a[3] - box_a[1])
    area_b = max(0, box_b[2] - box_b[0]) * max(0, box_b[3] - box_b[1])
    union = area_a + area_b - inter
    return inter / union if union > 0 else 0.0


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
    if dataset_path.is_file() and dataset_path.suffix.lower() in (".yaml", ".yml"):
        import yaml

        dataset_config = yaml.safe_load(dataset_path.read_text(encoding="utf-8")) or {}
        dataset_root = dataset_path.parent
        configured_root = dataset_config.get("path")
        if configured_root:
            configured_root = Path(configured_root)
            dataset_root = configured_root if configured_root.is_absolute() else dataset_root / configured_root
    else:
        dataset_root = dataset_path

    def split_directories(split_name: str) -> tuple[Path, Path]:
        configured_split = dataset_config.get(split_name)
        if isinstance(configured_split, list):
            configured_split = configured_split[0] if configured_split else None
        if configured_split:
            image_dir = Path(configured_split)
            image_dir = image_dir if image_dir.is_absolute() else dataset_root / image_dir
            parts = list(image_dir.parts)
            if "images" in parts:
                parts[parts.index("images")] = "labels"
                label_dir = Path(*parts)
            else:
                label_dir = dataset_root / "labels" / split_name
            return image_dir, label_dir
        return dataset_root / "images" / split_name, dataset_root / "labels" / split_name

    split = "val"
    evaluated_on_train = False
    img_dir, lbl_dir = split_directories(split)
    if not img_dir.exists():
        from ..logger import get_logger as _get_logger

        _get_logger(__name__).warning(
            "Validation split not found in %s - falling back to train split. "
            "Metrics may be inflated because the model is evaluated on training data.",
            dataset_root,
        )
        split = "train"
        evaluated_on_train = True
        img_dir, lbl_dir = split_directories(split)
        if not img_dir.exists():
            raise FileNotFoundError(f"No images/val (or train) directory found in {dataset_root}")

    samples: list[tuple[Path, list[dict]]] = []
    skipped = 0

    image_paths = sorted(
        path for path in img_dir.iterdir() if path.is_file() and path.suffix.lower() in IMAGE_EXTENSIONS
    )
    for img_path in image_paths:
        lbl_path = lbl_dir / f"{img_path.stem}.txt"

        try:
            with Image.open(img_path) as img:
                img_w, img_h = img.size
        except (OSError, ValueError):
            skipped += 1
            continue

        objects: list[dict] = []
        if lbl_path.exists():
            try:
                lines = lbl_path.read_text(encoding="utf-8").splitlines()
            except OSError:
                lines = []
            for line in lines:
                parts = line.strip().split()
                if len(parts) < 5:
                    continue
                try:
                    cls_id = int(parts[0])
                    coords = [float(value) for value in parts[1:]]
                except ValueError:
                    continue
                if cls_id < 0 or not all(math.isfinite(value) for value in coords):
                    continue
                if len(coords) == 4:
                    xc, yc, box_width, box_height = coords
                    x1 = (xc - box_width / 2) * img_w
                    y1 = (yc - box_height / 2) * img_h
                    x2 = (xc + box_width / 2) * img_w
                    y2 = (yc + box_height / 2) * img_h
                elif len(coords) >= 6 and len(coords) % 2 == 0:
                    xs = coords[0::2]
                    ys = coords[1::2]
                    x1 = min(xs) * img_w
                    y1 = min(ys) * img_h
                    x2 = max(xs) * img_w
                    y2 = max(ys) * img_h
                else:
                    continue
                objects.append({"class_id": cls_id, "bbox": [x1, y1, x2, y2]})
        samples.append((img_path, objects))

    print(
        f"  Loaded {len(samples)} images from {dataset_root.name}/{split}"
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

    all_detections_for_class.sort(key=lambda x: x["confidence"], reverse=True)

    tp = np.zeros(len(all_detections_for_class))
    fp = np.zeros(len(all_detections_for_class))
    gt_used = set()

    for i, det in enumerate(all_detections_for_class):
        best_iou = iou_thresh
        best_gt = -1
        for j, gt in enumerate(all_gts_for_class):
            if j in gt_used:
                continue
            if gt["img_idx"] != det["img_idx"]:
                continue
            iou = compute_iou(det["bbox_pixel"], gt["bbox"])
            if iou >= best_iou:
                best_iou = iou
                best_gt = j
        if best_gt >= 0:
            tp[i] = 1
            gt_used.add(best_gt)
        else:
            fp[i] = 1

    acc_tp = np.cumsum(tp)
    acc_fp = np.cumsum(fp)
    rec = acc_tp / num_gt
    prec = acc_tp / np.maximum(acc_tp + acc_fp, 1e-6)

    ap = 0.0
    for t in np.linspace(0, 1, 101):
        mask = rec >= t
        if np.any(mask):
            ap += np.max(prec[mask]) / 101
    return ap


def compute_map(preds: list[list[dict]], gts: list[list[dict]], iou_thresh: float = 0.5) -> float:
    # Compute mAP at given IoU threshold using 101-point interpolation. Averages per-class AP (COCO-style macro-averaged mAP).
    class_ids: set[int] = set()
    for img_gts in gts:
        for gt in img_gts:
            if gt["class_id"] >= 0:
                class_ids.add(gt["class_id"])
    for img_preds in preds:
        for d in img_preds:
            if d["class_id"] >= 0:
                class_ids.add(d["class_id"])

    if not class_ids:
        return 0.0

    per_class_aps = []
    for cid in class_ids:
        class_preds = []
        class_gts = []
        for img_idx, (img_preds, img_gts) in enumerate(zip(preds, gts, strict=True)):
            for d in img_preds:
                if d["class_id"] == cid:
                    class_preds.append({**d, "img_idx": img_idx})
            for gt in img_gts:
                if gt["class_id"] == cid:
                    class_gts.append({**gt, "img_idx": img_idx})
        ap = _compute_ap_for_class(class_preds, class_gts, iou_thresh)
        if not np.isnan(ap):
            per_class_aps.append(ap)

    return float(np.mean(per_class_aps)) if per_class_aps else 0.0


class ModelBenchmark:
    # Run one or more detection models against a validation dataset.

    def __init__(
        self,
        models: list[DetectionModel] | None = None,
        dataset: Path | str | None = None,
        conf: float = 0.5,
        iou: float = 0.7,
        max_images: int | None = None,
    ):
        self.models = models or []
        self.dataset = Path(dataset) if isinstance(dataset, (Path, str)) else None
        self.conf = conf
        self.iou = iou  # COCO-standard eval threshold (0.7); inference default is typically 0.45
        self.max_images = max_images
        self.evaluated_on_train = False
        if self.dataset:
            self.samples, self.evaluated_on_train = load_yolo_dataset(self.dataset)

    @classmethod
    def from_registry(
        cls,
        model_names: list[str],
        dataset_path: Path | str,
        conf: float = 0.5,
        iou: float = 0.7,
        max_images: int | None = None,
    ) -> ModelBenchmark:
        # Create benchmark from model names using ModelRegistry.
        registry = ModelRegistry()
        registry.discover()
        models = [registry.load_model(name) for name in model_names]
        return cls(models=models, dataset=dataset_path, conf=conf, iou=iou, max_images=max_images)

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
                    t0 = time.perf_counter()
                    result = model.predict(str(img_path), conf=0.0, iou=self.iou)
                    total_latency_ms += (time.perf_counter() - t0) * 1000
                    successful_predictions += 1

                    img_preds: list[dict] = []
                    for det in result.detections:
                        img_preds.append(
                            {
                                "class_id": det.class_id,
                                "confidence": det.confidence,
                                "bbox_pixel": list(det.bbox),
                            }
                        )

                    eval_preds = [pred for pred in img_preds if pred["confidence"] >= self.conf]
                    total_detections += len(eval_preds)
                    # Detection-first IoU-based matching (consistent with compute_map)
                    sorted_pred_indices = sorted(
                        range(len(eval_preds)), key=lambda i: eval_preds[i]["confidence"], reverse=True
                    )
                    gt_used = [False] * len(gt_objects)

                    tp_count: defaultdict[str, int] = defaultdict(int)
                    fp_count: defaultdict[str, int] = defaultdict(int)

                    for pi in sorted_pred_indices:
                        pred = eval_preds[pi]
                        pred_cid = pred["class_id"]
                        pred_cls = CLASS_NAMES[pred_cid] if 0 <= pred_cid < len(CLASS_NAMES) else f"class_{pred_cid}"
                        best_iou = 0.5
                        best_gi = -1
                        for gi, gt_obj in enumerate(gt_objects):
                            if gt_used[gi]:
                                continue
                            if gt_obj["class_id"] != pred_cid:
                                continue
                            iou_val = compute_iou(pred["bbox_pixel"], gt_obj["bbox"])
                            if iou_val >= best_iou:
                                best_iou = iou_val
                                best_gi = gi
                        if best_gi >= 0:
                            gt_used[best_gi] = True
                            tp_count[pred_cls] += 1
                        else:
                            fp_count[pred_cls] += 1

                    fn_count: defaultdict[str, int] = defaultdict(int)
                    for gi, used in enumerate(gt_used):
                        if not used:
                            cid = gt_objects[gi]["class_id"]
                            cls_name = CLASS_NAMES[cid] if 0 <= cid < len(CLASS_NAMES) else f"class_{cid}"
                            fn_count[cls_name] += 1

                    for cls_name in set(list(tp_count.keys()) + list(fp_count.keys()) + list(fn_count.keys())):
                        if cls_name not in per_class:
                            per_class[cls_name] = PerClassMetrics()
                        per_class[cls_name].tp += tp_count.get(cls_name, 0)
                        per_class[cls_name].fp += fp_count.get(cls_name, 0)
                        per_class[cls_name].fn += fn_count.get(cls_name, 0)

                    all_preds.append(img_preds)
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

            n = len(samples)
            avg_latency = total_latency_ms / successful_predictions if successful_predictions > 0 else 0.0

            total_tp = sum(m.tp for m in per_class.values())
            total_fp = sum(m.fp for m in per_class.values())
            total_fn = sum(m.fn for m in per_class.values())

            overall_prec = total_tp / (total_tp + total_fp) if (total_tp + total_fp) > 0 else 0.0
            overall_rec = total_tp / (total_tp + total_fn) if (total_tp + total_fn) > 0 else 0.0
            overall_f1 = (
                2 * overall_prec * overall_rec / (overall_prec + overall_rec)
                if (overall_prec + overall_rec) > 0
                else 0.0
            )

            map_thresholds = np.linspace(0.5, 0.95, 10)
            map_scores = np.array([compute_map(all_preds, all_gts, iou_thresh=t) for t in map_thresholds])
            map50 = float(map_scores[0])
            map50_95 = float(np.mean(map_scores))

            results.append(
                BenchmarkResult(
                    model_name=model.name,
                    model_path=str(model.path),
                    model_type=getattr(model, "model_type", str(model.path.suffix)),
                    total_images=n,
                    per_class=per_class,
                    overall_f1=overall_f1,
                    overall_precision=overall_prec,
                    overall_recall=overall_rec,
                    avg_latency_ms=avg_latency,
                    total_detections=total_detections,
                    map50=map50,
                    map50_95=map50_95,
                    errors=errors,
                    evaluated_on_train=self.evaluated_on_train,
                )
            )
            print("done")

        return results

    @staticmethod
    def export(results: list[BenchmarkResult], output_path: Path | str) -> None:
        # Save benchmark results to a JSON file.
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        data = [r.to_dict() for r in results]
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        print(f"  Results exported to {output_path}")

    @staticmethod
    def comparison_table(results: list[BenchmarkResult]) -> str:
        # Return a markdown table comparing models, sorted by F1 descending.
        sorted_res = sorted(results, key=lambda r: r.overall_f1, reverse=True)

        header = "| Model | Images | Precision | Recall | F1 | mAP50 | Latency (ms) |"
        sep = "|---|---:|---:|---:|---:|---:|---:|"
        rows = [header, sep]

        for r in sorted_res:
            rows.append(
                f"| {r.model_name} "
                f"| {r.total_images} "
                f"| {r.overall_precision:.1%} "
                f"| {r.overall_recall:.1%} "
                f"| {r.overall_f1:.1%} "
                f"| {r.map50:.1%} "
                f"| {r.avg_latency_ms:.1f} |"
            )

        return "\n".join(rows)
