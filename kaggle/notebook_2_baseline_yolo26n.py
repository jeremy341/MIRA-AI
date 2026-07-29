"""Kaggle single-cell script: train the YOLO26n baseline."""

from pathlib import Path
import shutil
import torch
import zipfile

from ultralytics import YOLO

INPUT = Path("/kaggle/input")
WORK = Path("/kaggle/working/mira_baseline")
WORK.mkdir(exist_ok=True)

archive = next(INPUT.rglob("*merged_mira_balanced*.zip"))
with zipfile.ZipFile(archive) as z:
    z.extractall(WORK)

yaml_path = next(WORK.rglob("dataset.yaml"))
yaml_path.write_text(
    "path: .\n"
    "train: images/train\n"
    "val: images/val\n"
    "test: images/test\n"
    "nc: 5\n"
    "names: ['glass', 'metal', 'paper', 'plastic', 'trash']\n"
)

runs = WORK / "runs"
run_dir = runs / "baseline_yolo26n"
last = run_dir / "weights" / "last.pt"
best = run_dir / "weights" / "best.pt"

print("GPU:", torch.cuda.get_device_name(0) if torch.cuda.is_available() else "CPU")

if best.exists():
    print("Baseline already complete:", best)
elif last.exists():
    print("Resuming baseline")
    YOLO(str(last)).train(resume=True)
else:
    YOLO("yolo26n.pt").train(
        data=str(yaml_path),
        project=str(runs),
        name="baseline_yolo26n",
        exist_ok=True,
        device=0,
        workers=4,
        amp=True,
        epochs=120,
        time=8.8,
        batch=32,
        imgsz=640,
        optimizer="MuSGD",
        cos_lr=True,
        close_mosaic=10,
    )

result = shutil.make_archive(
    "/kaggle/working/baseline_yolo26n",
    "zip",
    root_dir=run_dir,
)
print("Download this artifact:", result)
