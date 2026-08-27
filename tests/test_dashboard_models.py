"""Tests for MIRA dashboard backend models."""

from datetime import datetime

import pytest
from pydantic import ValidationError

from src.dashboard.backend.models import (
    CameraConfig,
    Detection,
    ModelConfig,
    Statistics,
    SystemMetrics,
    SystemStatus,
    WasteClass,
)


class TestWasteClass:
    def test_all_values(self):
        assert WasteClass.GLASS == "glass"
        assert WasteClass.METAL == "metal"
        assert WasteClass.PAPER == "paper"
        assert WasteClass.PLASTIC == "plastic"
        assert WasteClass.TRASH == "trash"

    def test_has_five_classes(self):
        assert len(WasteClass) == 5

    def test_is_str_enum(self):
        for wc in WasteClass:
            assert isinstance(wc, str)


class TestDetection:
    def test_valid_detection(self):
        det = Detection(class_name=WasteClass.GLASS, confidence=0.95, bbox=[10, 20, 100, 200])
        assert det.class_name == WasteClass.GLASS
        assert det.confidence == 0.95
        assert det.bbox == [10, 20, 100, 200]
        assert det.track_id is None
        assert isinstance(det.timestamp, datetime)

    def test_with_track_id(self):
        det = Detection(class_name=WasteClass.METAL, confidence=0.8, bbox=[0, 0, 50, 50], track_id=42)
        assert det.track_id == 42

    def test_confidence_boundary_zero(self):
        det = Detection(class_name=WasteClass.PAPER, confidence=0.0, bbox=[0, 0, 1, 1])
        assert det.confidence == 0.0

    def test_confidence_boundary_one(self):
        det = Detection(class_name=WasteClass.PLASTIC, confidence=1.0, bbox=[0, 0, 1, 1])
        assert det.confidence == 1.0

    def test_confidence_below_zero_rejected(self):
        with pytest.raises(ValidationError):
            Detection(class_name=WasteClass.TRASH, confidence=-0.1, bbox=[0, 0, 1, 1])

    def test_confidence_above_one_rejected(self):
        with pytest.raises(ValidationError):
            Detection(class_name=WasteClass.GLASS, confidence=1.1, bbox=[0, 0, 1, 1])

    def test_default_timestamp(self):
        before = datetime.now()
        det = Detection(class_name=WasteClass.GLASS, confidence=0.5, bbox=[0, 0, 10, 10])
        after = datetime.now()
        assert before <= det.timestamp <= after


class TestCameraConfig:
    def test_defaults(self):
        cfg = CameraConfig()
        assert cfg.index == 0
        assert cfg.width == 640
        assert cfg.height == 360
        assert cfg.fps == 30
        assert cfg.autofocus is False
        assert cfg.auto_exposure is True

    def test_custom_values(self):
        cfg = CameraConfig(index=1, width=1280, height=720, fps=60, autofocus=True)
        assert cfg.index == 1
        assert cfg.width == 1280
        assert cfg.height == 720
        assert cfg.fps == 60
        assert cfg.autofocus is True

    def test_model_dump(self):
        cfg = CameraConfig(index=2)
        d = cfg.model_dump()
        assert d["index"] == 2
        assert "width" in d
        assert "height" in d


class TestModelConfig:
    def test_defaults(self):
        cfg = ModelConfig(name="test.pt")
        assert cfg.name == "test.pt"
        assert cfg.conf_threshold == 0.25
        assert cfg.reject_threshold == 0.25
        assert cfg.iou_threshold == 0.45
        assert cfg.enable_tracking is True
        assert cfg.target_latency_ms == 1000

    def test_custom_values(self):
        cfg = ModelConfig(name="model.tflite", conf_threshold=0.25, enable_tracking=False)
        assert cfg.conf_threshold == 0.25
        assert cfg.enable_tracking is False

    def test_name_required(self):
        with pytest.raises(ValidationError):
            ModelConfig()


class TestSystemMetrics:
    def test_valid_metrics(self):
        m = SystemMetrics(
            fps=30.0,
            inference_latency_ms=15.0,
            avg_latency_ms=20.0,
            cpu_percent=45.0,
            memory_percent=60.0,
            detections_per_second=5.0,
            skip_frames=False,
        )
        assert m.fps == 30.0
        assert m.temperature_celsius is None
        assert isinstance(m.timestamp, datetime)

    def test_with_temperature(self):
        m = SystemMetrics(
            fps=30.0,
            inference_latency_ms=15.0,
            avg_latency_ms=20.0,
            cpu_percent=45.0,
            memory_percent=60.0,
            detections_per_second=5.0,
            skip_frames=False,
            temperature_celsius=55.5,
        )
        assert m.temperature_celsius == 55.5


class TestStatistics:
    def test_valid_statistics(self):
        now = datetime.now()
        s = Statistics(
            period_start=now,
            period_end=now,
            total_detections=10,
            class_counts={WasteClass.GLASS: 3, WasteClass.PLASTIC: 7},
            avg_confidence={WasteClass.GLASS: 0.85, WasteClass.PLASTIC: 0.92},
        )
        assert s.total_detections == 10
        assert s.sorting_accuracy is None

    def test_with_sorting_accuracy(self):
        now = datetime.now()
        s = Statistics(
            period_start=now,
            period_end=now,
            total_detections=5,
            class_counts={WasteClass.METAL: 5},
            avg_confidence={WasteClass.METAL: 0.78},
            sorting_accuracy=0.95,
        )
        assert s.sorting_accuracy == 0.95


class TestSystemStatus:
    def test_all_values(self):
        assert SystemStatus.IDLE == "idle"
        assert SystemStatus.INITIALIZING == "initializing"
        assert SystemStatus.RUNNING == "running"
        assert SystemStatus.PAUSED == "paused"
        assert SystemStatus.ERROR == "error"

    def test_has_five_states(self):
        assert len(SystemStatus) == 5
