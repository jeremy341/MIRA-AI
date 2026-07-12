import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATASETS = ROOT / "datasets"

TACO_TRASHNET_DIR = DATASETS / "mira_v2"
ROBOFLOW_DIR = DATASETS / "Trash Detection.yolov8 (1)"
WARP_DIR = DATASETS / "WaRP"  # <-- rename your WaRP folder to this
OUTPUT_DIR = DATASETS / "All_TACO+TrashNet+Roboflow+WaRP"

# Roboflow 64 classes -> 5 MIRA classes
ROBOFLOW_MAPPING = {
    4: 0, 20: 0, 21: 0, 22: 0, 23: 0,
    0: 1, 1: 1, 2: 1, 12: 1, 17: 1, 26: 1, 27: 1, 28: 1, 49: 1, 51: 1,
    8: 2, 13: 2, 14: 2, 24: 2, 25: 2, 29: 2, 30: 2, 36: 2, 37: 2, 38: 2, 39: 2, 40: 2, 58: 2, 59: 2, 63: 2,
    7: 3, 9: 3, 10: 3, 11: 3, 15: 3, 16: 3, 19: 3, 31: 3, 32: 3, 33: 3, 34: 3, 35: 3,
    41: 3, 42: 3, 43: 3, 44: 3, 45: 3, 46: 3, 47: 3, 48: 3, 53: 3, 54: 3, 55: 3, 56: 3, 60: 3,
    3: 4, 5: 4, 6: 4, 18: 4, 50: 4, 52: 4, 57: 4, 61: 4, 62: 4
}

# WaRP 28 classes -> 5 MIRA classes
# Fill in once you check WaRP's data.yaml
WARP_MAPPING = {
}

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
    print(f"  {split}: {count} images total")

# --- Step 2: Add Roboflow (64->5 remap) ---
print("\nAdding Roboflow Trash Detection (64 to 5 remap)...")
roboflow_map = {"train": "train", "valid": "val", "test": "val"}
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

print(f"  Added: {added} images | Skipped: {skipped}")

# --- Step 3: Add WaRP (28->5 remap) ---
print("\nAdding WaRP (28 to 5 remap)...")
added_warp = 0
skipped_warp = 0

for warp_split in ["train", "valid", "test"]:
    target_split = "train" if warp_split == "train" else "val"
    img_src = WARP_DIR / warp_split / "images"
    lbl_src = WARP_DIR / warp_split / "labels"
    dst_img = OUTPUT_DIR / "images" / target_split
    dst_lbl = OUTPUT_DIR / "labels" / target_split

    if not lbl_src.exists():
        continue

    for lbl_file in lbl_src.glob("*.txt"):
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
                skipped_warp += 1
        if new_lines:
            img_file = img_src / f"{lbl_file.stem}.jpg"
            if not img_file.exists():
                img_file = img_src / f"{lbl_file.stem}.png"
            if img_file.exists():
                shutil.copy2(img_file, dst_img / img_file.name)
                with open(dst_lbl / lbl_file.name, "w") as f:
                    f.writelines(new_lines)
                added_warp += 1

print(f"  Added: {added_warp} images | Skipped: {skipped_warp}")

# --- Step 4: Stats ---
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
print(f"Model 4: All (TACO + TrashNet + Roboflow + WaRP)")
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
