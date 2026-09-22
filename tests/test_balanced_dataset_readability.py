import hashlib
import json
import random
from collections import Counter
from pathlib import Path

import pytest

from scripts import build_balanced_dataset as builder


def make_record(source: str, split: str, name: str, class_ids: list[int], folder: Path):
    image = folder / name
    image.parent.mkdir(parents=True, exist_ok=True)
    image.write_bytes((source + name).encode())
    labels = tuple(f"{class_id} 0.500000 0.500000 0.200000 0.200000" for class_id in class_ids)
    return builder.Record(source, split, name, image, labels)


def test_remap_and_valid_lines_keep_their_distinct_text_rules():
    lines = [
        "2 .5 .5 .2 .2 9",
        "2 NaN .5 .2 .2",
        "9 .5 .5 .2 .2",
        "broken",
    ]
    assert builder.remap_lines(lines, {2: 4}) == ("4 .5 .5 .2 .2",)
    assert builder.valid_lines(lines) == ("2 .5 .5 .2 .2 9", "9 .5 .5 .2 .2")


def test_yolo_records_require_known_image_extension_paired_label_and_valid_rows(tmp_path):
    images = tmp_path / "images"
    labels = tmp_path / "labels"
    images.mkdir()
    labels.mkdir()
    (images / "good.JPG").write_bytes(b"good")
    (labels / "good.txt").write_text("1 .1 .2 .3 .4 extra\n-1 .2 .3 .4 .5\n", encoding="utf-8")
    (images / "missing.png").write_bytes(b"no label")
    (images / "unknown.gif").write_bytes(b"unknown")
    records = builder.yolo_records("trashnet", "train", images, labels)
    assert len(records) == 1
    assert records[0].labels == ("1 .1 .2 .3 .4 extra",)
    assert records[0].source_id == "good.JPG"


def test_coco_records_maps_names_and_formats_normalized_boxes(tmp_path):
    image = tmp_path / "item.jpg"
    image.write_bytes(b"item")
    annotations = tmp_path / "annotations.json"
    annotations.write_text(
        json.dumps(
            {
                "categories": [{"id": 7, "name": "Can"}, {"id": 8, "name": "Ignored"}],
                "images": [{"id": 2, "file_name": "item.jpg", "width": 100, "height": 50}],
                "annotations": [
                    {"image_id": 2, "category_id": 7, "bbox": [10, 5, 20, 10]},
                    {"image_id": 2, "category_id": 8, "bbox": [0, 0, 1, 1]},
                ],
            }
        ),
        encoding="utf-8",
    )
    records = builder.coco_records("taco", "train", annotations, tmp_path, {"Can": 1})
    assert records[0].labels == ("1 0.200000 0.200000 0.200000 0.200000",)


def test_taco_split_is_seeded_and_uses_seventy_fifteen_fifteen(monkeypatch, tmp_path):
    root = tmp_path / "taco_raw" / "TACO-master" / "data"
    root.mkdir(parents=True)
    (root / "annotations.json").write_text("{}", encoding="utf-8")
    rows = [builder.Record("taco", "unsplit", str(i), Path(str(i)), ("0 .5 .5 .2 .2",)) for i in range(20)]
    monkeypatch.setattr(builder, "DATASETS", tmp_path)
    monkeypatch.setattr(builder, "coco_records", lambda *args: list(rows))
    expected = list(rows)
    random.Random(42).shuffle(expected)
    split_rows = builder.load_taco()
    assert [r.source_id for r in split_rows] == [r.source_id for r in expected]
    assert [r.split for r in split_rows].count("train") == 14
    assert [r.split for r in split_rows].count("val") == 3
    assert [r.split for r in split_rows].count("test") == 3


def test_balancing_keeps_seeded_stable_ties_and_whole_records():
    records = [
        builder.Record("source", "train", f"{class_id}-{index}", Path(f"{class_id}-{index}"), (f"{class_id} a b c d",))
        for class_id in range(5)
        for index in range(5)
    ]
    selected, counts, target = builder.balance_training(records)
    assert target == 5
    assert counts == Counter({class_id: 5 for class_id in range(5)})
    assert len({id(record) for record in selected}) == len(selected)
    rng = random.Random(42)
    expected = []
    for class_id in (0, 4, 2, 1, 3):
        candidates = [record for record in records if record.counts.get(class_id, 0)]
        rng.shuffle(candidates)
        expected.extend(record.source_id for record in candidates)
    assert [record.source_id for record in selected] == expected


def test_balance_missing_class_uses_fallback_target_and_returns_all_records(capsys):
    records = [builder.Record("source", "train", "one", Path("one"), ("0 a b c d",))]
    selected, counts, target = builder.balance_training(records)
    assert selected == records
    assert counts == Counter({0: 1})
    assert target == 1
    assert "cannot balance" in capsys.readouterr().out


def test_writer_deduplicates_across_splits_in_val_test_train_order(monkeypatch, tmp_path):
    output = tmp_path / "output"
    output.mkdir()
    (output / "stale.txt").write_text("old", encoding="utf-8")
    val = make_record("val", "val", "same.jpg", [0], tmp_path / "val")
    train_duplicate = builder.Record("train", "train", "dup", val.image, val.labels)
    test = make_record("test", "test", "unique.jpg", [2], tmp_path / "test")
    monkeypatch.setattr(builder, "OUTPUT", output)
    builder.write_dataset({"train": [train_duplicate], "test": [test], "val": [val]}, Counter({0: 1}), 1)
    manifest = [json.loads(line) for line in (output / "manifest.jsonl").read_text(encoding="utf-8").splitlines()]
    assert [entry["split"] for entry in manifest] == ["val", "test"]
    assert manifest[0]["sha256"] == hashlib.sha256(val.image.read_bytes()).hexdigest()
    assert (output / "dataset.yaml").read_text(encoding="utf-8") == (
        "train: images/train\nval: images/val\ntest: images/test\nnc: 5\nnames: ['glass', 'metal', 'paper', 'plastic', 'trash']\n"
    )
    assert not list((output / "images" / "train").iterdir())
    assert not (output / "stale.txt").exists()


def test_main_assigns_only_trashnet_validation_to_validation(monkeypatch):
    records = [
        builder.Record("trashnet", "val", "gold", Path("gold"), ("0 a b c d",)),
        builder.Record("taco", "val", "heldout", Path("heldout"), ("0 a b c d",)),
        builder.Record("roboflow", "test", "test", Path("test"), ("0 a b c d",)),
        builder.Record("trashnet", "train", "train", Path("train"), ("0 a b c d",)),
    ]
    captured = {}
    monkeypatch.setattr(builder, "load_all_records", lambda: records)
    monkeypatch.setattr(builder, "balance_training", lambda train: (train, Counter(), 1))
    monkeypatch.setattr(builder, "write_dataset", lambda splits, counts, target: captured.update(splits))
    builder.main()
    assert [r.source_id for r in captured["val"]] == ["gold"]
    assert [r.source_id for r in captured["test"]] == ["heldout", "test"]
    assert [r.source_id for r in captured["train"]] == ["train"]
