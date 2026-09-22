from __future__ import annotations

import sys
from contextlib import nullcontext
from pathlib import Path
from types import SimpleNamespace

import pytest

from src.exceptions import ConfigError
from src.pipeline.strategies import TrainConfig, YOLOStrategy
from src.cli.train import _apply_train_argument_overrides
from scripts.generate_docker import (
    _build_training_params,
    generate_docker_compose,
    generate_dockerfile,
    generate_entrypoint,
    generate_train_script,
)


def test_train_config_validation_preserves_error_order_and_device_rules():
    config = TrainConfig(
        epochs=0,
        batch_size=0,
        imgsz=0,
        lr0=0,
        weight_decay=-1,
        patience=0,
        workers=-1,
        seed=-1,
        device="0",
    )

    assert config.validate() == [
        "epochs must be >= 1, got 0",
        "batch_size must be >= 1, got 0",
        "imgsz must be >= 1, got 0",
        "lr0 must be > 0, got 0",
        "weight_decay must be >= 0, got -1",
        "patience must be >= 1, got 0",
        "workers must be >= 0, got -1",
        "seed must be >= 0, got -1",
    ]
    assert TrainConfig(device="0,1").validate() == []
    assert any("device" in error for error in TrainConfig(device="cuda:0").validate())
    assert any("device" in error for error in TrainConfig(device="gpu0").validate())


def test_train_config_yaml_merges_unknown_keys_into_extra(tmp_path):
    config_file = tmp_path / "train.yaml"
    config_file.write_text(
        "name: from-file\nepochs: 3\nextra:\n  optimizer: SGD\n  keep: declared\nkeep: top-level\n",
        encoding="utf-8",
    )

    config = TrainConfig.from_yaml(config_file)

    assert (config.name, config.epochs) == ("from-file", 3)
    assert config.extra == {"optimizer": "SGD", "keep": "top-level"}


def test_train_config_yaml_preserves_failure_types(tmp_path):
    with pytest.raises(ConfigError, match="Config file not found"):
        TrainConfig.from_yaml(tmp_path / "missing.yaml")

    invalid_yaml = tmp_path / "invalid.yaml"
    invalid_yaml.write_text("broken: [ : yaml }\n", encoding="utf-8")
    with pytest.raises(ConfigError, match="parse"):
        TrainConfig.from_yaml(invalid_yaml)

    scalar_yaml = tmp_path / "scalar.yaml"
    scalar_yaml.write_text("a scalar\n", encoding="utf-8")
    with pytest.raises(ValueError, match="YAML mapping"):
        TrainConfig.from_yaml(scalar_yaml)


def test_cli_values_override_only_values_that_were_provided():
    config = TrainConfig(name="from-yaml", epochs=10, dataset="yaml.yaml")
    args = SimpleNamespace(
        model=None,
        dataset="cli.yaml",
        epochs=25,
        batch_size=None,
        name=None,
        device="cpu",
        data_dir=None,
    )

    _apply_train_argument_overrides(args, config)

    assert config.dataset == "cli.yaml"
    assert config.epochs == 25
    assert config.name == "from-yaml"
    assert config.batch_size == TrainConfig().batch_size
    assert config.device == "cpu"


def test_yolo_strategy_preserves_supported_extra_arguments(monkeypatch, tmp_path):
    seen = {}

    class FakeYOLO:
        def __init__(self, model):
            assert model == "model.pt"

        def train(self, **kwargs):
            seen.update(kwargs)
            return SimpleNamespace(box=SimpleNamespace(map50=0.6, map=0.4))

    monkeypatch.setitem(sys.modules, "ultralytics", SimpleNamespace(YOLO=FakeYOLO))
    monkeypatch.setattr("src.pipeline.strategies.serialize_config", lambda *args: None)
    monkeypatch.setattr("src.pipeline.strategies.serialize_result", lambda *args: None)
    monkeypatch.setattr("src.pipeline.strategies.experiment_metadata", lambda **kwargs: {})
    config = TrainConfig(
        model="model.pt",
        project=str(tmp_path),
        name="sample",
        extra={"optimizer": "AdamW", "plots": False, "export": {"plots": True}, "augmentation": {"hsv_h": 0.02, "format": "bad"}},
    )

    result = YOLOStrategy().train(config)

    assert seen["optimizer"] == "AdamW"
    assert seen["hsv_h"] == 0.02
    assert seen["plots"] is False
    assert "format" not in seen
    assert seen["deterministic"] is False
    assert result.metrics == {"map50": 0.6, "map": 0.4}
    assert Path(result.best_path).name == "best.pt"
    assert Path(result.model_path).name == "last.pt"


