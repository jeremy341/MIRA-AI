"""Kaggle single-cell script: train YOLO11n (EXP-019)."""

import shutil
import subprocess
import sys
from collections import Counter
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


def make_selected_zip(zip_path, files, root):
    """Create a ZIP from explicit files without recursively archiving WORK."""
    zip_path.unlink(missing_ok=True)
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for file_path in files:
            file_path = Path(file_path)
            if file_path.is_file():
                archive.write(file_path, file_path.relative_to(root))


def find_unique(root, pattern, description, required=True):
    matches = sorted(path for path in root.rglob(pattern) if path.is_file())
    if not matches and not required:
        return None
    if len(matches) != 1:
        found = "\n".join(f"  - {path}" for path in matches) or "  (none)"
        raise RuntimeError(f"Expected exactly one {description}; found {len(matches)}:\n{found}")
    return matches[0]


def dataset_roots(root):
    """Find dataset roots containing images/ and labels/ train/val/test splits."""
    roots = set()
    for train_dir in root.rglob("images/train"):
        if not train_dir.is_dir():
            continue
        candidate = train_dir.parent.parent
        if all(
            (candidate / "images" / split).is_dir()
            and (candidate / "labels" / split).is_dir()
            for split in ("train", "val", "test")
        ):
            roots.add(candidate)
    return sorted(roots)


# 1. LOCATE THE DATASET.
# Kaggle may mount it as a directory (the normal dataset input) or provide a ZIP.
direct_roots = dataset_roots(INPUT)
if len(direct_roots) == 1:
    data_root = direct_roots[0]
    print("Using mounted dataset directory:", data_root)
else:
    if len(direct_roots) > 1:
        found = "\n".join(f"  - {path}" for path in direct_roots)
        raise RuntimeError(f"Found multiple valid dataset directories:\n{found}")

    dataset_archive = find_unique(INPUT, "*merged_mira_balanced*.zip", "balanced dataset ZIP")
    dataset_dir = WORK / "dataset"
    if dataset_dir.exists():
        shutil.rmtree(dataset_dir)
    with zipfile.ZipFile(dataset_archive) as archive:
        archive.extractall(dataset_dir)
    extracted_roots = dataset_roots(dataset_dir)
    if len(extracted_roots) != 1:
        raise RuntimeError(f"Expected exactly one valid dataset after extraction; found {len(extracted_roots)}")
    data_root = extracted_roots[0]

print("Dataset Root Resolved:", data_root)

# 1b. VERIFY DATASET
for split in ("train", "val", "test"):
    img_dir = data_root / "images" / split
    lbl_dir = data_root / "labels" / split
    image_extensions = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}
    image_stems = {path.stem for path in img_dir.iterdir() if path.suffix.lower() in image_extensions}
    label_stems = {path.stem for path in lbl_dir.glob("*.txt")}
    missing_labels = image_stems - label_stems
    orphan_labels = label_stems - image_stems
    if missing_labels or orphan_labels:
        raise RuntimeError(
            f"{split} split mismatch: {len(missing_labels)} images lack labels, "
            f"{len(orphan_labels)} labels lack images"
        )
    img_count = len(image_stems)
    cls_bins = Counter()
    total_boxes = 0
    if lbl_dir.is_dir():
        for lbl_path in lbl_dir.glob("*.txt"):
            for line in lbl_path.read_text().splitlines():
                parts = line.strip().split()
                if parts:
                    cls_bins[int(parts[0])] += 1
                    total_boxes += 1
    print(f"  {split}: {img_count} images, {total_boxes} boxes  |  glass={cls_bins[0]} metal={cls_bins[1]} paper={cls_bins[2]} plastic={cls_bins[3]} trash={cls_bins[4]}")

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
run_dir = runs / "exp019_yolo11n"
last = run_dir / "weights" / "last.pt"
best = run_dir / "weights" / "best.pt"

# Restore a previous run only when this session has no working checkpoint.
checkpoint_archive = find_unique(INPUT, "exp019_yolo11n.zip", "EXP-019 checkpoint ZIP", required=False)
if not last.exists() and checkpoint_archive is not None:
    with zipfile.ZipFile(checkpoint_archive) as archive:
        archive.extractall(run_dir)

print("GPU Available:", torch.cuda.get_device_name(0) if torch.cuda.is_available() else "None (CPU)")

# 4. EXECUTE TRAINING / RESUME
if best.exists():
    print("EXP-019 training already complete:", best)
    model = YOLO(str(best))
elif last.exists():
    print("Resuming EXP-019 training from:", last)
    model = YOLO(str(last))
    model.train(resume=True)
else:
    print("Starting fresh EXP-019 YOLO11n training...")
    model = YOLO("yolo11n.pt")
    model.train(
        data=str(yaml_path),
        project=str(runs),
        name="exp019_yolo11n",
        exist_ok=True,
        device=0,
        workers=4,
        amp=True,
        epochs=120,
        batch=32,
        imgsz=640,
        optimizer="AdamW",
        lr0=0.001,
        cos_lr=True,
        close_mosaic=10,
    )

# 5. EVALUATE
print("\n" + "=" * 60)
print("EVALUATING BEST MODEL")
print("=" * 60)
metrics = model.val(data=str(yaml_path), split="val")
map50 = metrics.box.map50
map50_95 = metrics.box.map
per_class = metrics.box.maps  # per-class mAP50-95 (list or array)
print(f"  mAP50:    {map50:.4f}")
print(f"  mAP50-95: {map50_95:.4f}")
names = ["glass", "metal", "paper", "plastic", "trash"]
for i, name in enumerate(names):
    if hasattr(metrics.box, "ap_class_index"):
        # Map class indices to names
        for j, cls_idx in enumerate(metrics.box.ap_class_index):
            if cls_idx == i and j < len(per_class):
                print(f"  {name}: mAP50={metrics.box.ap50[j]:.4f}  mAP50-95={per_class[j]:.4f}")
                break

