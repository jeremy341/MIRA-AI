"""Tests for the shared model runner using a fake model (no weights, no GPU)."""

from __future__ import annotations

import numpy as np
import pytest

from src.dashboard.backend.v1 import model_runner


class _Boxes:
    def __init__(self):
        self.cls = [2, 4]
        self.conf = [0.9, 0.5]
        self.xyxy = [[1.2, 2.2, 10.4, 20.6], [5, 5, 8, 9]]
        self.id = None

    def __len__(self):
        return 2


class _Result:
    boxes = _Boxes()


class _FakeModel:
    def predict(self, frame, imgsz, conf, iou, verbose):
        return [_Result()]


@pytest.fixture
def fake_models(tmp_path, monkeypatch):
    (tmp_path / "demo.pt").write_bytes(b"x")
    monkeypatch.setattr(model_runner, "DETECTION_DIR", tmp_path)
    model_runner.set_model_factory(lambda path, task: _FakeModel())
    yield tmp_path
    model_runner.set_model_factory(None)


def test_list_and_resolve(fake_models):
    assert [m["name"] for m in model_runner.list_models()] == ["demo.pt"]
    assert model_runner.resolve_model_path("demo.pt").name == "demo.pt"
    for bad in ("../x.pt", "a/b.pt", "", "demo.txt"):
        with pytest.raises(ValueError):
            model_runner.resolve_model_path(bad)
    with pytest.raises(FileNotFoundError):
        model_runner.resolve_model_path("missing.pt")


def test_predict_frame_maps_results(fake_models):
    result = model_runner.predict_frame("demo.pt", np.zeros((32, 32, 3), dtype=np.uint8), confidence=0.25)
    assert [d.class_name for d in result.detections] == ["paper", "trash"]
    assert result.detections[0].bbox == (1, 2, 10, 21)
    assert result.latency_ms >= 0
