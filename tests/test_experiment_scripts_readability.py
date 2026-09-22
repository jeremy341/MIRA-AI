import json
import random
import sys
import types
from collections import Counter
from pathlib import Path as RealPath
from types import SimpleNamespace

import numpy as np
import pytest

from scripts import capture_classifier_frames, compare, profile, run_exp020, train_detector_kaggle
from scripts.build_balanced_dataset import Record
from src.pipeline.benchmark import BenchmarkResult, PerClassMetrics


def make_record(source: str, source_id: str, folder: RealPath, image_bytes: bytes = b"image") -> Record:
    image = folder / f"{source_id}.jpg"
    image.parent.mkdir(parents=True, exist_ok=True)
    image.write_bytes(image_bytes)
    labels = ("0 0.500000 0.500000 0.200000 0.200000",)
    return Record(source, "train", source_id, image, labels)


def test_exp020_selection_uses_seeded_source_quota_order(tmp_path):
    records_by_source = {
        "roboflow": [make_record("roboflow", str(i), tmp_path / "roboflow") for i in range(14)],
        "taco": [make_record("taco", str(i), tmp_path / "taco") for i in range(4)],
        "dmedhi": [make_record("dmedhi", "one", tmp_path / "dmedhi")],
        "trashnet": [make_record("trashnet", "one", tmp_path / "trashnet")],
    }
    records = [record for source_records in records_by_source.values() for record in source_records]
    expected_rng = random.Random(2026)
    expected_by_source = {source: list(items) for source, items in records_by_source.items()}
    for items in expected_by_source.values():
        expected_rng.shuffle(items)
    expected = [
        *expected_by_source["roboflow"],
        *expected_by_source["taco"],
        *expected_by_source["dmedhi"],
        *expected_by_source["trashnet"],
    ]
    selected = run_exp020.choose_records(records, total=20)
    assert selected == expected
    assert Counter(record.source for record in selected) == {
        "roboflow": 14,
        "taco": 4,
        "dmedhi": 1,
        "trashnet": 1,
    }


def test_exp020_selection_fallback_warns_and_fills_remaining_slots(tmp_path, capsys):
    records = [make_record("roboflow", str(i), tmp_path / "roboflow") for i in range(20)]
    with pytest.warns(UserWarning, match="fallback activated"):
        selected = run_exp020.choose_records(records, total=20)
    assert len(selected) == 20
    assert {record.source for record in selected} == {"roboflow"}
    assert "fallback activated" in capsys.readouterr().err


def test_exp020_writer_preserves_eval_split_priority_and_output_files(tmp_path, capsys):
    output = tmp_path / "dataset"
    output.mkdir()
    (output / "old.txt").write_text("old", encoding="utf-8")
    val_record = make_record("trashnet", "same", tmp_path / "val", b"duplicate")
    train_record = make_record("roboflow", "same", tmp_path / "train", b"duplicate")
    test_record = make_record("taco", "unique", tmp_path / "test", b"unique")
    with pytest.raises(FileExistsError, match="Use --force"):
        run_exp020.write_dataset({"train": [train_record]}, output, force=False)
    source_counts = run_exp020.write_dataset(
        {"train": [train_record], "val": [val_record], "test": [test_record]}, output, force=True
    )
    manifest = [
        json.loads(line)
        for line in (output / "manifest.jsonl").read_text(encoding="utf-8").splitlines()
    ]
    assert [item["split"] for item in manifest] == ["val", "test"]
    assert manifest[0]["source"] == "trashnet"
    assert not (output / "old.txt").exists()
    assert source_counts == {"train": Counter(), "val": Counter({"trashnet": 1}), "test": Counter({"taco": 1})}
    assert json.loads((output / "source_summary.json").read_text(encoding="utf-8")) == {
        "train": {},
        "val": {"trashnet": 1},
        "test": {"taco": 1},
    }
    assert (output / "dataset.yaml").read_text(encoding="utf-8") == (
        "train: images/train\nval: images/val\ntest: images/test\n"
        "nc: 5\nnames: ['glass', 'metal', 'paper', 'plastic', 'trash']\n"
    )
    assert "requested 1, dropped 1 duplicates" in capsys.readouterr().out


