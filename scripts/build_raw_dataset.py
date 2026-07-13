import json
import shutil
import random
from pathlib import Path

# ============================================================
# CONFIG
# ============================================================
TACO_DIR = Path(r"C:\Users\jerem\Documents\Jugend Forscht\MIRA-AI\datasets\TACO-master\TACO-master")
ANNOTATIONS_PATH = TACO_DIR / "data" / "annotations.json"
TRASHNET_DIR = Path(r"C:\Users\jerem\Documents\Jugend Forscht\MIRA-AI\archive (1)\dataset-resized")
OUTPUT_DIR = Path(r"C:\Users\jerem\Documents\Jugend Forscht\MIRA-AI\datasets\mira_v2")
TRAIN_SPLIT = 0.8
SEED = 42

random.seed(SEED)

# ============================================================
# CATEGORY REMAP
# ============================================================
REMAP = {
    "Aluminium foil": 1, "Battery": 4, "Aluminium blister pack": 4,
    "Carded blister pack": 4, "Other plastic bottle": 3, "Clear plastic bottle": 3,
    "Glass bottle": 0, "Plastic bottle cap": 3, "Metal bottle cap": 1,
    "Broken glass": 0, "Food Can": 1, "Aerosol": 1, "Drink can": 1,
    "Toilet tube": 2, "Other carton": 2, "Egg carton": 2, "Drink carton": 2,
    "Corrugated carton": 2, "Meal carton": 2, "Pizza box": 2, "Paper cup": 2,
    "Disposable plastic cup": 3, "Foam cup": 3, "Glass cup": 0,
    "Other plastic cup": 3, "Food waste": 4, "Glass jar": 0, "Plastic lid": 3,
    "Metal lid": 1, "Other plastic": 3, "Magazine paper": 2, "Tissues": 2,
    "Wrapping paper": 2, "Normal paper": 2, "Paper bag": 2,
    "Plastified paper bag": 2, "Plastic film": 3, "Six pack rings": 3,
    "Garbage bag": 3, "Other plastic wrapper": 3, "Single-use carrier bag": 3,
    "Polypropylene bag": 3, "Crisp packet": 3, "Spread tub": 3, "Tupperware": 3,
    "Disposable food container": 3, "Foam food container": 3,
    "Other plastic container": 3, "Plastic gloves": 3, "Plastic utensils": 3,
    "Pop tab": 1, "Rope & strings": 4, "Scrap metal": 1, "Shoe": 4,
    "Squeezable tube": 3, "Plastic straw": 3, "Paper straw": 2,
    "Styrofoam piece": 3, "Unlabeled litter": 4, "Cigarette": 4,
}

TRASHNET_MAP = {
    "cardboard": 2, "glass": 0, "metal": 1, "paper": 2, "plastic": 3, "trash": 4,
}

# ============================================================
# STEP 1: Convert TACO (COCO -> YOLO)
# ============================================================
print("=" * 50)
print("STEP 1: Converting TACO")
print("=" * 50)

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

print(f"  Annotations: {len(data['annotations'])} -> {sum(len(v) for v in image_annotations.values())} mapped")

# Build relative-path -> source file map
data_dir = TACO_DIR / "data"
batch_dirs = sorted([d for d in data_dir.iterdir() if d.is_dir() and d.name.startswith("batch_")])
rel_path_map = {}
for batch_dir in batch_dirs:
    for img_file in batch_dir.glob("*.jpg"):
        rel = f"{batch_dir.name}/{img_file.name}"
        rel_path_map[rel] = img_file
print(f"  Image files found: {len(rel_path_map)}")

# Collect valid TACO samples with batch-prefixed stem
taco_samples = []  # list of (src_file, dst_stem, [class_id, bbox])
for img_id, anns in image_annotations.items():
    rel_path = img_id_to_file[img_id]
    if rel_path not in rel_path_map:
        continue
    src = rel_path_map[rel_path]
    # Use batch prefix to avoid collisions e.g. batch_1_000006
    batch_name = src.parent.name
    stem = f"{batch_name}_{src.stem}"
    taco_samples.append((src, stem, anns))

print(f"  Valid TACO samples: {len(taco_samples)}")

# ============================================================
# STEP 2: Collect TrashNet samples
# ============================================================
print("\n" + "=" * 50)
print("STEP 2: Collecting TrashNet")
print("=" * 50)

tn_samples = []
for class_dir in sorted(TRASHNET_DIR.iterdir()):
    if not class_dir.is_dir() or class_dir.name not in TRASHNET_MAP:
        continue
    class_id = TRASHNET_MAP[class_dir.name]
    for img_file in class_dir.glob("*.*"):
        if img_file.suffix.lower() in (".jpg", ".jpeg", ".png"):
            tn_samples.append((img_file, class_id, img_file.stem))

print(f"  TrashNet samples: {len(tn_samples)}")

# ============================================================
# STEP 3: Combine, split, write
# ============================================================
print("\n" + "=" * 50)
print("STEP 3: Splitting & writing")
print("=" * 50)

