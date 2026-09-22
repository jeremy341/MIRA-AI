"""Generate a Kaggle training notebook from experiment config."""

import argparse
import json
import sys
from pathlib import Path

from .common import (
    build_training_params as _build_training_params,
    code_cell as _code_cell,
    load_experiment_config as _load_experiment_config,
    load_project_config as _load_project_config,
    markdown_cell as _md_cell,
)


def generate_kaggle_notebook(exp: dict, project: dict) -> dict:
    params = _build_training_params(exp, project)
    classes = project.get("classes", {})
    class_names = classes.get("names", ["glass", "metal", "paper", "plastic", "trash"])
    num_classes = classes.get("count", len(class_names))
    exp_name = exp.get("name", "mira_exp")
    export_formats = exp.get("export", {}).get("formats", ["tflite_int8", "onnx"])

    augmentation_arguments = [f"{name}={value}" for name, value in params["augmentation"].items()]
    aug_lines = ",\n        ".join(augmentation_arguments)

    export_cells = ""
    if "tflite_int8" in export_formats:
        export_cells += (
            f'print("\\nExporting to TFLite INT8...")\n'
            f'model.export(format="tflite", int8=True, imgsz={params["imgsz"]})\n'
            'print("  TFLite INT8 exported")\n'
        )
    if "onnx" in export_formats:
        export_cells += f'model.export(format="onnx", imgsz={params["imgsz"]})\nprint("  ONNX exported")\n'

    notebook = {
        "nbformat": 4,
        "nbformat_minor": 5,
        "metadata": {
            "kaggle": {
                "accelerator": "GPU",
                "dataSources": [],
                "isGpuEnabled": True,
                "isInternetEnabled": True,
                "language": "python",
            },
            "kernelspec": {
                "display_name": "Python 3",
                "language": "python",
                "name": "python3",
            },
            "language_info": {
                "name": "python",
                "version": "3.11.0",
            },
        },
        "cells": [
            _md_cell(
                f"# MIRA Training - {exp_name}\n\n"
                f"YOLO11 training notebook for Kaggle GPU.\n\n"
                f"**Classes:** {class_names}\n"
                f"**Model:** {params['model']}\n"
                f"**Epochs:** {params['epochs']}"
            ),
            _code_cell(
                "# Install dependencies\n"
                "!pip install -q ultralytics\n\n"
                "import yaml\n"
                "from pathlib import Path\n"
                "from ultralytics import YOLO"
            ),
            _md_cell("## Dataset Setup"),
            _code_cell(
                "# Detect dataset in /kaggle/input\n"
                "input_dir = Path('/kaggle/input')\n"
                "data_root = None\n"
                "for d in input_dir.iterdir():\n"
                "    if d.is_dir() and (d / 'images').exists():\n"
                "        data_root = d\n"
                "        break\n"
                "if data_root is None:\n"
                "    # Search deeper\n"
                "    for d in input_dir.iterdir():\n"
                "        if d.is_dir():\n"
                "            for sub in d.rglob('images/train'):\n"
                "                if sub.is_dir():\n"
                "                    data_root = sub.parent.parent\n"
                "                    break\n"
                "        if data_root:\n"
                "            break\n"
                "assert data_root is not None, 'No dataset found in /kaggle/input'\n"
                "print(f'Using dataset: {data_root}')"
            ),
            _code_cell(
                "# Write dataset.yaml\n"
                "work_dir = Path('/kaggle/working')\n"
                "yaml_path = work_dir / 'dataset.yaml'\n"
                f'names_yaml = "[" + ", ".join(f"\'{{c}}\'" for c in {class_names}) + "]"\n'
                f"yaml_content = f'train: {{data_root}}/images/train\\nval: {{data_root}}/images/val\\nnc: {num_classes}\\nnames: {{names_yaml}}\\n'\n"
                "yaml_path.write_text(yaml_content.strip())\n"
                "print(f'Written: {yaml_path}')"
            ),
            _md_cell("## Training"),
            _code_cell(
                f"model = YOLO('{params['model']}')\n\n"
                f"model.train(\n"
                f"    data=str(yaml_path),\n"
                f"    epochs={params['epochs']},\n"
                f"    batch={params['batch_size']},\n"
                f"    imgsz={params['imgsz']},\n"
                f"    patience={params['patience']},\n"
                "    device='0',\n"
                f"    project=str(work_dir / 'runs'),\n"
                f"    name='{exp_name}',\n"
                "    exist_ok=True,\n"
                f"    amp={params['amp']},\n"
                f"    workers={params['workers']},\n"
                f"    lr0={params['lr0']},\n"
                f"    lrf={params['lrf']},\n"
                f"    momentum={params['momentum']},\n"
                f"    weight_decay={params['weight_decay']},\n"
                f"    warmup_epochs={params['warmup_epochs']},\n"
                f"    warmup_momentum={params['warmup_momentum']},\n"
                "    box=7.5,\n"
                "    cls=0.5,\n"
                "    dfl=1.5,\n"
                f"    {aug_lines},\n"
                ")"
            ),
            _md_cell("## Evaluation"),
            _code_cell(
                "metrics = model.val()\n"
                "print(f'mAP50:    {metrics.box.map50:.3f}')\n"
                "print(f'mAP50-95: {metrics.box.map:.3f}')"
            ),
            _md_cell("## Export"),
            _code_cell(export_cells.strip()),
            _md_cell("## Download from Kaggle"),
            _code_cell(
                "# The trained model is saved to /kaggle/working/runs/\n"
                "# Enable 'Internet' and 'GPU' in notebook settings.\n"
                "# After training, download the weights from the Output panel."
            ),
        ],
    }
    return notebook


def main(default_project_root: Path | None = None):
    parser = argparse.ArgumentParser(description="Generate a Kaggle training notebook")
    parser.add_argument("--config", type=str, required=True, help="Path to experiment YAML config")
    parser.add_argument(
        "--output", type=str, default=None, help="Output .ipynb path (default: <exp_name>_kaggle.ipynb)"
    )
    parser.add_argument("--project-root", type=str, default=None, help="Path to MIRA project root")
    args = parser.parse_args()

    config_path = Path(args.config)
    if not config_path.exists():
        print(f"Error: Config not found: {config_path}", file=sys.stderr)
        sys.exit(1)

    if args.project_root:
        project_root = Path(args.project_root)
    elif default_project_root is not None:
        project_root = default_project_root
    else:
        project_root = Path(__file__).resolve().parent.parent.parent

    project_config = _load_project_config(project_root)
    experiment_config = _load_experiment_config(config_path)

    notebook = generate_kaggle_notebook(experiment_config, project_config)

    if args.output:
        output_path = Path(args.output)
    else:
        experiment_name = experiment_config.get("name", "mira_exp")
        output_path = Path(f"{experiment_name}_kaggle.ipynb")

    notebook_json = json.dumps(notebook, indent=1)
    output_path.write_text(notebook_json, encoding="utf-8")
    print(f"Kaggle notebook generated: {output_path}")


if __name__ == "__main__":
    main()