def test_profile_model_returns_existing_latency_metric_keys(monkeypatch, tmp_path):
    image = tmp_path / "frame.jpg"
    image.write_bytes(b"frame")

    class FakeRegistry:
        def discover(self):
            return 1

        def load_model(self, model_name):
            return SimpleNamespace(_imgsz=320)

    monkeypatch.setattr(profile, "ModelRegistry", FakeRegistry)
    measured = []

    def measure(model, image_path, imgsz, batch_size):
        measured.append((image_path, imgsz, batch_size))
        return 20.0

    monkeypatch.setattr(profile, "measure_inference", measure)
    monkeypatch.setattr(profile, "_CUDA_AVAILABLE", False)
    monkeypatch.setattr(profile, "_peak_gpu_memory_mb", lambda: None)
    monkeypatch.setattr(profile, "_peak_cpu_memory_mb", lambda: 12.5)
    results = profile.profile_model("detector.pt", image, iterations=3, warmup=2, batch_size=2)
    assert len(measured) == 5
    assert all(item == (image, 320, 2) for item in measured)
    assert results["model"] == "detector.pt"
    assert results["image"] == str(image)
    assert results["mean_latency_ms"] == 20.0
    assert results["throughput_fps"] == 100.0
    assert results["throughput_batch_fps"] == 100.0
    assert results["peak_cpu_memory_mb"] == 12.5
    assert results["peak_gpu_memory_mb"] is None
    assert set(results) == {
        "model", "image", "imgsz", "batch_size", "iterations", "warmup",
        "mean_latency_ms", "p50_latency_ms", "p90_latency_ms", "p99_latency_ms",
        "min_latency_ms", "max_latency_ms", "std_latency_ms", "throughput_fps",
        "throughput_batch_fps", "peak_gpu_memory_mb", "peak_cpu_memory_mb",
        "cuda_available", "timestamp",
    }


def test_exp020_training_keeps_model_settings_and_export_arguments(monkeypatch, tmp_path, capsys):
    calls = {}

    class FakeModel:
        def __init__(self, model_name):
            calls["model_name"] = model_name

        def train(self, **kwargs):
            calls["train"] = kwargs

        def val(self, **kwargs):
            calls["val"] = kwargs
            return SimpleNamespace(box=SimpleNamespace(map50=0.75, map=0.5))

        def export(self, **kwargs):
            calls.setdefault("exports", []).append(kwargs)

    torch = types.ModuleType("torch")
    torch.cuda = SimpleNamespace(is_available=lambda: True)
    ultralytics = types.ModuleType("ultralytics")
    ultralytics.YOLO = FakeModel
    monkeypatch.setitem(sys.modules, "torch", torch)
    monkeypatch.setitem(sys.modules, "ultralytics", ultralytics)
    args = SimpleNamespace(device="auto", epochs=8, batch=6, imgsz=384)
    data_yaml = tmp_path / "dataset.yaml"
    run_exp020.train(args, data_yaml)
    assert calls["model_name"] == "yolo11n.pt"
    assert calls["train"]["data"] == str(data_yaml)
    assert calls["train"]["epochs"] == 8
    assert calls["train"]["batch"] == 6
    assert calls["train"]["imgsz"] == 384
    assert calls["train"]["device"] == "0"
    assert calls["train"]["optimizer"] == "AdamW"
    assert calls["train"]["seed"] == 2026
    assert calls["val"] == {"data": str(data_yaml), "split": "val"}
    assert calls["exports"] == [
        {"format": "onnx", "imgsz": 384},
        {"format": "tflite", "int8": True, "imgsz": 384, "data": str(data_yaml)},
    ]
    assert "EXP020 val mAP50: 0.7500" in capsys.readouterr().out


def test_compare_tables_keep_f1_order_and_metric_formatting(tmp_path):
    small_model = tmp_path / "small.pt"
    large_model = tmp_path / "large.pt"
    small_model.write_bytes(b"x")
    large_model.write_bytes(b"x" * 1_048_576)
    results = [
        BenchmarkResult(
            model_name="Slow",
            model_path=str(large_model),
            model_type="yolo",
            overall_f1=0.5,
            overall_precision=0.6,
            overall_recall=0.4,
            avg_latency_ms=20.0,
            map50=0.55,
            map50_95=0.35,
        ),
        BenchmarkResult(
            model_name="Fast",
            model_path=str(small_model),
            model_type="yolo",
            overall_f1=0.8,
            overall_precision=0.9,
            overall_recall=0.7,
            avg_latency_ms=10.0,
            map50=0.85,
            map50_95=0.65,
            per_class={"glass": PerClassMetrics(tp=3, fp=1, fn=1)},
        ),
    ]
    comparison = compare.build_comparison(results)
    per_class = compare.build_per_class_table(results)
    assert comparison.index("Fast") < comparison.index("Slow")
    assert "| 0.0 | 10.0 | 100.0 | 90.0% | 70.0% | 80.0% | 85.0% | 65.0% |" in comparison
    assert "| Fast | 75.0% | 75.0% | 75.0% |" in per_class
    assert "| Slow | - | - | - |" in per_class


