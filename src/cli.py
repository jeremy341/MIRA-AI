import argparse
import sys
from pathlib import Path

_src_dir = str(Path(__file__).resolve().parent)
if _src_dir not in sys.path:
    sys.path.insert(0, _src_dir)

from version import __version__
from config import DETECTION_DIR, REJECT_THRESHOLD, ROOT_DIR, get_tflite_imgsz, resolve_safe_path
from exceptions import ConfigError, MiraError
from logger import get_logger
from model_picker import pick_model
from pipeline.registry import get_commands, register_command
from pipeline.models import ModelRegistry

logger = get_logger(__name__)


def resolve_detection_data_yaml(explicit_path=None):
    candidates = []
    if explicit_path:
        try:
            candidate = resolve_safe_path(explicit_path, base_dir=ROOT_DIR)
        except ConfigError as e:
            print(f"Error: {e}")
            sys.exit(2)
        if candidate.is_file():
            return candidate
        print(f"Warning: {explicit_path} is not a valid file, searching defaults...")

    # Scan datasets/ for any existing dataset.yaml
    datasets_dir = ROOT_DIR / "datasets"
    if datasets_dir.exists():
        for subdir in sorted(datasets_dir.iterdir()):
            if subdir.is_dir() and not subdir.name.startswith("."):
                yaml_candidate = subdir / "dataset.yaml"
                if yaml_candidate.exists():
                    candidates.append(yaml_candidate)

    for candidate in candidates:
        if candidate.exists():
            return candidate
    raise FileNotFoundError(
        "Could not find a YOLO dataset YAML. Please specify one with --data or generate a dataset using `mira merge`."
    )


def _pick_model_interactive(title="Available models"):
    """Show interactive picker for detection models. Returns model name or None."""
    registry = ModelRegistry()
    registry.discover()
    models = registry.list_models()
    labels = {m["name"]: m["label"] for m in models}
    return pick_model([m["name"] for m in models], labels=labels, title=title)


def _add_eval_yolo_args(parser):
    parser.add_argument(
        "--model", type=str, default=None, nargs="?", help="Model filename. Omit to use interactive picker."
    )
    parser.add_argument("--data", type=str, default=None, help="Optional dataset YAML path.")


@register_command("eval-yolo", "Evaluate YOLOv8 detection models", add_args=_add_eval_yolo_args)
def cmd_eval_yolo(args):
    model = args.model
    if model is None:
        model = _pick_model_interactive("Available detection models")
        if model is None:
            sys.exit(0)
    model_path = DETECTION_DIR / model
    if not model_path.exists():
        raise FileNotFoundError(f"Model file not found at {model_path}")
    from ultralytics import YOLO

    data_path = resolve_detection_data_yaml(args.data)
    task_type = "detect" if model_path.suffix == ".tflite" else None
    model = YOLO(str(model_path), task=task_type)
    val_imgsz = get_tflite_imgsz(model_path) if model_path.suffix == ".tflite" else 640
    model.val(data=str(data_path), imgsz=val_imgsz)


def _add_live_args(parser):
    parser.add_argument(
        "--model", type=str, default=None, nargs="?", help="Model filename. Omit to use interactive picker."
    )
    parser.add_argument("--camera", type=int, default=0, help="Camera device index (default: 0).")
    parser.add_argument(
        "--resolution",
        type=str,
        default="640x360",
        choices=["640x360", "1280x720", "1920x1080"],
        help="Camera capture resolution (default: 640x360).",
    )
    parser.add_argument("--target-latency", type=int, default=50, help="Target latency in ms (default: 50).")
    parser.add_argument("--conf", type=float, default=0.5, help="Confidence threshold (default: 0.5).")
    parser.add_argument(
        "--reject",
        type=float,
        default=REJECT_THRESHOLD,
        help="Reject threshold: uncertain detections below this are labeled 'unsicher' (default: 0.55).",
    )


@register_command("live", "Start real-time YOLOv8 webcam tracking stream", add_args=_add_live_args)
def cmd_live(args):
    model = args.model
    if model is None:
        model = _pick_model_interactive("Available detection models")
        if model is None:
            sys.exit(0)
    if "classifier" in model.lower():
        print(f"ERROR: '{model}' is a classifier model, not a detector.")
        sys.exit(1)
    from inference_engine import InferenceEngine

    w, h = map(int, args.resolution.split("x"))
    engine = InferenceEngine(
        model_name=model,
        camera_index=args.camera,
        cam_width=w,
        cam_height=h,
        target_latency_ms=args.target_latency,
        conf_threshold=args.conf,
        reject_threshold=args.reject,
    )
    engine.run()


