from pathlib import Path

import pytest
import yaml

from src.pipeline import dataset


def write_descriptor(folder: Path, name: str, values: dict) -> Path:
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / name
    path.write_text(yaml.safe_dump(values), encoding="utf-8")
    return path


def test_label_directory_path_replaces_images_components():
    assert Path(dataset._derive_label_path("images/train/images")) == Path("labels/train/labels")
    assert dataset._derive_label_path("") == ""


def test_source_yaml_parses_mapping_and_uses_project_root(tmp_path):
    registry = tmp_path / "datasets" / "registry"
    descriptor = write_descriptor(
        registry,
        "sample.yaml",
        {
            "key": "sample",
            "name": "Sample",
            "source_format": "yolo",
            "input_path": "datasets/raw/sample",
            "class_mapping": {"4": 2},
        },
    )
    source = dataset.DatasetSource.from_yaml(descriptor)
    assert source.input_path == (tmp_path / "datasets" / "raw" / "sample").resolve()
    assert source.class_mapping == {4: 2}
    assert source.description == ""
    assert source.splits == {}
    assert source.stats == {}


def test_source_yaml_rejects_unknown_format_and_root_escape(tmp_path):
    registry = tmp_path / "datasets" / "registry"
    descriptor = write_descriptor(
        registry,
        "bad.yaml",
        {"key": "bad", "name": "Bad", "source_format": "folder-per-class", "input_path": "raw"},
    )
    with pytest.raises(ValueError, match="Unknown source_format"):
        dataset.DatasetSource.from_yaml(descriptor)
    descriptor = write_descriptor(
        registry,
        "escape.yaml",
        {"key": "bad", "name": "Bad", "source_format": "yolo", "input_path": "../../outside"},
    )
    with pytest.raises(ValueError, match="escapes project root"):
        dataset.DatasetSource.from_yaml(descriptor)


def test_discover_sorts_files_and_skips_bad_descriptors(tmp_path):
    registry = tmp_path / "registry"
    write_descriptor(registry, "b.yaml", {"key": "b", "name": "B", "source_format": "yolo", "input_path": "b"})
    write_descriptor(registry, "a.yaml", {"key": "a", "name": "A", "source_format": "yolo", "input_path": "a"})
    write_descriptor(registry, "bad.yaml", {"key": "bad"})
    found = dataset.DatasetRegistry(registry)
    assert found.discover() == 2
    assert list(found.sources) == ["a", "b"]
    assert [item["key"] for item in found.list_sources()] == ["a", "b"]
    with pytest.raises(KeyError, match="missing"):
        found.get_source("missing")


def test_merge_remapped_train_only_uses_80_20_split_and_counts(monkeypatch, tmp_path):
    registry = dataset.DatasetRegistry(tmp_path / "empty")
    source_dir = tmp_path / "source"
    image_dir = source_dir / "images" / "train"
    label_dir = source_dir / "labels" / "train"
    image_dir.mkdir(parents=True)
    label_dir.mkdir(parents=True)
    for stem in ["one", "two", "three", "four", "five"]:
        (image_dir / f"{stem}.jpg").write_bytes(stem.encode())
        (label_dir / f"{stem}.txt").write_text("0 0.5 0.5 0.2 0.2\n", encoding="utf-8")
    source = dataset.DatasetSource(
        "sample", "Sample", "", "yolo", source_dir, {"train": "images/train"}, {0: 1}
    )
    registry.sources["sample"] = source
    output = tmp_path / "merged"
    result = registry.merge(["sample"], output)
    assert result.sources_used == ["sample"]
    assert result.total_added == 5
    assert result.total_skipped == 0
    train_files = sorted((output / "images" / "train").glob("*.jpg"))
    val_files = sorted((output / "images" / "val").glob("*.jpg"))
    assert len(train_files) == 4
    assert len(val_files) == 1
    assert all((output / "labels" / split / f"{file.stem}.txt").read_text().startswith("1 ")
               for split in ("train", "val") for file in (output / "images" / split).glob("*.jpg"))
    assert (output / "dataset.yaml").read_text(encoding="utf-8").startswith("train: images/train\nval: images/val\n")


def test_merge_dry_run_does_not_create_output_or_add_samples(tmp_path):
    registry = dataset.DatasetRegistry(tmp_path / "empty")
    source_dir = tmp_path / "source"
    source = dataset.DatasetSource("sample", "Sample", "", "yolo", source_dir, {}, None)
    registry.sources["sample"] = source
    output = tmp_path / "dry"
    result = registry.merge(["sample"], output, dry_run=True)
    assert not output.exists()
    assert result.total_added == 0
    assert result.total_skipped == 0
    assert result.sources_used == ["sample"]


def test_coco_merge_formats_labels_and_keeps_image_inside_source(monkeypatch, tmp_path):
    import sys
    import types

    source_dir = tmp_path / "coco"
    image = source_dir / "images" / "valid"
    image.mkdir(parents=True)
    (image / "can.jpg").write_bytes(b"image")
    annotations = source_dir / "annotations.json"
    annotations.write_text("{}", encoding="utf-8")

    class FakeCOCO:
        def __init__(self, path):
            self.path = path

        def getImgIds(self):
            return [3]

        def loadImgs(self, image_id):
            return [{"file_name": "can.jpg", "width": 100, "height": 50}]

        def getAnnIds(self, imgIds):
            return [8]

        def loadAnns(self, annotation_ids):
            return [{"category_id": 2, "bbox": [10, 5, 20, 10]}]

    pycocotools = types.ModuleType("pycocotools")
    coco_module = types.ModuleType("pycocotools.coco")
    coco_module.COCO = FakeCOCO
    pycocotools.coco = coco_module
    monkeypatch.setitem(sys.modules, "pycocotools", pycocotools)
    monkeypatch.setitem(sys.modules, "pycocotools.coco", coco_module)
    registry = dataset.DatasetRegistry(tmp_path / "empty")
    registry.sources["coco"] = dataset.DatasetSource(
        "coco", "COCO", "", "coco", source_dir, {"valid": "annotations.json"}, {2: 4}
    )
    output = tmp_path / "out"
    result = registry.merge(["coco"], output)
    assert result.total_added == 1
    output_label = next((output / "labels" / "val").glob("*.txt"))
    assert output_label.read_text(encoding="utf-8") == "4 0.200000 0.200000 0.200000 0.200000\n"
    assert len(list((output / "images" / "val").glob("*.jpg"))) == 1


def test_coco_merge_without_optional_dependency_skips_source(monkeypatch, tmp_path):
    import builtins

    original_import = builtins.__import__

    def import_without_coco(name, *args, **kwargs):
        if name == "pycocotools.coco":
            raise ImportError("not installed")
        return original_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", import_without_coco)
    registry = dataset.DatasetRegistry(tmp_path / "empty")
    source_dir = tmp_path / "source"
    source = dataset.DatasetSource("coco", "COCO", "", "coco", source_dir, {}, None)
    registry.sources["coco"] = source
    result = registry.merge(["coco"], tmp_path / "out")
    assert result.total_added == 0
    assert result.total_skipped == 0
