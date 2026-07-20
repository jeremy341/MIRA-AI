"""Tests for MIRA dataset validators."""

import sys
import pathlib

import pytest

_project_root = str(pathlib.Path(__file__).resolve().parent.parent)
_src_dir = str(pathlib.Path(__file__).resolve().parent.parent / "src")
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)
if _src_dir not in sys.path:
    sys.path.insert(0, _src_dir)


# ── Helpers ──────────────────────────────────────────────────────────


def _make_yolo_dataset(base, split="train", images=None, labels=None, valid_labels=None):
    """Create a minimal YOLO-format dataset structure in base directory."""
    img_dir = base / "images" / split
    lbl_dir = base / "labels" / split
    img_dir.mkdir(parents=True, exist_ok=True)
    lbl_dir.mkdir(parents=True, exist_ok=True)

    for name in (images or []):
        (img_dir / name).touch()

    for name, content in (labels or []):
        (lbl_dir / name).write_text(content)

    for name in (valid_labels or []):
        (lbl_dir / name).write_text("0 0.5 0.5 0.1 0.1\n")


# ── ValidationResult dataclass ───────────────────────────────────────


def test_validation_result_defaults():
    from src.pipeline.validators import ValidationResult

    r = ValidationResult()
    assert r.is_valid is True
    assert r.total_images == 0
    assert r.total_labels == 0
    assert r.orphaned_labels == []
    assert r.orphaned_images == []
    assert r.invalid_labels == []
    assert r.class_counts == {}
    assert r.warnings == []
    assert r.errors == []


def test_validation_result_with_values():
    from src.pipeline.validators import ValidationResult

    r = ValidationResult(
        is_valid=False,
        total_images=10,
        total_labels=8,
        orphaned_labels=["/fake/extra.txt"],
        errors=["Something wrong"],
    )
    assert r.is_valid is False
    assert r.total_images == 10
    assert len(r.errors) == 1


# ── validate_yolo_dataset — valid ────────────────────────────────────


def test_validate_valid_structure(tmp_path):
    from src.pipeline.validators import validate_yolo_dataset

    _make_yolo_dataset(
        tmp_path,
        valid_labels=["img1.txt", "img2.txt"],
        images=["img1.jpg", "img2.jpg"],
    )
    result = validate_yolo_dataset(tmp_path)
    assert result.is_valid is True
    assert result.total_images == 2
    assert result.total_labels == 2
    assert result.errors == []


def test_validate_valid_with_class_counts(tmp_path):
    from src.pipeline.validators import validate_yolo_dataset

    _make_yolo_dataset(
        tmp_path,
        images=["a.jpg", "b.jpg"],
        labels=[
            ("a.txt", "0 0.5 0.5 0.1 0.1\n1 0.3 0.3 0.2 0.2\n"),
            ("b.txt", "0 0.1 0.1 0.05 0.05\n"),
        ],
    )
    result = validate_yolo_dataset(tmp_path)
    assert result.class_counts[0] == 2
    assert result.class_counts[1] == 1


# ── validate_yolo_dataset — missing images ───────────────────────────


def test_validate_missing_images_dir(tmp_path):
    from src.pipeline.validators import validate_yolo_dataset

    lbl_dir = tmp_path / "labels" / "train"
    lbl_dir.mkdir(parents=True)
    (lbl_dir / "a.txt").write_text("0 0.5 0.5 0.1 0.1\n")

    result = validate_yolo_dataset(tmp_path)
    assert result.is_valid is False
    assert any("Missing images" in e for e in result.errors)


# ── validate_yolo_dataset — missing labels ───────────────────────────


def test_validate_missing_labels_dir(tmp_path):
    from src.pipeline.validators import validate_yolo_dataset

    img_dir = tmp_path / "images" / "train"
    img_dir.mkdir(parents=True)
    (img_dir / "a.jpg").touch()

    result = validate_yolo_dataset(tmp_path)
    assert result.is_valid is False
    assert any("Missing labels" in e for e in result.errors)


# ── validate_yolo_dataset — invalid label format ─────────────────────


