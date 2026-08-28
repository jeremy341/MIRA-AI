# Tests for generated training notebooks.

from pathlib import Path

import pytest
import yaml

from scripts.generate_colab import generate_colab_notebook
from scripts.generate_kaggle import generate_kaggle_notebook


@pytest.mark.parametrize(
    ("generator", "yaml_location"),
    [
        (generate_kaggle_notebook, "/kaggle/working"),
        (generate_colab_notebook, "/content/dataset.yaml"),
    ],
)
def test_generated_dataset_yaml_cell_writes_parseable_yaml(tmp_path, generator, yaml_location):
    project = {"classes": {"count": 2, "names": ["glass", "metal"]}}
    notebook = generator({}, project)
    source = next(
        "".join(cell["source"])
        for cell in notebook["cells"]
        if cell["cell_type"] == "code" and "# Write dataset.yaml" in "".join(cell["source"])
    )

    output_path = tmp_path / "dataset.yaml"

    def mapped_path(value):
        if str(value) == yaml_location:
            return tmp_path if str(value).endswith("working") else output_path
        return Path(value)

    exec(source, {"Path": mapped_path, "data_root": tmp_path / "data"})

    parsed = yaml.safe_load(output_path.read_text(encoding="utf-8"))
    assert set(parsed) == {"train", "val", "nc", "names"}
    assert parsed["nc"] == 2
    assert parsed["names"] == ["glass", "metal"]
