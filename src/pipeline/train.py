"""Training pipeline for MIRA — YOLO detection and classifier training.

Usage:
    from pipeline.train import TrainingPipeline, TrainConfig

    config = TrainConfig.from_yaml("experiments/exp014.yaml")
    result = TrainingPipeline().train_yolo(config)
"""

from __future__ import annotations

import time
from dataclasses import asdict, dataclass, field, fields
from pathlib import Path
from typing import Any

import yaml

from config import MODELS_DIR, PROJECT_CONFIG, ROOT_DIR

# ── Augmentation Configuration ───────────────────────────────────────


@dataclass
class AugmentConfig:
    hsv_h: float = 0.015
    hsv_s: float = 0.7
    hsv_v: float = 0.4
    degrees: float = 0.0
    translate: float = 0.1
    scale: float = 0.5
    shear: float = 0.0
    perspective: float = 0.0
    flipud: float = 0.0
    fliplr: float = 0.5
    mosaic: float = 1.0
    mixup: float = 0.0
    copy_paste: float = 0.0

    def to_ultralytics(self) -> dict[str, float]:
        return asdict(self)


# ── Export Configuration ─────────────────────────────────────────────


@dataclass
class ExportConfig:
    formats: list[str] = field(default_factory=lambda: ["tflite_int8"])
    calibration_samples: int = 100


# ── Training Configuration ───────────────────────────────────────────


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
    augmentation: AugmentConfig = field(default_factory=AugmentConfig)
    export: ExportConfig = field(default_factory=ExportConfig)
    project: str = "runs"
    exist_ok: bool = True

    @classmethod
    def from_yaml(cls, path: str | Path) -> TrainConfig:
        with open(path) as f:
            data = yaml.safe_load(f)

        if "epochs" in data and not isinstance(data["epochs"], int):
            raise ValueError(f"epochs must be an integer, got {type(data['epochs']).__name__}")
        if "batch_size" in data and not isinstance(data["batch_size"], int):
            raise ValueError(f"batch_size must be an integer, got {type(data['batch_size']).__name__}")
        if "lr0" in data and not isinstance(data["lr0"], (int, float)):
            raise ValueError(f"lr0 must be a number, got {type(data['lr0']).__name__}")
        if "epochs" in data and data["epochs"] <= 0:
            raise ValueError(f"epochs must be positive, got {data['epochs']}")

        known_fields = {f.name for f in fields(cls)}
        unknown = set(data.keys()) - known_fields - {"augmentation", "export"}
        if unknown:
            print(f"Warning: Unknown fields in {path}: {unknown}")

        aug_data = data.pop("augmentation", {})
        export_data = data.pop("export", {})
        config = cls(**data)
        if aug_data:
            config.augmentation = AugmentConfig(**aug_data)
        if export_data:
            config.export = ExportConfig(**export_data)
        return config

    def to_yaml(self, path: str | Path) -> None:
        data = asdict(self)
        with open(path, "w") as f:
            yaml.dump(data, f, default_flow_style=False, sort_keys=False)


# ── Training Result ──────────────────────────────────────────────────


@dataclass
class TrainResult:
    name: str
    model_path: str
    best_path: str
    epochs: int
    metrics: dict[str, Any]
    duration_seconds: float
    exported: list[str]


# ── Training Pipeline ────────────────────────────────────────────────


class TrainingPipeline:
    """High-level pipeline for training and exporting models."""

    def train_yolo(self, config: TrainConfig) -> TrainResult:
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
            **config.augmentation.to_ultralytics(),
        }

        t0 = time.time()
        results = model.train(**kwargs)  # type: ignore[arg-type]
        elapsed = time.time() - t0

        best_path = str(Path(config.project) / config.name / "weights" / "best.pt")
        last_path = str(Path(config.project) / config.name / "weights" / "last.pt")

        metrics = {}
        if hasattr(results, "box"):
            metrics["map50"] = getattr(results.box, "map50", 0.0)
            metrics["map"] = getattr(results.box, "map", 0.0)

        exported = self.export_model(
            str(best_path) if Path(best_path).exists() else str(last_path),
            config.export.formats,
            config.dataset,
        )

        return TrainResult(
            name=config.name,
            model_path=last_path,
            best_path=best_path,
            epochs=config.epochs,
            metrics=metrics,
            duration_seconds=elapsed,
            exported=exported,
        )

    def export_model(self, model_path: str, formats: list[str], dataset: str = "") -> list[str]:
        from ultralytics import YOLO

        model = YOLO(model_path)
        exported = []
        for fmt in formats:
            fmt_lower = fmt.lower().replace("-", "_")
            if fmt_lower == "tflite_int8":
                out = model.export(format="tflite", int8=True)
            elif fmt_lower == "tflite_fp32":
                out = model.export(format="tflite", int8=False)
            elif fmt_lower == "onnx":
                out = model.export(format="onnx")
            else:
                continue
            exported.append(str(out))
        return exported

    def train_classifier(
        self,
        config: TrainConfig,
        base_model: str = "mobilenetv2",
        fine_tune: bool = False,
        fine_tune_from: str | None = None,
    ) -> TrainResult:
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

        with strategy.scope():
            if fine_tune and fine_tune_from:
                model = keras.models.load_model(fine_tune_from)
                model.trainable = True
            elif base_model == "mobilenetv2":
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
                model.compile(
                    optimizer=keras.optimizers.Adam(learning_rate=config.lr0),
                    loss="sparse_categorical_crossentropy",
                    metrics=["accuracy"],
                )
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
        history = model.fit(
            train_ds,
            validation_data=val_ds,
            epochs=config.epochs,
            verbose=1,
        )
        elapsed = time.time() - t0

        model_path = str(MODELS_DIR / "classifier" / f"{config.name}.keras")
        Path(model_path).parent.mkdir(parents=True, exist_ok=True)
        model.save(model_path)

        return TrainResult(
            name=config.name,
            model_path=model_path,
            best_path=model_path,
            epochs=config.epochs,
            metrics={
                "loss": float(history.history["loss"][-1]),
                "accuracy": float(history.history["accuracy"][-1]),
            },
            duration_seconds=elapsed,
            exported=[],
        )
