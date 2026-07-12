# ============================================================
# MIRA-AI: YOLO11n Training Script (Kaggle GPU)
# Target: Edge deployment on Raspberry Pi
# ============================================================
# Upload dataset as ZIP to Kaggle, attach to notebook.
# Set DATASET_NAME below to match your Kaggle dataset name.

import os
from pathlib import Path

# ============================================================
# 1. CONFIG — Change this for each model
# ============================================================
DATASET_NAME = "TACO+TrashNet+Roboflow"  # Model 1
EPOCHS = 120
BATCH_SIZE = 32
IMG_SIZE = 640
PATIENCE = 30
DEVICE = 0  # 0 = GPU

# ============================================================
# 2. INSTALL DEPENDENCIES
# ============================================================
import subprocess, sys
subprocess.check_call([sys.executable, "-m", "pip", "install", "-q", "ultralytics"])

from ultralytics import YOLO

# ============================================================
# 3. FIND DATASET
# ============================================================
INPUT_DIR = "/kaggle/input"
data_root = None

for d in Path(INPUT_DIR).iterdir():
    if d.is_dir() and DATASET_NAME.lower().replace("+", "-") in d.name.lower().replace("+", "-").replace(" ", "-"):
        data_root = d
        break

if data_root is None:
    for d in Path(INPUT_DIR).iterdir():
        if d.is_dir() and (d / "images").exists():
            data_root = d
            break

if data_root is None:
    for d in Path(INPUT_DIR).iterdir():
        if d.is_dir():
            for sub in d.rglob("images/train"):
                if sub.is_dir():
                    data_root = sub.parent.parent
                    break
            if data_root:
                break

if data_root is None:
    raise FileNotFoundError(f"Dataset '{DATASET_NAME}' not found in {INPUT_DIR}")

print(f"Dataset: {data_root}")
train_imgs = list(data_root.rglob("images/train/*.jpg")) + list(data_root.rglob("images/train/*.png"))
val_imgs = list(data_root.rglob("images/val/*.jpg")) + list(data_root.rglob("images/val/*.png"))
print(f"  Train: {len(train_imgs)} images")
print(f"  Val:   {len(val_imgs)} images")

# ============================================================
# 4. WRITE dataset.yaml
# ============================================================
WORK_DIR = "/kaggle/working"
yaml_path = Path(WORK_DIR) / "dataset.yaml"
yaml_content = f"""train: {data_root}/images/train
val: {data_root}/images/val
nc: 5
names: ['glass', 'metal', 'paper', 'plastic', 'trash']
"""
yaml_path.write_text(yaml_content)
print(f"Written: {yaml_path}")

# ============================================================
# 5. TRAIN
# ============================================================
print(f"\nStarting training: {DATASET_NAME}...")
model = YOLO("yolo11n.pt")

results = model.train(
    data=str(yaml_path),
    epochs=EPOCHS,
    batch=BATCH_SIZE,
    imgsz=IMG_SIZE,
    patience=PATIENCE,
    device=DEVICE,
    project=str(Path(WORK_DIR) / "runs"),
    name=DATASET_NAME,
    exist_ok=True,
    amp=True,
    workers=4,
    lr0=0.01,
    lrf=0.01,
    momentum=0.937,
    weight_decay=0.0005,
    warmup_epochs=3,
    warmup_momentum=0.8,
    box=7.5,
    cls=0.5,
    dfl=1.5,
    hsv_h=0.015,
    hsv_s=0.7,
    hsv_v=0.4,
    degrees=0.0,
    translate=0.1,
    scale=0.5,
    shear=0.0,
    perspective=0.0,
    flipud=0.0,
    fliplr=0.5,
    mosaic=1.0,
    mixup=0.1,
    copy_paste=0.1,
)

# ============================================================
# 6. EVALUATE
# ============================================================
print("\nEvaluating...")
metrics = model.val()
print(f"\n  mAP50:    {metrics.box.map50:.3f}")
print(f"  mAP50-95: {metrics.box.map:.3f}")

# ============================================================
# 7. EXPORT
# ============================================================
print("\nExporting to TFLite INT8...")
model.export(format="tflite", int8=True, imgsz=IMG_SIZE)
print("  TFLite INT8 exported")

model.export(format="onnx", imgsz=IMG_SIZE)
print("  ONNX exported")

print(f"\nDone! Results in: {WORK_DIR}/runs/{DATASET_NAME}/weights/")
