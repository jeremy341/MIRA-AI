#!/usr/bin/env python3
"""Build a balanced MIRA dataset without train/test leakage.

Sources:
  - dmedhi (train/validation)
  - TACO (deterministic 70/15/15 split)
  - Roboflow (official train/valid/test splits)
  - SAM-labeled TrashNet (train/val — tabletop gold-standard splits)

Uses TrashNet's ground-level tabletop val as the primary validation set
and mixes TACO + Roboflow test splits for the final test set.

SortWaste is EXCLUDED — its street-level 95.9% plastic distribution
is incompatible with the tabletop robot-arm use case.

The output is written to ``datasets/merged_mira_balanced`` and includes a
manifest with source provenance for every copied sample.
"""

from __future__ import annotations

import hashlib
import json
import random
import shutil
from collections import Counter
from dataclasses import dataclass
from io import BytesIO
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
DATASETS = ROOT / "datasets"
OUTPUT = DATASETS / "merged_mira_balanced"
CLASSES = ["glass", "metal", "paper", "plastic", "trash"]
IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tiff"}

ROBOFLOW_MAP = {
    0: 1,
    1: 1,
    2: 1,
    3: 4,
    4: 0,
    5: 1,
    6: 4,
    7: 3,
    8: 2,
    9: 3,
    10: 4,
    11: 3,
    12: 1,
    13: 2,
    14: 2,
    15: 3,
    16: 3,
    17: 1,
    18: 4,
    19: 3,
    20: 0,
    21: 0,
    22: 0,
    23: 0,
    24: 2,
    25: 2,
    26: 1,
    27: 1,
    28: 1,
    29: 2,
    30: 2,
    31: 3,
    32: 3,
    33: 3,
    34: 3,
    35: 3,
    36: 2,
    37: 2,
    38: 2,
    39: 2,
    40: 2,
    41: 3,
    42: 3,
    43: 3,
    44: 3,
    45: 3,
    46: 3,
    47: 3,
    48: 3,
    49: 1,
    50: 4,
    51: 1,
    52: 4,
    53: 3,
    54: 3,
    55: 3,
    56: 3,
    57: 4,
    58: 2,
    59: 2,
    60: 3,
    61: 4,
    62: 4,
    63: 2,
}
TACO_MAP = {
    "Aluminium foil": 1,
    "Battery": 4,
    "Aluminium blister pack": 4,
    "Carded blister pack": 4,
    "Other plastic bottle": 3,
    "Clear plastic bottle": 3,
    "Glass bottle": 0,
    "Plastic bottle cap": 3,
    "Metal bottle cap": 1,
    "Broken glass": 0,
    "Food Can": 1,
    "Aerosol": 1,
    "Drink can": 1,
    "Toilet tube": 2,
    "Other carton": 2,
    "Egg carton": 2,
    "Drink carton": 2,
    "Corrugated carton": 2,
    "Meal carton": 2,
    "Pizza box": 2,
    "Paper cup": 2,
    "Disposable plastic cup": 3,
    "Foam cup": 3,
    "Glass cup": 0,
    "Other plastic cup": 3,
    "Food waste": 4,
    "Glass jar": 0,
    "Plastic lid": 3,
    "Metal lid": 1,
    "Other plastic": 3,
    "Magazine paper": 2,
    "Tissues": 2,
    "Wrapping paper": 2,
    "Normal paper": 2,
    "Paper bag": 2,
    "Plastified paper bag": 2,
    "Plastic film": 3,
    "Six pack rings": 3,
    "Garbage bag": 3,
    "Other plastic wrapper": 3,
    "Single-use carrier bag": 3,
    "Polypropylene bag": 3,
    "Crisp packet": 3,
    "Spread tub": 3,
    "Tupperware": 3,
    "Disposable food container": 3,
    "Foam food container": 3,
    "Other plastic container": 3,
    "Plastic gloves": 3,
    "Plastic glooves": 3,
    "Plastic utensils": 3,
    "Pop tab": 1,
    "Rope & strings": 4,
    "Scrap metal": 1,
    "Shoe": 4,
    "Squeezable tube": 3,
    "Plastic straw": 3,
    "Paper straw": 2,
    "Styrofoam piece": 3,
    "Unlabeled litter": 4,
    "Cigarette": 4,
}


