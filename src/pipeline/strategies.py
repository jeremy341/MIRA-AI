"""Training strategy registry for extensible training pipelines.

Allows registering new training strategies (YOLO, classifier, etc.)
without modifying the TrainingPipeline class.
"""

from __future__ import annotations

import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from ..config import PROJECT_CONFIG, ROOT_DIR, MODELS_DIR
from ..exceptions import ConfigError
from ..logger import get_logger
from ..serialization import serialize_result, serialize_config, experiment_metadata

logger = get_logger(__name__)


@dataclass
class TrainConfig:
    name: str = "exp"
    model: str = PROJECT_CONFIG.get("training", {}).get("default_model", "yolo11n.pt")
    dataset: str = ""
    data_dir: str = ""
    epochs: int = PROJECT_CONFIG.get("training", {}).get("default_epochs", 120)
    batch_size: int = PROJECT_CONFIG.get("training", {}).get("default_batch_size", 32)
    imgsz: int = PROJECT_CONFIG.get("training", {}).get("default_imgsz", 640)
    lr0: float = PROJECT_CONFIG.get("training", {}).get("default_lr", 0.01)
    lrf: float = 0.01
    momentum: float = 0.937
    weight_decay: float = 0.0005
    warmup_epochs: int = 3
    warmup_momentum: float = 0.8
    patience: int = PROJECT_CONFIG.get("training", {}).get("early_stopping_patience", 30)
    device: str = "0"
    workers: int = 4
    amp: bool = True
    seed: int = 42
    project: str = "runs"
    exist_ok: bool = True
    extra: dict[str, Any] = field(default_factory=dict)

    def validate(self) -> list[str]:
        """Validate this configuration and return a list of error messages."""
        errors: list[str] = []

        if self.epochs < 1:
            errors.append(f"epochs must be >= 1, got {self.epochs}")
        if self.batch_size < 1:
            errors.append(f"batch_size must be >= 1, got {self.batch_size}")
        if self.imgsz < 1:
            errors.append(f"imgsz must be >= 1, got {self.imgsz}")
        if self.lr0 <= 0:
            errors.append(f"lr0 must be > 0, got {self.lr0}")
        if self.weight_decay < 0:
            errors.append(f"weight_decay must be >= 0, got {self.weight_decay}")
        if self.patience < 1:
            errors.append(f"patience must be >= 1, got {self.patience}")
        if self.workers < 0:
            errors.append(f"workers must be >= 0, got {self.workers}")
        if self.seed < 0:
            errors.append(f"seed must be >= 0, got {self.seed}")

        # Device validation
        if self.device != "cpu" and not all(c.isdigit() or c in (",", ":") for c in self.device):
            errors.append(f"device must be 'cpu', comma-separated GPU IDs, or 'cuda:N', got '{self.device}'")

        return errors

    @classmethod
    def from_yaml(cls, path: str | Path) -> TrainConfig:
        import yaml
        from dataclasses import fields as dc_fields

        try:
            with open(path, encoding="utf-8") as f:
                data = yaml.safe_load(f)
        except FileNotFoundError:
            raise ConfigError(f"Config file not found: {path}")
        if not isinstance(data, dict):
            raise ValueError(f"Config file {path} must contain a YAML mapping, got {type(data).__name__}")

        known = {f.name for f in dc_fields(cls)}
        extra = {k: v for k, v in data.items() if k not in known}
        config = cls(**{k: v for k, v in data.items() if k in known}, extra=extra)

        errors = config.validate()
        if errors:
            raise ConfigError(
                f"Validation failed for '{path}' with {len(errors)} error(s):\n  - " + "\n  - ".join(errors)
            )

        return config


@dataclass
class TrainResult:
    name: str
    model_path: str
    best_path: str
    epochs: int
    metrics: dict[str, Any]
    duration_seconds: float
    exported: list[str] = field(default_factory=list)


class TrainingStrategy(ABC):
    """Abstract strategy for training a model type."""

    @abstractmethod
    def train(self, config: TrainConfig) -> TrainResult: ...


