# ============================================================
# MIRA-AI: SAM Auto-Labeling for TrashNet
# Generates proper bounding boxes replacing full-image bboxes
# ============================================================
# Run on Kaggle with GPU. Attach TrashNet as dataset input.

import os, shutil, random
from pathlib import Path

# ============================================================
# CONFIG
# ============================================================
# Auto-discover TrashNet dataset in /kaggle/input/
INPUT_DIR = "/kaggle/input"
if Path(INPUT_DIR).exists():
    possible = [d for d in Path(INPUT_DIR).iterdir() if d.is_dir()]
    if possible:
        data_root = possible[0]
        # Check if dataset-resized/ is a subdir
        candidate = data_root / "dataset-resized"
        if candidate.exists():
            TRASHNET_DIR = candidate
        else:
            TRASHNET_DIR = data_root
        print(f"Auto-detected TrashNet: {TRASHNET_DIR}")
    else:
        TRASHNET_DIR = Path("/kaggle/input/trashnet-resized/dataset-resized")
else:
    TRASHNET_DIR = Path(r"C:\Users\jerem\Documents\Jugend Forscht\MIRA-AI\archive (1)\dataset-resized")

OUTPUT_DIR = Path("/kaggle/working/trashnet_labeled")
DEVICE = 0

# Class mapping (folder name -> MIRA class ID)
CLASS_MAP = {
    "cardboard": 2,  # cardboard -> paper
    "glass": 0,
    "metal": 1,
    "paper": 2,
    "plastic": 3,
    "trash": 4,
}

# ============================================================
# INSTALL
# ============================================================
import subprocess, sys
subprocess.check_call([sys.executable, "-m", "pip", "install", "-q", "ultralytics"])
subprocess.check_call([sys.executable, "-m", "pip", "install", "-q", "opencv-python"])

from ultralytics import SAM
import numpy as np
import cv2

# ============================================================
# LOAD MOBILE-SAM (lightweight, fast)
# ============================================================
print("Loading MobileSAM...")
model = SAM("mobile_sam.pt")
print("MobileSAM loaded.")

# ============================================================
# COLLECT IMAGES
# ============================================================
samples = []
for class_dir in sorted(TRASHNET_DIR.iterdir()):
    if not class_dir.is_dir() or class_dir.name not in CLASS_MAP:
        continue
    class_id = CLASS_MAP[class_dir.name]
    for img_file in class_dir.glob("*.*"):
        if img_file.suffix.lower() in (".jpg", ".jpeg", ".png"):
            samples.append((img_file, class_id))

print(f"Found {len(samples)} TrashNet images to label")

# ============================================================
# CREATE OUTPUT DIRS
# ============================================================
train_img_dir = OUTPUT_DIR / "images" / "train"
train_lbl_dir = OUTPUT_DIR / "labels" / "train"
val_img_dir = OUTPUT_DIR / "images" / "val"
val_lbl_dir = OUTPUT_DIR / "labels" / "val"
for d in [train_img_dir, train_lbl_dir, val_img_dir, val_lbl_dir]:
    d.mkdir(parents=True, exist_ok=True)

# ============================================================
# RUN SAM INFERENCE
# ============================================================
print("\nRunning SAM auto-labeling...")
random.seed(42)
random.shuffle(samples)
split_idx = int(len(samples) * 0.8)
train_samples = samples[:split_idx]
val_samples = samples[split_idx:]

def process_samples(samples, img_dir, lbl_dir, split_name):
    total = len(samples)
    success = 0
    no_mask = 0
    
    for idx, (img_path, class_id) in enumerate(samples):
        stem = img_path.stem
        dst_img = img_dir / f"{stem}.jpg"
        dst_lbl = lbl_dir / f"{stem}.txt"
        
        # Validate image can be read
        test_img = cv2.imread(str(img_path))
        if test_img is None:
            print(f"  Skipping bad image: {img_path.name}")
            shutil.copy2(img_path, dst_img)
            with open(dst_lbl, "w") as f:
                f.write(f"{class_id} 0.5 0.5 1.0 1.0\n")
            no_mask += 1
            continue
        
        # Run SAM prediction
        try:
            results = model.predict(img_path, device=DEVICE, verbose=False)
        except Exception as e:
            print(f"  SAM failed on {img_path.name}: {e}")
            shutil.copy2(img_path, dst_img)
            with open(dst_lbl, "w") as f:
                f.write(f"{class_id} 0.5 0.5 1.0 1.0\n")
            no_mask += 1
            continue
        
        # Copy image
        shutil.copy2(img_path, dst_img)
        
        # Try to extract bbox from SAM masks
        box_found = False
        if results[0].masks is not None and len(results[0].masks) > 0:
            masks = results[0].masks.data.cpu().numpy()
            
            # Pick the largest mask (main object)
            areas = [mask.sum() for mask in masks]
            best_idx = int(np.argmax(areas))
            best_mask = masks[best_idx]
            
            # Convert mask to bbox
            ys, xs = np.where(best_mask > 0)
            if len(xs) > 0 and len(ys) > 0:
                x1, y1 = xs.min(), ys.min()
                x2, y2 = xs.max(), ys.max()
                h, w = best_mask.shape
                
                # Convert to YOLO format (x_center, y_center, width, height) normalized
                xc = ((x1 + x2) / 2) / w
                yc = ((y1 + y2) / 2) / h
                bw = (x2 - x1) / w
                bh = (y2 - y1) / h
                
                # Clamp to [0, 1]
                xc = max(0, min(1, xc))
                yc = max(0, min(1, yc))
                bw = max(0, min(1, bw))
                bh = max(0, min(1, bh))
                
                with open(dst_lbl, "w") as f:
                    f.write(f"{class_id} {xc:.6f} {yc:.6f} {bw:.6f} {bh:.6f}\n")
                box_found = True
                success += 1
        
        if not box_found:
            # Fallback to full-image bbox
            with open(dst_lbl, "w") as f:
                f.write(f"{class_id} 0.5 0.5 1.0 1.0\n")
            no_mask += 1
        
        if (idx + 1) % 50 == 0:
            print(f"  {split_name}: {idx+1}/{total} (masks: {success}, fallback: {no_mask})")
    
    print(f"  {split_name} done: {total} images | SAM bboxes: {success} | fallback: {no_mask}")

print("\nProcessing training set...")
process_samples(train_samples, train_img_dir, train_lbl_dir, "Train")
print("\nProcessing validation set...")
process_samples(val_samples, val_img_dir, val_lbl_dir, "Val")

# ============================================================
# SUMMARY
# ============================================================
total_train = sum(1 for _ in train_img_dir.glob("*.jpg"))
total_val = sum(1 for _ in val_img_dir.glob("*.jpg"))
print(f"\nDone! {total_train} train + {total_val} val = {total_train + total_val} images labeled with SAM bboxes.")
print(f"Output: {OUTPUT_DIR}")
