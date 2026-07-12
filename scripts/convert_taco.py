import json
import os
import shutil
import random
from pathlib import Path

# ============================================================
# CONFIG
# ============================================================
TACO_DIR = Path(r"C:\Users\jerem\Documents\Jugend Forscht\MIRA-AI\datasets\TACO-master\TACO-master")
ANNOTATIONS_PATH = TACO_DIR / "data" / "annotations.json"
OUTPUT_DIR = Path(r"C:\Users\jerem\Documents\Jugend Forscht\MIRA-AI\datasets\mira_v1")
TRAIN_SPLIT = 0.8
SEED = 42

random.seed(SEED)

# ============================================================
# CATEGORY REMAP: TACO 60 classes → MIRA 5 classes
# ============================================================
REMAP = {
    "Aluminium foil": 1,
    "Battery": 4,
    "Aluminium blister pack": 4,
    "Carded blister pack": 4,
    "Other plastic bottle": 3,
    "Clear plastic bottle": 3,
    "Glass bottle": 0,
    "Plastic bottle cap": 3,
    "Metal bottle cap": 1,
    "Broken glass": 0,
    "Food Can": 1,
    "Aerosol": 1,
    "Drink can": 1,
    "Toilet tube": 2,
    "Other carton": 2,
    "Egg carton": 2,
    "Drink carton": 2,
    "Corrugated carton": 2,
    "Meal carton": 2,
    "Pizza box": 2,
    "Paper cup": 2,
    "Disposable plastic cup": 3,
    "Foam cup": 3,
    "Glass cup": 0,
    "Other plastic cup": 3,
    "Food waste": 4,
    "Glass jar": 0,
    "Plastic lid": 3,
    "Metal lid": 1,
    "Other plastic": 3,
    "Magazine paper": 2,
    "Tissues": 2,
    "Wrapping paper": 2,
    "Normal paper": 2,
    "Paper bag": 2,
    "Plastified paper bag": 2,
    "Plastic film": 3,
    "Six pack rings": 3,
    "Garbage bag": 3,
    "Other plastic wrapper": 3,
    "Single-use carrier bag": 3,
    "Polypropylene bag": 3,
    "Crisp packet": 3,
    "Spread tub": 3,
    "Tupperware": 3,
    "Disposable food container": 3,
    "Foam food container": 3,
    "Other plastic container": 3,
    "Plastic gloves": 3,
    "Plastic utensils": 3,
    "Pop tab": 1,
    "Rope & strings": 4,
    "Scrap metal": 1,
    "Shoe": 4,
    "Squeezable tube": 3,
    "Plastic straw": 3,
    "Paper straw": 2,
    "Styrofoam piece": 3,
    "Unlabeled litter": 4,
    "Cigarette": 4,
}

# ============================================================
# LOAD ANNOTATIONS
# ============================================================
print("Loading TACO annotations...")
with open(ANNOTATIONS_PATH) as f:
    data = json.load(f)

cat_name_to_id = {c["name"]: c["id"] for c in data["categories"]}
img_id_to_file = {img["id"]: img["file_name"] for img in data["images"]}

image_annotations = {}
for ann in data["annotations"]:
    cat_id = ann["category_id"]
    cat_name = next(c["name"] for c in data["categories"] if c["id"] == cat_id)
    if cat_name not in REMAP:
        continue
    mira_class = REMAP[cat_name]
    bbox = ann["bbox"]
    img_id = ann["image_id"]
    if img_id not in image_annotations:
        image_annotations[img_id] = []
    image_annotations[img_id].append((mira_class, bbox))

print(f"  Total images in annotations: {len(data['images'])}")
print(f"  Total annotations: {len(data['annotations'])}")
print(f"  Filtered images with mapped annotations: {len(image_annotations)}")
print(f"  Total mapped annotations: {sum(len(v) for v in image_annotations.values())}")

# ============================================================
# COLLECT IMAGE FILES (keyed by relative path like "batch_1/000006.jpg")
# ============================================================
print("\nCollecting image files...")
data_dir = TACO_DIR / "data"
batch_dirs = sorted([d for d in data_dir.iterdir() if d.is_dir() and d.name.startswith("batch_")])
img_path_map = {}
for batch_dir in batch_dirs:
    for img_file in batch_dir.glob("*.jpg"):
        rel_path = f"{batch_dir.name}/{img_file.name}"
        img_path_map[rel_path] = img_file