class YOLOStrategy(TrainingStrategy):
    """Train a YOLO detection model via Ultralytics."""

    def train(self, config: TrainConfig) -> TrainResult:
        from ultralytics import YOLO

        model = YOLO(config.model)
        kwargs = {
            "data": config.dataset,
            "epochs": config.epochs,
            "batch": config.batch_size,
            "imgsz": config.imgsz,
            "lr0": config.lr0,
            "lrf": config.lrf,
            "momentum": config.momentum,
            "weight_decay": config.weight_decay,
            "warmup_epochs": config.warmup_epochs,
            "warmup_momentum": config.warmup_momentum,
            "patience": config.patience,
            "device": config.device,
            "workers": config.workers,
            "amp": config.amp,
            "project": config.project,
            "name": config.name,
            "exist_ok": config.exist_ok,
            "seed": config.seed,
            "deterministic": False,
        }
        if config.extra:
            for key in list(config.extra.keys()):
                val = config.extra[key]
                if isinstance(val, dict):
                    for subkey, subval in val.items():
                        if subkey not in kwargs:
                            kwargs[subkey] = subval

            training_keys = {
                "data",
                "epochs",
                "batch",
                "imgsz",
                "lr0",
                "lrf",
                "momentum",
                "weight_decay",
                "warmup_epochs",
                "warmup_momentum",
                "patience",
                "device",
                "workers",
                "amp",
                "project",
                "name",
                "exist_ok",
                "seed",
                "deterministic",
                "optimizer",
                "cos_lr",
                "close_mosaic",
                "resume",
                "pretrained",
                "verbose",
                "val",
                "save",
                "save_period",
                "cache",
                "plots",
                "overlap_mask",
                "mask_ratio",
                "dropout",
                "single_cls",
                "nbs",
                "multi_scale",
                "hsv_h",
                "hsv_s",
                "hsv_v",
                "degrees",
                "translate",
                "scale",
                "shear",
                "perspective",
                "flipud",
                "fliplr",
                "mosaic",
                "mixup",
                "copy_paste",
                "erasing",
                "crop_fraction",
                "box",
                "cls",
                "dfl",
            }
            filtered = {k: v for k, v in config.extra.items() if k in training_keys}
            kwargs.update(filtered)

        t0 = time.time()
        results = model.train(**kwargs)
        elapsed = time.time() - t0

        best_path = str(Path(config.project) / config.name / "weights" / "best.pt")
        last_path = str(Path(config.project) / config.name / "weights" / "last.pt")

        metrics = {}
        if hasattr(results, "box"):
            metrics["map50"] = getattr(results.box, "map50", 0.0)
            metrics["map"] = getattr(results.box, "map", 0.0)

        train_result = TrainResult(
            name=config.name,
            model_path=last_path,
            best_path=best_path,
            epochs=config.epochs,
            metrics=metrics,
            duration_seconds=elapsed,
        )

        results_dir = Path(config.project) / config.name
        serialize_config(config, results_dir / "config.yaml")
        serialize_result(train_result, results_dir / "results.json")
        meta = experiment_metadata(
            command="train_yolo",
            args={"model": config.model, "dataset": config.dataset, "epochs": config.epochs},
        )
        serialize_result(meta, results_dir / "metadata.json")

        return train_result


