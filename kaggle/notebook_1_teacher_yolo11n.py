"""Kaggle single-cell script: train the YOLO11n teacher."""

import shutil
import subprocess
import sys
from pathlib import Path
import zipfile

import torch
from IPython.display import FileLink, display

# 0. INSTALL ULTRALYTICS DEPENDENCY
print("Installing/Updating Ultralytics framework...")
subprocess.check_call([sys.executable, "-m", "pip", "install", "-q", "ultralytics"])

from ultralytics import YOLO

INPUT = Path("/kaggle/input")
WORK = Path("/kaggle/working")


def find_unique(root, pattern, description, required=True):
    matches = sorted(path for path in root.rglob(pattern) if path.is_file())
    if not matches and not required:
        return None
    if len(matches) != 1:
        found = "\n".join(f"  - {path}" for path in matches) or "  (none)"
        raise RuntimeError(f"Expected exactly one {description}; found {len(matches)}:\n{found}")
    return matches[0]


# 1. EXTRACT THE PORTABLE DATASET AND LOCATE ITS YAML
dataset_archive = find_unique(INPUT, "*merged_mira_balanced*.zip", "balanced dataset ZIP")
dataset_dir = WORK / "dataset"
if dataset_dir.exists():
    shutil.rmtree(dataset_dir)
with zipfile.ZipFile(dataset_archive) as archive:
    archive.extractall(dataset_dir)
source_yaml = find_unique(dataset_dir, "dataset.yaml", "dataset.yaml")
data_root = source_yaml.parent

print("Dataset Root Resolved:", data_root)

# 2. WRITE DATASET.YAML WITH ABSOLUTE PATHS
yaml_path = WORK / "dataset.yaml"
yaml_content = f"""train: {data_root}/images/train
val: {data_root}/images/val
test: {data_root}/images/test
nc: 5
names: ['glass', 'metal', 'paper', 'plastic', 'trash']
"""
yaml_path.write_text(yaml_content, encoding="utf-8")
print("YAML configuration written to:", yaml_path)

# 3. SET UP OUTPUT PATHS & CHECKPOINTS
runs = WORK / "runs"
run_dir = runs / "teacher_yolo11n"
last = run_dir / "weights" / "last.pt"

# Restore a previous run only when this session has no working checkpoint.
checkpoint_archive = find_unique(INPUT, "teacher_yolo11n.zip", "teacher checkpoint ZIP", required=False)
if not last.exists() and checkpoint_archive is not None:
    with zipfile.ZipFile(checkpoint_archive) as archive:
        archive.extractall(run_dir)

print("GPU Available:", torch.cuda.get_device_name(0) if torch.cuda.is_available() else "None (CPU)")

# 4. EXECUTE TRAINING / RESUME
if last.exists():
    print("Resuming teacher training from:", last)
    model = YOLO(str(last))
    model.train(resume=True)
else:
    print("Starting fresh YOLO11n Teacher training...")
    model = YOLO("yolo11n.pt")
    model.train(
        data=str(yaml_path),
        project=str(runs),
        name="teacher_yolo11n",
        exist_ok=True,
        device=0,
        workers=4,
        amp=True,
        epochs=120,
        time=8.8,
        batch=32,
        imgsz=640,
        optimizer="AdamW",
        lr0=0.001,
        cos_lr=True,
        close_mosaic=10,
    )

# 5. ZIP RESULTS AND DISPLAY DOWNLOAD LINK
if run_dir.exists():
    zip_path = WORK / "teacher_yolo11n"
    shutil.make_archive(
        str(zip_path),
        "zip",
        root_dir=str(run_dir),
    )
    print("\n" + "="*80)
    print("[SUCCESS] Teacher training results zipped successfully!")
    print("Click the link below to download your artifact:")
    print("="*80)
    display(FileLink("teacher_yolo11n.zip"))
else:
    print(f"[ERROR] Run directory not found at: {run_dir}")