@dataclass(frozen=True)
class Record:
    source: str
    split: str
    source_id: str
    image: Path
    labels: tuple[str, ...]

    @property
    def counts(self) -> Counter[int]:
        return Counter(int(line.split()[0]) for line in self.labels)


def remap_lines(lines: list[str], mapping: dict[int, int]) -> tuple[str, ...]:
    result = []
    for line in lines:
        fields = line.split()
        if len(fields) < 5:
            continue
        try:
            old_id = int(fields[0])
        except ValueError:
            continue
        if old_id in mapping:
            result.append(f"{mapping[old_id]} {' '.join(fields[1:5])}")
    return tuple(result)


def yolo_records(
    source: str, split: str, image_dir: Path, label_dir: Path, mapping: dict[int, int] | None = None
) -> list[Record]:
    records = []
    for image in sorted(image_dir.iterdir()):
        if image.suffix.lower() not in IMAGE_EXTS:
            continue
        label = label_dir / f"{image.stem}.txt"
        if not label.exists():
            continue
        lines = label.read_text(encoding="utf-8").splitlines()
        labels = (
            remap_lines(lines, mapping)
            if mapping is not None
            else tuple(line for line in lines if len(line.split()) >= 5)
        )
        if labels:
            records.append(Record(source, split, image.name, image, labels))
    return records


def coco_records(
    source: str, split: str, annotation_file: Path, image_root: Path, name_map: dict[str, int]
) -> list[Record]:
    data = json.loads(annotation_file.read_text(encoding="utf-8"))
    categories = {item["id"]: item["name"] for item in data["categories"]}
    image_info = {item["id"]: item for item in data["images"]}
    annotations: dict[int, list[dict]] = {}
    for annotation in data["annotations"]:
        annotations.setdefault(annotation["image_id"], []).append(annotation)

    records = []
    for image_id, info in image_info.items():
        image = image_root / info["file_name"]
        if not image.exists():
            continue
        labels = []
        for annotation in annotations.get(image_id, []):
            target = name_map.get(categories.get(annotation["category_id"], ""))
            if target is None:
                continue
            x, y, width, height = annotation["bbox"]
            if info["width"] <= 0 or info["height"] <= 0:
                continue
            labels.append(
                f"{target} {(x + width / 2) / info['width']:.6f} "
                f"{(y + height / 2) / info['height']:.6f} "
                f"{width / info['width']:.6f} {height / info['height']:.6f}"
            )
        if labels:
            records.append(Record(source, split, str(image_id), image, tuple(labels)))
    return records


def load_taco() -> list[Record]:
    root = DATASETS / "taco_raw" / "TACO-master" / "data"
    records = coco_records("taco", "unsplit", root / "annotations.json", root, TACO_MAP)
    random.Random(42).shuffle(records)
    n = len(records)
    return [
        Record(r.source, "train" if i < n * 0.70 else "val" if i < n * 0.85 else "test", r.source_id, r.image, r.labels)
        for i, r in enumerate(records)
    ]


def load_dmedhi() -> list[Record]:
    import pyarrow.parquet as parquet

    output = DATASETS / "raw" / "dmedhi" / "converted"
    records = []
    mapping = {"Glass": 0, "Metal": 1, "Paper": 2, "Cardboard": 2, "Plastic": 3, "Trash": 4, "Garbage": 4}
    for parquet_file, split in [
        ("train-00000-of-00001.parquet", "train"),
        ("validation-00000-of-00001.parquet", "val"),
    ]:
        table = parquet.read_table(DATASETS / "raw" / "dmedhi" / "data" / parquet_file)
        for index, row in enumerate(table.to_pylist()):
            target = mapping.get(row["class_name"])
            boxes = row["bbox"]
            if target is None or not boxes:
                continue
            image_data = row["image"]["bytes"]
            image = Image.open(BytesIO(image_data))
            image_path = output / split / f"dmedhi_{split}_{index:06d}.jpg"
            image_path.parent.mkdir(parents=True, exist_ok=True)
            if not image_path.exists():
                image.convert("RGB").save(image_path, "JPEG", quality=95)
            width, height = image.size
            labels = []
            for x, y, box_width, box_height in boxes:
                labels.append(
                    f"{target} {(x + box_width / 2) / width:.6f} "
                    f"{(y + box_height / 2) / height:.6f} "
                    f"{box_width / width:.6f} {box_height / height:.6f}"
                )
            records.append(Record("dmedhi", split, str(index), image_path, tuple(labels)))
    return records