class ClassifierStrategy(TrainingStrategy):
    """Train a TensorFlow/Keras classifier."""

    def train(self, config: TrainConfig) -> TrainResult:
        import tensorflow as tf
        from tensorflow import keras

        data_dir = Path(config.data_dir) if config.data_dir else ROOT_DIR / "data" / "classes"
        if not data_dir.exists():
            raise FileNotFoundError(f"Classifier data directory not found: {data_dir}")

        train_ds = tf.keras.utils.image_dataset_from_directory(
            str(data_dir),
            validation_split=0.2,
            subset="training",
            seed=config.seed,
            image_size=(config.imgsz, config.imgsz),
            batch_size=config.batch_size,
            label_mode="int",
        )
        val_ds = tf.keras.utils.image_dataset_from_directory(
            str(data_dir),
            validation_split=0.2,
            subset="validation",
            seed=config.seed,
            image_size=(config.imgsz, config.imgsz),
            batch_size=config.batch_size,
            label_mode="int",
        )
        class_names = train_ds.class_names
        num_classes = len(class_names)

        strategy = (
            tf.distribute.MirroredStrategy()
            if tf.config.list_physical_devices("GPU")
            else tf.distribute.OneDeviceStrategy("CPU")
        )

        base_model = config.extra.get("base_model", "mobilenetv2")
        fine_tune = config.extra.get("fine_tune", False)

        with strategy.scope():
            if base_model == "mobilenetv2":
                base = keras.applications.MobileNetV2(
                    input_shape=(config.imgsz, config.imgsz, 3),
                    include_top=False,
                    weights="imagenet",
                )
                base.trainable = not fine_tune
                x = keras.layers.GlobalAveragePooling2D()(base.output)
                x = keras.layers.Dropout(0.2)(x)
                out = keras.layers.Dense(num_classes, activation="softmax")(x)
                model = keras.Model(inputs=base.input, outputs=out)
            else:
                model = keras.Sequential(
                    [
                        keras.layers.Input(shape=(config.imgsz, config.imgsz, 3)),
                        keras.layers.Rescaling(1.0 / 255),
                        keras.layers.Conv2D(32, 3, activation="relu"),
                        keras.layers.MaxPooling2D(),
                        keras.layers.Conv2D(64, 3, activation="relu"),
                        keras.layers.MaxPooling2D(),
                        keras.layers.Flatten(),
                        keras.layers.Dense(128, activation="relu"),
                        keras.layers.Dense(num_classes, activation="softmax"),
                    ]
                )

            model.compile(
                optimizer=keras.optimizers.Adam(learning_rate=config.lr0),
                loss="sparse_categorical_crossentropy",
                metrics=["accuracy"],
            )

        t0 = time.time()
        history = model.fit(train_ds, validation_data=val_ds, epochs=config.epochs, verbose=1)
        elapsed = time.time() - t0

        model_path = str(MODELS_DIR / "classifier" / f"{config.name}.keras")
        Path(model_path).parent.mkdir(parents=True, exist_ok=True)
        model.save(model_path)

        train_result = TrainResult(
            name=config.name,
            model_path=model_path,
            best_path=model_path,
            epochs=config.epochs,
            metrics={
                "loss": float(history.history["loss"][-1]),
                "accuracy": float(history.history["accuracy"][-1]),
            },
            duration_seconds=elapsed,
        )

        results_dir = Path(config.project) / config.name
        serialize_config(config, results_dir / "config.yaml")
        serialize_result(train_result, results_dir / "results.json")
        meta = experiment_metadata(
            command="train_classifier",
            args={"base_model": base_model, "fine_tune": fine_tune, "epochs": config.epochs},
        )
        serialize_result(meta, results_dir / "metadata.json")

        return train_result


# ── Strategy Registry ────────────────────────────────────────────────

_STRATEGIES: dict[str, type[TrainingStrategy]] = {}
_DEFAULTS_LOADED = False


def register_strategy(name: str, strategy_cls: type[TrainingStrategy]):
    """Register a training strategy for a given task name."""
    _STRATEGIES[name] = strategy_cls


def get_strategy(name: str) -> TrainingStrategy:
    """Get a training strategy by name."""
    _ensure_defaults()
    cls = _STRATEGIES.get(name)
    if cls is None:
        raise KeyError(f"Unknown training strategy '{name}'. Available: {list(_STRATEGIES.keys())}")
    return cls()


def list_strategies() -> list[str]:
    """List all registered strategy names."""
    _ensure_defaults()
    return list(_STRATEGIES.keys())


def _ensure_defaults():
    global _DEFAULTS_LOADED
    if not _DEFAULTS_LOADED:
        _init_defaults()
        _DEFAULTS_LOADED = True


def _init_defaults():
    register_strategy("detection", YOLOStrategy)
    register_strategy("classifier", ClassifierStrategy)