# 6. QUICK SANITY CHECK — detect on a few val images
print("\n" + "=" * 60)
print("SANITY CHECK: Detection on 10 val images")
print("=" * 60)
val_img_dir = data_root / "images" / "val"
val_images = sorted(val_img_dir.glob("*.*"))[:10]
detections_found = 0
for img_path in val_images:
    r = model.predict(str(img_path), imgsz=640, conf=0.25, verbose=False)
    n = len(r[0].boxes) if r[0].boxes else 0
    detections_found += min(n, 1)
    prints = []
    for box in r[0].boxes if r[0].boxes else []:
        cls_name = names[int(box.cls[0])]
        conf = float(box.conf[0])
        prints.append(f"{cls_name}@{conf:.2f}")
    print(f"  {img_path.name}: {n} dets  {'  '.join(prints)}")
print(f"\n  Images with detections: {detections_found}/{len(val_images)}")

# 7. EXPORT
print("\n" + "=" * 60)
print("EXPORTING MODELS")
print("=" * 60)

# 7a. PyTorch best.pt — copy with clean name
export_pt = WORK / "mira_exp019.pt"
if best.exists():
    shutil.copy2(str(best), str(export_pt))
    print(f"Copied best.pt -> {export_pt}")

# 7b. TFLite Full Integer Quantization at 640px
print("\nExporting TFLite INT8 (full integer, 640px)...")
model.export(format="tflite", int8=True, data=str(yaml_path), imgsz=640)
# Move exported file to clean name
export_tflite_640 = WORK / "mira_exp019_int8_640.tflite"
tflite_candidates = sorted(run_dir.rglob("*.tflite"))
if tflite_candidates:
    shutil.copy2(str(tflite_candidates[-1]), str(export_tflite_640))
    print(f"TFLite INT8 640px: {export_tflite_640} ({export_tflite_640.stat().st_size/1024:.0f} KB)")

# 7c. TFLite Full Integer Quantization at 320px (for CPU/RPi)
print("\nExporting TFLite INT8 (full integer, 320px)...")
model.export(format="tflite", int8=True, data=str(yaml_path), imgsz=320)
export_tflite_320 = WORK / "mira_exp019_int8_320.tflite"
tflite_candidates2 = sorted(run_dir.rglob("*.tflite"))
new_candidates = [p for p in tflite_candidates2 if p not in tflite_candidates]
if new_candidates:
    shutil.copy2(str(new_candidates[-1]), str(export_tflite_320))
    print(f"TFLite INT8 320px: {export_tflite_320} ({export_tflite_320.stat().st_size/1024:.0f} KB)")
elif tflite_candidates:
    # Fallback: last exported tflite is the 320 one
    fresh = sorted(run_dir.rglob("*.tflite"))[-1]
    shutil.copy2(str(fresh), str(export_tflite_320))
    print(f"TFLite INT8 320px: {export_tflite_320} ({export_tflite_320.stat().st_size/1024:.0f} KB)")

# 7d. ONNX
print("\nExporting ONNX...")
model.export(format="onnx", imgsz=640)
export_onnx = WORK / "mira_exp019.onnx"
onnx_candidates = sorted(run_dir.rglob("*.onnx"))
if onnx_candidates:
    shutil.copy2(str(onnx_candidates[-1]), str(export_onnx))
    print(f"ONNX: {export_onnx} ({export_onnx.stat().st_size/1024:.0f} KB)")

# 8. WRITE RESULTS SUMMARY
summary = WORK / "EXP019_RESULTS.txt"
with open(summary, "w") as f:
    f.write("EXP-019: YOLO11n trained on merged_mira_balanced (no SortWaste)\n")
    f.write(f"{'='*60}\n")
    f.write("Dataset: 5,108 train / 415 val (TrashNet tabletop) / 1,375 test\n")
    f.write("Epochs: 120, Batch: 32, Imgsz: 640, Optimizer: AdamW, lr0=0.001\n")
    f.write(f"\nmAP50:    {map50:.4f}\n")
    f.write(f"mAP50-95: {map50_95:.4f}\n")
    f.write(f"Sanity check: {detections_found}/{len(val_images)} val images have detections at conf=0.25\n")
print(f"\nResults summary: {summary}")

# 9. ZIP RESULTS AND DISPLAY DOWNLOAD LINK
# Archive only the intended files. Do not archive all of WORK: that can include
# the archive itself and cause unbounded growth or fill Kaggle's disk.
zip_path = WORK / "exp019_yolo11n.zip"
make_selected_zip(zip_path, run_dir.rglob("*"), run_dir)

export_zip = WORK / "exp019_exports.zip"
export_files = [
    WORK / "mira_exp019.pt",
    WORK / "mira_exp019_int8_640.tflite",
    WORK / "mira_exp019_int8_320.tflite",
    WORK / "mira_exp019.onnx",
    WORK / "EXP019_RESULTS.txt",
]
make_selected_zip(export_zip, export_files, WORK)

print("\n" + "=" * 60)
print("[SUCCESS] EXP-019 complete!")
print("=" * 60)
print("Download links:")
display(FileLink("exp019_yolo11n.zip"))
if WORK.joinpath("exp019_exports.zip").exists():
    display(FileLink("exp019_exports.zip"))
