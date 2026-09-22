from pathlib import Path
import sys

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from src.notebooks.kaggle import generate_kaggle_notebook, main as _generate_main
from src.notebooks.common import (
    build_training_params as _build_training_params,
    code_cell as _code_cell,
    load_experiment_config as _load_experiment_config,
    load_project_config as _load_project_config,
    markdown_cell as _md_cell,
    notebook_cell_lines as _cell_lines,
)

__all__ = [
    "_build_training_params",
    "_cell_lines",
    "_code_cell",
    "_load_experiment_config",
    "_load_project_config",
    "_md_cell",
    "generate_kaggle_notebook",
    "main",
]


def main():
    _generate_main(_PROJECT_ROOT)


if __name__ == "__main__":
    main()
