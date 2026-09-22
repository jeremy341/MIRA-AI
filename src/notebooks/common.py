import sys
from pathlib import Path

import yaml


def load_experiment_config(config_path: Path) -> dict:
    try:
        with open(config_path, encoding="utf-8") as config_file:
            return yaml.safe_load(config_file)
    except yaml.YAMLError as error:
        print(f"Error: invalid YAML in {config_path}: {error}", file=sys.stderr)
        sys.exit(1)


def load_project_config(project_root: Path) -> dict:
    try:
        with open(project_root / "mira.yaml", encoding="utf-8") as config_file:
            return yaml.safe_load(config_file)
    except yaml.YAMLError as error:
        print(f"Error: invalid YAML in mira.yaml: {error}", file=sys.stderr)
        sys.exit(1)


def build_training_params(exp: dict, project: dict) -> dict:
    training_defaults = project.get("training", {})
    augmentation = exp.get("augmentation", training_defaults.get("augmentation", {}))

    return {
        "model": exp.get("model", training_defaults.get("default_model", "yolo11n.pt")),
        "epochs": exp.get("epochs", training_defaults.get("default_epochs", 120)),
        "batch_size": exp.get("batch_size", training_defaults.get("default_batch_size", 32)),
        "imgsz": exp.get("imgsz", training_defaults.get("default_imgsz", 640)),
        "lr0": exp.get("lr0", training_defaults.get("default_lr", 0.01)),
        "lrf": exp.get("lrf", 0.01),
        "momentum": exp.get("momentum", 0.937),
        "weight_decay": exp.get("weight_decay", 0.0005),
        "warmup_epochs": exp.get("warmup_epochs", 3),
        "warmup_momentum": exp.get("warmup_momentum", 0.8),
        "patience": exp.get("patience", training_defaults.get("early_stopping_patience", 30)),
        "workers": exp.get("workers", 4),
        "amp": exp.get("amp", True),
        "augmentation": augmentation,
    }


def notebook_cell_lines(source: str) -> list[str]:
    source_lines = source.split("\n")
    notebook_lines = []

    for line in source_lines[:-1]:
        notebook_lines.append(line + "\n")

    if source_lines[-1]:
        notebook_lines.append(source_lines[-1])

    return notebook_lines


def markdown_cell(source: str) -> dict:
    return {
        "cell_type": "markdown",
        "metadata": {},
        "source": notebook_cell_lines(source),
    }


def code_cell(source: str) -> dict:
    return {
        "cell_type": "code",
        "metadata": {},
        "source": notebook_cell_lines(source),
        "execution_count": None,
        "outputs": [],
    }
