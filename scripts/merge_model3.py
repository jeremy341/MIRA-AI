#!/usr/bin/env py
"""Create a WaRP-only YOLO dataset (28 WaRP classes remapped to 5 MIRA classes).

Usage:
    py scripts/merge_model3.py
    py scripts/merge_model3.py --output-dir datasets/MyCustom
    py scripts/merge_model3.py --dry-run
"""
import argparse
import shutil
import random
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATASETS = ROOT / "datasets"

# WaRP 28 classes (0-indexed) -> 5 MIRA classes
# Based on datasets/WaRP/Warp-D/classes.txt
# 0:glass, 1:metal, 2:paper, 3:plastic, 4:trash
WARP_MAPPING = {
    # Glass
    1: 0, 2: 0, 17: 0, 18: 0, 25: 0, 26: 0, 27: 0,
    # Metal
    8: 1,
    # Paper
    9: 2, 10: 2, 13: 2,
    # Plastic
    0: 3, 3: 3, 4: 3, 5: 3, 6: 3, 7: 3, 11: 3, 12: 3, 14: 3,
    15: 3, 16: 3, 19: 3, 20: 3, 21: 3, 22: 3, 23: 3, 24: 3,
    # Trash: none in this dataset
}


def parse_args():
    p = argparse.ArgumentParser(description="Create WaRP-only YOLO dataset (28->5 remap)")
    p.add_argument("--output-dir", type=Path, default=DATASETS / "WaRP_only",
                   help="Output dataset directory")
    p.add_argument("--dry-run", action="store_true",
                   help="Preview stats without copying files")
    return p.parse_args()


def merge(args):
    WARP_DIR = DATASETS / "WaRP" / "Warp-D"
    OUTPUT_DIR = args.output_dir

    if args.dry_run:
        print("[DRY RUN] Would create WaRP-only dataset:")
        print(f"  Source: {WARP_DIR}")
        print(f"  Output: {OUTPUT_DIR}")
        return

    # Create output structure
    for split in ["train", "val"]:
        (OUTPUT_DIR / "images" / split).mkdir(parents=True, exist_ok=True)
        (OUTPUT_DIR / "labels" / split).mkdir(parents=True, exist_ok=True)

    # --- Step 1: Create valid split from WaRP train (80/20) ---
    print("Creating WaRP valid split from train (80/20)...")
    warp_train_imgs = WARP_DIR / "train" / "images"
    warp_train_lbls = WARP_DIR / "train" / "labels"
    all_warp_files = sorted([f.stem for f in warp_train_imgs.glob("*")])
    random.seed(42)
    random.shuffle(all_warp_files)
    split_idx = int(len(all_warp_files) * 0.8)
    warp_train_stems = all_warp_files[:split_idx]
    warp_val_stems = all_warp_files[split_idx:]
    print(f"  Train: {len(warp_train_stems)} | Val: {len(warp_val_stems)}")

    # --- Step 2: Add WaRP train (28->5 remap) -> train ---
    print("\nAdding WaRP (28 to 5 remap)...")
    added = 0
    skipped = 0

    for target_split, stems in [("train", warp_train_stems), ("val", warp_val_stems)]:
        dst_img = OUTPUT_DIR / "images" / target_split
        dst_lbl = OUTPUT_DIR / "labels" / target_split
        for stem in stems:
            lbl_file = warp_train_lbls / f"{stem}.txt"
            if not lbl_file.exists():
                continue
            with open(lbl_file, "r") as f:
                lines = f.readlines()
            new_lines = []
            for line in lines:
                parts = line.split()
                if not parts:
                    continue
                old_id = int(parts[0])
                if old_id in WARP_MAPPING:
                    new_id = WARP_MAPPING[old_id]
                    new_lines.append(f"{new_id} {' '.join(parts[1:])}\n")
                else:
                    skipped += 1
            if new_lines:
                img_file = warp_train_imgs / f"{stem}.jpg"
                if not img_file.exists():
                    img_file = warp_train_imgs / f"{stem}.png"
                if img_file.exists():
                    shutil.copy2(img_file, dst_img / img_file.name)
                    with open(dst_lbl / lbl_file.name, "w") as f:
                        f.writelines(new_lines)
                    added += 1

    # Also add WaRP test split -> val
    warp_test_imgs = WARP_DIR / "test" / "images"
    warp_test_lbls = WARP_DIR / "test" / "labels"
    if warp_test_lbls.exists():
        for lbl_file in warp_test_lbls.glob("*.txt"):
            with open(lbl_file, "r") as f:
                lines = f.readlines()
            new_lines = []
            for line in lines:
                parts = line.split()
                if not parts:
                    continue
                old_id = int(parts[0])
                if old_id in WARP_MAPPING:
                    new_id = WARP_MAPPING[old_id]
                    new_lines.append(f"{new_id} {' '.join(parts[1:])}\n")
                else:
                    skipped += 1
            if new_lines:
                img_file = warp_test_imgs / f"{lbl_file.stem}.jpg"
                if not img_file.exists():
                    img_file = warp_test_imgs / f"{lbl_file.stem}.png"
                if img_file.exists():
                    shutil.copy2(img_file, OUTPUT_DIR / "images" / "val" / img_file.name)
                    with open(OUTPUT_DIR / "labels" / "val" / lbl_file.name, "w") as f:
                        f.writelines(new_lines)
                    added += 1

    print(f"  Added: {added} images | Skipped: {skipped} annotations (unmapped)")

    # --- Step 3: Stats ---
    print(f"\n{'='*50}")
    class_counts = {0: 0, 1: 0, 2: 0, 3: 0, 4: 0}
    total_imgs = 0
    for split in ["train", "val"]:
        split_count = sum(1 for _ in (OUTPUT_DIR / "images" / split).glob("*"))
        total_imgs += split_count
        for lbl in (OUTPUT_DIR / "labels" / split).glob("*.txt"):
            for line in lbl.read_text().splitlines():
                if line.strip():
                    cid = int(line.split()[0])
                    class_counts[cid] = class_counts.get(cid, 0) + 1

    total_annots = sum(class_counts.values())
    names = {0: "glass", 1: "metal", 2: "paper", 3: "plastic", 4: "trash"}
    print(f"Model 3: WaRP only")
    print(f"  Total: {total_imgs} images, {total_annots} annotations")
    for cid in range(5):
        pct = class_counts[cid] / total_annots * 100 if total_annots else 0
        bar = "#" * int(pct / 2)
        print(f"  {names[cid]:8s}: {class_counts[cid]:5d} ({pct:5.1f}%) {bar}")

    yaml_content = f"""train: {OUTPUT_DIR / 'images' / 'train'}
val: {OUTPUT_DIR / 'images' / 'val'}
nc: 5
names: ['glass', 'metal', 'paper', 'plastic', 'trash']
"""
    (OUTPUT_DIR / "dataset.yaml").write_text(yaml_content)
    print(f"\nSaved: {OUTPUT_DIR / 'dataset.yaml'}")
    print("Done!")


if __name__ == "__main__":
    merge(parse_args())
