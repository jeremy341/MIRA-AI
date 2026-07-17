"""Merge TACO + TrashNet + Roboflow Trash Detection into one YOLO dataset.

Usage:
    py scripts/merge_dataset_model1.py
    py scripts/merge_dataset_model1.py --output-dir datasets/MyCustom
    py scripts/merge_dataset_model1.py --dry-run
"""
import argparse
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATASETS = ROOT / "datasets"
from class_mappings import ROBOFLOW_MAPPING


def parse_args():
    p = argparse.ArgumentParser(description="Merge TACO+TrashNet+Roboflow into one YOLO dataset")
    p.add_argument("--output-dir", type=Path, default=DATASETS / "mira_tnr",
                   help="Output dataset directory (default: datasets/mira_tnr)")
    p.add_argument("--dry-run", action="store_true",
                   help="Preview stats without copying files")
    return p.parse_args()


def merge(args):
    TACO_TRASHNET_DIR = DATASETS / "mira_v2"
    ROBOFLOW_DIR = DATASETS / "roboflow_raw"
    OUTPUT_DIR = args.output_dir

    if args.dry_run:
        print("[DRY RUN] Would merge:")
        print(f"  TACO+TrashNet: {TACO_TRASHNET_DIR}")
        print(f"  Roboflow:      {ROBOFLOW_DIR}")
        print(f"  Output:        {OUTPUT_DIR}")
        return

    # Create output structure
    for split in ["train", "val"]:
        (OUTPUT_DIR / "images" / split).mkdir(parents=True, exist_ok=True)
        (OUTPUT_DIR / "labels" / split).mkdir(parents=True, exist_ok=True)

    # --- Step 1: Copy mira_v2 (TACO + TrashNet) ---
    print("Copying TACO + TrashNet (mira_v2)...")
    for split in ["train", "val"]:
        src_img = TACO_TRASHNET_DIR / "images" / split
        src_lbl = TACO_TRASHNET_DIR / "labels" / split
        dst_img = OUTPUT_DIR / "images" / split
        dst_lbl = OUTPUT_DIR / "labels" / split
        for img in src_img.glob("*"):
            shutil.copy2(img, dst_img / img.name)
        for lbl in src_lbl.glob("*"):
            shutil.copy2(lbl, dst_lbl / lbl.name)
        count = sum(1 for _ in (OUTPUT_DIR / "images" / split).glob("*"))
        print(f"  {split}: {count} images total after TACO+TrashNet")

    # --- Step 2: Add Roboflow Trash Detection (64->5 remap) ---
    print("\nAdding Roboflow Trash Detection (64 to 5 remap)...")
    roboflow_map = {"train": "train", "valid": "val", "test": "train"}

    added = 0
    skipped = 0
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
                    skipped += 1

            if new_lines:
                img_file = img_src / f"{lbl_file.stem}.jpg"
                if not img_file.exists():
                    img_file = img_src / f"{lbl_file.stem}.png"
                if img_file.exists():
                    shutil.copy2(img_file, dst_img / img_file.name)
                    with open(dst_lbl / lbl_file.name, "w") as f:
                        f.writelines(new_lines)
                    added += 1

    print(f"  Added: {added} images | Skipped: {skipped} annotations (unmapped classes)")

    # --- Step 3: Print final stats ---
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
    print(f"Model 1: TACO + TrashNet + Roboflow")
    print(f"  Total: {total_imgs} images, {total_annots} annotations")
    for cid in range(5):
        pct = class_counts[cid] / total_annots * 100 if total_annots else 0
        bar = "#" * int(pct / 2)
        print(f"  {names[cid]:8s}: {class_counts[cid]:5d} ({pct:5.1f}%) {bar}")

    # --- Step 4: Write dataset.yaml ---
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
