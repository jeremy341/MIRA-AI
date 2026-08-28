# MIRA Research Pipeline - modular ML pipeline for recycling detection.

from .dataset import DatasetRegistry, DatasetSource, MergeResult
from .strategies import TrainConfig, TrainResult, register_strategy, get_strategy
from .train import TrainingPipeline
from .models import DetectionModel, YOLOAdapter, ModelRegistry
from .benchmark import ModelBenchmark
from .validators import validate_yolo_dataset, dataset_summary

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
