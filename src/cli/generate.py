"""CLI command for generating cloud training notebooks and Docker infrastructure."""

import sys
from pathlib import Path

from src.config import ROOT_DIR
from src.pipeline.registry import register_command

_GENERATE_PARSER = None


def _add_generate_args(parser):
    global _GENERATE_PARSER
    _GENERATE_PARSER = parser
    sub = parser.add_subparsers(dest="target", help="Target platform to generate for")

    kaggle = sub.add_parser("kaggle", help="Generate a Kaggle training notebook")
    kaggle.add_argument("--config", type=str, required=True, help="Path to experiment YAML config")
    kaggle.add_argument("--output", type=str, default=None, help="Output .ipynb path")
    kaggle.add_argument("--project-root", type=str, default=None, help="Path to MIRA project root")

    colab = sub.add_parser("colab", help="Generate a Google Colab training notebook")
    colab.add_argument("--config", type=str, required=True, help="Path to experiment YAML config")
    colab.add_argument("--output", type=str, default=None, help="Output .ipynb path")
    colab.add_argument("--project-root", type=str, default=None, help="Path to MIRA project root")

    docker = sub.add_parser("docker", help="Generate Docker training infrastructure")
    docker.add_argument("--config", type=str, required=True, help="Path to experiment YAML config")
    docker.add_argument("--output", type=str, default=None, help="Output directory")
    docker.add_argument("--project-root", type=str, default=None, help="Path to MIRA project root")


@register_command("generate", "Generate cloud training scripts (kaggle, colab, docker)", add_args=_add_generate_args)
def cmd_generate(args):
    if args.target is None:
        if _GENERATE_PARSER:
            _GENERATE_PARSER.print_help()
        return
    target = args.target
    config_path = Path(args.config)
    if not config_path.exists():
        print(f"Error: Config not found: {config_path}")
        sys.exit(1)

    project_root = Path(args.project_root) if args.project_root else ROOT_DIR

    import yaml

    if not config_path.exists():
        print(f"Error: Config file not found: {config_path}")
        sys.exit(1)
    with open(config_path, encoding="utf-8") as f:
        exp_config = yaml.safe_load(f)
    mira_yaml_path = project_root / "mira.yaml"
    if not mira_yaml_path.exists():
        print(f"Error: Project config not found: {mira_yaml_path}")
        sys.exit(1)
    with open(mira_yaml_path, encoding="utf-8") as f:
        project_config = yaml.safe_load(f)

    if target == "kaggle":
        from scripts.generate_kaggle import generate_kaggle_notebook

        notebook = generate_kaggle_notebook(exp_config, project_config)
        import json

        out = Path(args.output) if args.output else Path(f"{exp_config.get('name', 'mira_exp')}_kaggle.ipynb")
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(notebook, indent=1), encoding="utf-8")
        print(f"Kaggle notebook generated: {out}")

    elif target == "colab":
        from scripts.generate_colab import generate_colab_notebook

        notebook = generate_colab_notebook(exp_config, project_config)
        import json

        out = Path(args.output) if args.output else Path(f"{exp_config.get('name', 'mira_exp')}_colab.ipynb")
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(notebook, indent=1), encoding="utf-8")
        print(f"Colab notebook generated: {out}")

    elif target == "docker":
        from scripts.generate_docker import (
            _build_training_params,
            generate_docker_compose,
            generate_dockerfile,
            generate_entrypoint,
            generate_train_script,
        )

        params = _build_training_params(exp_config, project_config)
        out_dir = Path(args.output) if args.output else Path(f"docker_{exp_config.get('name', 'mira_exp')}")
        out_dir.mkdir(parents=True, exist_ok=True)

        files = {
            "Dockerfile": generate_dockerfile(params),
            "docker-compose.yml": generate_docker_compose(),
            "train.py": generate_train_script(params, exp_config),
            "entrypoint.sh": generate_entrypoint(params, exp_config),
        }
        for name, content in files.items():
            (out_dir / name).write_text(content, encoding="utf-8")
            print(f"  Created: {out_dir / name}")
        print(f"\nDocker infrastructure generated in: {out_dir}/")
    else:
        print(f"Unknown target: {target}")
        sys.exit(1)

