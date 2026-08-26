# Generate Docker training infrastructure from experiment config.

from __future__ import annotations
import argparse
import sys
from pathlib import Path
import yaml


def _load_experiment_config(config_path: Path) -> dict:
    try:
        with open(config_path, encoding="utf-8") as f:
            return yaml.safe_load(f)
    except yaml.YAMLError as e:
        print(f"Error: invalid YAML in {config_path}: {e}", file=sys.stderr)
        sys.exit(1)


def _load_project_config(project_root: Path) -> dict:
    try:
        with open(project_root / "mira.yaml", encoding="utf-8") as f:
            return yaml.safe_load(f)
    except yaml.YAMLError as e:
        print(f"Error: invalid YAML in mira.yaml: {e}", file=sys.stderr)
        sys.exit(1)


def _build_training_params(exp: dict, project: dict) -> dict:
    train = project.get("training", {})
    aug = exp.get("augmentation", train.get("augmentation", {}))

    return {
        "model": exp.get("model", train.get("default_model", "yolo11n.pt")),
        "epochs": exp.get("epochs", train.get("default_epochs", 120)),
        "batch_size": exp.get("batch_size", train.get("default_batch_size", 32)),
        "imgsz": exp.get("imgsz", train.get("default_imgsz", 640)),
        "lr0": exp.get("lr0", train.get("default_lr", 0.01)),
        "lrf": exp.get("lrf", 0.01),
        "momentum": exp.get("momentum", 0.937),
        "weight_decay": exp.get("weight_decay", 0.0005),
        "warmup_epochs": exp.get("warmup_epochs", 3),
        "warmup_momentum": exp.get("warmup_momentum", 0.8),
        "patience": exp.get("patience", train.get("early_stopping_patience", 30)),
        "workers": exp.get("workers", 4),
        "amp": exp.get("amp", True),
        "augmentation": aug,
    }


def generate_dockerfile(params: dict) -> str:
    return (
        "# MIRA Training - Dockerfile\n"
        "# Based on ultralytics/ultralytics:latest with CUDA support\n"
        "FROM ultralytics/ultralytics:latest\n"
        "\n"
        "WORKDIR /app\n"
        "\n"
        "# Copy training script\n"
        "COPY train.py .\n"
        "COPY entrypoint.sh .\n"
        "\n"
        "# Make entrypoint executable\n"
        "RUN chmod +x entrypoint.sh\n"
        "\n"
        'ENTRYPOINT ["./entrypoint.sh"]\n'
    )


def generate_entrypoint(params: dict, exp: dict) -> str:
    exp_name = exp.get("name", "mira_exp")
    aug = params.get("augmentation", {})
    if not isinstance(aug, dict):
        aug = {}
    aug_args = " ".join(f"{k}={v}" for k, v in aug.items())

    export_formats = exp.get("export", {}).get("formats", ["tflite_int8", "onnx"])
    export_lines = []
    if "tflite_int8" in export_formats:
        export_lines.append(
            f'echo "Exporting to TFLite INT8..."\n'
            f"yolo export model=runs/{exp_name}/weights/best.pt format=tflite int8=True imgsz={params['imgsz']}\n"
            'echo "  TFLite INT8 exported"'
        )
    if "onnx" in export_formats:
        export_lines.append(
            f"yolo export model=runs/{exp_name}/weights/best.pt format=onnx imgsz={params['imgsz']}\n"
            'echo "  ONNX exported"'
        )

    export_block = "\n\n".join(export_lines)

    nc = exp.get("nc", 5)
    names = exp.get("names", ["glass", "metal", "paper", "plastic", "trash"])

    lines = [
        "#!/bin/bash",
        "set -e",
        "",
        'echo "============================================"',
        f'echo "  MIRA Training - {exp_name}"',
        'echo "============================================"',
        'echo ""',
        "",
        "# Check for dataset",
        'DATASET_DIR="/data/dataset"',
        'if [ ! -d "$DATASET_DIR/images/train" ]; then',
        '    echo "ERROR: Dataset not found at $DATASET_DIR"',
        '    echo ""',
        '    echo "Mount your dataset directory to /data/dataset:"',
        "    echo '  docker run -v /path/to/your/dataset:/data/dataset ...'",
        '    echo ""',
        '    echo "Expected structure:"',
        "    echo '  dataset/'",
        "    echo '    images/train/*.jpg'",
        "    echo '    images/val/*.jpg'",
        "    echo '    labels/train/*.txt'",
        "    echo '    labels/val/*.txt'",
        "    exit 1",
        "fi",
        "",
        "# Write dataset.yaml",
        "cat > /tmp/dataset.yaml << EOF",
        "train: $DATASET_DIR/images/train",
        "val: $DATASET_DIR/images/val",
        f"nc: {nc}",
        f"names: {names}",
        "EOF",
        'echo "Dataset: $DATASET_DIR"',
        f'echo "Model: {params["model"]}"',
        f'echo "Epochs: {params["epochs"]}"',
        f'echo "Batch size: {params["batch_size"]}"',
        'echo ""',
        "",
        "# Run training",
        "yolo detect train \\",
        f"    model={params['model']} \\",
        "    data=/tmp/dataset.yaml \\",
        f"    epochs={params['epochs']} \\",
        f"    batch={params['batch_size']} \\",
        f"    imgsz={params['imgsz']} \\",
        f"    patience={params['patience']} \\",
        "    device='0' \\",
        "    project=runs \\",
        f"    name={exp_name} \\",
        "    exist_ok=True \\",
        f"    amp={str(params['amp']).lower()} \\",
        f"    workers={params['workers']} \\",
        f"    lr0={params['lr0']} \\",
        f"    lrf={params['lrf']} \\",
        f"    momentum={params['momentum']} \\",
        f"    weight_decay={params['weight_decay']} \\",
        f"    warmup_epochs={params['warmup_epochs']} \\",
        f"    warmup_momentum={params['warmup_momentum']} \\",
        "    box=7.5 cls=0.5 dfl=1.5 \\",
        f"    {aug_args}",
        "",
        'echo ""',
        'echo "Training complete!"',
        f'echo "Results: runs/{exp_name}/weights/"',
        "",
        "# Export models",
        export_block,
        "",
        'echo ""',
        'echo "Done! All weights saved to runs/' + exp_name + '/weights/"',
        f"ls -la runs/{exp_name}/weights/",
        "",
    ]
    return "\n".join(lines)


