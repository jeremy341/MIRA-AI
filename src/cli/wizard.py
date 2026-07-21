import sys

from config import PROJECT_CONFIG
from pipeline.registry import register_command


def _add_wizard_args(parser):
    parser.add_argument("--auto-start", action="store_true", help="Skip confirmation and start training immediately.")


@register_command("wizard", "Interactive training setup wizard", add_args=_add_wizard_args)
def cmd_wizard(args):
    from deploy import detect_hardware
    from pipeline.dataset import DatasetRegistry

    print()
    print("=" * 50)
    print("  MIRA Training Wizard")
    print("=" * 50)
    print()

    training_cfg = PROJECT_CONFIG.get("training", {})
    default_model = training_cfg.get("default_model", "yolo11n.pt")
    default_epochs = training_cfg.get("default_epochs", 120)
    default_batch = training_cfg.get("default_batch_size", 32)

    # Step 1: Task selection
    print("Step 1: What do you want to train?")
    print("  [1] Detection model (YOLO)")
    print("  [2] Classifier model")
    while True:
        choice = input("  > ").strip()
        if choice in ("1", "2", ""):
            break
        print("  Please enter 1 or 2.")

    task = "detection" if choice in ("1", "") else "classifier"

    # Step 2: Dataset selection
    ds_registry = DatasetRegistry()
    ds_registry.discover()
    sources = ds_registry.list_sources()
    available_keys = [s["key"] for s in sources if s["exists"]]

    if not available_keys:
        print("\n  No datasets found. Run 'mira merge' first.")
        sys.exit(1)

    print("\nStep 2: Select a dataset")
    print(f"  Discovered datasets: {', '.join(available_keys)}")
    default_ds = available_keys[0]
    ds_choice = input(f"  Enter dataset key [{default_ds}]: ").strip() or default_ds

    if ds_choice not in available_keys:
        print(f"  Unknown dataset '{ds_choice}'. Available: {', '.join(available_keys)}")
        sys.exit(1)

    # Resolve dataset YAML path
    source = ds_registry.get_source(ds_choice)
    dataset_yaml = source.input_path / "dataset.yaml"
    if not dataset_yaml.exists():
        print(f"  Dataset YAML not found at {dataset_yaml}")
        sys.exit(1)

    # Step 3: Model config
    print("\nStep 3: Configure model")
    base_model = input(f"  Base model [{default_model}]: ").strip() or default_model

    # Step 4: Training parameters
    print("\nStep 4: Training parameters")
    hw = detect_hardware()
    gpu_status = "GPU available" if hw.has_cuda else "CPU only"
    print(f"  Auto-detected: {gpu_status} {'GPU' if hw.has_cuda else 'CPU'}")

    epochs_input = input(f"  Epochs [{default_epochs}]: ").strip()
    epochs = int(epochs_input) if epochs_input else default_epochs

    if hw.has_cuda:
        default_batch_gpu = default_batch
    else:
        default_batch_gpu = 8

    batch_input = input(f"  Batch size [{default_batch_gpu}]: ").strip()
    batch_size = int(batch_input) if batch_input else default_batch_gpu

    device = "0" if hw.has_cuda else "cpu"

    # Step 5: Export options
    print("\nStep 5: Export options")
    export_input = input("  Export formats (comma-separated, e.g. tflite_int8,onnx) [tflite_int8]: ").strip()
    export_formats = export_input if export_input else "tflite_int8"

    # Summary
    print()
    print("Ready to train! Review config:")
    print(f"  Task:       {task}")
    print(f"  Model:      {base_model}")
    print(f"  Dataset:    {ds_choice}")
    print(f"  Epochs:     {epochs}")
    print(f"  Batch size: {batch_size}")
    print(f"  Device:     {device}")
    print(f"  Export:     {export_formats}")
    print()

    if args.auto_start:
        confirm = "y"
    else:
        confirm = input("Start training? [Y/n]: ").strip().lower()

    if confirm in ("n", "no"):
        print("Aborted.")
        return

    print("\nTraining...")

    import argparse

    train_args = argparse.Namespace(
        config=None,
        model=base_model,
        dataset=str(dataset_yaml),
        epochs=epochs,
        batch_size=batch_size,
        name=None,
        device=device,
        data_dir=None,
        task=task,
        base_model="mobilenetv2",
        fine_tune=False,
        dry_run=False,
    )

    from cli.train import cmd_train

    cmd_train(train_args)