def test_kaggle_training_selects_matching_dataset_and_keeps_training_arguments(monkeypatch, tmp_path):
    input_dir = tmp_path / "input"
    matched = input_dir / "Mira-Requested-Data"
    fallback = input_dir / "other-data"
    for root in (matched, fallback):
        (root / "images" / "train").mkdir(parents=True)
        (root / "images" / "val").mkdir(parents=True)
    (matched / "images" / "train" / "one.jpg").write_bytes(b"image")
    (matched / "images" / "val" / "one.png").write_bytes(b"image")
    monkeypatch.setenv("KAGGLE_INPUT_PATH", str(input_dir))
    work_root = tmp_path / "working"
    work_root.mkdir()
    original_path = RealPath

    def mapped_path(value, *args, **kwargs):
        if str(value) == "/kaggle/working":
            return work_root
        return original_path(value, *args, **kwargs)

    monkeypatch.setattr(train_detector_kaggle, "Path", mapped_path)
    calls = {}

    class FakeModel:
        def __init__(self, model_name):
            calls["model_name"] = model_name

        def train(self, **kwargs):
            calls["train"] = kwargs

        def val(self):
            return SimpleNamespace(box=SimpleNamespace(map50=0.8, map=0.6))

        def export(self, **kwargs):
            calls.setdefault("exports", []).append(kwargs)

    ultralytics = types.ModuleType("ultralytics")
    ultralytics.YOLO = FakeModel
    monkeypatch.setitem(sys.modules, "ultralytics", ultralytics)
    monkeypatch.setattr(train_detector_kaggle.subprocess, "check_call", lambda command: calls.update(pip=command))
    monkeypatch.setattr(sys, "argv", [
        "train_detector_kaggle.py", "--dataset", "requested", "--model", "custom.pt",
        "--epochs", "9", "--batch-size", "4", "--img-size", "512", "--patience", "7", "--lr0", "0.02",
    ])
    train_detector_kaggle.main()
    assert calls["model_name"] == "custom.pt"
    assert calls["train"]["data"] == str(work_root / "dataset.yaml")
    assert calls["train"]["epochs"] == 9
    assert calls["train"]["batch"] == 4
    assert calls["train"]["imgsz"] == 512
    assert calls["train"]["patience"] == 7
    assert calls["train"]["lr0"] == 0.02
    assert calls["train"]["mixup"] == 0.1
    assert calls["exports"] == [{"format": "tflite", "int8": True, "imgsz": 512}, {"format": "onnx", "imgsz": 512}]
    assert (work_root / "dataset.yaml").read_text(encoding="utf-8") == (
        f"train: {matched}/images/train\nval: {matched}/images/val\nnc: 5\nnames: ['glass', 'metal', 'paper', 'plastic', 'trash']\n"
    )


def test_capture_loop_saves_selected_class_and_releases_camera(monkeypatch, tmp_path):
    frame = np.zeros((8, 8, 3), dtype=np.uint8)
    saved = []
    calls = {"read": 0, "destroy": 0, "release": 0}

    class FakeCamera:
        def isOpened(self):
            return True

        def read(self):
            calls["read"] += 1
            return True, frame

        def release(self):
            calls["release"] += 1

    monkeypatch.setattr(capture_classifier_frames, "DATA_DIR", tmp_path / "classes")
    monkeypatch.setattr(capture_classifier_frames, "setup_camera_properties", lambda *args: None)
    monkeypatch.setattr(capture_classifier_frames.cv2, "VideoCapture", lambda *args: FakeCamera())
    monkeypatch.setattr(capture_classifier_frames.cv2, "putText", lambda image, *args: image)
    monkeypatch.setattr(capture_classifier_frames.cv2, "imshow", lambda *args: None)
    keys = iter([ord("1"), ord("q")])
    monkeypatch.setattr(capture_classifier_frames.cv2, "waitKey", lambda delay: next(keys))
    monkeypatch.setattr(capture_classifier_frames.cv2, "imwrite", lambda path, image: saved.append((path, image)) or True)
    monkeypatch.setattr(capture_classifier_frames.cv2, "destroyAllWindows", lambda: calls.update(destroy=1))
    monkeypatch.setattr(sys, "argv", ["capture_classifier_frames.py"])
    capture_classifier_frames.main()
    assert calls["read"] == 12
    assert calls["release"] == 1
    assert calls["destroy"] == 1
    assert len(saved) == 1
    assert str(saved[0][0]).startswith(str(tmp_path / "classes" / "glass"))
    assert str(saved[0][0]).endswith(".jpg")
    assert saved[0][1] is frame
