"""Structured benchmarking module for MIRA detection models.

Runs models against a YOLO-format validation set and produces
per-class + micro-averaged metrics with exportable results.
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from config import CLASS_NAMES

# ── Data classes ─────────────────────────────────────────────────────


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
            "errors": self.errors,
        }


# ── Dataset loader ───────────────────────────────────────────────────


def load_yolo_dataset(dataset_path: Path | str) -> list[tuple[Path, set[int]]]:
    """Load images/val + labels/val from a YOLO-format dataset.

    Returns list of (image_path, set_of_class_ids) pairs.
    Falls back to the train split when val is unavailable.
    """
    dataset_path = Path(dataset_path)

    for split in ("val", "train"):
        img_dir = dataset_path / "images" / split
        lbl_dir = dataset_path / "labels" / split
        if img_dir.exists() and lbl_dir.exists():
            break
    else:
        raise FileNotFoundError(f"No images/val (or train) directory found in {dataset_path}")

    samples: list[tuple[Path, set[int]]] = []
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

        classes: set[int] = set()
        with open(lbl_path) as f:
            for line in f:
                parts = line.strip().split()
                if parts:
                    classes.add(int(parts[0]))
        samples.append((img_path, classes))

    print(
        f"  Loaded {len(samples)} images from {dataset_path.name}/{split}"
        + (f" (skipped {skipped})" if skipped else "")
    )
    return samples


# ── Benchmark runner ─────────────────────────────────────────────────


class ModelBenchmark:
    """Run one or more detection models against a validation dataset."""

    def __init__(
        self,
        models: list[tuple[str, Path]],
        dataset: Path | str,
        conf: float = 0.5,
        iou: float = 0.7,
        max_images: int | None = None,
    ):
        self.models = models
        self.dataset = Path(dataset) if not isinstance(dataset, Path) else dataset
        self.conf = conf
        self.iou = iou
        self.max_images = max_images
        self.samples = load_yolo_dataset(self.dataset)

    def run(self) -> list[BenchmarkResult]:
        """Evaluate every model and return structured results."""
        from ultralytics import YOLO

        if self.max_images:
            self.samples = self.samples[: self.max_images]

        results: list[BenchmarkResult] = []

        for model_name, model_path in self.models:
            is_int8 = "int8" in model_name.lower() and model_path.suffix == ".tflite"
            effective_conf = min(self.conf, 0.25) if is_int8 else self.conf
            task_type = "detect" if model_path.suffix == ".tflite" else None

            print(f"  Running {model_name}... ", end="", flush=True)

            try:
                model = YOLO(str(model_path), task=task_type)
            except Exception as exc:
                print(f"ERROR: {exc}")
                results.append(
                    BenchmarkResult(
                        model_name=model_name,
                        model_path=str(model_path),
                        model_type=model_path.suffix,
                        errors=[str(exc)],
                    )
                )
                continue

            per_class: dict[str, PerClassMetrics] = {name: PerClassMetrics() for name in CLASS_NAMES}
            total_detections = 0
            total_latency_ms = 0.0
            errors: list[str] = []

            for img_path, gt_classes in self.samples:
                try:
                    t0 = time.perf_counter()
                    preds = model(
                        str(img_path),
                        conf=effective_conf,
                        iou=self.iou,
                        verbose=False,
                    )
                    total_latency_ms += (time.perf_counter() - t0) * 1000

                    pred_classes: set[int] = set()
                    boxes = preds[0].boxes
                    if boxes is not None:
                        pred_classes = set(boxes.cls.int().tolist())
                        total_detections += len(pred_classes)

                    for cls_id in range(len(CLASS_NAMES)):
                        cls_name = CLASS_NAMES[cls_id]
                        m = per_class[cls_name]
                        in_gt = cls_id in gt_classes
                        in_pred = cls_id in pred_classes
                        if in_gt and in_pred:
                            m.tp += 1
                        elif not in_gt and in_pred:
                            m.fp += 1
                        elif in_gt and not in_pred:
                            m.fn += 1

                except Exception as exc:
                    errors.append(f"{img_path.name}: {exc}")

            n = len(self.samples)
            avg_latency = total_latency_ms / n if n > 0 else 0.0

            # Micro-averaged overall metrics
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

            results.append(
                BenchmarkResult(
                    model_name=model_name,
                    model_path=str(model_path),
                    model_type=model_path.suffix,
                    total_images=n,
                    per_class=per_class,
                    overall_f1=overall_f1,
                    overall_precision=overall_prec,
                    overall_recall=overall_rec,
                    avg_latency_ms=avg_latency,
                    total_detections=total_detections,
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
        with open(output_path, "w") as f:
            json.dump(data, f, indent=2)
        print(f"  Results exported to {output_path}")

    @staticmethod
    def comparison_table(results: list[BenchmarkResult]) -> str:
        """Return a markdown table comparing models, sorted by F1 descending."""
        sorted_res = sorted(results, key=lambda r: r.overall_f1, reverse=True)

        header = "| Model | Images | Precision | Recall | F1 | Latency (ms) | Detections | Errors |"
        sep = "|---|---:|---:|---:|---:|---:|---:|---:|"
        rows = [header, sep]

        for r in sorted_res:
            rows.append(
                f"| {r.model_name} "
                f"| {r.total_images} "
                f"| {r.overall_precision:.1%} "
                f"| {r.overall_recall:.1%} "
                f"| {r.overall_f1:.1%} "
                f"| {r.avg_latency_ms:.1f} "
                f"| {r.total_detections} "
                f"| {len(r.errors)} |"
            )

        return "\n".join(rows)
