"""Kaggle single-cell script: train the YOLO11x teacher."""

from pathlib import Path
import shutil
import torch
import zipfile

from ultralytics import YOLO

INPUT = Path("/kaggle/input")
WORK = Path("/kaggle/working/mira_teacher")
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
run_dir = runs / "teacher_yolo11x"
last = run_dir / "weights" / "last.pt"
best = run_dir / "weights" / "best.pt"

print("GPU:", torch.cuda.get_device_name(0) if torch.cuda.is_available() else "CPU")

if best.exists():
    print("Teacher already complete:", best)
elif last.exists():
    print("Resuming teacher")
    YOLO(str(last)).train(resume=True)
else:
    YOLO("yolo11x.pt").train(
        data=str(yaml_path),
        project=str(runs),
        name="teacher_yolo11x",
        exist_ok=True,
        device=0,
        workers=4,
        amp=True,
        epochs=120,
        time=8.8,
        batch=4,
        imgsz=1024,
        optimizer="AdamW",
        lr0=0.001,
        cos_lr=True,
        close_mosaic=10,
    )

result = shutil.make_archive(
    "/kaggle/working/teacher_yolo11x",
    "zip",
    root_dir=run_dir,
)
print("Download this artifact:", result)
