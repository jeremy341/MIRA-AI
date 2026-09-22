# training pipeline - delegates to registered strategies

from __future__ import annotations

import copy
from datetime import datetime, timezone
from pathlib import Path

from ..exceptions import PipelineError
from ..logger import logger
from .strategies import TrainConfig, TrainResult, get_strategy
from .strategies import register_strategy as _register_strategy


def _prepare_training_config(config: TrainConfig, extra_values: dict | None = None) -> TrainConfig:
    config = copy.deepcopy(config)
    if extra_values:
        config.extra.update(extra_values)
    if not config.project:
        config.project = "runs/train"
    if config.name is None or config.name == "exp":
        config.name = datetime.now(timezone.utc).strftime("%Y-%m-%d_%H-%M-%S")
    return config


class TrainingPipeline:
    def train(self, task: str, config: TrainConfig) -> TrainResult:
        try:
            strategy = get_strategy(task)
            result = strategy.train(config)
        except PipelineError:
            raise
        except Exception as e:
            logger.error(f"Training failed for task '{task}' with config '{config.name}': {e}")
            raise PipelineError(f"Training failed for task '{task}': {e}") from e
        return result

    def export_model(self, model_path: str, formats: list[str], dataset: str = "") -> list[str]:
        try:
            from ultralytics import YOLO
        except ImportError as e:
            raise PipelineError(
                "ultralytics is required for model export. Install it with: pip install ultralytics"
            ) from e

        try:
            model = YOLO(model_path)
        except Exception as e:
            logger.error(f"Failed to load model from '{model_path}': {e}")
            raise PipelineError(f"Failed to load model '{model_path}': {e}") from e

        fixed_formats = {
            "tflite_fp32": {"format": "tflite", "int8": False},
            "tflite": {"format": "tflite", "int8": False},
            "onnx": {"format": "onnx"},
            "tensorrt": {"format": "engine", "quantize": True, "imgsz": 640, "workspace": 4},
        }
        exported = []
        for fmt in formats:
            normalized_format = fmt.lower().replace("-", "_")
            try:
                if normalized_format == "tflite_int8":
                    export_kwargs = {"format": "tflite", "int8": True}
                    if dataset:
                        export_kwargs["data"] = dataset
                elif normalized_format in fixed_formats:
                    export_kwargs = fixed_formats[normalized_format]
                else:
                    export_kwargs = None

                if export_kwargs is None:
                    logger.warning("Unknown export format '%s', skipping", fmt)
                    continue

                out = model.export(**export_kwargs)
            except Exception as e:
                logger.error(f"Export to format '{fmt}' failed: {e}")
                raise PipelineError(f"Model export to format '{fmt}' failed: {e}") from e
            if out:
                exported.append(str(out))
        return exported

    def train_yolo(self, config: TrainConfig) -> TrainResult:
        config = _prepare_training_config(config)
        result = self.train("detection", config)

        results_dir = Path(config.project) / config.name
        logger.info(f"Experiment saved to {results_dir}")
        return result

    def train_classifier(
        self, config: TrainConfig, base_model: str = "mobilenetv2", fine_tune: bool = False
    ) -> TrainResult:
        config = _prepare_training_config(config, {"base_model": base_model, "fine_tune": fine_tune})

        try:
            result = self.train("classifier", config)
        except PipelineError:
            raise
        except Exception as e:
            logger.error(f"Classifier training failed: {e}")
            raise PipelineError(
                f"Classifier training failed: {e}. Check that your data directory contains valid image subfolders."
            ) from e
        results_dir = Path(config.project) / config.name
        print(f"  Experiment saved to {results_dir}")
        return result

    @classmethod
    def register_strategy(cls, task: str, strategy_cls):
        _register_strategy(task, strategy_cls)
