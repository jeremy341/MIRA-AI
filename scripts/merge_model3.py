import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATASETS = ROOT / "datasets"

WARP_DIR = DATASETS / "WaRP"  # <-- rename your WaRP folder to this
OUTPUT_DIR = DATASETS / "WaRP"

# WaRP 28 classes -> 5 MIRA classes
# 0:glass, 1:metal, 2:paper, 3:plastic, 4:trash
WARP_MAPPING = {
    # Fill in once you check WaRP's data.yaml
}

# Create output structure
for split in ["train", "val"]:
    (OUTPUT_DIR / "images" / split).mkdir(parents=True, exist_ok=True)
    (OUTPUT_DIR / "labels" / split).mkdir(parents=True, exist_ok=True)

print("Copying WaRP (28 to 5 remap)...")
added = 0
skipped = 0

for warp_split in ["train", "valid", "test"]:
    target_split = "train" if warp_split == "train" else "val"
    img_src = WARP_DIR / warp_split / "images"
    lbl_src = WARP_DIR / warp_split / "labels"
    dst_img = OUTPUT_DIR / "images" / target_split
    dst_lbl = OUTPUT_DIR / "labels" / target_split

    if not lbl_src.exists():
        print(f"  Skipping {warp_split}/labels - not found")
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

print(f"  Added: {added} images | Skipped: {skipped} annotations (unmapped)")

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
print(f"Model 3: WaRP only")
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
