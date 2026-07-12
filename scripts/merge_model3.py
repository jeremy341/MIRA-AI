#!/usr/bin/env py
"""Create a WaRP-only YOLO dataset (28 WaRP classes remapped to 5 MIRA classes).

Usage:
    py scripts/merge_model3.py
    py scripts/merge_model3.py --output-dir datasets/MyCustom
    py scripts/merge_model3.py --dry-run
"""
import argparse
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATASETS = ROOT / "datasets"
from warp_utils import WARP_MAPPING, WARP_DIR, create_warp_split, copy_remapped_images, add_warp_test_to_val, print_stats, write_dataset_yaml


def parse_args():
    p = argparse.ArgumentParser(description="Create WaRP-only YOLO dataset (28->5 remap)")
    p.add_argument("--output-dir", type=Path, default=DATASETS / "WaRP_only",
                   help="Output dataset directory")
    p.add_argument("--dry-run", action="store_true",
                   help="Preview stats without copying files")
    return p.parse_args()


def merge(args):
    OUTPUT_DIR = args.output_dir

    if args.dry_run:
        print("[DRY RUN] Would create WaRP-only dataset:")
        print(f"  Source: {WARP_DIR}")
        print(f"  Output: {OUTPUT_DIR}")
        return

    for split in ["train", "val"]:
        (OUTPUT_DIR / "images" / split).mkdir(parents=True, exist_ok=True)
        (OUTPUT_DIR / "labels" / split).mkdir(parents=True, exist_ok=True)

    print("Creating WaRP valid split from train (80/20)...")
    warp_train_stems, warp_val_stems = create_warp_split()
    print(f"  Train: {len(warp_train_stems)} | Val: {len(warp_val_stems)}")

    print("\nAdding WaRP (28 to 5 remap)...")
    added = 0
    skipped = 0
    for target_split, stems in [("train", warp_train_stems), ("val", warp_val_stems)]:
        a, s = copy_remapped_images(
            stems,
            WARP_DIR / "train" / "images",
            WARP_DIR / "train" / "labels",
            OUTPUT_DIR / "images" / target_split,
            OUTPUT_DIR / "labels" / target_split,
            WARP_MAPPING,
        )
        added += a
        skipped += s

    a, s = add_warp_test_to_val(OUTPUT_DIR, WARP_MAPPING)
    added += a
    skipped += s

    print(f"  Added: {added} images | Skipped: {skipped} annotations (unmapped)")
    print_stats(OUTPUT_DIR, "Model 3: WaRP only")
    write_dataset_yaml(OUTPUT_DIR)
    print("Done!")


if __name__ == "__main__":
    merge(parse_args())
