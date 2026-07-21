"""Plugin registry for MIRA pipeline.

Allows registering CLI commands and model adapters without editing existing files.

Usage:
    from pipeline.registry import register_command

    @register_command("train", "Train a YOLO or classification model")
    def cmd_train(args):
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


# ── Model Adapter Registry ──────────────────────────────────────────


@dataclass
class ModelAdapterEntry:
    model_type: str  # "yolo_pt", "yolo_tflite", "tflite", "keras", "onnx"
    adapter_class: type  # Class implementing the DetectionModel protocol
    description: str = ""


_MODEL_ADAPTERS: dict[str, ModelAdapterEntry] = {}


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
