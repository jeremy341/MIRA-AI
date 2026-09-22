from pathlib import Path
import sys

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from src.notebooks.docker import (
    _build_training_params,
    generate_docker_compose,
    generate_dockerfile,
    generate_entrypoint,
    generate_train_script,
    main as _generate_main,
)
from src.notebooks.common import (
    load_experiment_config as _load_experiment_config,
    load_project_config as _load_project_config,
)

__all__ = [
    "_build_training_params",
    "_load_experiment_config",
    "_load_project_config",
    "generate_docker_compose",
    "generate_dockerfile",
    "generate_entrypoint",
    "generate_train_script",
    "main",
]


def main():
    _generate_main(_PROJECT_ROOT)


if __name__ == "__main__":
    main()
