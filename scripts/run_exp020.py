#!/usr/bin/env python3
"""Prepare and train EXP020 with Roboflow-dominant source weighting.

Typical local use:
    py -3 scripts/run_exp020.py --prepare-only
    py -3 scripts/run_exp020.py --train

The raw datasets are never modified. EXP020 is written to its own directory.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import random
import shutil
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUTPUT = ROOT / "datasets" / "exp020_roboflow_dominant"
CLASSES = ["glass", "metal", "paper", "plastic", "trash"]
SOURCE_SHARES = {"roboflow": 0.70, "taco": 0.20, "dmedhi": 0.05, "trashnet": 0.05}

sys.path.insert(0, str(ROOT / "scripts"))
from build_balanced_dataset import Record, load_all_records  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build and train the Roboflow-dominant MIRA EXP020.")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--prepare-only", action="store_true", help="Build the dataset but do not train.")
    group.add_argument("--train", action="store_true", help="Build the dataset and train YOLO11n.")
    parser.add_argument("--force", action="store_true", help="Replace the existing EXP020 output directory.")
    parser.add_argument("--train-images", type=int, default=6000, help="Number of training images (default: 6000).")
    parser.add_argument("--epochs", type=int, default=120)
    parser.add_argument("--batch", type=int, default=32)
    parser.add_argument("--imgsz", type=int, default=640)
    parser.add_argument("--device", default="auto", help="auto, cpu, 0, 1, ...")
    parser.add_argument("--output", type=Path, default=OUTPUT)
    return parser.parse_args()


def choose_records(records: list[Record], total: int, seed: int = 2026) -> list[Record]:
    """Choose a deterministic source-weighted training subset.

    Shares are image shares, deliberately making Roboflow the dominant source.
    If a source has fewer images than its quota, the remaining slots are filled
    from the other sources without changing the raw data.
    """
    rng = random.Random(seed)
    by_source: dict[str, list[Record]] = {}
    for record in records:
        by_source.setdefault(record.source, []).append(record)
    for source_records in by_source.values():
        rng.shuffle(source_records)

    # Largest-remainder to guarantee sum(requested) == total.
    # Use Fraction to avoid float tie-bias (e.g., 0.05*6000 float epsilon).
    from fractions import Fraction
    ideal_frac = {source: Fraction(str(share)) * total for source, share in SOURCE_SHARES.items()}
    base = {source: int(frac // 1) for source, frac in ideal_frac.items()}
    frac_part = {source: ideal_frac[source] - base[source] for source in ideal_frac}
    remainder = total - sum(base.values())
    order = list(SOURCE_SHARES.keys())
    frac_sorted = sorted(
        ideal_frac.keys(),
        key=lambda s: (frac_part[s], -order.index(s)),
        reverse=True,
    )
    for i in range(remainder):
        base[frac_sorted[i % len(frac_sorted)]] += 1
    requested = base
    if len(by_source.get("roboflow", [])) < requested["roboflow"]:
        raise RuntimeError(
            f"EXP020 needs at least {requested['roboflow']} Roboflow training images for the "
            f"70% policy, but only {len(by_source.get('roboflow', []))} are available. "
            "Add/restore Roboflow data or lower --train-images."
        )
    selected: list[Record] = []
    remaining = total
    for source, quota in requested.items():
        take = min(quota, len(by_source.get(source, [])))
        selected.extend(by_source.get(source, [])[:take])
        remaining -= take

    if remaining > 0:
        # Some source(s) short — warn that fallback changes effective ratios.
        short = {
            s: (requested[s], len(by_source.get(s, [])))
            for s in requested
            if len(by_source.get(s, [])) < requested[s]
        }
        msg = (
            f"Warning: fallback activated — requested mix {dict(requested)} could not be satisfied; "
            f"short sources {short}; filling {remaining} slots from remaining images (effective ratios will differ). "
        )
        print(msg, file=sys.stderr)
        import warnings
        warnings.warn(msg, UserWarning, stacklevel=2)
        unused = {
            source: items[requested.get(source, 0) :]
            for source, items in by_source.items()
            if len(items) > requested.get(source, 0)
        }
        fallback = [item for items in unused.values() for item in items]
        rng.shuffle(fallback)
        take_fallback = min(remaining, len(fallback))
        if take_fallback < remaining:
            print(f"Warning: fallback pool only has {len(fallback)} images but {remaining} needed; capping fallback to {take_fallback}.", file=sys.stderr)
        selected.extend(fallback[:take_fallback])
        remaining -= take_fallback

    if len(selected) < total:
        raise RuntimeError(
            f"Only {len(selected)} training images are available, but {total} were requested. "
            "Download/restore all source datasets first or lower --train-images."
        )
    return selected[:total]


def write_dataset(records: dict[str, list[Record]], output: Path, force: bool) -> dict[str, Counter]:
    if output.exists():
        if not force:
            raise FileExistsError(f"{output} already exists. Use --force to rebuild it.")
        shutil.rmtree(output)

    hashes: set[str] = set()
    counts: dict[str, Counter] = {split: Counter() for split in records}
    source_counts: dict[str, Counter] = {split: Counter() for split in records}
    manifest: list[dict[str, object]] = []
    # Track requested vs actual for dedup reporting.
    requested_totals: dict[str, int] = {split: len(srec) for split, srec in records.items()}
    requested_source_counts: dict[str, Counter] = {
        split: Counter(r.source for r in srec) for split, srec in records.items()
    }
    dropped_per_split: dict[str, int] = {split: 0 for split in records}
    # Cross-split dedup: preserve val/test over train by processing eval splits first.
    priority = ["val", "test", "train"]
    ordered_splits = [s for s in priority if s in records] + [s for s in records if s not in priority]
    for split in ordered_splits:
        split_records = records[split]
        image_dir = output / "images" / split
        label_dir = output / "labels" / split
        image_dir.mkdir(parents=True, exist_ok=True)
        label_dir.mkdir(parents=True, exist_ok=True)
        for index, record in enumerate(split_records):
            digest = hashlib.sha256(record.image.read_bytes()).hexdigest()
            if digest in hashes:
                dropped_per_split[split] += 1
                continue
            hashes.add(digest)
            stem = f"{record.source}_{getattr(record, 'source_split', getattr(record, 'split', 'unknown'))}_{index:06d}_{record.image.stem}"
            destination = image_dir / f"{stem}{record.image.suffix.lower()}"
            shutil.copy2(record.image, destination)
            (label_dir / f"{stem}.txt").write_text("\n".join(record.labels) + "\n", encoding="utf-8")
            counts[split].update(record.counts)
            source_counts[split][record.source] += 1
            manifest.append(
                {"split": split, "source": record.source, "source_id": record.source_id,
                 "image": str(destination.relative_to(output)), "sha256": digest}
            )

    (output / "manifest.jsonl").write_text(
        "\n".join(json.dumps(item) for item in manifest) + "\n", encoding="utf-8"
    )
    (output / "dataset.yaml").write_text(
        "train: images/train\nval: images/val\ntest: images/test\n"
        f"nc: 5\nnames: {CLASSES}\n",
        encoding="utf-8",
    )
    (output / "source_summary.json").write_text(
        json.dumps({split: dict(value) for split, value in source_counts.items()}, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"EXP020 dataset: {output}")
    for split in ("train", "val", "test"):
        actual = sum(source_counts[split].values())
        requested = requested_totals.get(split, actual)
        dropped = dropped_per_split.get(split, 0)
        extra = f" (requested {requested}, dropped {dropped} duplicates)" if dropped or requested != actual else ""
        print(f"  {split}: {actual} images | {dict(source_counts[split])} | requested {requested}{extra}")
        if requested_source_counts.get(split):
            if dict(requested_source_counts[split]) != dict(source_counts[split]):
                print(f"    requested sources: {dict(requested_source_counts[split])} -> actual {dict(source_counts[split])}")
    print(f"  train: {sum(source_counts['train'].values())} images | {dict(source_counts['train'])}")
    print(f"  val:   {sum(source_counts['val'].values())} images | {dict(source_counts['val'])}")
    print(f"  test:  {sum(source_counts['test'].values())} images | {dict(source_counts['test'])}")
    print(f"  train boxes: {dict(counts['train'])}")
    return source_counts


def prepare(args: argparse.Namespace) -> Path:
    try:
        all_records = load_all_records()
    except (FileNotFoundError, ImportError) as exc:
        raise RuntimeError(
            "Could not load the source datasets. Expected datasets/taco_raw, "
            "datasets/roboflow_raw, datasets/trashnet_labeled and datasets/raw/dmedhi."
        ) from exc

    train_candidates = [record for record in all_records if record.split == "train"]
    selected_train = choose_records(train_candidates, args.train_images)
    # Use every available held-out source split. This tests more than tabletop data.
    validation = [record for record in all_records if record.split == "val"]
    test = [record for record in all_records if record.split == "test"]
    write_dataset({"train": selected_train, "val": validation, "test": test}, args.output, args.force)
    return args.output / "dataset.yaml"


def train(args: argparse.Namespace, data_yaml: Path) -> None:
    try:
        import torch
        from ultralytics import YOLO
    except ImportError as exc:
        raise RuntimeError("Training needs ultralytics and torch. Install the project dependencies first.") from exc

    device = ("0" if torch.cuda.is_available() else "cpu") if args.device == "auto" else args.device
    run_dir = ROOT / "runs" / "exp020_roboflow_dominant"
    print(f"Training YOLO11n from scratch on device={device}")
    model = YOLO("yolo11n.pt")
    model.train(
        data=str(data_yaml), epochs=args.epochs, batch=args.batch, imgsz=args.imgsz,
        patience=30, device=device, project=str(run_dir.parent), name=run_dir.name,
        exist_ok=True, amp=device != "cpu", workers=4,
        optimizer="AdamW", lr0=0.001, lrf=0.01, weight_decay=0.0005,
        warmup_epochs=3, hsv_h=0.015, hsv_s=0.7, hsv_v=0.4,
        translate=0.1, scale=0.5, fliplr=0.5, mosaic=1.0, mixup=0.0, copy_paste=0.0,
        seed=2026,
    )
    metrics = model.val(data=str(data_yaml), split="val")
    print(f"EXP020 val mAP50: {metrics.box.map50:.4f}")
    print(f"EXP020 val mAP50-95: {metrics.box.map:.4f}")
    print("Exporting ONNX and INT8 TFLite...")
    model.export(format="onnx", imgsz=args.imgsz)
    model.export(format="tflite", int8=True, imgsz=args.imgsz, data=str(data_yaml))
    print(f"Finished. Weights and exports are under {run_dir / 'weights'}")


def main() -> None:
    args = parse_args()
    if not args.prepare_only and not args.train:
        args.prepare_only = True
    data_yaml = prepare(args)
    if args.train:
        train(args, data_yaml)


if __name__ == "__main__":
    main()
