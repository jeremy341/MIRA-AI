"""Plugin registry for MIRA pipeline.

Allows registering new CLI commands, dataset sources, and model adapters
without editing existing files. Use decorators to register plugins.

Usage:
    from pipeline.registry import register_command, register_dataset_source, register_model_adapter

    @register_command("train", "Train a YOLO or classification model")
    def cmd_train(args):
        ...

    @register_dataset_source("my_source", "My custom dataset")
    def load_my_source(registry_dir):
        ...
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

# ── Command Registry ────────────────────────────────────────────────


@dataclass
class CommandEntry:
    name: str
    help_text: str
    fn: Callable
    add_args: Callable | None = None  # fn(parser) to add custom args


_COMMANDS: dict[str, CommandEntry] = {}


def register_command(name: str, help_text: str, add_args: Callable | None = None):
    """Decorator to register a CLI command.

    Args:
        name: Command name (e.g. "train", "benchmark")
        help_text: Help text shown in `mira --help`
        add_args: Optional function that adds arguments to the subparser
    """

    def decorator(func):
        _COMMANDS[name] = CommandEntry(name=name, help_text=help_text, fn=func, add_args=add_args)
        return func

    return decorator


def get_commands() -> dict[str, CommandEntry]:
    """Return all registered commands."""
    return dict(_COMMANDS)


# ── Dataset Source Registry ─────────────────────────────────────────


@dataclass
class DatasetSourceEntry:
    key: str
    name: str
    loader: Callable  # fn(output_dir, dry_run=False) -> (added, skipped)


_DATASET_SOURCES: dict[str, DatasetSourceEntry] = {}


def register_dataset_source(key: str, name: str):
    """Decorator to register a dataset source for the merger.

    The decorated function should accept (output_dir, dry_run=False)
    and return (added_count, skipped_count).
    """

    def decorator(func):
        _DATASET_SOURCES[key] = DatasetSourceEntry(key=key, name=name, loader=func)
        return func

    return decorator


def get_dataset_sources() -> dict[str, DatasetSourceEntry]:
    """Return all registered dataset sources."""
    return dict(_DATASET_SOURCES)


# ── Model Adapter Registry ──────────────────────────────────────────


@dataclass
class ModelAdapterEntry:
    model_type: str  # "yolo_pt", "yolo_tflite", "tflite", "keras", "onnx"
    adapter_class: type  # Class implementing the DetectionModel protocol
    description: str = ""


_MODEL_ADAPTERS: dict[str, ModelAdapterEntry] = {}


def register_model_adapter(model_type: str, description: str = ""):
    """Decorator to register a model adapter for a specific model format.

    The decorated class must implement the DetectionModel protocol
    defined in pipeline.models.
    """

    def decorator(cls):
        _MODEL_ADAPTERS[model_type] = ModelAdapterEntry(
            model_type=model_type, adapter_class=cls, description=description
        )
        return cls

    return decorator


def init_adapters() -> None:
    """Register built-in model adapters."""
    from pipeline.models import YOLOAdapter, YOLOTFLiteAdapter, ThirdPartyAdapter

    for key, desc, cls in [
        ("yolo_pt", "Ultralytics YOLO .pt models", YOLOAdapter),
        ("yolo_tflite", "YOLO-exported TFLite models", YOLOTFLiteAdapter),
        ("third_party", "Third-party models", ThirdPartyAdapter),
    ]:
        if key not in _MODEL_ADAPTERS:
            _MODEL_ADAPTERS[key] = ModelAdapterEntry(model_type=key, adapter_class=cls, description=desc)


def get_model_adapters() -> dict[str, ModelAdapterEntry]:
    """Return all registered model adapters."""
    init_adapters()
    return dict(_MODEL_ADAPTERS)
