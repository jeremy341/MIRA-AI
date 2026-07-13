"""Shared WaRP dataset utilities for merge_dataset_model2/3/4.py.

Handles the 28->5 class remapping, valid split creation, and stats printing.
"""
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

WARP_DIR = DATASETS / "WaRP" / "Warp-D"
CLASS_NAMES = {0: "glass", 1: "metal", 2: "paper", 3: "plastic", 4: "trash"}


def create_warp_split():
    """Create 80/20 train/val split from WaRP train (no valid/ exists).

    Returns:
        tuple: (train_stems, val_stems) — list of image stems for each split
    """
    warp_train_imgs = WARP_DIR / "train" / "images"
    all_files = sorted([f.stem for f in warp_train_imgs.glob("*")])
    random.seed(42)
    random.shuffle(all_files)
    split_idx = int(len(all_files) * 0.8)
    return all_files[:split_idx], all_files[split_idx:]


def remap_label_file(lbl_file, mapping):
    """Read a YOLO label file and remap class IDs using the mapping.

    Returns:
        list: remapped lines (empty if no valid annotations remain)
    """
    with open(lbl_file, "r") as f:
        lines = f.readlines()
    new_lines = []
    for line in lines:
        parts = line.split()
        if not parts:
            continue
        old_id = int(parts[0])
        if old_id in mapping:
            new_id = mapping[old_id]
            new_lines.append(f"{new_id} {' '.join(parts[1:])}\n")
    return new_lines


def copy_remapped_images(stems, src_img_dir, src_lbl_dir, dst_img_dir, dst_lbl_dir, mapping):
    """Copy images and remapped labels for a list of stems.

    Returns:
        tuple: (added, skipped) counts
    """
    added = 0
    skipped = 0
    for stem in stems:
        lbl_file = src_lbl_dir / f"{stem}.txt"
        if not lbl_file.exists():
            continue
        new_lines = remap_label_file(lbl_file, mapping)
        if not new_lines:
            skipped += 1
            continue
        img_file = src_img_dir / f"{stem}.jpg"
        if not img_file.exists():
            img_file = src_img_dir / f"{stem}.png"
        if img_file.exists():
            shutil.copy2(img_file, dst_img_dir / img_file.name)
            with open(dst_lbl_dir / lbl_file.name, "w") as f:
                f.writelines(new_lines)
            added += 1
        else:
            skipped += 1
    return added, skipped


def add_warp_test_to_val(output_dir, mapping):
    """Copy WaRP test split -> val with class remapping.

    Returns:
        tuple: (added, skipped) counts
    """
    test_imgs = WARP_DIR / "test" / "images"
    test_lbls = WARP_DIR / "test" / "labels"
    if not test_lbls.exists():
        return 0, 0
    return copy_remapped_images(
        stems=[f.stem for f in test_lbls.glob("*.txt")],
        src_img_dir=test_imgs,
        src_lbl_dir=test_lbls,
        dst_img_dir=output_dir / "images" / "val",
        dst_lbl_dir=output_dir / "labels" / "val",
        mapping=mapping,
    )


def print_stats(output_dir, model_label):
    """Print class distribution stats for the merged dataset."""
    print(f"\n{'='*50}")
    class_counts = {0: 0, 1: 0, 2: 0, 3: 0, 4: 0}
    total_imgs = 0
    for split in ["train", "val"]:
        split_count = sum(1 for _ in (output_dir / "images" / split).glob("*"))
        total_imgs += split_count
        for lbl in (output_dir / "labels" / split).glob("*.txt"):
            for line in lbl.read_text().splitlines():
                if line.strip():
                    cid = int(line.split()[0])
                    class_counts[cid] = class_counts.get(cid, 0) + 1

    total_annots = sum(class_counts.values())
    print(f"{model_label}")
    print(f"  Total: {total_imgs} images, {total_annots} annotations")
    for cid in range(5):
        pct = class_counts[cid] / total_annots * 100 if total_annots else 0
        bar = "#" * int(pct / 2)
        print(f"  {CLASS_NAMES[cid]:8s}: {class_counts[cid]:5d} ({pct:5.1f}%) {bar}")


def write_dataset_yaml(output_dir):
    """Write dataset.yaml for the merged dataset."""
    yaml_content = f"""train: {output_dir / 'images' / 'train'}
val: {output_dir / 'images' / 'val'}
nc: 5
names: ['glass', 'metal', 'paper', 'plastic', 'trash']
"""
    (output_dir / "dataset.yaml").write_text(yaml_content)
    print(f"\nSaved: {output_dir / 'dataset.yaml'}")
