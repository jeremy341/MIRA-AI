"""Kaggle single-cell script: distill YOLO26n and export/evaluate it."""

from pathlib import Path
import shutil
import torch
import zipfile

from ultralytics import YOLO

INPUT = Path("/kaggle/input")
WORK = Path("/kaggle/working/mira_distill")
WORK.mkdir(exist_ok=True)

dataset_archive = next(INPUT.rglob("*merged_mira_balanced*.zip"))
with zipfile.ZipFile(dataset_archive) as z:
    z.extractall(WORK / "dataset")

yaml_path = next((WORK / "dataset").rglob("dataset.yaml"))
yaml_path.write_text(
    "path: .\n"
    "train: images/train\n"
    "val: images/val\n"
    "test: images/test\n"
    "nc: 5\n"
    "names: ['glass', 'metal', 'paper', 'plastic', 'trash']\n"
)

teacher_archive = next(INPUT.rglob("*teacher_yolo11x*.zip"))
with zipfile.ZipFile(teacher_archive) as z:
    z.extractall(WORK / "teacher")

teacher_files = list((WORK / "teacher").rglob("best.pt"))
assert teacher_files, "teacher_yolo11x best.pt was not found"
teacher = teacher_files[0]

runs = WORK / "runs"
run_dir = runs / "distill_yolo26n"
last = run_dir / "weights" / "last.pt"
best = run_dir / "weights" / "best.pt"

print("Teacher:", teacher)
print("GPU:", torch.cuda.get_device_name(0) if torch.cuda.is_available() else "CPU")

if best.exists():
    print("Distilled model already complete:", best)
elif last.exists():
    print("Resuming distillation")
    YOLO(str(last)).train(resume=True)
else:
    YOLO("yolo26n.pt").train(
        data=str(yaml_path),
        project=str(runs),
        name="distill_yolo26n",
        exist_ok=True,
        device=0,
        workers=4,
        amp=True,
        epochs=120,
        time=10.8,
        batch=32,
        imgsz=640,
        optimizer="MuSGD",
        cos_lr=True,
        close_mosaic=10,
        distill_model=str(teacher),
        dis=6.0,
    )

if best.exists():
    model = YOLO(str(best))
    val = model.val(data=str(yaml_path), split="val", imgsz=640, device=0)
    test = model.val(data=str(yaml_path), split="test", imgsz=640, device=0)
    print("Validation mAP50:", val.box.map50)
    print("Test mAP50:", test.box.map50)

    try:
        model.export(format="onnx", imgsz=640)
    except Exception as error:
        print("ONNX export failed:", error)

    try:
        model.export(format="tflite", imgsz=640, int8=True)
    except Exception as error:
        print("TFLite export failed:", error)

result = shutil.make_archive(
    "/kaggle/working/distill_yolo26n_results",
    "zip",
    root_dir=run_dir,
)
print("Download this artifact:", result)
