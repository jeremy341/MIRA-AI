"""Merge ALL datasets: TACO + TrashNet + Roboflow + WaRP into one YOLO dataset.

Usage:
    py scripts/merge_dataset_model4.py
    py scripts/merge_dataset_model4.py --output-dir datasets/MyCustom
    py scripts/merge_dataset_model4.py --dry-run
"""
import argparse
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATASETS = ROOT / "datasets"
from warp_utils import WARP_MAPPING, WARP_DIR, create_warp_split, copy_remapped_images, add_warp_test_to_val
from class_mappings import ROBOFLOW_MAPPING

ROBOFLOW_DIR = DATASETS / "roboflow_raw"


def parse_args():
    p = argparse.ArgumentParser(description="Merge ALL datasets into one YOLO dataset")
    p.add_argument("--output-dir", type=Path, default=DATASETS / "mira_all",
                   help="Output dataset directory")
    p.add_argument("--dry-run", action="store_true",
                   help="Preview stats without copying files")
    return p.parse_args()


def merge(args):
    OUTPUT_DIR = args.output_dir

    if args.dry_run:
        print("[DRY RUN] Would merge ALL datasets:")
        print(f"  TACO+TrashNet: {DATASETS / 'mira_v2'}")
        print(f"  Roboflow:      {ROBOFLOW_DIR}")
        print(f"  WaRP:          {WARP_DIR}")
        print(f"  Output:        {OUTPUT_DIR}")
        return

    for split in ["train", "val"]:
        (OUTPUT_DIR / "images" / split).mkdir(parents=True, exist_ok=True)
        (OUTPUT_DIR / "labels" / split).mkdir(parents=True, exist_ok=True)

    # --- Step 1: Copy mira_v2 (TACO + TrashNet) ---
    print("Copying TACO + TrashNet (mira_v2)...")
    for split in ["train", "val"]:
        src_img = DATASETS / "mira_v2" / "images" / split
        src_lbl = DATASETS / "mira_v2" / "labels" / split
        dst_img = OUTPUT_DIR / "images" / split
        dst_lbl = OUTPUT_DIR / "labels" / split
        for img in src_img.glob("*"):
            shutil.copy2(img, dst_img / img.name)
        for lbl in src_lbl.glob("*"):
            shutil.copy2(lbl, dst_lbl / lbl.name)
        count = sum(1 for _ in (OUTPUT_DIR / "images" / split).glob("*"))
        print(f"  {split}: {count} images total")

    # --- Step 2: Add Roboflow (64->5 remap) ---
    print("\nAdding Roboflow Trash Detection (64 to 5 remap)...")
    roboflow_map = {"train": "train", "valid": "val", "test": "train"}
    added_robo = 0
    skipped_robo = 0

    for robo_split, target_split in roboflow_map.items():
        img_src = ROBOFLOW_DIR / robo_split / "images"
        lbl_src = ROBOFLOW_DIR / robo_split / "labels"
        dst_img = OUTPUT_DIR / "images" / target_split
        dst_lbl = OUTPUT_DIR / "labels" / target_split

        for lbl_file in lbl_src.glob("*.txt"):
            with open(lbl_file, "r") as f:
                lines = f.readlines()
            new_lines = []
            for line in lines:
                parts = line.split()
                if not parts:
                    continue
                old_id = int(parts[0])
                if old_id in ROBOFLOW_MAPPING:
                    new_id = ROBOFLOW_MAPPING[old_id]
                    new_lines.append(f"{new_id} {' '.join(parts[1:])}\n")
                else:
                    skipped_robo += 1
            if new_lines:
                img_file = img_src / f"{lbl_file.stem}.jpg"
                if not img_file.exists():
                    img_file = img_src / f"{lbl_file.stem}.png"
                if img_file.exists():
                    shutil.copy2(img_file, dst_img / img_file.name)
                    with open(dst_lbl / lbl_file.name, "w") as f:
                        f.writelines(new_lines)
                    added_robo += 1

    print(f"  Added: {added_robo} images | Skipped: {skipped_robo}")

    # --- Step 3: Add WaRP (28->5 remap) ---
    print("\nCreating WaRP valid split from train (80/20)...")
    warp_train_stems, warp_val_stems = create_warp_split()
    print(f"  Train: {len(warp_train_stems)} | Val: {len(warp_val_stems)}")

    print("\nAdding WaRP (28 to 5 remap)...")
    added_warp = 0
    skipped_warp = 0
    for target_split, stems in [("train", warp_train_stems), ("val", warp_val_stems)]:
        a, s = copy_remapped_images(
            stems,
            WARP_DIR / "train" / "images",
            WARP_DIR / "train" / "labels",
            OUTPUT_DIR / "images" / target_split,
            OUTPUT_DIR / "labels" / target_split,
            WARP_MAPPING,
        )
        added_warp += a
        skipped_warp += s

    a, s = add_warp_test_to_val(OUTPUT_DIR, WARP_MAPPING)
    added_warp += a
    skipped_warp += s

    print(f"  Added: {added_warp} images | Skipped: {skipped_warp}")

    # --- Step 4: Stats ---
    from warp_utils import print_stats, write_dataset_yaml
    print_stats(OUTPUT_DIR, "Model 4: All (TACO + TrashNet + Roboflow + WaRP)")
    write_dataset_yaml(OUTPUT_DIR)
    print("Done!")


if __name__ == "__main__":
    merge(parse_args())
