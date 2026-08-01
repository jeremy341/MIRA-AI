"""CLI commands for diagnostics, config display, model listing, and benchmarking."""

import sys

from src.config import DEFAULT_CONF, ROOT_DIR
from src.version import __version__
from src.pipeline.registry import register_command


@register_command("doctor", "Run comprehensive environment and project health check")
def cmd_doctor(args):
    """Run a comprehensive health check of the MIRA environment."""
    from src.config import validate_config
    from src.deploy import check_environment, detect_hardware, suggest_model
    from src.pipeline.dataset import DatasetRegistry
    from src.pipeline.models import ModelRegistry

    print(f"\n  MIRA Doctor v{__version__}")
    print(f"  {'=' * 60}")

    # Config validation
    print("\n  [1/5] Configuration")
    config_errors = validate_config()
    if config_errors:
        print(f"    [!] {len(config_errors)} config error(s):")
        for e in config_errors:
            print(f"      - {e}")
    else:
        print("    [OK] mira.yaml is valid")

    # Hardware
    print("\n  [2/5] Hardware")
    info = detect_hardware()
    print(f"    Platform: {info.platform} ({info.arch})")
    print(f"    Memory: {info.memory_mb} MB")
    print(f"    CPUs: {info.cpu_count}")
    if info.has_cuda:
        print(f"    [OK] CUDA: {info.cuda_version}")
    else:
        print("    [!] No CUDA detected")
    print(f"    Suggested model: {suggest_model(info)}")

    # Environment
    print("\n  [3/5] Environment")
    env_warnings = check_environment()
    if env_warnings:
        for w in env_warnings:
            print(f"    ! {w}")
    else:
        print("    [OK] All required libraries available")

    # Models
    print("\n  [4/5] Models")
    registry = ModelRegistry()
    count = registry.discover()
    if count:
        print(f"    [OK] {count} model(s) discovered")
    else:
        print("    [!] No models found in models/detection/")

    # Datasets
    print("\n  [5/5] Datasets")
    ds_registry = DatasetRegistry()
    ds_count = ds_registry.discover()
    available = [s for s in ds_registry.list_sources() if s["exists"]]
    if available:
        print(f"    [OK] {len(available)}/{ds_count} dataset source(s) available")
        for s in available:
            print(f"      - {s['key']}: {s['name']}")
    else:
        print("    [!] No dataset sources available")

    print(f"\n  {'=' * 60}")
    if config_errors or env_warnings:
        print("  Status: ISSUES FOUND â€” see details above")
    else:
        print("  Status: HEALTHY")
    print()


def _add_config_args(parser):
    parser.add_argument(
        "--validate", action="store_true", help="Validate the configuration and check referenced paths."
    )


@register_command("config", "Display current project configuration", add_args=_add_config_args)
def cmd_config(args):
    """Display the current mira.yaml configuration."""
    import json

    from src.config import DETECTION_DIR, MODELS_DIR, PROJECT_CONFIG, ROOT_DIR, get_project_config, validate_config

    if args.validate:
        errors = validate_config()
        if errors:
            print("\n  Configuration errors:")
            for e in errors:
                print(f"    X {e}")
            print()
            sys.exit(1)

        print("\n  mira.yaml is valid")

        classes = PROJECT_CONFIG.get("classes", {})
        names = classes.get("names", [])
        print(f"  Classes: {', '.join(names)}")

        training = PROJECT_CONFIG.get("training", {})
        model = training.get("default_model", "yolo11n.pt")
        epochs = training.get("default_epochs", 120)
        batch = training.get("default_batch_size", 32)
        print(f"  Training: {model}, {epochs} epochs, batch {batch}")

        datasets_dir = ROOT_DIR / "datasets"
        if datasets_dir.exists():
            found = [
                d.name
                for d in datasets_dir.iterdir()
                if d.is_dir() and not d.name.startswith(".") and d.name != "registry"
            ]
            if found:
                print(f"  Datasets: {', '.join(found)}")
            else:
                print("  Datasets: none found")
        else:
            print("  Datasets: directory missing")

        if MODELS_DIR.exists():
            pt_count = len(list(DETECTION_DIR.glob("*.pt"))) if DETECTION_DIR.exists() else 0
            tflite_count = len(list(DETECTION_DIR.glob("*.tflite"))) if DETECTION_DIR.exists() else 0
            print(f"  Models: {pt_count} .pt, {tflite_count} .tflite")
        else:
            print("  Models: directory missing")

        print()
        return

    cfg = get_project_config()
    print("\n  Current MIRA Configuration (mira.yaml)")
    print(f"  {'=' * 50}")
    print(json.dumps(dict(cfg), indent=4))
    print()


@register_command("models", "List all discovered model files in the models/ directory")
def cmd_models(args):
    from src.pipeline.models import ModelRegistry

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
    import yaml as _yaml

    print(f"{'File':<50} {'Description'}")
    print("-" * 80)
    for p in yaml_files:
        with open(p, encoding="utf-8") as f:
            try:
                data = _yaml.safe_load(f)
            except _yaml.YAMLError as e:
                print(f"  Warning: Could not parse {p.name}: {e}")
                continue
        desc = (data or {}).get("name", (data or {}).get("model", ""))
        print(f"{p.name:<50} {desc}")


def _add_benchmark_args(parser):
    parser.add_argument("--models", type=str, nargs="+", required=True, help="Model paths to benchmark.")
    parser.add_argument("--dataset", type=str, default=None, help="Dataset YAML for evaluation (optional).")
    parser.add_argument(
        "--conf", type=float, default=DEFAULT_CONF, help=f"Confidence threshold (default: {DEFAULT_CONF})."
    )
    parser.add_argument("--max-images", type=int, default=100, help="Max images to evaluate (default: 100).")
    parser.add_argument("--output", type=str, default=None, help="Output path for benchmark report.")


@register_command("benchmark", "Benchmark multiple models for accuracy and latency", add_args=_add_benchmark_args)
def cmd_benchmark(args):
    from src.pipeline.benchmark import ModelBenchmark

    from .inference import resolve_detection_data_yaml

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
