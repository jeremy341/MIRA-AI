"""Dataset validators for MIRA pipeline.

Provides validation and integrity checking for YOLO-format datasets
before and after merge operations.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


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
    """Validate a YOLO-format dataset.

    Checks:
    - Directory structure exists (images/train, labels/train, etc.)
    - Each label file has a corresponding image
    - Label files are valid (proper format, valid class IDs)
    - No orphaned files
    """
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

        images = {p.stem: p for p in img_dir.glob("*") if p.suffix.lower() in (".jpg", ".jpeg", ".png")}
        labels = {p.stem: p for p in lbl_dir.glob("*.txt")}

        for stem in labels:
            lbl_path = lbl_dir / f"{stem}.txt"
            img = images.get(stem)

            if img is None:
                result.orphaned_labels.append(str(lbl_path))
                continue

            result.total_labels += 1

            # Validate label content
            with open(lbl_path) as f:
                for line_num, line in enumerate(f, 1):
                    parts = line.strip().split()
                    if len(parts) < 5:
                        result.invalid_labels.append((str(lbl_path), f"line {line_num}: < 5 values"))
                        continue
                    try:
                        cls_id = int(parts[0])
                        if cls_id < 0:
                            result.invalid_labels.append((str(lbl_path), f"line {line_num}: negative class ID"))
                            continue
                        coords = [float(p) for p in parts[1:5]]
                        if not all(0.0 <= c <= 1.0 for c in coords):
                            result.invalid_labels.append((str(lbl_path), f"line {line_num}: coords out of [0,1]"))
                            continue
                        result.class_counts[cls_id] = result.class_counts.get(cls_id, 0) + 1
                    except (ValueError, IndexError):
                        result.invalid_labels.append((str(lbl_path), f"line {line_num}: parse error"))

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


def dataset_summary(dataset_path: str | Path) -> dict[str, Any]:
    """Generate a human-readable summary of a dataset."""
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
