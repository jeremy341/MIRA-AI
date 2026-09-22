# Dataset validators for MIRA pipeline.

from __future__ import annotations

import math
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from ..config import NUM_CLASSES

IMAGE_EXTENSIONS = (".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tiff")


@dataclass
class ValidationResult:
    is_valid: bool = True
    dataset_path: str = ""
    total_images: int = 0
    total_labels: int = 0
    orphaned_labels: list[str] = field(default_factory=list)
    orphaned_images: list[str] = field(default_factory=list)
    invalid_labels: list[tuple[str, str]] = field(default_factory=list)
    class_counts: dict[int, int] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)


def validate_yolo_dataset(dataset_path: str | Path) -> ValidationResult:
    path = Path(dataset_path)
    result = ValidationResult(dataset_path=str(path.resolve()))

    splits = ["train", "val"]
    found_split = False

    for split in splits:
        img_dir = path / "images" / split
        lbl_dir = path / "labels" / split

        if not img_dir.exists() and not lbl_dir.exists():
            continue

        found_split = True

        if not img_dir.exists():
            result.errors.append(f"Missing images/{split} directory")
            result.is_valid = False
            continue

        if not lbl_dir.exists():
            result.errors.append(f"Missing labels/{split} directory")
            result.is_valid = False
            continue

        images = _collect_images(img_dir, result)
        labels = {p.stem: p for p in lbl_dir.glob("*.txt")}

        for stem in labels:
            lbl_path = lbl_dir / f"{stem}.txt"
            img = images.get(stem)

            if img is None:
                result.orphaned_labels.append(str(lbl_path))
                continue

            result.total_labels += 1
            _validate_label_file(lbl_path, result)

        for stem in images:
            if stem not in labels:
                result.orphaned_images.append(str(images[stem]))
            else:
                result.total_images += 1

    if not found_split:
        result.errors.append("No train or val split found")
        result.is_valid = False

    if result.total_images == 0 and not result.errors:
        result.warnings.append("Dataset contains 0 images")
        result.is_valid = False

    if result.orphaned_labels:
        result.warnings.append(f"{len(result.orphaned_labels)} label(s) without matching image")

    if result.orphaned_images:
        result.warnings.append(f"{len(result.orphaned_images)} image(s) without matching label")

    if result.invalid_labels:
        result.errors.append(f"{len(result.invalid_labels)} invalid label(s) found")
        result.is_valid = False

    return result


def _collect_images(image_directory: Path, result: ValidationResult) -> dict[str, Path]:
    images: dict[str, Path] = {}
    for image_path in image_directory.glob("*"):
        if image_path.suffix.lower() not in IMAGE_EXTENSIONS:
            continue

        stem = image_path.stem
        if stem in images:
            result.warnings.append(
                f"Duplicate image stem '{stem}' in {image_directory}: {images[stem]} and {image_path}"
            )
        images[stem] = image_path
    return images


def _validate_label_file(label_path: Path, result: ValidationResult) -> None:
    with open(label_path, encoding="utf-8") as label_file:
        for line_number, line in enumerate(label_file, 1):
            parts = line.strip().split()
            if len(parts) < 5:
                result.invalid_labels.append((str(label_path), f"line {line_number}: < 5 values"))
                continue
            if len(parts) != 5 and (len(parts) < 7 or (len(parts) - 1) % 2 != 0):
                result.invalid_labels.append((str(label_path), f"line {line_number}: invalid coordinate count"))
                continue

            try:
                class_id = int(parts[0])
                if class_id < 0:
                    result.invalid_labels.append((str(label_path), f"line {line_number}: negative class ID"))
                    continue
                if class_id >= NUM_CLASSES:
                    result.invalid_labels.append((str(label_path), f"line {line_number}: class ID out of range"))
                    continue

                coordinates = [float(value) for value in parts[1:]]
                all_coordinates_are_valid = all(
                    math.isfinite(coordinate) and 0.0 <= coordinate <= 1.0 for coordinate in coordinates
                )
                if not all_coordinates_are_valid:
                    result.invalid_labels.append((str(label_path), f"line {line_number}: coords out of [0,1]"))
                    continue
                if len(coordinates) == 4 and (coordinates[2] <= 0.0 or coordinates[3] <= 0.0):
                    result.invalid_labels.append((str(label_path), f"line {line_number}: non-positive box size"))
                    continue

                result.class_counts[class_id] = result.class_counts.get(class_id, 0) + 1
            except (ValueError, IndexError):
                result.invalid_labels.append((str(label_path), f"line {line_number}: parse error"))


def dataset_summary(dataset_path: str | Path) -> dict[str, Any]:
    # Generate a human-readable summary of a dataset.
    result = validate_yolo_dataset(dataset_path)
    return {
        "path": result.dataset_path,
        "valid": result.is_valid,
        "images": result.total_images,
        "labels": result.total_labels,
        "orphaned_labels": len(result.orphaned_labels),
        "orphaned_images": len(result.orphaned_images),
        "invalid_labels": len(result.invalid_labels),
        "class_counts": result.class_counts,
        "warnings": result.warnings,
        "errors": result.errors,
    }
