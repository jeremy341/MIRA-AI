"""Kaggle single-cell script: explore YOLO26n distillation and export/evaluate it."""

import shutil
import subprocess
import sys
from pathlib import Path
import zipfile

# Match the Ultralytics installation used by Kaggle notebooks 1 and 2.
print("Installing/Updating Ultralytics framework...")
subprocess.check_call([sys.executable, "-m", "pip", "install", "-q", "ultralytics"])

import torch
import ultralytics
from ultralytics import YOLO
from ultralytics.cfg import DEFAULT_CFG_DICT
from ultralytics.engine.trainer import BaseTrainer

INPUT = Path("/kaggle/input")
WORK = Path("/kaggle/working/mira_distill")
WORK.mkdir(exist_ok=True)


def validate_distillation_environment():
    missing = sorted({"distill_model", "dis"} - DEFAULT_CFG_DICT.keys())
    if missing:
        raise RuntimeError(
            f"Ultralytics {ultralytics.__version__} does not expose the required "
            f"distillation settings: {', '.join(missing)}. Stop before training and "
            "use an Ultralytics release that supports distill_model, dis, and MuSGD."
        )

    try:
        optimizer = BaseTrainer.build_optimizer(object(), torch.nn.Linear(2, 2), name="MuSGD")
    except Exception as error:
        raise RuntimeError(
            f"Ultralytics {ultralytics.__version__} cannot construct MuSGD. Stop "
            "before training and use a release that supports distill_model, dis, "
            "and MuSGD."
        ) from error
    if type(optimizer).__name__ != "MuSGD":
        raise RuntimeError(
            f"Ultralytics {ultralytics.__version__} resolved MuSGD to "
            f"{type(optimizer).__name__}, so this distillation run is not compatible."
        )

    print(f"Validated Ultralytics {ultralytics.__version__}: distill_model, dis, and MuSGD are available.")


def find_unique(root, pattern, description, required=True):
    matches = sorted(path for path in root.rglob(pattern) if path.is_file())
    if not matches and not required:
        return None
    if len(matches) != 1:
        found = "\n".join(f"  - {path}" for path in matches) or "  (none)"
        raise RuntimeError(f"Expected exactly one {description}; found {len(matches)}:\n{found}")
    return matches[0]


validate_distillation_environment()

dataset_archive = find_unique(INPUT, "*merged_mira_balanced*.zip", "balanced dataset ZIP")
dataset_dir = WORK / "dataset"
if dataset_dir.exists():
    shutil.rmtree(dataset_dir)
with zipfile.ZipFile(dataset_archive) as z:
    z.extractall(dataset_dir)

yaml_path = find_unique(dataset_dir, "dataset.yaml", "dataset.yaml")
data_root = yaml_path.parent
yaml_path.write_text(
    f"train: {data_root / 'images' / 'train'}\n"
    f"val: {data_root / 'images' / 'val'}\n"
    f"test: {data_root / 'images' / 'test'}\n"
    "nc: 5\n"
    "names: ['glass', 'metal', 'paper', 'plastic', 'trash']\n",
    encoding="utf-8",
)

teacher_archive = find_unique(INPUT, "teacher_yolo11n.zip", "YOLO11n teacher ZIP")
teacher_dir = WORK / "teacher"
if teacher_dir.exists():
    shutil.rmtree(teacher_dir)
with zipfile.ZipFile(teacher_archive) as z:
    z.extractall(teacher_dir)

teacher = find_unique(teacher_dir, "best.pt", "YOLO11n teacher best.pt")

runs = WORK / "runs"
run_dir = runs / "distill_yolo26n"
last = run_dir / "weights" / "last.pt"
best = run_dir / "weights" / "best.pt"

checkpoint_archive = find_unique(INPUT, "distill_yolo26n_results.zip", "distillation checkpoint ZIP", required=False)
if not last.exists() and checkpoint_archive is not None:
    with zipfile.ZipFile(checkpoint_archive) as archive:
        archive.extractall(run_dir)

print("Exploratory/reference teacher selected for Kaggle quota constraints:", teacher)
print("GPU:", torch.cuda.get_device_name(0) if torch.cuda.is_available() else "CPU")

if last.exists():
    print("Resuming distillation from:", last)
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