all_samples = []
# TACO: (src, stem, anns)
for src, stem, anns in taco_samples:
    all_samples.append(("taco", src, stem, anns))
# TrashNet: (src, class_id, stem)
for src, class_id, stem in tn_samples:
    all_samples.append(("trashnet", src, class_id, stem))

random.shuffle(all_samples)
split_idx = int(len(all_samples) * TRAIN_SPLIT)
train_samples = all_samples[:split_idx]
val_samples = all_samples[split_idx:]

print(f"  Train: {len(train_samples)} | Val: {len(val_samples)}")

train_img_dir = OUTPUT_DIR / "images" / "train"
train_lbl_dir = OUTPUT_DIR / "labels" / "train"
val_img_dir = OUTPUT_DIR / "images" / "val"
val_lbl_dir = OUTPUT_DIR / "labels" / "val"
for d in [train_img_dir, train_lbl_dir, val_img_dir, val_lbl_dir]:
    d.mkdir(parents=True, exist_ok=True)

def write_split(samples, img_dir, lbl_dir, split_name):
    copied = 0
    for item in samples:
        source_type = item[0]
        if source_type == "taco":
            _, src, stem, anns = item
            img_info = None
            # Need img dimensions from COCO data -- find matching image
            rel = f"{src.parent.name}/{src.name}"
            for img in data["images"]:
                if img["file_name"] == rel:
                    img_info = img
                    break
            if img_info is None:
                continue
            img_w, img_h = img_info["width"], img_info["height"]
            shutil.copy2(src, img_dir / f"{stem}.jpg")
            lines = []
            for class_id, bbox in anns:
                x, y, w, h = bbox
                xc = (x + w / 2) / img_w
                yc = (y + h / 2) / img_h
                wn = w / img_w
                hn = h / img_h
                lines.append(f"{class_id} {xc:.6f} {yc:.6f} {wn:.6f} {hn:.6f}")
            with open(lbl_dir / f"{stem}.txt", "w") as f:
                f.write("\n".join(lines))
        else:
            _, src, class_id, stem = item
            dst_img = img_dir / f"{stem}.jpg"
            dst_lbl = lbl_dir / f"{stem}.txt"
            suffix = 1
            while dst_img.exists():
                dst_img = img_dir / f"{stem}_{suffix}.jpg"
                dst_lbl = lbl_dir / f"{stem}_{suffix}.txt"
                suffix += 1
            shutil.copy2(src, dst_img)
            with open(dst_lbl, "w") as f:
                f.write(f"{class_id} 0.5 0.5 1.0 1.0\n")
        copied += 1
    print(f"  {split_name}: {copied} images written")

write_split(train_samples, train_img_dir, train_lbl_dir, "Train")
write_split(val_samples, val_img_dir, val_lbl_dir, "Val")

# ============================================================
# STEP 4: Count & report
# ============================================================
print("\n" + "=" * 50)
print("CLASS DISTRIBUTION")
print("=" * 50)

class_counts = {0: 0, 1: 0, 2: 0, 3: 0, 4: 0}
for lbl_dir in [train_lbl_dir, val_lbl_dir]:
    for lbl_file in lbl_dir.glob("*.txt"):
        with open(lbl_file) as f:
            for line in f:
                line = line.strip()
                if line:
                    cid = int(line.split()[0])
                    class_counts[cid] = class_counts.get(cid, 0) + 1

total_imgs = sum(1 for _ in train_img_dir.glob("*.jpg")) + sum(1 for _ in val_img_dir.glob("*.jpg"))
total_lbls = sum(class_counts.values())
total_train = sum(1 for _ in train_img_dir.glob("*.jpg"))
total_val = sum(1 for _ in val_img_dir.glob("*.jpg"))

print(f"  Train: {total_train} images")
print(f"  Val:   {total_val} images")
print(f"  Total: {total_imgs} images, {total_lbls} annotations\n")

class_names = {0: "glass", 1: "metal", 2: "paper", 3: "plastic", 4: "trash"}
for cid in range(5):
    pct = class_counts[cid] / total_lbls * 100 if total_lbls else 0
    bar = "#" * int(pct / 2)
    print(f"  {class_names[cid]:8s}: {class_counts[cid]:5d} ({pct:5.1f}%) {bar}")
print(f"  {'TOTAL':8s}: {total_lbls:5d}")

# ============================================================
# WRITE dataset.yaml
# ============================================================
yaml_path = OUTPUT_DIR / "dataset.yaml"
yaml_content = f"""train: {OUTPUT_DIR / 'images' / 'train'}
val: {OUTPUT_DIR / 'images' / 'val'}
nc: 5
names: ['glass', 'metal', 'paper', 'plastic', 'trash']
"""
with open(yaml_path, "w") as f:
    f.write(yaml_content)
print(f"\nSaved: {yaml_path}")

print(f"\nDone! Dataset in: {OUTPUT_DIR}")
