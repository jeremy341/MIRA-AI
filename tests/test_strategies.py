"""Tests for MIRA training strategy registry and configs."""

import sys
import pathlib
from dataclasses import fields as dc_fields
from unittest.mock import patch

import pytest
import yaml

_project_root = str(pathlib.Path(__file__).resolve().parent.parent)
_src_dir = str(pathlib.Path(__file__).resolve().parent.parent / "src")
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)
if _src_dir not in sys.path:
    sys.path.insert(0, _src_dir)


# ── TrainConfig defaults ─────────────────────────────────────────────


def test_train_config_defaults():
    from src.pipeline.strategies import TrainConfig

    cfg = TrainConfig()
    assert cfg.name == "exp"
    assert cfg.model.endswith(".pt")
    assert cfg.epochs >= 1
    assert cfg.batch_size >= 1
    assert cfg.imgsz >= 32
    assert cfg.patience >= 1
    assert cfg.amp is True
    assert cfg.seed == 42
    assert cfg.extra == {}


def test_train_config_custom_values():
    from src.pipeline.strategies import TrainConfig

    cfg = TrainConfig(name="my_exp", epochs=50, batch_size=8, imgsz=320)
    assert cfg.name == "my_exp"
    assert cfg.epochs == 50
    assert cfg.batch_size == 8
    assert cfg.imgsz == 320


# ── TrainConfig.from_yaml ────────────────────────────────────────────


def test_train_config_from_yaml(tmp_path):
    from src.pipeline.strategies import TrainConfig

    cfg_file = tmp_path / "train.yaml"
    cfg_file.write_text(yaml.dump({
        "name": "yaml_exp",
        "model": "yolov8s.pt",
        "epochs": 30,
        "batch_size": 16,
        "imgsz": 480,
        "patience": 10,
    }))

    cfg = TrainConfig.from_yaml(str(cfg_file))
    assert cfg.name == "yaml_exp"
    assert cfg.model == "yolov8s.pt"
    assert cfg.epochs == 30
    assert cfg.batch_size == 16
    assert cfg.imgsz == 480
    assert cfg.patience == 10


def test_train_config_from_yaml_extra_fields(tmp_path):
    from src.pipeline.strategies import TrainConfig

    cfg_file = tmp_path / "train.yaml"
    cfg_file.write_text(yaml.dump({
        "name": "with_extra",
        "unknown_key": "hello",
        "another": 42,
    }))

    cfg = TrainConfig.from_yaml(str(cfg_file))
    assert cfg.name == "with_extra"
    assert cfg.extra.get("unknown_key") == "hello"
    assert cfg.extra.get("another") == 42


def test_train_config_from_yaml_non_dict_raises(tmp_path):
    from src.pipeline.strategies import TrainConfig

    cfg_file = tmp_path / "bad.yaml"
    cfg_file.write_text(yaml.dump(["not", "a", "dict"]))

    with pytest.raises(ValueError, match="must contain a YAML mapping"):
        TrainConfig.from_yaml(str(cfg_file))


# ── TrainResult ──────────────────────────────────────────────────────


def test_train_result_dataclass():
    from src.pipeline.strategies import TrainResult

    r = TrainResult(
        name="exp01",
        model_path="/models/exp01/last.pt",
        best_path="/models/exp01/best.pt",
        epochs=50,
        metrics={"map50": 0.85},
        duration_seconds=120.5,
    )
    assert r.name == "exp01"
    assert r.epochs == 50
    assert r.metrics["map50"] == 0.85
    assert r.exported == []


def test_train_result_with_exported():
    from src.pipeline.strategies import TrainResult

    r = TrainResult(
        name="exp02",
        model_path="/m.pt",
        best_path="/b.pt",
        epochs=10,
        metrics={},
        duration_seconds=1.0,
        exported=["model.onnx", "model.tflite"],
    )
    assert len(r.exported) == 2


# ── Strategy constructors ────────────────────────────────────────────


def test_yolo_strategy_constructor():
    from src.pipeline.strategies import YOLOStrategy

    s = YOLOStrategy()
    assert hasattr(s, "train")
    assert callable(s.train)


def test_classifier_strategy_constructor():
    from src.pipeline.strategies import ClassifierStrategy

    s = ClassifierStrategy()
    assert hasattr(s, "train")
    assert callable(s.train)


# ── Strategy registry ────────────────────────────────────────────────


@pytest.fixture
def _clean_strategy_registry():
    """Save and restore the global strategy registry."""
    import src.pipeline.strategies as mod

    saved = dict(mod._STRATEGIES)
    mod._STRATEGIES.clear()
    yield
    mod._STRATEGIES.clear()
    mod._STRATEGIES.update(saved)


def test_register_and_get_strategy(_clean_strategy_registry):
    from src.pipeline.strategies import (
        YOLOStrategy,
        register_strategy,
        get_strategy,
    )

    register_strategy("my_det", YOLOStrategy)
    s = get_strategy("my_det")
    assert isinstance(s, YOLOStrategy)


def test_get_strategy_unknown_raises(_clean_strategy_registry):
    from src.pipeline.strategies import get_strategy

    with pytest.raises(KeyError, match="Unknown training strategy"):
        get_strategy("nonexistent_strategy")


def test_register_duplicate_name_overwrites(_clean_strategy_registry):
    from src.pipeline.strategies import (
        YOLOStrategy,
        ClassifierStrategy,
        register_strategy,
        get_strategy,
    )

    register_strategy("dup_test", YOLOStrategy)
    register_strategy("dup_test", ClassifierStrategy)
    s = get_strategy("dup_test")
    assert isinstance(s, ClassifierStrategy)


def test_list_strategies(_clean_strategy_registry):
    from src.pipeline.strategies import (
        YOLOStrategy,
        ClassifierStrategy,
        register_strategy,
        list_strategies,
    )

    register_strategy("list_a", YOLOStrategy)
    register_strategy("list_b", ClassifierStrategy)
    names = list_strategies()
    assert "list_a" in names
    assert "list_b" in names
    assert len(names) == 2


def test_registry_isolated_between_tests(_clean_strategy_registry):
    from src.pipeline.strategies import _STRATEGIES

    assert len(_STRATEGIES) == 0
