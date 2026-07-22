"""Structured benchmarking module for MIRA detection models.

Runs models against a YOLO-format validation set and produces
per-class + micro-averaged metrics with exportable results.
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

from ..config import CLASS_NAMES
from .models import DetectionModel, ModelRegistry


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
    """Compute IoU between two boxes in xyxy format."""
    x1 = max(box_a[0], box_b[0])
    y1 = max(box_a[1], box_b[1])
    x2 = min(box_a[2], box_b[2])
    y2 = min(box_a[3], box_b[3])
    inter = max(0, x2 - x1) * max(0, y2 - y1)
    area_a = (box_a[2] - box_a[0]) * (box_a[3] - box_a[1])
    area_b = (box_b[2] - box_b[0]) * (box_b[3] - box_b[1])
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
        }


def load_yolo_dataset(dataset_path: Path | str) -> list[tuple[Path, list[dict]]]:
    """Load images/val + labels/val from a YOLO-format dataset.

    Returns list of (image_path, gt_objects) where gt_objects is a list of
    dicts with keys: class_id, bbox (xyxy pixel).
    Falls back to the train split when val is unavailable.
    """
    from PIL import Image

    dataset_path = Path(dataset_path)

    if dataset_path.is_file() and dataset_path.suffix in (".yaml", ".yml"):
        dataset_path = dataset_path.parent

    for split in ("val", "train"):
        img_dir = dataset_path / "images" / split
        lbl_dir = dataset_path / "labels" / split
        if img_dir.exists() and lbl_dir.exists():
            break
    else:
        raise FileNotFoundError(f"No images/val (or train) directory found in {dataset_path}")

    samples: list[tuple[Path, list[dict]]] = []
    skipped = 0

    for lbl_path in sorted(lbl_dir.glob("*.txt")):
        stem = lbl_path.stem
        img_path = None
        for ext in (".jpg", ".png", ".jpeg"):
            candidate = img_dir / f"{stem}{ext}"
            if candidate.exists():
                img_path = candidate
                break
        if img_path is None:
            skipped += 1
            continue

        with Image.open(img_path) as img:
            img_w, img_h = img.size

        objects: list[dict] = []
        with open(lbl_path, encoding="utf-8") as f:
            for line in f:
                parts = line.strip().split()
                if len(parts) < 5:
                    continue
                cls_id = int(parts[0])
                coords = [float(p) for p in parts[1:]]
                if len(coords) == 4:
                    # Detection format: x_center, y_center, width, height
                    xc, yc, w, h = coords
                    x1 = (xc - w / 2) * img_w
                    y1 = (yc - h / 2) * img_h
                    x2 = (xc + w / 2) * img_w
                    y2 = (yc + h / 2) * img_h
                else:
                    # Segmentation polygon: x1, y1, x2, y2, ...
                    xs = [coords[i] for i in range(0, len(coords), 2)]
                    ys = [coords[i] for i in range(1, len(coords), 2)]
                    x1 = min(xs) * img_w
                    y1 = min(ys) * img_h
                    x2 = max(xs) * img_w
                    y2 = max(ys) * img_h
                objects.append(
                    {
                        "class_id": cls_id,
                        "bbox": [x1, y1, x2, y2],
                    }
                )
        samples.append((img_path, objects))

    print(
        f"  Loaded {len(samples)} images from {dataset_path.name}/{split}"
        + (f" (skipped {skipped})" if skipped else "")
    )
    return samples


def compute_map(preds: list[list[dict]], gts: list[list[dict]], iou_thresh: float = 0.5) -> float:
    """Compute mAP at given IoU threshold using 101-point interpolation."""
    all_detections: list[dict] = []
    num_gt = 0
    for img_idx, (img_preds, img_gts) in enumerate(zip(preds, gts, strict=True)):
        num_gt += len(img_gts)
        for d in img_preds:
            all_detections.append({**d, "img_idx": img_idx})
    all_detections.sort(key=lambda x: x["confidence"], reverse=True)

    tp = np.zeros(len(all_detections))
    fp = np.zeros(len(all_detections))
    gt_used = [set() for _ in gts]

    for i, det in enumerate(all_detections):
        img_idx = det["img_idx"]
        best_iou = iou_thresh
        best_gt = -1
        for j, gt in enumerate(gts[img_idx]):
            if j in gt_used[img_idx]:
                continue
            iou = compute_iou(det["bbox_pixel"], gt["bbox"])
            if iou >= best_iou:
                best_iou = iou
                best_gt = j
        if best_gt >= 0 and det["class_id"] == gts[img_idx][best_gt]["class_id"]:
            tp[i] = 1
            gt_used[img_idx].add(best_gt)
        else:
            fp[i] = 1

    acc_tp = np.cumsum(tp)
    acc_fp = np.cumsum(fp)
    rec = acc_tp / max(num_gt, 1)
    prec = acc_tp / np.maximum(acc_tp + acc_fp, 1e-6)

    ap = 0.0
    for t in np.arange(0, 1.01, 0.01):
        mask = rec >= t
        if np.any(mask):
            ap += np.max(prec[mask]) / 101
    return ap


class ModelBenchmark:
    """Run one or more detection models against a validation dataset."""

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
        self.iou = iou
        self.max_images = max_images
        self.samples = load_yolo_dataset(self.dataset) if self.dataset else []

    @classmethod
    def from_registry(
        cls,
        model_names: list[str],
        dataset_path: Path | str,
        conf: float = 0.5,
        iou: float = 0.7,
        max_images: int | None = None,
    ) -> ModelBenchmark:
        """Create benchmark from model names using ModelRegistry."""
        registry = ModelRegistry()
        registry.discover()
        models = [registry.load_model(name) for name in model_names]
        return cls(models=models, dataset=dataset_path, conf=conf, iou=iou, max_images=max_images)

    def run(self) -> list[BenchmarkResult]:
        """Evaluate every model and return structured results."""

        if self.max_images and self.samples:
            self.samples = self.samples[: self.max_images]

        results: list[BenchmarkResult] = []

        for model in self.models:
            print(f"  Running {model.name}... ", end="", flush=True)

            per_class: dict[str, PerClassMetrics] = {name: PerClassMetrics() for name in CLASS_NAMES}
            total_detections = 0
            total_latency_ms = 0.0
            errors: list[str] = []

            all_preds: list[list[dict]] = []
            all_gts: list[list[dict]] = []

            for img_path, gt_objects in self.samples:
                try:
                    t0 = time.perf_counter()
                    result = model.predict(str(img_path), conf=self.conf, iou=self.iou)
                    total_latency_ms += (time.perf_counter() - t0) * 1000

                    img_preds: list[dict] = []
                    for det in result.detections:
                        total_detections += 1
                        img_preds.append(
                            {
                                "class_id": det.class_id,
                                "confidence": det.confidence,
                                "bbox_pixel": list(det.bbox),
                            }
                        )

                    # IoU-based per-class matching (GT bbox already in xyxy pixel)
                    gt_boxes = [obj["bbox"] for obj in gt_objects]
                    pred_boxes = [d["bbox_pixel"] for d in img_preds]
                    gt_matched = [False] * len(gt_objects)
                    pred_matched = [False] * len(img_preds)

                    for gi, gt_box in enumerate(gt_boxes):
                        best_iou = self.iou
                        best_pi = -1
                        for pi, pred_box in enumerate(pred_boxes):
                            if pred_matched[pi]:
                                continue
                            iou_val = compute_iou(gt_box, pred_box)
                            gt_class = gt_objects[gi]["class_id"]
                            pred_class = img_preds[pi]["class_id"]
                            if iou_val >= best_iou and gt_class == pred_class:
                                best_iou = iou_val
                                best_pi = pi
                        if best_pi >= 0:
                            gt_matched[gi] = True
                            pred_matched[best_pi] = True

                    for gi, matched in enumerate(gt_matched):
                        cid = gt_objects[gi]["class_id"]
                        cls_name = CLASS_NAMES[cid] if cid < len(CLASS_NAMES) else f"class_{cid}"
                        if cls_name not in per_class:
                            per_class[cls_name] = PerClassMetrics()
                        if matched:
                            per_class[cls_name].tp += 1
                        else:
                            per_class[cls_name].fn += 1

                    for pi, matched in enumerate(pred_matched):
                        if not matched:
                            cid = img_preds[pi]["class_id"]
                            cls_name = CLASS_NAMES[cid] if cid < len(CLASS_NAMES) else f"class_{cid}"
                            if cls_name not in per_class:
                                per_class[cls_name] = PerClassMetrics()
                            per_class[cls_name].fp += 1

                    all_preds.append(img_preds)
                    all_gts.append(gt_objects)

                except Exception as exc:
                    errors.append(f"{img_path.name}: {exc}")
                    all_preds.append([])
                    all_gts.append(gt_objects)

            n = len(self.samples)
            avg_latency = total_latency_ms / n if n > 0 else 0.0

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

            map50 = compute_map(all_preds, all_gts, iou_thresh=0.5)
            map50_95 = float(
                np.mean([compute_map(all_preds, all_gts, iou_thresh=t) for t in np.arange(0.5, 0.96, 0.05)])
            )

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
                )
            )
            print("done")

        return results

    @staticmethod
    def export(results: list[BenchmarkResult], output_path: Path | str) -> None:
        """Save benchmark results to a JSON file."""
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        data = [r.to_dict() for r in results]
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        print(f"  Results exported to {output_path}")

    @staticmethod
    def comparison_table(results: list[BenchmarkResult]) -> str:
        """Return a markdown table comparing models, sorted by F1 descending."""
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