print(f"  Found {len(img_path_map)} images in batch directories")

# ============================================================
# CREATE OUTPUT DIRECTORIES
# ============================================================
train_img_dir = OUTPUT_DIR / "images" / "train"
train_lbl_dir = OUTPUT_DIR / "labels" / "train"
val_img_dir = OUTPUT_DIR / "images" / "val"
val_lbl_dir = OUTPUT_DIR / "labels" / "val"

for d in [train_img_dir, train_lbl_dir, val_img_dir, val_lbl_dir]:
    d.mkdir(parents=True, exist_ok=True)

# ============================================================
# SPLIT AND CONVERT
# ============================================================
valid_img_ids = [img_id for img_id in image_annotations if img_id_to_file[img_id] in img_path_map]
print(f"\nImages with both annotations and files: {len(valid_img_ids)}")

random.shuffle(valid_img_ids)
split_idx = int(len(valid_img_ids) * TRAIN_SPLIT)
train_ids = valid_img_ids[:split_idx]
val_ids = valid_img_ids[split_idx:]

print(f"  Train: {len(train_ids)} | Val: {len(val_ids)}")

def convert_and_copy(img_ids, img_dir, lbl_dir, split_name):
    count = 0
    for img_id in img_ids:
        file_name = img_id_to_file[img_id]
        src_path = img_path_map[file_name]
        stem = Path(file_name).stem
        dst_img = img_dir / f"{stem}.jpg"
        dst_lbl = lbl_dir / f"{stem}.txt"

        shutil.copy2(src_path, dst_img)

        img_info = next(img for img in data["images"] if img["id"] == img_id)
        img_w = img_info["width"]
        img_h = img_info["height"]

        lines = []
        for class_id, bbox in image_annotations[img_id]:
            x, y, w, h = bbox
            x_center = (x + w / 2) / img_w
            y_center = (y + h / 2) / img_h
            w_norm = w / img_w
            h_norm = h / img_h
            lines.append(f"{class_id} {x_center:.6f} {y_center:.6f} {w_norm:.6f} {h_norm:.6f}")

        with open(dst_lbl, "w") as f:
            f.write("\n".join(lines))

        count += 1
        if count % 100 == 0:
            print(f"  {split_name}: {count}/{len(img_ids)}")

    print(f"  {split_name}: done ({count} images)")

print("\nConverting train set...")
convert_and_copy(train_ids, train_img_dir, train_lbl_dir, "Train")
print("\nConverting val set...")
convert_and_copy(val_ids, val_img_dir, val_lbl_dir, "Val")

# ============================================================
# GENERATE dataset.yaml
# ============================================================
yaml_path = OUTPUT_DIR / "dataset.yaml"
yaml_content = f"""train: {OUTPUT_DIR / 'images' / 'train'}
val: {OUTPUT_DIR / 'images' / 'val'}
nc: 5
names: ['glass', 'metal', 'paper', 'plastic', 'trash']
"""
with open(yaml_path, "w") as f:
    f.write(yaml_content)

print(f"\nDataset YAML written to: {yaml_path}")

# ============================================================
# COUNT CLASSES
# ============================================================
class_counts = {0:0, 1:0, 2:0, 3:0, 4:0}
for img_id in valid_img_ids:
    for class_id, _ in image_annotations[img_id]:
        class_counts[class_id] += 1

total = sum(class_counts.values())
print("\nClass distribution:")
class_names = {0:"glass", 1:"metal", 2:"paper", 3:"plastic", 4:"trash"}
for cid in range(5):
    pct = class_counts[cid] / total * 100
    bar = "#" * int(pct / 2)
    print(f"  {class_names[cid]:8s}: {class_counts[cid]:5d} ({pct:5.1f}%) {bar}")
print(f"  {'TOTAL':8s}: {total:5d}")

print(f"\nDone! Dataset in: {OUTPUT_DIR}")
print(f"  Train: {len(train_ids)} images")
print(f"  Val:   {len(val_ids)} images")
