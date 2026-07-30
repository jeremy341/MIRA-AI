"""Tests for MIRA training strategies and configuration."""

from __future__ import annotations

import tempfile
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

from src.exceptions import ConfigError
from src.pipeline.strategies import (
    TrainConfig,
    TrainResult,
    YOLOStrategy,
    ClassifierStrategy,
    get_strategy,
    list_strategies,
    register_strategy,
)


# ── TrainConfig tests ────────────────────────────────────────────────


def test_train_config_defaults():
    cfg = TrainConfig()
    assert cfg.name == "exp"
    assert cfg.epochs >= 1
    assert cfg.batch_size >= 1
    assert cfg.imgsz >= 1


def test_train_config_validation_positive():
    cfg = TrainConfig(epochs=10, batch_size=8, imgsz=320, lr0=0.001)
    errors = cfg.validate()
    assert errors == []


def test_train_config_validation_negative_epochs():
    cfg = TrainConfig(epochs=-1)
    errors = cfg.validate()
    assert any("epochs" in e for e in errors)


def test_train_config_validation_zero_batch():
    cfg = TrainConfig(batch_size=0)
    errors = cfg.validate()
    assert any("batch_size" in e for e in errors)


def test_train_config_validation_negative_lr():
    cfg = TrainConfig(lr0=-0.01)
    errors = cfg.validate()
    assert any("lr0" in e for e in errors)


def test_train_config_validation_invalid_device():
    cfg = TrainConfig(device="invalid")
    errors = cfg.validate()
    assert any("device" in e for e in errors)


def test_train_config_from_yaml_valid():
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        import yaml

        yaml.dump({"name": "test", "epochs": 50, "batch_size": 16}, f)
        f.flush()
        cfg = TrainConfig.from_yaml(f.name)
        assert cfg.name == "test"
        assert cfg.epochs == 50
        assert cfg.batch_size == 16
    Path(f.name).unlink()


def test_train_config_from_yaml_invalid():
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        import yaml

        yaml.dump({"epochs": -5}, f)
        f.flush()
        with pytest.raises(ConfigError):
            TrainConfig.from_yaml(f.name)
    Path(f.name).unlink()


def test_train_config_from_yaml_non_dict():
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        f.write("just a string\n")
        f.flush()
        with pytest.raises(ValueError):
            TrainConfig.from_yaml(f.name)
    Path(f.name).unlink()


def test_yolo_train_only_flattens_supported_training_groups(tmp_path, monkeypatch):
    config_path = tmp_path / "experiment.yaml"
    config_path.write_text(
        """
model: test.pt
dataset: data.yaml
project: runs
optimizer: AdamW
augmentation:
  hsv_h: 0.02
export:
  plots: false
  format: onnx
""",
        encoding="utf-8",
    )
    config = TrainConfig.from_yaml(config_path)
    train_kwargs = {}

    class FakeYOLO:
        def __init__(self, model):
            assert model == "test.pt"

        def train(self, **kwargs):
            train_kwargs.update(kwargs)
            return SimpleNamespace()

    monkeypatch.setitem(sys.modules, "ultralytics", SimpleNamespace(YOLO=FakeYOLO))
    monkeypatch.setattr("src.pipeline.strategies.serialize_config", lambda *args: None)
    monkeypatch.setattr("src.pipeline.strategies.serialize_result", lambda *args: None)

    YOLOStrategy().train(config)

    assert train_kwargs["optimizer"] == "AdamW"
    assert train_kwargs["hsv_h"] == 0.02
    assert "plots" not in train_kwargs
    assert "format" not in train_kwargs


# ── TrainResult tests ────────────────────────────────────────────────


def test_train_result_creation():
    result = TrainResult(
        name="test_exp",
        model_path="/fake/model.pt",
        best_path="/fake/best.pt",
        epochs=10,
        metrics={"map50": 0.5},
        duration_seconds=100.0,
    )
    assert result.name == "test_exp"
    assert result.metrics["map50"] == 0.5


# ── Strategy registry tests ──────────────────────────────────────────


def test_get_strategy_detection():
    strategy = get_strategy("detection")
    assert isinstance(strategy, YOLOStrategy)


def test_get_strategy_classifier():
    strategy = get_strategy("classifier")
    assert isinstance(strategy, ClassifierStrategy)


def test_get_strategy_unknown():
    with pytest.raises(KeyError):
        get_strategy("nonexistent")


def test_list_strategies():
    strategies = list_strategies()
    assert "detection" in strategies
    assert "classifier" in strategies


def test_register_strategy_custom():
    from src.pipeline.strategies import _STRATEGIES

    class DummyStrategy(YOLOStrategy):
        pass

    register_strategy("dummy", DummyStrategy)
    strategy = get_strategy("dummy")
    assert isinstance(strategy, DummyStrategy)
    _STRATEGIES.pop("dummy", None)
