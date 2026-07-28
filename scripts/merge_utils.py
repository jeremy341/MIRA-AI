"""Shared utilities for MIRA dataset merging.

Provides generic remapping, stats printing, and YAML writing used by
merge_dataset.py and the individual merge_dataset_model*.py wrappers.
"""

import sys
import shutil
import random
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

_src_dir = str(ROOT / "src")
if _src_dir not in sys.path:
    sys.path.insert(0, _src_dir)
from config import CLASS_NAMES as _CLASS_NAMES_LIST, NUM_CLASSES

CLASS_NAMES = {i: n for i, n in enumerate(_CLASS_NAMES_LIST)}
MIRA_CLASSES = list(CLASS_NAMES.values())


def remap_label_file(lbl_file, mapping):
    """Read a YOLO label file and remap class IDs using the mapping.

    Returns:
        list: remapped lines (empty if no valid annotations remain)
    """
    with open(lbl_file, encoding="utf-8") as f:
        lines = f.readlines()
    new_lines = []
    skipped_count = 0
    for line in lines:
        parts = line.split()
        if not parts:
            continue
        try:
            old_id = int(parts[0])
        except ValueError:
            continue
        if old_id in mapping:
            new_id = mapping[old_id]
            new_lines.append(f"{new_id} {' '.join(parts[1:])}\n")
        else:
            skipped_count += 1
    if skipped_count > 0:
        print(f"Warning: {skipped_count} annotations skipped — no valid classes after remap", file=sys.stderr)
    return new_lines


def copy_passthrough(src_img_dir, src_lbl_dir, dst_img_dir, dst_lbl_dir):
    """Copy images and labels without remapping (source already in MIRA format).

    Returns:
        tuple: (added, skipped) counts
    """
    dst_img_dir.mkdir(parents=True, exist_ok=True)
    dst_lbl_dir.mkdir(parents=True, exist_ok=True)
    added = 0
    image_exts = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tiff"}
    for img in src_img_dir.iterdir():
        if img.suffix.lower() in image_exts:
            shutil.copy2(img, dst_img_dir / img.name)
            added += 1
    for lbl in src_lbl_dir.glob("*.txt"):
        shutil.copy2(lbl, dst_lbl_dir / lbl.name)
    return added, 0


def copy_remapped_images(stems, src_img_dir, src_lbl_dir, dst_img_dir, dst_lbl_dir, mapping):
    """Copy images and remapped labels for a list of stems.

    Returns:
        tuple: (added, skipped) counts
    """
    dst_img_dir.mkdir(parents=True, exist_ok=True)
    dst_lbl_dir.mkdir(parents=True, exist_ok=True)
    added = 0
    skipped = 0
    for stem in stems:
        lbl_file = src_lbl_dir / f"{stem}.txt"
        if not lbl_file.exists():
            continue
        new_lines = remap_label_file(lbl_file, mapping)
        if not new_lines:
            skipped += 1
            print(f"  Warning: {stem} skipped — no valid classes after remap")
            continue
        for ext in (".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tiff"):
            img_file = src_img_dir / f"{stem}{ext}"
            if img_file.exists():
                break
        else:
            img_file = None
        if img_file is not None:
            shutil.copy2(img_file, dst_img_dir / img_file.name)
            with open(dst_lbl_dir / lbl_file.name, "w") as f:
                f.writelines(new_lines)
            added += 1
        else:
            skipped += 1
    return added, skipped


def create_split_from_train(src_img_dir, val_ratio=0.2, seed=42):
    """Create an 80/20 train/val split from a train directory.

    Returns:
        tuple: (train_stems, val_stems)
    """
    image_exts = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tiff"}
    all_files = sorted([f.stem for f in src_img_dir.iterdir() if f.suffix.lower() in image_exts])
    random.seed(seed)
    random.shuffle(all_files)
    split_idx = int(len(all_files) * (1 - val_ratio))
    return all_files[:split_idx], all_files[split_idx:]


def print_stats(output_dir, label):
    """Print class distribution stats for a merged dataset."""
    print(f"\n{'=' * 50}")
    class_counts = {i: 0 for i in range(NUM_CLASSES)}
    total_imgs = 0
    for split in ["train", "val"]:
        split_count = sum(1 for _ in (output_dir / "images" / split).glob("*"))
        total_imgs += split_count
        for lbl in (output_dir / "labels" / split).glob("*.txt"):
            for line in lbl.read_text().splitlines():
                if line.strip():
                    try:
                        cid = int(line.split()[0])
                    except (ValueError, IndexError):
                        continue
                    class_counts[cid] = class_counts.get(cid, 0) + 1

    total_annots = sum(class_counts.values())
    print(f"{label}")
    print(f"  Total: {total_imgs} images, {total_annots} annotations")
    for cid in range(NUM_CLASSES):
        pct = class_counts[cid] / total_annots * 100 if total_annots else 0
        bar = "#" * int(pct / 2)
        print(f"  {CLASS_NAMES[cid]:8s}: {class_counts[cid]:5d} ({pct:5.1f}%) {bar}")


def write_dataset_yaml(output_dir):
    """Write dataset.yaml for a merged dataset."""
    yaml_content = f"""train: {output_dir / "images" / "train"}
val: {output_dir / "images" / "val"}
nc: {NUM_CLASSES}
names: {MIRA_CLASSES}
"""
    (output_dir / "dataset.yaml").write_text(yaml_content)
    print(f"\nSaved: {output_dir / 'dataset.yaml'}")
