import json
from pathlib import Path

import pytest

from scripts.generate_colab import generate_colab_notebook
from scripts.generate_kaggle import generate_kaggle_notebook
from src.pipeline import merge_utils


def notebook_configurations():
    experiment = {
        "name": "readability-check",
        "model": "custom.pt",
        "epochs": 7,
        "augmentation": {"fliplr": 0.25},
        "export": {"formats": ["onnx"]},
    }
    project = {
        "classes": {"count": 2, "names": ["glass", "metal"]},
        "training": {"default_batch_size": 8},
    }
    return experiment, project


@pytest.mark.parametrize(
    ("generator", "training_heading", "export_command"),
    [
        (generate_colab_notebook, "## Mount Google Drive", 'model.export(format="onnx", imgsz=640)'),
        (generate_kaggle_notebook, "## Dataset Setup", 'model.export(format="onnx", imgsz=640)'),
    ],
)
def test_notebook_cells_keep_order_and_configuration_text(generator, training_heading, export_command):
    experiment, project = notebook_configurations()

    notebook = generator(experiment, project)
    markdown_cells = [
        "".join(cell["source"])
        for cell in notebook["cells"]
        if cell["cell_type"] == "markdown"
    ]
    all_code = "\n".join(
        "".join(cell["source"])
        for cell in notebook["cells"]
        if cell["cell_type"] == "code"
    )

    assert markdown_cells[0].startswith("# MIRA Training - readability-check")
    assert markdown_cells.index(training_heading) < markdown_cells.index("## Training")
    assert markdown_cells.index("## Training") < markdown_cells.index("## Evaluation")
    assert markdown_cells.index("## Evaluation") < markdown_cells.index("## Export")
    assert "epochs=7" in all_code
    assert "batch=8" in all_code
    assert "fliplr=0.25" in all_code
    assert export_command in all_code


def test_label_remapping_preserves_coordinate_text_and_reports_skipped_rows(tmp_path, capsys):
    label_path = tmp_path / "sample.txt"
    label_path.write_text(
        "2 0.100 0.20 0.3 0.4 extra\n"
        "5 0.1 0.2 0.3 0.4\n"
        "bad 0.1 0.2 0.3 0.4\n",
        encoding="utf-8",
    )

    remapped_lines = merge_utils.remap_label_file(label_path, {2: 1})

    assert remapped_lines == ["1 0.100 0.20 0.3 0.4 extra\n"]
    assert capsys.readouterr().err == (
        "Warning: 2 annotations skipped - no valid classes after remap\n"
    )


def test_train_split_uses_sorted_image_stems_and_seeded_shuffle(tmp_path):
    image_folder = tmp_path / "images"
    image_folder.mkdir()
    for stem in ("a", "b", "c", "d", "e"):
        (image_folder / f"{stem}.jpg").write_bytes(b"image")
    (image_folder / "ignore.gif").write_bytes(b"image")

    train_stems, validation_stems = merge_utils.create_split_from_train(image_folder)

    assert train_stems == ["d", "b", "c", "e"]
    assert validation_stems == ["a"]


def test_remapped_copy_copies_image_and_exact_label_file(tmp_path):
    source_images = tmp_path / "source" / "images"
    source_labels = tmp_path / "source" / "labels"
    output_images = tmp_path / "output" / "images"
    output_labels = tmp_path / "output" / "labels"
    source_images.mkdir(parents=True)
    source_labels.mkdir(parents=True)
    image_path = source_images / "sample.PNG"
    image_path.write_bytes(b"same image bytes")
    label_path = source_labels / "sample.txt"
    label_path.write_text("2 0.2 0.3 0.4 0.5\n", encoding="utf-8")

    added, skipped = merge_utils.copy_remapped_images(
        ["sample"], source_images, source_labels, output_images, output_labels, {2: 4}
    )

    assert (added, skipped) == (1, 0)
    assert (output_images / "sample.PNG").read_bytes() == b"same image bytes"
    assert (output_labels / "sample.txt").read_text(encoding="utf-8") == "4 0.2 0.3 0.4 0.5\n"


def test_serialization_json_output_has_stable_keys_and_indent(tmp_path):
    from src.serialization import serialize_result

    output_path = tmp_path / "nested" / "metrics.json"
    result_path = serialize_result({"score": 0.75}, output_path)

    assert result_path == output_path
    assert output_path.read_text(encoding="utf-8") == json.dumps(
        {"score": 0.75, "__schema_version__": "1.0"},
        indent=2,
    )