def load_all_records() -> list[Record]:
    records = []
    records.extend(load_dmedhi())
    records.extend(load_taco())

    roboflow = DATASETS / "roboflow_raw"
    for source_split, output_split in (("train", "train"), ("valid", "val"), ("test", "test")):
        records.extend(
            yolo_records(
                "roboflow",
                output_split,
                roboflow / source_split / "images",
                roboflow / source_split / "labels",
                ROBOFLOW_MAP,
            )
        )

    trashnet = DATASETS / "trashnet_labeled"
    records.extend(yolo_records("trashnet", "train", trashnet / "images" / "train", trashnet / "labels" / "train"))
    records.extend(yolo_records("trashnet", "val", trashnet / "images" / "val", trashnet / "labels" / "val"))
    return records


def balance_training(records: list[Record]) -> tuple[list[Record], dict[int, int], int]:
    totals = Counter()
    for record in records:
        totals.update(record.counts)
    target = min(1800, min(totals.get(class_id, 0) for class_id in range(5)))

    rng = random.Random(42)
    selected_by_id: dict[int, Record] = {}
    counts = Counter()
    for class_id in (0, 4, 2, 1, 3):
        candidates = [record for record in records if class_id in record.counts and id(record) not in selected_by_id]
        rng.shuffle(candidates)
        candidates.sort(key=lambda record: (record.counts[class_id], sum(record.counts.values())))
        for record in candidates:
            if counts[class_id] >= target:
                break
            selected_by_id[id(record)] = record
            counts.update(record.counts)

    selected = list(selected_by_id.values())
    return selected, counts, target


def write_dataset(records_by_split: dict[str, list[Record]], requested_train_counts: Counter, target: int) -> None:
    if OUTPUT.exists():
        shutil.rmtree(OUTPUT)
    for split in ("train", "val", "test"):
        (OUTPUT / "images" / split).mkdir(parents=True, exist_ok=True)
        (OUTPUT / "labels" / split).mkdir(parents=True, exist_ok=True)

    manifest = []
    hashes: set[str] = set()
    copied = Counter()
    copied_boxes = {split: Counter() for split in records_by_split}
    for split, records in records_by_split.items():
        for index, record in enumerate(records):
            digest = hashlib.sha256(record.image.read_bytes()).hexdigest()
            if digest in hashes:
                continue
            hashes.add(digest)
            safe_stem = f"{record.source}_{record.split}_{index:06d}_{record.image.stem}"
            destination = OUTPUT / "images" / split / f"{safe_stem}{record.image.suffix.lower()}"
            shutil.copy2(record.image, destination)
            (OUTPUT / "labels" / split / f"{safe_stem}.txt").write_text(
                "\n".join(record.labels) + "\n", encoding="utf-8"
            )
            manifest.append(
                {
                    "split": split,
                    "source": record.source,
                    "source_split": record.split,
                    "source_id": record.source_id,
                    "image": str(destination.relative_to(OUTPUT)),
                    "labels": list(record.labels),
                    "sha256": digest,
                }
            )
            copied[split] += 1
            copied_boxes[split].update(record.counts)

    (OUTPUT / "manifest.jsonl").write_text("\n".join(json.dumps(item) for item in manifest) + "\n", encoding="utf-8")
    (OUTPUT / "dataset.yaml").write_text(
        f"train: images/train\nval: images/val\ntest: images/test\nnc: 5\nnames: {CLASSES}\n",
        encoding="utf-8",
    )
    print(f"Output: {copied['train']} train, {copied['val']} val, {copied['test']} test")
    print(f"Training target per class before deduplication: {target} boxes")
    print(f"Training boxes after deduplication: {dict(copied_boxes['train'])}")


def main() -> None:
    records = load_all_records()
    by_source = Counter(record.source for record in records)
    print("Loaded records:", dict(by_source))

    train_candidates = [r for r in records if r.split == "train"]
    # TrashNet val is the tabletop gold standard. Everything else is test.
    val_records = [r for r in records if r.split == "val" and r.source == "trashnet"]
    test_records = [r for r in records if r.split in ("val", "test") and r.source != "trashnet"]
    selected, counts, target = balance_training(train_candidates)
    print("Selected training sources:", dict(Counter(r.source for r in selected)))
    write_dataset({"train": selected, "val": val_records, "test": test_records}, counts, target)


if __name__ == "__main__":
    main()
