# CLI commands for training, exporting, and auto-detecting training parameters.

import argparse
import re
import sys
from pathlib import Path

from src.config import ROOT_DIR
from src.pipeline.registry import register_command


def _validate_name(name):
    if not re.match(r"^[a-zA-Z0-9_\-]+$", name):
        raise argparse.ArgumentTypeError(f"Invalid name '{name}'. Use only letters, numbers, hyphens, underscores.")
    return name


def _add_train_args(parser):
    parser.add_argument("--config", type=str, default=None, help="Path to a YAML config file for TrainConfig.")
    parser.add_argument(
        "--model",
        type=str,
        default=None,
        help="Base model name or path (default: yolo11n.pt).",
    )
    parser.add_argument(
        "--dataset", type=str, default=None, help="Path to dataset YAML (default: auto-detect from registry)."
    )
    parser.add_argument("--epochs", type=int, default=None, help="Number of training epochs (default: 120).")
    parser.add_argument("--batch-size", type=int, default=None, help="Batch size (default: 32).")
    parser.add_argument("--name", type=_validate_name, default=None, help="Experiment/run name (default: exp).")
    parser.add_argument("--device", type=str, default=None, help="CUDA device or 'cpu' (default: 0).")
    parser.add_argument(
        "--data-dir", type=str, default=None, help="Data directory for classifier training (default: data/classes)."
    )
    parser.add_argument(
        "--task",
        type=str,
        default="detection",
        choices=["detection", "classifier"],
        help="Training task: detection (YOLO) or classifier (MobileNetV2).",
    )
    parser.add_argument(
        "--base-model",
        type=str,
        default="mobilenetv2",
        help="Base model for classifier training (mobilenetv2, custom_cnn).",
    )
    parser.add_argument("--fine-tune", action="store_true", help="Enable fine-tuning for classifier training.")
    parser.add_argument("--dry-run", action="store_true", help="Validate configuration without starting training.")
    parser.add_argument("--auto", action="store_true", help="Auto-detect hardware and configure training parameters.")


def _apply_train_argument_overrides(args, config):
    argument_to_config_field = (
        ("model", "model"),
        ("dataset", "dataset"),
        ("epochs", "epochs"),
        ("batch_size", "batch_size"),
        ("name", "name"),
        ("device", "device"),
        ("data_dir", "data_dir"),
    )
    for argument_name, config_field in argument_to_config_field:
        value = getattr(args, argument_name)
        if value is not None:
            setattr(config, config_field, value)


def _configure_training_from_hardware(args, config):
    from src.deploy import detect_hardware

    hardware = detect_hardware()
    print("\n  Auto-detecting hardware...")

    if hardware.has_cuda:
        config.device = "0"
        if args.batch_size is None:
            config.batch_size = 32
        print("  GPU detected - device=cuda:0, batch_size=32")
    else:
        config.device = "cpu"
        if args.batch_size is None:
            config.batch_size = 8
        print("  CPU only - device=cpu, batch_size=8")

    if args.model is None:
        from src.pipeline.models import ModelRegistry

        model_registry = ModelRegistry()
        model_registry.discover()
        available_models = model_registry.list_models()
        pytorch_models = [model for model in available_models if model["name"].endswith(".pt")]
        if pytorch_models:
            config.model = pytorch_models[-1]["name"]
            print(f"  Base model: {config.model}")

    if args.dataset is None:
        from src.pipeline.dataset import DatasetRegistry

        dataset_registry = DatasetRegistry()
        dataset_registry.discover()
        sources = dataset_registry.list_sources()
        available_datasets = [source for source in sources if source["exists"]]
        if available_datasets:
            selected_dataset = available_datasets[0]
            dataset_yaml = Path(selected_dataset["path"]) / "dataset.yaml"
            if dataset_yaml.exists():
                config.dataset = dataset_yaml
                print(f"  Dataset: {selected_dataset['key']}")

    print()


def _resolve_detection_dataset(config):
    from src.cli.inference import resolve_detection_data_yaml

    try:
        config.dataset = str(resolve_detection_data_yaml())
    except FileNotFoundError as error:
        print(f"Configuration error: {error}")
        sys.exit(2)


@register_command("train", "Train a YOLO detection or classification model", add_args=_add_train_args)
def cmd_train(args):
    from src.pipeline.strategies import TrainConfig
    from src.pipeline.train import TrainingPipeline

    if args.config:
        try:
            config = TrainConfig.from_yaml(args.config)
        except FileNotFoundError:
            print(f"Error: Config file not found: {args.config}")
            sys.exit(1)
    else:
        config = TrainConfig()

    _apply_train_argument_overrides(args, config)

    if args.auto:
        _configure_training_from_hardware(args, config)

    errors = config.validate()
    if errors:
        print("Configuration errors:")
        for e in errors:
            print(f"  - {e}")
        sys.exit(2)

    if args.task == "detection" and not config.dataset:
        _resolve_detection_dataset(config)

    if args.dry_run:
        print("Configuration is valid. Dry run - no training started.")
        print(f"  model: {config.model}")
        print(f"  dataset: {config.dataset}")
        print(f"  epochs: {config.epochs}")
        print(f"  batch_size: {config.batch_size}")
        print(f"  imgsz: {config.imgsz}")
        return

    pipeline = TrainingPipeline()
    if args.task == "classifier":
        if not config.data_dir:
            config.data_dir = str(ROOT_DIR / "data" / "classes")
        result = pipeline.train_classifier(config, base_model=args.base_model, fine_tune=args.fine_tune)
    else:
        result = pipeline.train_yolo(config)
        export_formats = getattr(args, "export_formats", None)
        if export_formats:
            formats = [value.strip() for value in export_formats.split(",") if value.strip()]
            result.exported.extend(pipeline.export_model(result.best_path, formats, config.dataset))
    print(f"\nTraining complete: {result.name}")
    print(f"  Best model: {result.best_path}")
    print(f"  Duration:   {result.duration_seconds:.1f}s")
    if result.metrics:
        print(f"  Metrics:    {result.metrics}")
    if result.exported:
        print(f"  Exported:   {result.exported}")


def _add_export_args(parser):
    parser.add_argument("--model", type=str, required=True, help="Path to the .pt model to export.")
    parser.add_argument(
        "--formats",
        type=str,
        nargs="+",
        default=["tflite_int8"],
        help="Export formats (default: tflite_int8). Options: tflite_int8, tflite_fp32, onnx.",
    )
    parser.add_argument("--dataset", type=str, default="", help="Dataset YAML for INT8 calibration (optional).")
    parser.add_argument("--dry-run", action="store_true", help="Validate model path without exporting.")


@register_command("export", "Export a trained .pt model to TFLite / ONNX", add_args=_add_export_args)
def cmd_export(args):
    from src.pipeline.train import TrainingPipeline

    model_path = Path(args.model)
    if not model_path.is_absolute():
        model_path = (ROOT_DIR / model_path).resolve()
    if not model_path.exists():
        print(f"Error: Model not found at {model_path}")
        print("Run 'mira models' to see available models.")
        sys.exit(1)

    if args.dry_run:
        print(f"Model found: {model_path}")
        print(f"Formats: {', '.join(args.formats)}")
        print("Dry run - no export performed.")
        return

    pipeline = TrainingPipeline()
    exported = pipeline.export_model(str(model_path), args.formats, args.dataset)
    if exported:
        print("Exported:")
        for p in exported:
            print(f"  {p}")
    else:
        print("No files exported.")
