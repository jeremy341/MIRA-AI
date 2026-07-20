import argparse
import pathlib
import subprocess
import sys
from pathlib import Path

_src_dir = str(Path(__file__).resolve().parent)
if _src_dir not in sys.path:
    sys.path.insert(0, _src_dir)

_scripts_dir = str(Path(_src_dir).parent / "scripts")
if _scripts_dir not in sys.path:
    sys.path.insert(0, _scripts_dir)

from version import __version__
from config import (
    DETECTION_DIR,
    REF_DIR,
    REJECT_THRESHOLD,
    ROOT_DIR,
    SCRIPT_DIR,
    get_detection_models,
    get_tflite_imgsz,
)
from model_picker import pick_model
from pipeline.registry import get_commands, register_command
from pipeline.models import ModelRegistry


def run_script(script_path, args_list=None):
    if not script_path.exists():
        raise FileNotFoundError(f"Script not found at {script_path}")
    cmd = [sys.executable, str(script_path)]
    if args_list:
        cmd.extend(args_list)
    subprocess.run(cmd, check=True)


def resolve_detection_data_yaml(explicit_path=None):
    candidates = []
    if explicit_path:
        candidate = pathlib.Path(explicit_path).expanduser()
        if not candidate.is_absolute():
            candidate = (ROOT_DIR / candidate).resolve()
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
        "Could not find a YOLO dataset YAML. "
        "Please specify one with --data or generate a dataset using `mira merge`."
    )


def _pick_model_interactive(title="Available models"):
    """Show interactive picker for detection models. Returns model name or None."""
    registry = ModelRegistry()
    registry.discover()
    models = registry.list_models()
    labels = {m["name"]: m["label"] for m in models}
    return pick_model([m["name"] for m in models], labels=labels, title=title)


# ── Legacy / Script Commands ─────────────────────────────────────────


@register_command("data-build", "[DEPRECATED] Use mira merge instead")
def cmd_data_build(args):
    print("[DEPRECATED] This command is no longer available.")
    print("Use 'mira merge' to merge dataset sources.")
    print("Example: mira merge --sources taco_trashnet roboflow warp --output datasets/mira_merged")


@register_command("data-viz", "Visualize dataset distribution and sample grids")
def cmd_data_viz(args):
    run_script(ROOT_DIR / "scripts" / "visualize_classifier_dataset.py")


@register_command("train-baseline", "Train baseline CNN classification model (EXP-001)")
def cmd_train_baseline(args):
    run_script(REF_DIR / "train_classifier_baseline.py")


@register_command("train-transfer", "Train frozen MobileNetV2 classification model (EXP-002)")
def cmd_train_transfer(args):
    run_script(REF_DIR / "train_classifier_transfer.py")


@register_command("train-tune", "Train fine-tuned MobileNetV2 classification model (EXP-003)")
def cmd_train_tune(args):
    run_script(REF_DIR / "train_classifier_finetune.py")


@register_command("train-detection", "Initiate local YOLOv8 training pipeline (legacy)")
def cmd_train_detection(args):
    run_script(REF_DIR / "train_detector.py")


@register_command("quant-class", "Execute Keras post-training quantization (EXP-004)")
def cmd_quant_class(args):
    run_script(REF_DIR / "quantize_classifier.py")


@register_command("quant-yolo", "Execute YOLOv8 quantization")
def cmd_quant_yolo(args):
    run_script(REF_DIR / "quantize_detector.py")


@register_command("field-bench", "Field benchmark: capture real images, test all models, compare accuracy")
def cmd_field_bench(args):
    run_script(SCRIPT_DIR / "field_benchmark.py")


# ── Commands with arguments ──────────────────────────────────────────


def _add_eval_class_args(parser):
    parser.add_argument("--model", type=str, required=True, help="Model filename in /models")
    parser.add_argument("--exp", type=str, required=True, help="Experiment folder name")


@register_command("eval-class", "Evaluate classification models (EXP-001 - EXP-004)", add_args=_add_eval_class_args)
def cmd_eval_class(args):
    run_script(REF_DIR / "evaluate_classifier.py", ["--model", args.model, "--exp", args.exp])


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
    parser.add_argument("--data-dir", type=str, default=None, help="Data directory for classifier training (default: data/classes).")
    parser.add_argument("--task", type=str, default="detection", choices=["detection", "classifier"],
                        help="Training task: detection (YOLO) or classifier (MobileNetV2).")
    parser.add_argument("--base-model", type=str, default="mobilenetv2",
                        help="Base model for classifier training (mobilenetv2, custom_cnn).")
    parser.add_argument("--fine-tune", action="store_true",
                        help="Enable fine-tuning for classifier training.")


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

        with open(p) as f:
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


@register_command("export", "Export a trained .pt model to TFLite / ONNX", add_args=_add_export_args)
def cmd_export(args):
    from pipeline.train import TrainingPipeline

    pipeline = TrainingPipeline()
    exported = pipeline.export_model(args.model, args.formats, args.dataset)
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
    print(f"\n  Hardware Diagnostics")
    print(f"  {'=' * 50}")
    print(f"  Platform:     {info.platform} ({info.arch})")
    print(f"  Python:       {info.python_version.split()[0]}")
    print(f"  CPU cores:    {info.cpu_count}")
    print(f"  Memory:       {info.memory_mb} MB")
    if info.is_raspberry_pi:
        print(f"  Model:        Raspberry Pi ({info.pi_model})")
    if info.is_jetson:
        print(f"  Model:        NVIDIA Jetson")
    print(f"  CUDA:         {'Yes (' + info.cuda_version + ')' if info.has_cuda else 'No'}")
    print(f"  PyTorch:      {'Yes' if info.has_torch else 'No'}")
    print(f"  TensorFlow:   {'Yes' if info.has_tensorflow else 'No'}")
    print(f"  TFLite:       {'Yes' if info.has_tflite_runtime else 'No'}")
    print(f"\n  Suggested model: {suggest_model(info)}")

    warnings = check_environment()
    if warnings:
        print(f"\n  Warnings:")
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
        print(f"\n  Class distribution:")
        for cls_id, count in sorted(result.class_counts.items()):
            print(f"    class {cls_id}: {count} instances")

    if result.warnings:
        print(f"\n  Warnings:")
        for w in result.warnings:
            print(f"    ! {w}")

    if result.errors:
        print(f"\n  Errors:")
        for e in result.errors:
            print(f"    ! {e}")

    if result.orphaned_labels:
        print(f"\n  Orphaned labels ({len(result.orphaned_labels)}):")
        for p in result.orphaned_labels[:5]:
            print(f"    {p}")
        if len(result.orphaned_labels) > 5:
            print(f"    ... and {len(result.orphaned_labels) - 5} more")

    print()


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
        commands[args.command].fn(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
