import pathlib
import shutil

# 1. PFADE DEFINIEREN
ROOT_DIR = pathlib.Path(__file__).resolve().parent.parent
WILD_DIR = ROOT_DIR / "wild_data"
CLEAN_DIR = ROOT_DIR / "clean_data"  # Your auto-labeled TrashNet
OUTPUT_DIR = ROOT_DIR / "yolo_data"

# Struktur für das finale Dataset
for split in ['train', 'val']:
    (OUTPUT_DIR / "images" / split).mkdir(parents=True, exist_ok=True)
    (OUTPUT_DIR / "labels" / split).mkdir(parents=True, exist_ok=True)

# 2. MAPPING DEFINIEREN (Roboflow Index -> MIRA ID)
# 0:glass, 1:metal, 2:paper, 3:plastic, 4:trash
MAPPING = {
    # Glass
    4: 0, 20: 0, 21: 0, 22: 0, 23: 0,
    # Metal
    0: 1, 1: 1, 2: 1, 12: 1, 17: 1, 26: 1, 27: 1, 28: 1, 49: 1, 51: 1,
    # Paper
    8: 2, 13: 2, 14: 2, 24: 2, 25: 2, 29: 2, 30: 2, 36: 2, 37: 2, 38: 2, 39: 2, 40: 2, 58: 2, 59: 2, 63: 2,
    # Plastic
    7: 3, 9: 3, 10: 3, 11: 3, 15: 3, 16: 3, 19: 3, 31: 3, 32: 3, 33: 3, 34: 3, 35: 3,
    41: 3, 42: 3, 43: 3, 44: 3, 45: 3, 46: 3, 47: 3, 48: 3, 53: 3, 54: 3, 55: 3, 56: 3, 60: 3,
    # Trash (Reject)
    3: 4, 5: 4, 6: 4, 18: 4, 50: 4, 52: 4, 57: 4, 61: 4, 62: 4
}


def process_wild_data(source_dir, split_name, target_split):
    img_src = source_dir / split_name / "images"
    lbl_src = source_dir / split_name / "labels"

    img_dest = OUTPUT_DIR / "images" / target_split
    lbl_dest = OUTPUT_DIR / "labels" / target_split

    print(f"Processing Wild Data ({split_name})...")
    for lbl_file in lbl_src.glob("*.txt"):
        with open(lbl_file, 'r') as f:
            lines = f.readlines()

        new_lines = []
        for line in lines:
            parts = line.split()
            old_id = int(parts[0])
            if old_id in MAPPING:
                new_id = MAPPING[old_id]
                new_lines.append(f"{new_id} {' '.join(parts[1:])}\n")

        if new_lines:
            # Copy image
            img_file = img_src / f"{lbl_file.stem}.jpg"
            if not img_file.exists(): img_file = img_src / f"{lbl_file.stem}.png"

            shutil.copy(img_file, img_dest / img_file.name)
            # Write new label
            with open(lbl_dest / lbl_file.name, 'w') as f:
                f.writelines(new_lines)


# 3. AUSFÜHRUNG
# Remap Roboflow Data (Mapping validation and test into 'val' split for simplicity)
process_wild_data(WILD_DIR, "train", "train")
process_wild_data(WILD_DIR, "valid", "val")
process_wild_data(WILD_DIR, "test", "val")

# Copy Clean Data (assuming it's already 0-4)
print("Merging Clean Data...")
for split in ['train', 'val']:
    for f in (CLEAN_DIR / "images" / split).glob("*"):
        shutil.copy(f, OUTPUT_DIR / "images" / split / f.name)
    for f in (CLEAN_DIR / "labels" / split).glob("*"):
        shutil.copy(f, OUTPUT_DIR / "labels" / split / f.name)

# 4. GENERATE YAML
yaml_content = f"""path: {str(OUTPUT_DIR)}
train: images/train
val: images/val

names:
  0: glass
  1: metal
  2: paper
  3: plastic
  4: trash
"""
with open(OUTPUT_DIR / "dataset.yaml", 'w') as f:
    f.write(yaml_content)

print(f"Super Dataset ready in {OUTPUT_DIR}")

