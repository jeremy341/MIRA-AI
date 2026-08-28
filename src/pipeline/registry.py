# registry for CLI commands and model adapters

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from ..logger import get_logger

_logging = get_logger(__name__)


@dataclass
class CommandEntry:
    name: str
    help_text: str
    fn: Callable
    add_args: Callable | None = None  # fn(parser) to add custom args


_COMMANDS: dict[str, CommandEntry] = {}


def register_command(name: str, help_text: str, add_args: Callable | None = None):

    def decorator(func):
        if name in _COMMANDS:
            _logging.warning("Command '%s' being overwritten", name)
        _COMMANDS[name] = CommandEntry(name=name, help_text=help_text, fn=func, add_args=add_args)
        return func

    return decorator


def get_commands() -> dict[str, CommandEntry]:
    return dict(_COMMANDS)


@dataclass
class ModelAdapterEntry:
    model_type: str  # "yolo_pt", "yolo_tflite", "tflite", "keras", "onnx"
    adapter_class: type  # Class implementing the DetectionModel protocol
    description: str = ""


_MODEL_ADAPTERS: dict[str, ModelAdapterEntry] = {}


def init_adapters() -> None:
    # Register built-in model adapters.
    from .models import YOLOAdapter, YOLOTFLiteAdapter, ThirdPartyAdapter

    for key, desc, cls in [
        ("yolo_pt", "Ultralytics YOLO .pt models", YOLOAdapter),
        ("yolo_tflite", "YOLO-exported TFLite models", YOLOTFLiteAdapter),
        ("third_party", "Third-party models", ThirdPartyAdapter),
    ]:
        if key not in _MODEL_ADAPTERS:
            _MODEL_ADAPTERS[key] = ModelAdapterEntry(model_type=key, adapter_class=cls, description=desc)


def get_model_adapters() -> dict[str, ModelAdapterEntry]:
    # Return all registered model adapters.
    init_adapters()
    return dict(_MODEL_ADAPTERS)
