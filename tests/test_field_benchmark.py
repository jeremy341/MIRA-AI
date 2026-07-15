"""Tests for MIRA field benchmark metric computation."""
import sys
import pathlib

# Add src/ to path so field_benchmark can find config module
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "src"))

import pytest
from field_benchmark import compute_metrics, load_dataset


def test_compute_metrics_tp_fp_fn_counts():
    results = {
        "model_a": {
            "img1.png": {"true": {0, 1}, "pred": {0, 1}},
            "img2.png": {"true": {0}, "pred": {0}},
            "img3.png": {"true": {1}, "pred": set()},
        }
    }
    metrics = compute_metrics(results)
    per_class = metrics["model_a"]

    assert per_class["glass"]["tp"] == 2
    assert per_class["glass"]["fp"] == 0
    assert per_class["glass"]["fn"] == 0
    assert per_class["metal"]["tp"] == 1
    assert per_class["metal"]["fp"] == 0
    assert per_class["metal"]["fn"] == 1


def test_compute_metrics_precision_recall_f1():
    results = {
        "model_b": {
            **{f"img{i}.png": {"true": {2}, "pred": {2}} for i in range(10)},
            **{f"img{i+10}.png": {"true": set(), "pred": {2}} for i in range(2)},
            **{f"img{i+12}.png": {"true": {2}, "pred": set()} for i in range(3)},
        },
    }
    metrics = compute_metrics(results)
    prec = metrics["model_b"]["paper"]["precision"]
    rec = metrics["model_b"]["paper"]["recall"]
    f1 = metrics["model_b"]["paper"]["f1"]

    assert abs(prec - 10 / 12) < 1e-9
    assert abs(rec - 10 / 13) < 1e-9
    assert abs(f1 - 2 * prec * rec / (prec + rec)) < 1e-9


def test_compute_metrics_zero_division_no_detections():
    results = {
        "dead_model": {
            "img1.png": {"true": {0}, "pred": set()},
            "img2.png": {"true": set(), "pred": set()},
        }
    }
    metrics = compute_metrics(results)
    prec = metrics["dead_model"]["glass"]["precision"]
    rec = metrics["dead_model"]["glass"]["recall"]
    f1 = metrics["dead_model"]["glass"]["f1"]

    assert prec == 0.0
    assert rec == 0.0
    assert f1 == 0.0


def test_compute_metrics_all_false_positives():
    results = {
        "fp_model": {
            "img1.png": {"true": set(), "pred": {3}},
            "img2.png": {"true": set(), "pred": {3}},
        }
    }
    metrics = compute_metrics(results)
    prec = metrics["fp_model"]["plastic"]["precision"]
    rec = metrics["fp_model"]["plastic"]["recall"]

    # FP model: 0 TP, 2 FP, 0 FN => precision = 0/2 = 0.0, recall = 0/0 = 0.0
    assert prec == 0.0
    assert rec == 0.0


def test_compute_metrics_per_class_independence():
    results = {
        "mixed_model": {
            "img1.png": {"true": {0}, "pred": {0}},
            "img2.png": {"true": {1}, "pred": {0}},
            "img3.png": {"true": {2}, "pred": {2}},
        }
    }
    metrics = compute_metrics(results)
    assert metrics["mixed_model"]["glass"]["tp"] == 1
    assert metrics["mixed_model"]["glass"]["fp"] == 1
    assert metrics["mixed_model"]["metal"]["fn"] == 1
    assert metrics["mixed_model"]["metal"]["tp"] == 0
    assert metrics["mixed_model"]["paper"]["tp"] == 1


def test_load_dataset_missing_val_split_raises():
    import tempfile

    with tempfile.TemporaryDirectory() as tmpdir:
        dataset_path = pathlib.Path(tmpdir) / "nonexistent"
        with pytest.raises(FileNotFoundError, match="Validation images not found"):
            load_dataset(dataset_path)


def test_load_dataset_missing_labels_raises():
    import tempfile

    with tempfile.TemporaryDirectory() as tmpdir:
        dataset_path = pathlib.Path(tmpdir)
        img_dir = dataset_path / "images" / "val"
        img_dir.mkdir(parents=True)
        (img_dir / "test.jpg").touch()

        with pytest.raises(FileNotFoundError, match="Validation labels not found"):
            load_dataset(dataset_path)
