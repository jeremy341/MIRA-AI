import json
from pathlib import Path

import numpy as np
import pytest
from PIL import Image

from scripts import evaluate
from src.config import CLASS_NAMES
from src.pipeline.benchmark import (
    BenchmarkResult,
    ModelBenchmark,
    PerClassMetrics,
    compute_iou,
    compute_map,
    load_yolo_dataset,
    match_predictions,
)
from src.pipeline.models import Detection


def detection(class_id, box, confidence=0.9):
    return Detection(class_id, f"class_{class_id}", confidence, tuple(box))


def test_matching_keeps_confidence_order_and_inclusive_iou_boundary():
    truths = [detection(0, [0, 0, 8, 10]), detection(0, [2, 0, 10, 10])]
    high_confidence = detection(0, [0, 0, 10, 10], 0.95)
    low_confidence = detection(0, [2, 0, 10, 10], 0.8)

    result = match_predictions([low_confidence, high_confidence], truths, 0.7)

    assert result.true_positives == 1
    assert result.false_positives == 1
    assert result.false_negatives == 1


def test_matching_accepts_iou_equal_to_threshold():
    prediction = detection(0, [0, 0, 10, 10])
    truth = detection(0, [0, 0, 6, 10])

    result = match_predictions([prediction], [truth], 0.6)

    assert (result.true_positives, result.false_positives, result.false_negatives) == (1, 0, 0)


def test_iou_returns_zero_for_zero_area_and_touches():
    assert compute_iou([0, 0, 0, 0], [0, 0, 1, 1]) == 0
    assert compute_iou([0, 0, 1, 1], [1, 0, 2, 1]) == 0


def test_map_uses_bbox_pixel_key_and_excludes_classes_without_ground_truth():
    predictions = [[
        {"class_id": 0, "confidence": 0.9, "bbox_pixel": [0, 0, 10, 10]},
        {"class_id": 1, "confidence": 1.0, "bbox_pixel": [20, 20, 30, 30]},
    ]]
    ground_truth = [[{"class_id": 0, "bbox": [0, 0, 10, 10]}]]

    assert compute_map(predictions, ground_truth) == pytest.approx(1.0)
    assert compute_map([[]], [[]]) == 0.0


def test_benchmark_json_keys_and_comparison_sorting_are_stable():
    result = BenchmarkResult(
        model_name="model",
        model_path="model.pt",
        model_type=".pt",
        per_class={"glass": PerClassMetrics(tp=1)},
    )

    assert list(result.to_dict()) == [
        "model_name", "model_path", "model_type", "total_images", "per_class",
        "overall_f1", "overall_precision", "overall_recall", "avg_latency_ms",
        "total_detections", "map50", "map50_95", "errors", "evaluated_on_train",
    ]
    table = ModelBenchmark.comparison_table([
        BenchmarkResult("low", "low.pt", ".pt", overall_f1=0.2),
        BenchmarkResult("high", "high.pt", ".pt", overall_f1=0.9),
    ])
    assert table.index("high") < table.index("low")


class PredictionModel:
    def __init__(self, detections):
        self.detections = detections
        self.calls = []
        self.name = "mira"

    def predict(self, image_path, conf, iou):
        self.calls.append((image_path, conf, iou))
        return type("Prediction", (), {"detections": self.detections})()


def test_confusion_matrix_uses_gt_rows_prediction_columns_and_background():
    valid_class = min(1, len(CLASS_NAMES) - 1)
    model = PredictionModel([detection(valid_class, [0, 0, 10, 10])])
    samples = [(Path("image.jpg"), [
        {"class_id": 0, "bbox": [0, 0, 10, 10]},
        {"class_id": 0, "bbox": [20, 20, 30, 30]},
    ])]

    matrix = evaluate.build_confusion_matrix(model, samples, 0.25)
    background = len(CLASS_NAMES)

    assert matrix.shape == (background + 1, background + 1)
    assert matrix[0, valid_class] == 1
    assert matrix[0, background] == 1
    assert model.calls == [("image.jpg", 0.25, 0.5)]


def test_per_class_ap_ignores_conf_threshold_and_counts_wrong_confidence_detections():
    model = PredictionModel([detection(0, [0, 0, 10, 10], 0.01)])
    samples = [(Path("image.jpg"), [{"class_id": 0, "bbox": [0, 0, 10, 10]}])]

    precision, recall, ap = evaluate.compute_per_class_ap(model, samples, 0.99, 0)

    assert precision.tolist() == [1.0, 1.0]
    assert recall.tolist() == [0.0, 1.0]
    assert ap == pytest.approx(1.0)
    assert model.calls == [("image.jpg", 0.0, 0.5)]