def test_classifier_strategy_preserves_split_model_and_result_artifacts(monkeypatch, tmp_path):
    calls = {"datasets": [], "fit": None, "saved": None, "serialized": []}

    class FakeModel:
        def __init__(self, *args, **kwargs):
            pass

        def compile(self, **kwargs):
            calls["compile"] = kwargs

        def fit(self, train_data, **kwargs):
            calls["fit"] = (train_data, kwargs)
            return SimpleNamespace(history={"loss": [0.8], "accuracy": [0.9]})

        def save(self, model_path):
            calls["saved"] = model_path

    class FakeLayer:
        def __init__(self, *args, **kwargs):
            pass

        def __call__(self, value):
            return value

    class FakeBase:
        output = object()
        input = object()
        trainable = False

    fake_keras = SimpleNamespace(
        applications=SimpleNamespace(MobileNetV2=lambda **kwargs: FakeBase()),
        layers=SimpleNamespace(
            GlobalAveragePooling2D=FakeLayer,
            Dropout=FakeLayer,
            Dense=FakeLayer,
        ),
        Model=FakeModel,
        optimizers=SimpleNamespace(Adam=lambda **kwargs: kwargs),
    )

    def image_dataset_from_directory(path, **kwargs):
        calls["datasets"].append((path, kwargs))
        return SimpleNamespace(class_names=["glass", "plastic"])

    fake_tensorflow = SimpleNamespace(
        keras=SimpleNamespace(
            utils=SimpleNamespace(image_dataset_from_directory=image_dataset_from_directory),
        ),
        distribute=SimpleNamespace(
            MirroredStrategy=lambda: SimpleNamespace(scope=nullcontext),
            OneDeviceStrategy=lambda device: SimpleNamespace(scope=nullcontext),
        ),
        config=SimpleNamespace(list_physical_devices=lambda device: []),
    )
    fake_tensorflow.keras = SimpleNamespace(**vars(fake_keras), utils=fake_tensorflow.keras.utils)
    monkeypatch.setitem(sys.modules, "tensorflow", fake_tensorflow)
    monkeypatch.setattr("src.pipeline.strategies.MODELS_DIR", tmp_path / "models")
    monkeypatch.setattr("src.pipeline.strategies.serialize_config", lambda *args: calls["serialized"].append(args))
    monkeypatch.setattr("src.pipeline.strategies.serialize_result", lambda *args: calls["serialized"].append(args))
    monkeypatch.setattr("src.pipeline.strategies.experiment_metadata", lambda **kwargs: {"command": kwargs["command"]})
    config = TrainConfig(name="classifier", data_dir=str(tmp_path), project=str(tmp_path), epochs=2, imgsz=224)
    config.extra.update({"base_model": "mobilenetv2", "fine_tune": True})

    from src.pipeline.strategies import ClassifierStrategy

    result = ClassifierStrategy().train(config)

    assert [dataset_args[1]["subset"] for dataset_args in calls["datasets"]] == ["training", "validation"]
    assert all(dataset_args[1]["validation_split"] == 0.2 for dataset_args in calls["datasets"])
    assert result.metrics == {"loss": 0.8, "accuracy": 0.9}
    assert result.model_path == calls["saved"]
    assert Path(result.model_path).name == "classifier.keras"
    assert len(calls["serialized"]) == 3


def test_docker_parameter_defaults_and_generated_output_contracts():
    params = _build_training_params({}, {})
    assert params["model"] == "yolo11n.pt"
    assert params["epochs"] == 120
    assert params["class_names"] == ["glass", "metal", "paper", "plastic", "trash"]
    assert "FROM ultralytics/ultralytics:latest" in generate_dockerfile(params)
    compose = generate_docker_compose()
    assert "../datasets:/data/dataset" in compose
    assert "runtime: nvidia" in compose

    exp = {"name": "contract", "export": {"formats": []}}
    params.update({"augmentation": {"mosaic": 0.5}, "num_classes": 5, "class_names": ["glass"]})
    entrypoint = generate_entrypoint(params, exp)
    assert 'DATASET_DIR="/data/dataset"' in entrypoint
    assert "yolo detect train" in entrypoint
    assert "mosaic=0.5" in entrypoint
    assert "Exporting to TFLite INT8" not in entrypoint
    train_script = generate_train_script(params, exp)
    assert 'DATASET = Path(\'/tmp/dataset.yaml\')' in train_script
    assert "model.val()" in train_script
    assert "model.export(" not in train_script


def test_generate_docker_keeps_empty_augmentation_output(monkeypatch):
    params = _build_training_params({}, {})
    params["augmentation"] = {}
    script = generate_train_script(params, {"name": "empty_aug", "export": {"formats": []}})
    assert "        ,\n" in script