def generate_docker_compose() -> str:
    lines = [
        "# MIRA Training - Docker Compose with GPU support",
        "# Usage:",
        "#   docker compose up",
        "#   docker compose up --build",
        "#   docker compose down",
        "services:",
        "  training:",
        "    build:",
        "      context: .",
        "      dockerfile: Dockerfile",
        "    volumes:",
        "# Mount your dataset here",
        "      - ../datasets:/data/dataset",
        "# Mount output directory to save models",
        "      - ../models:/app/models",
        "      - ../runs:/app/runs",
        "    deploy:",
        "      resources:",
        "        reservations:",
        "          devices:",
        "            - driver: nvidia",
        "              count: all",
        "              capabilities: [gpu]",
        "    runtime: nvidia",
        "    environment:",
        "      - NVIDIA_VISIBLE_DEVICES=all",
        "      - NVIDIA_DRIVER_CAPABILITIES=compute,utility",
        "# Override command for custom behavior:",
        '#   command: ["yolo", "detect", "train", "model=yolo11n.pt", "data=/tmp/dataset.yaml", "epochs=50"]',
        "",
    ]
    return "\n".join(lines)


def generate_train_script(params: dict, exp: dict) -> str:
    exp_name = exp.get("name", "mira_exp")
    aug = params["augmentation"]

    aug_kwargs = ",\n        ".join(f"{k}={v}" for k, v in aug.items())

    lines = [
        '"""Train YOLO detection model inside Docker."""',
        "",
        "from pathlib import Path",
        "",
        "from ultralytics import YOLO",
        "",
        f'EXP_NAME = "{exp_name}"',
        f'MODEL = "{params["model"]}"',
        "DATASET = Path('/tmp/dataset.yaml')",
        "",
        "",
        "def main():",
        "    model = YOLO(MODEL)",
        "",
        "    model.train(",
        "        data=str(DATASET),",
        f"        epochs={params['epochs']},",
        f"        batch={params['batch_size']},",
        f"        imgsz={params['imgsz']},",
        f"        patience={params['patience']},",
        "        device=0,",
        '        project="runs",',
        "        name=EXP_NAME,",
        "        exist_ok=True,",
        f"        amp={params['amp']},",
        f"        workers={params['workers']},",
        f"        lr0={params['lr0']},",
        f"        lrf={params['lrf']},",
        f"        momentum={params['momentum']},",
        f"        weight_decay={params['weight_decay']},",
        f"        warmup_epochs={params['warmup_epochs']},",
        f"        warmup_momentum={params['warmup_momentum']},",
        "        box=7.5,",
        "        cls=0.5,",
        "        dfl=1.5,",
        f"        {aug_kwargs},",
        "    )",
        "",
        "    metrics = model.val()",
        "    print(f'mAP50:    {metrics.box.map50:.3f}')",
        "    print(f'mAP50-95: {metrics.box.map:.3f}')",
        "",
        "    # Export",
        f'    model.export(format="tflite", int8=True, imgsz={params["imgsz"]})',
        f'    model.export(format="onnx", imgsz={params["imgsz"]})',
        '    print("Export complete!")',
        "",
        "",
        'if __name__ == "__main__":',
        "    main()",
        "",
    ]
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Generate Docker training infrastructure")
    parser.add_argument("--config", type=str, required=True, help="Path to experiment YAML config")
    parser.add_argument("--output", type=str, default=None, help="Output directory (default: docker_<exp_name>/)")
    parser.add_argument("--project-root", type=str, default=None, help="Path to MIRA project root")
    args = parser.parse_args()

    config_path = Path(args.config)
    if not config_path.exists():
        print(f"Error: Config not found: {config_path}", file=sys.stderr)
        sys.exit(1)

    if args.project_root:
        project_root = Path(args.project_root)
    else:
        project_root = Path(__file__).resolve().parent.parent

    project_config = _load_project_config(project_root)
    exp_config = _load_experiment_config(config_path)

    params = _build_training_params(exp_config, project_config)

    if args.output:
        output_dir = Path(args.output)
    else:
        exp_name = exp_config.get("name", "mira_exp")
        output_dir = Path(f"docker_{exp_name}")

    output_dir.mkdir(parents=True, exist_ok=True)

    files = {
        "Dockerfile": generate_dockerfile(params),
        "docker-compose.yml": generate_docker_compose(),
        "train.py": generate_train_script(params, exp_config),
        "entrypoint.sh": generate_entrypoint(params, exp_config),
    }

    for name, content in files.items():
        path = output_dir / name
        path.write_text(content, encoding="utf-8")
        print(f"  Created: {path}")

    print(f"\nDocker infrastructure generated in: {output_dir}/")
    print(f"  cd {output_dir} && docker compose up --build")


if __name__ == "__main__":
    main()
