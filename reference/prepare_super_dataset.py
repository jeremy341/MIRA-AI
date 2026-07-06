import cv2
import numpy as np
import pathlib
import random
import shutil

# 1. PFADE UND ORTE AUFLÖSEN
SCRIPT_DIR = pathlib.Path(__file__).resolve().parent
ROOT_DIR = SCRIPT_DIR.parent
WILD_DIR = ROOT_DIR / "wild_data"
CLASSES_DIR = ROOT_DIR / "data" / "classes"

# Isoliertes Ausgabe-Verzeichnis, um yolo_data nicht zu überschreiben [2]
OUTPUT_DIR = ROOT_DIR / "mira_wild_data"

# Bereinige und erstelle die Zielordner-Struktur [2]
if OUTPUT_DIR.exists():
    shutil.rmtree(OUTPUT_DIR)
for split in ['train', 'val']:
    (OUTPUT_DIR / "images" / split).mkdir(parents=True, exist_ok=True)
    (OUTPUT_DIR / "labels" / split).mkdir(parents=True, exist_ok=True)

CLASSES = ['glass', 'metal', 'paper', 'plastic', 'trash']
CLASS_TO_ID = {name: idx for idx, name in enumerate(CLASSES)}

random.seed(123)
np.random.seed(123)

# 2. KLASSEN-MAPPING DEFINIEREN (64 Klassen -> 5 MIRA-Klassen) [2]
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
    # Trash
    3: 4, 5: 4, 6: 4, 18: 4, 50: 4, 52: 4, 57: 4, 61: 4, 62: 4
}


# 3. KANTENDETEKTION FÜR SAUBERE BILDER (Auto-Labeling) [2]
def get_bounding_box(image):
    """
    Berechnet die Bounding Box auf einheitlichen Hintergründen mittels Canny-Kanten.
    Fällt bei Fehlern auf eine Standard-Box (70% des Bildbereichs) zurück.
    """
    h, w = image.shape[:2]
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)

    edges = cv2.Canny(blurred, 50, 150)
    dilated = cv2.dilate(edges, None, iterations=2)

    contours, _ = cv2.findContours(dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    if not contours:
        return 0.5, 0.5, 0.7, 0.7

    largest_contour = max(contours, key=cv2.contourArea)
    if cv2.contourArea(largest_contour) < 500:
        return 0.5, 0.5, 0.7, 0.7

    x, y, box_w, box_h = cv2.boundingRect(largest_contour)

    if box_w < 30 or box_h < 30:
        return 0.5, 0.5, 0.7, 0.7

    x_center = (x + box_w / 2.0) / w
    y_center = (y + box_h / 2.0) / h
    norm_w = box_w / w
    norm_h = box_h / h

    return x_center, y_center, norm_w, norm_h


# 4. VERARBEITUNGS-FUNKTIONEN
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
            img_file = img_src / f"{lbl_file.stem}.jpg"
            if not img_file.exists():
                img_file = img_src / f"{lbl_file.stem}.png"

            shutil.copy(img_file, img_dest / img_file.name)
            with open(lbl_dest / lbl_file.name, 'w') as f:
                f.writelines(new_lines)


def process_clean_data(entries, target_split):
    img_dest = OUTPUT_DIR / "images" / target_split
    lbl_dest = OUTPUT_DIR / "labels" / target_split

    for idx, (img_path, class_name) in enumerate(entries):
        img = cv2.imread(str(img_path))
        if img is None:
            continue

        bbox = get_bounding_box(img)
        file_id = f"clean_{class_name}_{img_path.stem}_{idx}"

        shutil.copy(str(img_path), str(img_dest / f"{file_id}.jpg"))

        class_id = CLASS_TO_ID[class_name]
        with open(lbl_dest / f"{file_id}.txt", "w") as f:
            f.write(f"{class_id} {bbox[0]:.6f} {bbox[1]:.6f} {bbox[2]:.6f} {bbox[3]:.6f}\n")


# 5. EXECUTION PIPELINE [2]
# Remap Roboflow wild data
process_wild_data(WILD_DIR, "train", "train")
process_wild_data(WILD_DIR, "valid", "val")
process_wild_data(WILD_DIR, "test", "val")

# Process and merge local clean classes [2]
print("Processing local clean raw classes...")
clean_entries = []
for class_name in CLASSES:
    class_folder = CLASSES_DIR / class_name
    if class_folder.exists():
        img_paths = list(class_folder.glob("*.jpg")) + list(class_folder.glob("*.png")) + list(
            class_folder.glob("*.jpeg"))
        for p in img_paths:
            clean_entries.append((p, class_name))

random.shuffle(clean_entries)
split_idx = int(len(clean_entries) * 0.8)
train_entries = clean_entries[:split_idx]
val_entries = clean_entries[split_idx:]

print("Merging clean training splits...")
process_clean_data(train_entries, "train")
print("Merging clean validation splits...")
process_clean_data(val_entries, "val")

# 6. CONFIGURATION SPEICHERN (dataset.yaml)
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

print(f"Pristine Wild Calibration Dataset successfully generated under {OUTPUT_DIR}")