def test_dataset_loader_keeps_polygon_boxes_and_falls_back_to_train(tmp_path):
    dataset_root = tmp_path / "dataset"
    image_dir = dataset_root / "images" / "train"
    label_dir = dataset_root / "labels" / "train"
    image_dir.mkdir(parents=True)
    label_dir.mkdir(parents=True)
    image_path = image_dir / "sample.png"
    Image.new("RGB", (100, 50)).save(image_path)
    (label_dir / "sample.txt").write_text("1 0.1 0.2 0.5 0.2 0.4 0.8\n", encoding="utf-8")

    samples, evaluated_on_train = load_yolo_dataset(dataset_root)

    assert evaluated_on_train is True
    assert samples == [(image_path, [{"class_id": 1, "bbox": [10.0, 10.0, 50.0, 40.0]}])]


def test_benchmark_preserves_threshold_latency_and_failure_accounting(monkeypatch):
    class Model:
        name = "mira"
        path = Path("mira.pt")
        model_type = "test"

        def __init__(self):
            self.calls = []

        def predict(self, image_path, conf, iou):
            self.calls.append((image_path, conf, iou))
            if image_path == "bad.jpg":
                raise RuntimeError("broken image")
            return type("Prediction", (), {"detections": [detection(0, [0, 0, 10, 10], 0.2)]})()

    model = Model()
    benchmark = ModelBenchmark(models=[model], conf=0.5)
    benchmark.samples = [
        (Path("good.jpg"), [{"class_id": 0, "bbox": [0, 0, 10, 10]}]),
        (Path("bad.jpg"), [{"class_id": 0, "bbox": [0, 0, 10, 10]}]),
    ]
    clock = iter([5.0, 5.002, 6.0])
    monkeypatch.setattr("src.pipeline.benchmark.time.perf_counter", lambda: next(clock))

    result = benchmark.run()[0]

    assert model.calls == [("good.jpg", 0.0, 0.7), ("bad.jpg", 0.0, 0.7)]
    assert result.total_images == 2
    assert result.total_detections == 0
    assert result.overall_recall == 0.0
    assert result.map50 == pytest.approx(51 / 101)
    assert result.avg_latency_ms == pytest.approx(2.0)
    assert result.errors == ["bad.jpg: broken image"]
    assert result.per_class[CLASS_NAMES[0]].fn == 1


def test_main_writes_summary_json_table_and_plot_files(tmp_path, monkeypatch, capsys):
    model_path = tmp_path / "mira.pt"
    model_path.write_bytes(b"model")
    output_dir = tmp_path / "output"
    model = PredictionModel([])
    result = BenchmarkResult("mira", str(model_path), ".pt", total_images=1)

    class Registry:
        def discover(self):
            return None

        def load_model(self, name):
            return model

    class Benchmark:
        def __init__(self, **kwargs):
            self.samples = []
            self.evaluated_on_train = False

        def run(self):
            return [result]

        @staticmethod
        def comparison_table(results):
            return "comparison"

    samples = [(Path("image.jpg"), [])]
    monkeypatch.setattr(evaluate, "parse_args", lambda: type("Args", (), {
        "model": "mira.pt", "data": "dataset.yaml", "conf": 0.25, "output": str(output_dir),
    })())
    monkeypatch.setattr(evaluate, "DETECTION_DIR", tmp_path)
    monkeypatch.setattr(evaluate, "ROOT_DIR", tmp_path)
    monkeypatch.setattr(evaluate, "resolve_safe_path", lambda path, root: model_path)
    monkeypatch.setattr(evaluate, "ModelRegistry", Registry)
    monkeypatch.setattr(evaluate, "ModelBenchmark", Benchmark)
    monkeypatch.setattr(evaluate, "load_yolo_dataset", lambda path: (samples, False))
    monkeypatch.setattr(evaluate, "build_confusion_matrix", lambda *args: np.zeros((2, 2), dtype=int))
    monkeypatch.setattr(evaluate, "plot_confusion_matrix", lambda matrix, target: (target / "confusion_matrix.png").write_bytes(b"x"))
    monkeypatch.setattr(evaluate, "plot_pr_curves", lambda model, samples, conf, target: (
        (target / "pr_curves.png").write_bytes(b"x"), {"paper": 0.5}
    )[1])
    monkeypatch.setattr(evaluate, "plot_class_metrics", lambda *args: (output_dir / "class_metrics.png").write_bytes(b"x"))
    monkeypatch.setattr(evaluate, "_validate_dataset_path", lambda path: None)

    evaluate.main()

    exported = json.loads((output_dir / "metrics.json").read_text(encoding="utf-8"))
    assert exported["eval_args"] == {"conf": 0.25, "data": str(tmp_path / "dataset.yaml"), "model": "mira.pt"}
    assert exported["per_class_ap"] == {"paper": 0.5}
    assert exported["confusion_matrix"] == [[0, 0], [0, 0]]
    assert (output_dir / "comparison_table.txt").read_text(encoding="utf-8") == "comparison"
    assert (output_dir / "confusion_matrix.png").exists()
    assert (output_dir / "pr_curves.png").exists()
    assert (output_dir / "class_metrics.png").exists()
    assert "mAP50-95" in capsys.readouterr().out