# ── New Pipeline Commands ────────────────────────────────────────────


def _add_merge_args(parser):
    parser.add_argument("--sources", type=str, nargs="+", required=True, help="Registered source keys to merge.")
    parser.add_argument("--output", type=str, required=True, help="Output directory for merged dataset.")
    parser.add_argument("--custom", type=str, default=None, help="Optional path to a custom YOLO-format dataset.")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be merged without copying files.")


@register_command("merge", "Merge registered dataset sources into a unified YOLO dataset", add_args=_add_merge_args)
def cmd_merge(args):
    from pipeline.dataset import DatasetRegistry

    registry = DatasetRegistry()
    n = registry.discover()
    print(f"Discovered {n} dataset sources.")
    output = Path(args.output)
    result = registry.merge(
        sources=args.sources,
        output=output,
        custom_path=Path(args.custom) if args.custom else None,
        dry_run=args.dry_run,
    )
    print(f"\nMerge complete: {result.total_added} added, {result.total_skipped} skipped")
    print(f"Output: {result.output_dir}")


@register_command("datasets", "List registered dataset sources from datasets/registry/*.yaml")
def cmd_datasets(args):
    from pipeline.dataset import DatasetRegistry

    registry = DatasetRegistry()
    registry.discover()
    sources = registry.list_sources()
    if not sources:
        print("No dataset sources found in datasets/registry/")
        return
    print(f"{'Key':<24} {'Name':<32} {'Format':<12} {'Exists':<8}")
    print("-" * 76)
    for s in sources:
        exists = "yes" if s["exists"] else "NO"
        print(f"{s['key']:<24} {s['name']:<32} {s['format']:<12} {exists:<8}")


def _add_train_args(parser):
    parser.add_argument("--config", type=str, default=None, help="Path to a YAML config file for TrainConfig.")
    parser.add_argument(
        "--model",
        type=str,
        default=None,
        help="Base model name or path (default: yolo11n.pt).",
    )
    parser.add_argument("--dataset", type=str, default=None, help="Path to dataset YAML (default: '').")
    parser.add_argument("--epochs", type=int, default=None, help="Number of training epochs (default: 120).")
    parser.add_argument("--batch-size", type=int, default=None, help="Batch size (default: 32).")
    parser.add_argument("--name", type=str, default=None, help="Experiment/run name (default: exp).")
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


@register_command("train", "Train a YOLO detection model via the new pipeline", add_args=_add_train_args)
def cmd_train(args):
    from pipeline.strategies import TrainConfig
    from pipeline.train import TrainingPipeline

    if args.config:
        config = TrainConfig.from_yaml(args.config)
    else:
        config = TrainConfig()

    if args.model is not None:
        config.model = args.model
    if args.dataset is not None:
        config.dataset = args.dataset
    if args.epochs is not None:
        config.epochs = args.epochs
    if args.batch_size is not None:
        config.batch_size = args.batch_size
    if args.name is not None:
        config.name = args.name
    if args.device is not None:
        config.device = args.device
    if args.data_dir is not None:
        config.data_dir = args.data_dir

    # Validate before running
    errors = config.validate()
    if errors:
        print("Configuration errors:")
        for e in errors:
            print(f"  - {e}")
        sys.exit(2)

    if args.dry_run:
        print("Configuration is valid. Dry run — no training started.")
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
    print(f"\nTraining complete: {result.name}")
    print(f"  Best model: {result.best_path}")
    print(f"  Duration:   {result.duration_seconds:.1f}s")
    if result.metrics:
        print(f"  Metrics:    {result.metrics}")
    if result.exported:
        print(f"  Exported:   {result.exported}")


@register_command("experiments", "List all experiment YAML configs in experiments/")
def cmd_experiments(args):
    exp_dir = ROOT_DIR / "experiments"
    if not exp_dir.exists():
        print("No experiments/ directory found.")
        return
    yaml_files = sorted(exp_dir.glob("*.yaml"))
    if not yaml_files:
        print("No experiment YAML files found.")
        return
    print(f"{'File':<50} {'Description'}")
    print("-" * 80)
    for p in yaml_files:
        import yaml as _yaml

        with open(p, encoding="utf-8") as f:
            data = _yaml.safe_load(f) or {}
        desc = data.get("name", data.get("model", ""))
        print(f"{p.name:<50} {desc}")


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
    from pipeline.train import TrainingPipeline

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
        print("Dry run — no export performed.")
        return

    pipeline = TrainingPipeline()
    exported = pipeline.export_model(str(model_path), args.formats, args.dataset)
    if exported:
        print("Exported:")
        for p in exported:
            print(f"  {p}")
    else:
        print("No files exported.")


