import sys
import random
import shutil
from pathlib import Path

_src_dir = str(Path(__file__).resolve().parent.parent / "src")
if _src_dir not in sys.path:
    sys.path.insert(0, _src_dir)
from config import CLASS_NAMES, NUM_CLASSES

ROOT = Path(__file__).resolve().parent.parent
DATASETS = ROOT / "datasets"

TACO_DIR = DATASETS / "mira_v2"
TRASHNET_DIR = DATASETS / "trashnet_labeled"
OUTPUT_DIR = DATASETS / "mira_v3"

TRAIN_SPLIT = 0.8
SEED = 42
random.seed(SEED)

for split in ["train", "val"]:
    for sub in ["images", "labels"]:
        (OUTPUT_DIR / sub / split).mkdir(parents=True, exist_ok=True)

print("Copying TACO (mira_v2)...")
taco_train = list((TACO_DIR / "images" / "train").glob("*.jpg"))
taco_val = list((TACO_DIR / "images" / "val").glob("*.jpg"))
print(f"  TACO train: {len(taco_train)}, val: {len(taco_val)}")

for split in ["train", "val"]:
    src_img = TACO_DIR / "images" / split
    src_lbl = TACO_DIR / "labels" / split
    dst_img = OUTPUT_DIR / "images" / split
    dst_lbl = OUTPUT_DIR / "labels" / split
    for img in src_img.glob("*.jpg"):
        shutil.copy2(img, dst_img / img.name)
    for lbl in src_lbl.glob("*.txt"):
        shutil.copy2(lbl, dst_lbl / lbl.name)

print("  TACO copied")

print("Copying SAM-labeled TrashNet...")
tn_train = list((TRASHNET_DIR / "images" / "train").glob("*.jpg"))
tn_val = list((TRASHNET_DIR / "images" / "val").glob("*.jpg"))
print(f"  TrashNet train: {len(tn_train)}, val: {len(tn_val)}")

for split in ["train", "val"]:
    src_img = TRASHNET_DIR / "images" / split
    src_lbl = TRASHNET_DIR / "labels" / split
    dst_img = OUTPUT_DIR / "images" / split
    dst_lbl = OUTPUT_DIR / "labels" / split
    for img in src_img.glob("*.jpg"):
        shutil.copy2(img, dst_img / img.name)
    for lbl in src_lbl.glob("*.txt"):
        shutil.copy2(lbl, dst_lbl / lbl.name)

print("  TrashNet copied")

class_counts = {i: 0 for i in range(NUM_CLASSES)}
for split in ["train", "val"]:
    for lbl in (OUTPUT_DIR / "labels" / split).glob("*.txt"):
        for line in lbl.read_text().splitlines():
            if line.strip():
                cid = int(line.split()[0])
                class_counts[cid] = class_counts.get(cid, 0) + 1

total_imgs = sum(1 for _ in (OUTPUT_DIR / "images" / "train").glob("*.jpg")) + sum(
    1 for _ in (OUTPUT_DIR / "images" / "val").glob("*.jpg")
)
total_lbls = sum(class_counts.values())
total_train = sum(1 for _ in (OUTPUT_DIR / "images" / "train").glob("*.jpg"))
total_val = sum(1 for _ in (OUTPUT_DIR / "images" / "val").glob("*.jpg"))

print(f"\n{'=' * 50}")
print("mira_v3: TACO + SAM-TrashNet")
print(f"  Train: {total_train} images")
print(f"  Val:   {total_val} images")
print(f"  Total: {total_imgs} images, {total_lbls} annotations\n")

names = {i: n for i, n in enumerate(CLASS_NAMES)}
for cid in range(NUM_CLASSES):
    pct = class_counts[cid] / total_lbls * 100 if total_lbls else 0
    bar = "#" * int(pct / 2)
    print(f"  {names[cid]:8s}: {class_counts[cid]:5d} ({pct:5.1f}%) {bar}")
print(f"  {'TOTAL':8s}: {total_lbls:5d}")

yaml_path = OUTPUT_DIR / "dataset.yaml"
names_str = str(CLASS_NAMES)
yaml_content = f"""train: {OUTPUT_DIR / "images" / "train"}
val: {OUTPUT_DIR / "images" / "val"}
nc: {NUM_CLASSES}
names: {names_str}
"""
yaml_path.write_text(yaml_content)
print(f"\nSaved: {yaml_path}")
