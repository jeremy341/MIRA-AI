import shutil, random
from pathlib import Path

TACO_DIR = Path(r"C:\Users\jerem\Documents\Jugend Forscht\MIRA-AI\datasets\mira_v2")
TRASHNET_DIR = Path(r"C:\Users\jerem\Documents\Jugend Forscht\MIRA-AI\datasets\trashnet_labeled")
OUTPUT_DIR = Path(r"C:\Users\jerem\Documents\Jugend Forscht\MIRA-AI\datasets\mira_v3")

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

class_counts = {0: 0, 1: 0, 2: 0, 3: 0, 4: 0}
for split in ["train", "val"]:
    for lbl in (OUTPUT_DIR / "labels" / split).glob("*.txt"):
        for line in lbl.read_text().splitlines():
            if line.strip():
                cid = int(line.split()[0])
                class_counts[cid] = class_counts.get(cid, 0) + 1

total_imgs = sum(1 for _ in (OUTPUT_DIR / "images" / "train").glob("*.jpg")) + sum(1 for _ in (OUTPUT_DIR / "images" / "val").glob("*.jpg"))
total_lbls = sum(class_counts.values())
total_train = sum(1 for _ in (OUTPUT_DIR / "images" / "train").glob("*.jpg"))
total_val = sum(1 for _ in (OUTPUT_DIR / "images" / "val").glob("*.jpg"))

print(f"\n{'='*50}")
print(f"mira_v3: TACO + SAM-TrashNet")
print(f"  Train: {total_train} images")
print(f"  Val:   {total_val} images")
print(f"  Total: {total_imgs} images, {total_lbls} annotations\n")

names = {0: "glass", 1: "metal", 2: "paper", 3: "plastic", 4: "trash"}
for cid in range(5):
    pct = class_counts[cid] / total_lbls * 100 if total_lbls else 0
    bar = "#" * int(pct / 2)
    print(f"  {names[cid]:8s}: {class_counts[cid]:5d} ({pct:5.1f}%) {bar}")
print(f"  {'TOTAL':8s}: {total_lbls:5d}")

yaml_path = OUTPUT_DIR / "dataset.yaml"
yaml_content = f"""train: {OUTPUT_DIR / 'images' / 'train'}
val: {OUTPUT_DIR / 'images' / 'val'}
nc: 5
names: ['glass', 'metal', 'paper', 'plastic', 'trash']
"""
yaml_path.write_text(yaml_content)
print(f"\nSaved: {yaml_path}")
