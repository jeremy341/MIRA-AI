"""MIRA Research Pipeline — modular ML pipeline for recycling detection."""

from pipeline.dataset import DatasetRegistry, DatasetSource, MergeResult
from pipeline.strategies import TrainConfig, TrainResult, register_strategy, get_strategy
from pipeline.train import TrainingPipeline
from pipeline.models import DetectionModel, YOLOAdapter, ModelRegistry
from pipeline.benchmark import ModelBenchmark
from pipeline.validators import validate_yolo_dataset, dataset_summary

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
    "validate_yolo_dataset",
    "dataset_summary",
    "register_strategy",
    "get_strategy",
]
