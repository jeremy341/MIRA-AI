"""Training pipeline for MIRA — delegates to registered training strategies.

Usage:
    from pipeline.train import TrainingPipeline, TrainConfig, TrainResult

    config = TrainConfig.from_yaml("experiments/exp014.yaml")
    result = TrainingPipeline().train("detection", config)
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path


from ..exceptions import PipelineError
from ..logger import logger
from .strategies import TrainConfig, TrainResult, get_strategy, register_strategy as _register_strategy


class TrainingPipeline:
    """High-level training pipeline that delegates to registered strategies."""

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

        exported = []
        for fmt in formats:
            fmt_lower = fmt.lower().replace("-", "_")
            try:
                out = (
                    model.export(format="tflite", int8=True)
                    if fmt_lower == "tflite_int8"
                    else model.export(format="tflite", int8=False)
                    if fmt_lower == "tflite_fp32"
                    else model.export(format="onnx")
                    if fmt_lower == "onnx"
                    else model.export(format="engine", half=True, imgsz=640, workspace=4)
                    if fmt_lower == "tensorrt"
                    else None
                )
                if out is None:
                    logger.warning("Unknown export format '%s', skipping", fmt)
            except Exception as e:
                logger.error(f"Export to format '{fmt}' failed: {e}")
                raise PipelineError(f"Model export to format '{fmt}' failed: {e}") from e
            if out:
                exported.append(str(out))
        return exported

    def train_yolo(self, config: TrainConfig) -> TrainResult:
        config.project = "runs/train"
        if config.name is None or config.name == "exp":
            config.name = datetime.now(timezone.utc).strftime("%Y-%m-%d_%H-%M-%S")

        result = self.train("detection", config)

        results_dir = Path(config.project) / config.name
        logger.info(f"Experiment saved to {results_dir}")
        return result

    def train_classifier(
        self, config: TrainConfig, base_model: str = "mobilenetv2", fine_tune: bool = False
    ) -> TrainResult:
        config.extra["base_model"] = base_model
        config.extra["fine_tune"] = fine_tune

        config.project = "runs/train"
        if config.name is None or config.name == "exp":
            config.name = datetime.now(timezone.utc).strftime("%Y-%m-%d_%H-%M-%S")

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
        """Register a custom training strategy."""
        _register_strategy(task, strategy_cls)
