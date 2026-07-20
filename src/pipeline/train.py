"""Training pipeline for MIRA — delegates to registered training strategies.

Usage:
    from pipeline.train import TrainingPipeline, TrainConfig, TrainResult

    config = TrainConfig.from_yaml("experiments/exp014.yaml")
    result = TrainingPipeline().train("detection", config)
"""

from __future__ import annotations

from pathlib import Path

import yaml

from pipeline.strategies import TrainConfig, TrainResult, get_strategy, register_strategy


class TrainingPipeline:
    """High-level training pipeline that delegates to registered strategies."""

    def train(self, task: str, config: TrainConfig) -> TrainResult:
        strategy = get_strategy(task)
        return strategy.train(config)

    def export_model(self, model_path: str, formats: list[str], dataset: str = "") -> list[str]:
        from ultralytics import YOLO

        model = YOLO(model_path)
        exported = []
        for fmt in formats:
            fmt_lower = fmt.lower().replace("-", "_")
            out = model.export(format="tflite", int8=True) if fmt_lower == "tflite_int8" else \
                  model.export(format="tflite", int8=False) if fmt_lower == "tflite_fp32" else \
                  model.export(format="onnx") if fmt_lower == "onnx" else \
                  model.export(format="engine", half=True, imgsz=640, workspace=4) if fmt_lower == "tensorrt" else \
                  None
            if out:
                exported.append(str(out))
        return exported

    def train_yolo(self, config: TrainConfig) -> TrainResult:
        return self.train("detection", config)

    def train_classifier(self, config: TrainConfig, base_model: str = "mobilenetv2", fine_tune: bool = False) -> TrainResult:
        config.extra["base_model"] = base_model
        config.extra["fine_tune"] = fine_tune
        return self.train("classifier", config)

    @classmethod
    def register_strategy(cls, task: str, strategy_cls):
        """Register a custom training strategy."""
        register_strategy(task, strategy_cls)
