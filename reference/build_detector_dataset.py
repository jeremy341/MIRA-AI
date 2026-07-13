import cv2
import numpy as np
import pathlib
import random
import shutil

# 1. PATH RESOLUTION
SCRIPT_DIR = pathlib.Path(__file__).resolve().parent
ROOT_DIR = SCRIPT_DIR.parent
DATA_DIR = ROOT_DIR / "data"
CLASSES_DIR = DATA_DIR / "classes"

# The output folder sits safely at the root level [2]
YOLO_DIR = ROOT_DIR / "yolo_data"
IMAGES_TRAIN = YOLO_DIR / "images" / "train"
IMAGES_VAL = YOLO_DIR / "images" / "val"
LABELS_TRAIN = YOLO_DIR / "labels" / "train"
LABELS_VAL = YOLO_DIR / "labels" / "val"

# Clean and recreate YOLO directory structure [2]
if YOLO_DIR.exists():
    shutil.rmtree(YOLO_DIR)
for folder in [IMAGES_TRAIN, IMAGES_VAL, LABELS_TRAIN, LABELS_VAL]:
    folder.mkdir(parents=True, exist_ok=True)

# 5-Class Target System [2]
CLASSES = ['glass', 'metal', 'paper', 'plastic', 'trash']
CLASS_TO_ID = {name: idx for idx, name in enumerate(CLASSES)}

random.seed(123)


def get_bounding_box(image):
    """
    Finds the centered object using Canny Edge Detection and morphological dilation.
    If detection fails or is suspiciously small, falls back to a standard central 70% box.
    """
    h, w = image.shape[:2]
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)

    # Canny Edge Detection
    edges = cv2.Canny(blurred, 50, 150)
    # Dilate edges to close gaps in contours
    dilated = cv2.dilate(edges, None, iterations=2)

    contours, _ = cv2.findContours(dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    # Fallback: Assume the object is centered and occupies 70% of the frame [2]
    if not contours:
        return 0.5, 0.5, 0.7, 0.7

    largest_contour = max(contours, key=cv2.contourArea)
    x, y, box_w, box_h = cv2.boundingRect(largest_contour)

    # Fallback if the detected box is too small (noise) [2]
    if box_w < 30 or box_h < 30:
        return 0.5, 0.5, 0.7, 0.7

    # Calculate YOLO normalized coordinates (center_x, center_y, width, height) [2]
    x_center = (x + box_w / 2.0) / w
    y_center = (y + box_h / 2.0) / h
    norm_w = box_w / w
    norm_h = box_h / h

    return x_center, y_center, norm_w, norm_h


# 2. DATASET PROCESSING
print("Starting YOLO dataset auto-labeling on clean images...")

dataset_entries = []

for class_name in CLASSES:
    class_folder = CLASSES_DIR / class_name
    if not class_folder.exists():
        print(f"Warning: Class folder {class_name} not found, skipping.")
        continue

    img_paths = list(class_folder.glob("*.jpg")) + list(class_folder.glob("*.png")) + list(class_folder.glob("*.jpeg"))
    for img_path in img_paths:
        dataset_entries.append((img_path, class_name))

random.shuffle(dataset_entries)

# 80/20 Train-Validation Split [2]
split_idx = int(len(dataset_entries) * 0.8)
train_entries = dataset_entries[:split_idx]
val_entries = dataset_entries[split_idx:]


def process_and_save(entries, img_dir, label_dir):
    valid_count = 0
    for idx, (img_path, class_name) in enumerate(entries):
        img = cv2.imread(str(img_path))
        if img is None:
            continue

        bbox = get_bounding_box(img)
        file_id = f"{class_name}_{img_path.stem}_{idx}"

        # Copy original image cleanly without altering it [2]
        shutil.copy(str(img_path), str(img_dir / f"{file_id}.jpg"))

        # Save YOLO label format
        class_id = CLASS_TO_ID[class_name]
        with open(label_dir / f"{file_id}.txt", "w") as f:
            f.write(f"{class_id} {bbox[0]:.6f} {bbox[1]:.6f} {bbox[2]:.6f} {bbox[3]:.6f}\n")

        valid_count += 1
        if valid_count % 500 == 0:
            print(f"Processed {valid_count} images...")

    return valid_count


print(f"Processing training data ({len(train_entries)} items)...")
train_count = process_and_save(train_entries, IMAGES_TRAIN, LABELS_TRAIN)

print(f"Processing validation data ({len(val_entries)} items)...")
val_count = process_and_save(val_entries, IMAGES_VAL, LABELS_VAL)

print(f"Dataset complete. Train: {train_count} | Val: {val_count}")

# 3. WRITE DATASET.YAML [2]
yaml_content = f"""path: {str(YOLO_DIR)}
train: images/train
val: images/val

names:
  0: glass
  1: metal
  2: paper
  3: plastic
  4: trash
"""
with open(YOLO_DIR / "dataset.yaml", "w") as f:
    f.write(yaml_content)

print(f"YOLO configuration written to {YOLO_DIR / 'dataset.yaml'}")