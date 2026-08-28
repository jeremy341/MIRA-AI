# Shared utilities for MIRA dataset merging.

import sys
import shutil
import random
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from src.config import CLASS_NAMES as _CLASS_NAMES_LIST, NUM_CLASSES

CLASS_NAMES = {i: n for i, n in enumerate(_CLASS_NAMES_LIST)}
MIRA_CLASSES = list(CLASS_NAMES.values())


def remap_label_file(lbl_file, mapping):
    lines = lbl_file.read_text(encoding="utf-8").splitlines()
    new_lines = []
    skipped_count = 0
    for line in lines:
        parts = line.split()
        if not parts:
            continue
        if len(parts) < 5:
            skipped_count += 1
            continue
        try:
            old_id = int(parts[0])
            coords = [float(value) for value in parts[1:5]]
        except ValueError:
            skipped_count += 1
            continue
        if old_id in mapping and all(0.0 <= value <= 1.0 for value in coords):
            new_id = mapping[old_id]
            new_lines.append(f"{new_id} {' '.join(parts[1:])}\n")
        else:
            skipped_count += 1
    if skipped_count > 0:
        print(f"Warning: {skipped_count} annotations skipped - no valid classes after remap", file=sys.stderr)
    return new_lines


def copy_passthrough(src_img_dir, src_lbl_dir, dst_img_dir, dst_lbl_dir):
    if not src_img_dir.exists() or not src_lbl_dir.exists():
        return 0, 0
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
    dst_img_dir.mkdir(parents=True, exist_ok=True)
    dst_lbl_dir.mkdir(parents=True, exist_ok=True)
    added = 0
    skipped = 0
    image_exts = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tiff"}
    for stem in stems:
        lbl_file = src_lbl_dir / f"{stem}.txt"
        if not lbl_file.exists():
            continue
        new_lines = remap_label_file(lbl_file, mapping)
        if not new_lines:
            skipped += 1
            print(f"  Warning: {stem} skipped - no valid classes after remap")
            continue
        img_file = next(
            (
                candidate
                for candidate in src_img_dir.iterdir()
                if candidate.stem == stem and candidate.suffix.lower() in image_exts
            ),
            None,
        )
        if img_file is not None:
            shutil.copy2(img_file, dst_img_dir / img_file.name)
            with open(dst_lbl_dir / lbl_file.name, "w") as f:
                f.writelines(new_lines)
            added += 1
        else:
            skipped += 1
    return added, skipped


def create_split_from_train(src_img_dir, val_ratio=0.2, seed=42):
    image_exts = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tiff"}
    all_files = sorted(f.stem for f in src_img_dir.iterdir() if f.suffix.lower() in image_exts)
    random.Random(seed).shuffle(all_files)
    split_idx = int(len(all_files) * (1 - val_ratio))
    return all_files[:split_idx], all_files[split_idx:]


def print_stats(output_dir, label):
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
    yaml_content = f"train: images/train\nval: images/val\nnc: {NUM_CLASSES}\nnames: {MIRA_CLASSES}\n"
    (output_dir / "dataset.yaml").write_text(yaml_content, encoding="utf-8")
    print(f"\nSaved: {output_dir / 'dataset.yaml'}")