def test_validate_invalid_label_too_few_fields(tmp_path):
    from src.pipeline.validators import validate_yolo_dataset

    _make_yolo_dataset(
        tmp_path,
        images=["img1.jpg"],
        labels=[("img1.txt", "0 0.5 0.5\n")],
    )
    result = validate_yolo_dataset(tmp_path)
    assert result.is_valid is False
    assert len(result.invalid_labels) > 0


def test_validate_invalid_label_non_numeric(tmp_path):
    from src.pipeline.validators import validate_yolo_dataset

    _make_yolo_dataset(
        tmp_path,
        images=["img1.jpg"],
        labels=[("img1.txt", "abc 0.5 0.5 0.1 0.1\n")],
    )
    result = validate_yolo_dataset(tmp_path)
    assert result.is_valid is False
    assert len(result.invalid_labels) > 0


# ── validate_yolo_dataset — out-of-range class IDs ───────────────────


def test_validate_negative_class_id(tmp_path):
    from src.pipeline.validators import validate_yolo_dataset

    _make_yolo_dataset(
        tmp_path,
        images=["img1.jpg"],
        labels=[("img1.txt", "-1 0.5 0.5 0.1 0.1\n")],
    )
    result = validate_yolo_dataset(tmp_path)
    assert result.is_valid is False
    assert len(result.invalid_labels) > 0


def test_validate_coords_out_of_range(tmp_path):
    from src.pipeline.validators import validate_yolo_dataset

    _make_yolo_dataset(
        tmp_path,
        images=["img1.jpg"],
        labels=[("img1.txt", "0 1.5 0.5 0.1 0.1\n")],
    )
    result = validate_yolo_dataset(tmp_path)
    assert result.is_valid is False
    assert len(result.invalid_labels) > 0


# ── validate_yolo_dataset — orphaned files ───────────────────────────


def test_validate_orphaned_labels(tmp_path):
    from src.pipeline.validators import validate_yolo_dataset

    _make_yolo_dataset(
        tmp_path,
        images=["a.jpg"],
        labels=[("a.txt", "0 0.5 0.5 0.1 0.1\n"), ("orphan.txt", "0 0.5 0.5 0.1 0.1\n")],
    )
    result = validate_yolo_dataset(tmp_path)
    assert len(result.orphaned_labels) == 1
    assert "orphan" in result.orphaned_labels[0]
    assert any("without matching image" in w for w in result.warnings)


def test_validate_orphaned_images(tmp_path):
    from src.pipeline.validators import validate_yolo_dataset

    _make_yolo_dataset(
        tmp_path,
        images=["a.jpg", "orphan.jpg"],
        valid_labels=["a.txt"],
    )
    result = validate_yolo_dataset(tmp_path)
    assert len(result.orphaned_images) == 1
    assert "orphan" in result.orphaned_images[0]
    assert any("without matching label" in w for w in result.warnings)


# ── validate_yolo_dataset — non-existent path ────────────────────────


def test_validate_nonexistent_path():
    from src.pipeline.validators import validate_yolo_dataset

    result = validate_yolo_dataset("/nonexistent/path/to/dataset")
    assert result.is_valid is False
    assert any("No train or val split" in e for e in result.errors)


# ── validate_yolo_dataset — no split found ───────────────────────────


def test_validate_empty_dir_no_split(tmp_path):
    from src.pipeline.validators import validate_yolo_dataset

    result = validate_yolo_dataset(tmp_path)
    assert result.is_valid is False
    assert any("No train or val split" in e for e in result.errors)


# ── dataset_summary ──────────────────────────────────────────────────


def test_dataset_summary_output_format(tmp_path):
    from src.pipeline.validators import dataset_summary

    _make_yolo_dataset(
        tmp_path,
        images=["img1.jpg"],
        valid_labels=["img1.txt"],
    )
    summary = dataset_summary(tmp_path)
    assert isinstance(summary, dict)
    assert "path" in summary
    assert "valid" in summary
    assert "images" in summary
    assert "labels" in summary
    assert "orphaned_labels" in summary
    assert "orphaned_images" in summary
    assert "invalid_labels" in summary
    assert "class_counts" in summary
    assert "warnings" in summary
    assert "errors" in summary
    assert summary["valid"] is True
    assert summary["images"] == 1
    assert summary["labels"] == 1
