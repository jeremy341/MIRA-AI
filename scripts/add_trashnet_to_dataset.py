import sys
import shutil
import random
from pathlib import Path

_src_dir = str(Path(__file__).resolve().parent.parent / "src")
_scripts_dir = str(Path(__file__).resolve().parent)
if _src_dir not in sys.path:
    sys.path.insert(0, _src_dir)
if _scripts_dir not in sys.path:
    sys.path.insert(0, _scripts_dir)

from config import CLASS_NAMES as CLASS_NAMES_LIST, NUM_CLASSES
from class_mappings import TRASHNET_FOLDER_MAP as CLASS_MAP

# ============================================================
# CONFIG
# ============================================================
ROOT = Path(__file__).resolve().parent.parent
DATASETS = ROOT / "datasets"
TRASHNET_DIR = ROOT / "archive (1)" / "dataset-resized"
OUTPUT_DIR = DATASETS / "mira_v1"
TRAIN_SPLIT = 0.8
SEED = 42

random.seed(SEED)

train_img_dir = OUTPUT_DIR / "images" / "train"
train_lbl_dir = OUTPUT_DIR / "labels" / "train"
val_img_dir = OUTPUT_DIR / "images" / "val"
val_lbl_dir = OUTPUT_DIR / "labels" / "val"
for d in (train_img_dir, train_lbl_dir, val_img_dir, val_lbl_dir):
    d.mkdir(parents=True, exist_ok=True)

# ============================================================
# COLLECT ALL TRASHNET IMAGES WITH CLASS ID
# ============================================================
print("Scanning TrashNet...")
samples = []
for class_dir in sorted(TRASHNET_DIR.iterdir()):
    if not class_dir.is_dir() or class_dir.name not in CLASS_MAP:
        continue
    class_id = CLASS_MAP[class_dir.name]
    for img_file in class_dir.glob("*.*"):
        if img_file.suffix.lower() in (".jpg", ".jpeg", ".png"):
            samples.append((img_file, class_id))

print(f"  Found {len(samples)} images")

# ============================================================
# SPLIT
# ============================================================
random.shuffle(samples)
split_idx = int(len(samples) * TRAIN_SPLIT)
train_samples = samples[:split_idx]
val_samples = samples[split_idx:]
print(f"  Train: {len(train_samples)} | Val: {len(val_samples)}")


def add_samples(samples, img_dir, lbl_dir, split_name):
    copied = 0
    skipped = 0
    for img_file, class_id in samples:
        stem = img_file.stem
        # Avoid overwriting existing TACO files — add suffix
        dst_img = img_dir / f"{stem}.jpg"
        dst_lbl = lbl_dir / f"{stem}.txt"
        suffix = 1
        while dst_img.exists():
            dst_img = img_dir / f"{stem}_{suffix}.jpg"
            dst_lbl = lbl_dir / f"{stem}_{suffix}.txt"
            suffix += 1

        shutil.copy2(img_file, dst_img)

        # Full-image bounding box: [0 0 1 1]
        with open(dst_lbl, "w") as f:
            f.write(f"{class_id} 0.5 0.5 1.0 1.0\n")

        copied += 1

    print(f"  {split_name}: {copied} added, {skipped} skipped")


print("\nAdding TrashNet to training set...")
add_samples(train_samples, train_img_dir, train_lbl_dir, "Train")
print("\nAdding TrashNet to validation set...")
add_samples(val_samples, val_img_dir, val_lbl_dir, "Val")

# ============================================================
# COUNT ALL (TACO + TrashNet) CLASS DISTRIBUTION
# ============================================================
class_counts = {i: 0 for i in range(NUM_CLASSES)}
for lbl_dir in [train_lbl_dir, val_lbl_dir]:
    for lbl_file in lbl_dir.glob("*.txt"):
        with open(lbl_file) as f:
            for line in f:
                line = line.strip()
                if line:
                    class_id = int(line.split()[0])
                    if class_id in class_counts:
                        class_counts[class_id] += 1

total_imgs = sum(1 for _ in train_img_dir.glob("*.jpg")) + sum(1 for _ in val_img_dir.glob("*.jpg"))
total_lbls = sum(class_counts.values())
total_train = sum(1 for _ in train_img_dir.glob("*.jpg"))
total_val = sum(1 for _ in val_img_dir.glob("*.jpg"))

print("\n" + "=" * 50)
print("FINAL DATASET: mira_v1")
print(f"  Train: {total_train} images")
print(f"  Val:   {total_val} images")
print(f"  Total: {total_imgs} images, {total_lbls} annotations")
print()

class_names = {i: n for i, n in enumerate(CLASS_NAMES_LIST)}
for cid in range(NUM_CLASSES):
    pct = class_counts[cid] / total_lbls * 100 if total_lbls else 0
    bar = "#" * int(pct / 2)
    print(f"  {class_names[cid]:8s}: {class_counts[cid]:5d} ({pct:5.1f}%) {bar}")
print(f"  {'TOTAL':8s}: {total_lbls:5d}")

# ============================================================
# UPDATE dataset.yaml
# ============================================================
yaml_path = OUTPUT_DIR / "dataset.yaml"
yaml_content = f"""train: {OUTPUT_DIR / "images" / "train"}
val: {OUTPUT_DIR / "images" / "val"}
nc: {NUM_CLASSES}
names: {CLASS_NAMES_LIST}
"""
with open(yaml_path, "w") as f:
    f.write(yaml_content)
print(f"\nUpdated: {yaml_path}")
