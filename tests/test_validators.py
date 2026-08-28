from __future__ import annotations

# Tests for MIRA dataset validators.

import tempfile
from pathlib import Path

from src.pipeline.validators import validate_yolo_dataset, dataset_summary


def _make_yolo_dataset(tmp_path: Path, train_labels: list[str], val_labels: list[str] | None = None):
    # Create a minimal YOLO-format dataset structure.
    for split, labels in [("train", train_labels), ("val", val_labels or [])]:
        img_dir = tmp_path / "images" / split
        lbl_dir = tmp_path / "labels" / split
        img_dir.mkdir(parents=True)
        lbl_dir.mkdir(parents=True)
        for i, content in enumerate(labels):
            # Create a dummy image file
            (img_dir / f"img_{i}.jpg").write_text("fake_image")
            # Create label file
            (lbl_dir / f"img_{i}.txt").write_text(content)
    return tmp_path


def test_valid_dataset():
    with tempfile.TemporaryDirectory() as tmp:
        path = _make_yolo_dataset(
            Path(tmp),
            train_labels=["0 0.5 0.5 0.2 0.2", "1 0.3 0.3 0.1 0.1"],
            val_labels=["0 0.5 0.5 0.2 0.2"],
        )
        result = validate_yolo_dataset(path)
        assert result.is_valid
        assert result.total_images == 3
        assert result.total_labels == 3


def test_missing_train_split():
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp)
        (path / "images" / "val").mkdir(parents=True)
        (path / "labels" / "val").mkdir(parents=True)
        (path / "images" / "val" / "a.jpg").write_text("fake")
        (path / "labels" / "val" / "a.txt").write_text("0 0.5 0.5 0.1 0.1")
        result = validate_yolo_dataset(path)
        assert result.is_valid  # val exists, so it's valid


def test_no_splits_found():
    with tempfile.TemporaryDirectory() as tmp:
        result = validate_yolo_dataset(Path(tmp))
        assert not result.is_valid
        assert any("No train or val split found" in e for e in result.errors)


def test_orphaned_labels():
    with tempfile.TemporaryDirectory() as tmp:
        path = _make_yolo_dataset(Path(tmp), train_labels=[])
        lbl_dir = path / "labels" / "train"
        lbl_dir.mkdir(parents=True, exist_ok=True)
        (lbl_dir / "orphan.txt").write_text("0 0.5 0.5 0.1 0.1")
        result = validate_yolo_dataset(path)
        assert len(result.orphaned_labels) == 1


def test_orphaned_images():
    with tempfile.TemporaryDirectory() as tmp:
        path = _make_yolo_dataset(Path(tmp), train_labels=["0 0.5 0.5 0.1 0.1"])
        img_dir = path / "images" / "train"
        (img_dir / "no_label.jpg").write_text("fake")
        result = validate_yolo_dataset(path)
        assert len(result.orphaned_images) == 1


def test_invalid_label_too_few_values():
    with tempfile.TemporaryDirectory() as tmp:
        path = _make_yolo_dataset(Path(tmp), train_labels=["0 0.5 0.5"])
        result = validate_yolo_dataset(path)
        assert not result.is_valid
        assert len(result.invalid_labels) == 1


def test_invalid_label_negative_class():
    with tempfile.TemporaryDirectory() as tmp:
        path = _make_yolo_dataset(Path(tmp), train_labels=["-1 0.5 0.5 0.1 0.1"])
        result = validate_yolo_dataset(path)
        assert not result.is_valid
        assert any("negative class ID" in err for _, err in result.invalid_labels)


def test_invalid_label_coords_out_of_range():
    with tempfile.TemporaryDirectory() as tmp:
        path = _make_yolo_dataset(Path(tmp), train_labels=["0 0.5 0.5 1.5 0.1"])
        result = validate_yolo_dataset(path)
        assert not result.is_valid
        assert any("coords out of" in err for _, err in result.invalid_labels)


def test_invalid_label_parse_error():
    with tempfile.TemporaryDirectory() as tmp:
        path = _make_yolo_dataset(Path(tmp), train_labels=["0 abc def 0.1 0.1"])
        result = validate_yolo_dataset(path)
        assert not result.is_valid
        assert any("parse error" in err for _, err in result.invalid_labels)


def test_empty_dataset():
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp)
        (path / "images" / "train").mkdir(parents=True)
        (path / "labels" / "train").mkdir(parents=True)
        result = validate_yolo_dataset(path)
        assert not result.is_valid  # empty dataset is not valid
        assert result.total_images == 0
        assert any("0 images" in w for w in result.warnings)


def test_dataset_summary():
    with tempfile.TemporaryDirectory() as tmp:
        path = _make_yolo_dataset(
            Path(tmp),
            train_labels=["0 0.5 0.5 0.2 0.2"],
        )
        summary = dataset_summary(path)
        assert summary["valid"] is True
        assert summary["images"] == 1
        assert summary["labels"] == 1
        assert "class_counts" in summary
