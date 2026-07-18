"""MIRA Research Pipeline — modular ML pipeline for recycling detection."""

from pipeline.dataset import DatasetRegistry, DatasetSource, MergeResult
from pipeline.train import TrainingPipeline, TrainConfig, TrainResult
from pipeline.models import DetectionModel, YOLOAdapter, ModelRegistry
from pipeline.benchmark import ModelBenchmark

__all__ = [
    "DatasetRegistry",
    "DatasetSource",
    "MergeResult",
    "TrainingPipeline",
    "TrainConfig",
    "TrainResult",
    "DetectionModel",
    "YOLOAdapter",
    "ModelRegistry",
    "ModelBenchmark",
]