def _add_benchmark_args(parser):
    parser.add_argument("--models", type=str, nargs="+", required=True, help="Model paths to benchmark.")
    parser.add_argument("--dataset", type=str, default=None, help="Dataset YAML for evaluation (optional).")
    parser.add_argument("--conf", type=float, default=0.25, help="Confidence threshold (default: 0.25).")
    parser.add_argument("--max-images", type=int, default=100, help="Max images to evaluate (default: 100).")
    parser.add_argument("--output", type=str, default=None, help="Output path for benchmark report.")


@register_command("benchmark", "Benchmark multiple models for accuracy and latency", add_args=_add_benchmark_args)
def cmd_benchmark(args):
    from pipeline.benchmark import ModelBenchmark

    dataset = resolve_detection_data_yaml(args.dataset)

    bench = ModelBenchmark.from_registry(
        model_names=args.models,
        dataset_path=dataset,
        conf=args.conf,
        max_images=args.max_images,
    )
    results = bench.run()
    print(ModelBenchmark.comparison_table(results))
    if args.output:
        ModelBenchmark.export(results, args.output)


@register_command("models", "List all discovered model files in the models/ directory")
def cmd_models(args):
    from pipeline.models import ModelRegistry

    registry = ModelRegistry()
    registry.discover()
    models = registry.list_models()
    if not models:
        print("No model files found.")
        return
    print(f"{'Label':<50} {'Type':<16} {'Size':<10}")
    print("-" * 76)
    for m in models:
        size = m.get("size_mb")
        size_str = f"{size:.1f} MB" if isinstance(size, (int, float)) else ""
        print(f"{m['label']:<50} {m['model_type']:<16} {size_str:<10}")


# ── New Phase 2 Commands ─────────────────────────────────────────────


@register_command("diagnostics", "Check hardware capabilities and environment")
def cmd_diagnostics(args):
    from deploy import detect_hardware, check_environment, suggest_model

    info = detect_hardware()
    print("\n  Hardware Diagnostics")
    print(f"  {'=' * 50}")
    print(f"  Platform:     {info.platform} ({info.arch})")
    print(f"  Python:       {info.python_version.split()[0]}")
    print(f"  CPU cores:    {info.cpu_count}")
    print(f"  Memory:       {info.memory_mb} MB")
    if info.is_raspberry_pi:
        print(f"  Model:        Raspberry Pi ({info.pi_model})")
    if info.is_jetson:
        print("  Model:        NVIDIA Jetson")
    print(f"  CUDA:         {'Yes (' + info.cuda_version + ')' if info.has_cuda else 'No'}")
    print(f"  PyTorch:      {'Yes' if info.has_torch else 'No'}")
    print(f"  TensorFlow:   {'Yes' if info.has_tensorflow else 'No'}")
    print(f"  TFLite:       {'Yes' if info.has_tflite_runtime else 'No'}")
    print(f"\n  Suggested model: {suggest_model(info)}")

    warnings = check_environment()
    if warnings:
        print("\n  Warnings:")
        for w in warnings:
            print(f"    ! {w}")
    print()


def _add_validate_args(parser):
    parser.add_argument("--dataset", type=str, required=True, help="Path to dataset directory to validate.")


@register_command("validate", "Validate a YOLO-format dataset", add_args=_add_validate_args)
def cmd_validate(args):
    from pipeline.validators import validate_yolo_dataset

    result = validate_yolo_dataset(args.dataset)
    print(f"\n  Dataset validation: {args.dataset}")
    print(f"  {'=' * 50}")
    print(f"  Valid:          {'YES' if result.is_valid else 'NO'}")
    print(f"  Images:         {result.total_images}")
    print(f"  Labels:         {result.total_labels}")

    if result.class_counts:
        print("\n  Class distribution:")
        for cls_id, count in sorted(result.class_counts.items()):
            print(f"    class {cls_id}: {count} instances")

    if result.warnings:
        print("\n  Warnings:")
        for w in result.warnings:
            print(f"    ! {w}")

    if result.errors:
        print("\n  Errors:")
        for e in result.errors:
            print(f"    ! {e}")

    if result.orphaned_labels:
        print(f"\n  Orphaned labels ({len(result.orphaned_labels)}):")
        for p in result.orphaned_labels[:5]:
            print(f"    {p}")
        if len(result.orphaned_labels) > 5:
            print(f"    ... and {len(result.orphaned_labels) - 5} more")

    print()


# ── Phase 3 Commands ─────────────────────────────────────────────────


@register_command("doctor", "Run comprehensive environment and project health check")
def cmd_doctor(args):
    """Run a comprehensive health check of the MIRA environment."""
    from deploy import detect_hardware, check_environment, suggest_model
    from config import validate_config
    from pipeline.models import ModelRegistry

    print(f"\n  MIRA Doctor v{__version__}")
    print(f"  {'=' * 60}")

    # Config validation
    print("\n  [1/5] Configuration")
    config_errors = validate_config()
    if config_errors:
        print(f"    ! {len(config_errors)} config error(s):")
        for e in config_errors:
            print(f"      - {e}")
    else:
        print("    ✓ mira.yaml is valid")

    # Hardware
    print("\n  [2/5] Hardware")
    info = detect_hardware()
    print(f"    Platform: {info.platform} ({info.arch})")
    print(f"    Memory: {info.memory_mb} MB")
    print(f"    CPUs: {info.cpu_count}")
    if info.has_cuda:
        print(f"    ✓ CUDA: {info.cuda_version}")
    else:
        print("    ⚠ No CUDA detected")
    print(f"    Suggested model: {suggest_model(info)}")

    # Environment
    print("\n  [3/5] Environment")
    env_warnings = check_environment()
    if env_warnings:
        for w in env_warnings:
            print(f"    ! {w}")
    else:
        print("    ✓ All required libraries available")

    # Models
    print("\n  [4/5] Models")
    registry = ModelRegistry()
    count = registry.discover()
    if count:
        print(f"    ✓ {count} model(s) discovered")
    else:
        print("    ⚠ No models found in models/detection/")

    # Datasets
    print("\n  [5/5] Datasets")
    from pipeline.dataset import DatasetRegistry

    ds_registry = DatasetRegistry()
    ds_count = ds_registry.discover()
    available = [s for s in ds_registry.list_sources() if s["exists"]]
    if available:
        print(f"    ✓ {len(available)}/{ds_count} dataset source(s) available")
        for s in available:
            print(f"      - {s['key']}: {s['name']}")
    else:
        print("    ⚠ No dataset sources available")

    print(f"\n  {'=' * 60}")
    if config_errors or env_warnings:
        print("  Status: ISSUES FOUND — see details above")
    else:
        print("  Status: HEALTHY")
    print()


@register_command("config", "Display current project configuration")
def cmd_config(args):
    """Display the current mira.yaml configuration."""
    from config import get_project_config
    import json

    cfg = get_project_config()
    print("\n  Current MIRA Configuration (mira.yaml)")
    print(f"  {'=' * 50}")
    print(json.dumps(dict(cfg), indent=4))
    print()


@register_command("dashboard", "Launch the real-time detection dashboard")
def cmd_dashboard(args):
    """Start the MIRA dashboard server."""
    import uvicorn
    from dashboard.main import app

    print("Starting MIRA Dashboard on http://0.0.0.0:8000")
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")


# ── Main dispatcher ──────────────────────────────────────────────────


def main():
    parser = argparse.ArgumentParser(
        description="MIRA CLI — Machine Intelligence for Recycling Automation",
        epilog="""\
Examples:
  mira live --model mira_exp014_int8.tflite
  mira train --config experiments/exp014_yolo11n_multidataset.yaml
  mira train --model yolo11n.pt --dataset datasets/mira_v2/dataset.yaml --epochs 50
  mira merge --sources taco_trashnet roboflow warp --output datasets/mira_merged
  mira benchmark --models mira_exp014.pt mira_exp014_int8.tflite
  mira models
  mira experiments
  mira doctor
""",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--version", action="version", version=f"MIRA {__version__}")
    subparsers = parser.add_subparsers(dest="command", help="Available subcommands")

    for name, entry in get_commands().items():
        sub = subparsers.add_parser(name, help=entry.help_text)
        if entry.add_args:
            entry.add_args(sub)

    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        return

    commands = get_commands()
    if args.command in commands:
        try:
            commands[args.command].fn(args)
        except MiraError as e:
            logger.error(str(e))
            print(f"\nError: {e}")
            sys.exit(1)
        except KeyboardInterrupt:
            print("\nInterrupted by user.")
            sys.exit(130)
        except Exception as e:
            logger.exception(f"Unexpected error in command '{args.command}': {e}")
            print(f"\nUnexpected error: {e}")
            sys.exit(1)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
