# YOLO11n Training Script for Kaggle GPU.


import argparse
import os
import subprocess
import sys
from pathlib import Path

_ROOT_DIR = Path(__file__).resolve().parent.parent
if str(_ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(_ROOT_DIR))
from src.config import CLASS_NAMES, NUM_CLASSES


def parse_args():
    p = argparse.ArgumentParser(description="Train YOLO detection model on Kaggle GPU")
    p.add_argument("--dataset", type=str, required=True, help="Kaggle dataset name (e.g. mira_tnr, trashnet, roboflow)")
    p.add_argument("--model", type=str, default="yolo11n.pt", help="Base model architecture (default: yolo11n.pt)")
    p.add_argument("--epochs", type=int, default=120, help="Training epochs (default: 120)")
    p.add_argument("--batch-size", type=int, default=32, help="Batch size (default: 32)")
    p.add_argument("--img-size", type=int, default=640, help="Image size (default: 640)")
    p.add_argument("--patience", type=int, default=30, help="Early stopping patience (default: 30)")
    p.add_argument("--device", type=int, default=0, help="GPU device ID (default: 0)")
    p.add_argument("--lr0", type=float, default=0.01, help="Initial learning rate (default: 0.01)")
    return p.parse_args()


def main():
    args = parse_args()
    if args.epochs < 1 or args.batch_size < 1 or args.img_size < 1 or args.patience < 1:
        raise ValueError("epochs, batch-size, img-size, and patience must be positive")

    subprocess.check_call([sys.executable, "-m", "pip", "install", "-q", "ultralytics"])

    from ultralytics import YOLO

    input_dir = os.environ.get("KAGGLE_INPUT_PATH", "/kaggle/input")
    data_root = None

    normalized_dataset = args.dataset.lower().replace("+", "-")
    for d in Path(input_dir).iterdir():
        normalized_name = d.name.lower().replace("+", "-").replace(" ", "-")
        if d.is_dir() and normalized_dataset in normalized_name and (d / "images" / "train").is_dir():
            data_root = d
            break

    if data_root is None:
        for d in Path(input_dir).iterdir():
            if d.is_dir() and (d / "images" / "train").is_dir():
                data_root = d
                break

    if data_root is None:
        for d in Path(input_dir).iterdir():
            if d.is_dir():
                for sub in d.rglob("images/train"):
                    if sub.is_dir():
                        data_root = sub.parent.parent
                        break
                if data_root:
                    break

    if data_root is None:
        raise FileNotFoundError(
            f"Dataset '{args.dataset}' not found in {input_dir}.\n"
            "  Expected structure: datasets/<name>/images/{train,val}/ and labels/{train,val}/\n"
            "  Run: python scripts/merge_dataset_model1.py  (or model2/3/4) to create the dataset."
        )

    print(f"Dataset: {data_root}")
    train_imgs = list(data_root.rglob("images/train/*.jpg")) + list(data_root.rglob("images/train/*.png"))
    val_imgs = list(data_root.rglob("images/val/*.jpg")) + list(data_root.rglob("images/val/*.png"))
    print(f"  Train: {len(train_imgs)} images")
    print(f"  Val:   {len(val_imgs)} images")

    work_dir = "/kaggle/working"
    yaml_path = Path(work_dir) / "dataset.yaml"
    yaml_content = (
        f"train: {data_root}/images/train\nval: {data_root}/images/val\nnc: {NUM_CLASSES}\nnames: {CLASS_NAMES}\n"
    )
    yaml_path.write_text(yaml_content, encoding="utf-8")
    print(f"Written: {yaml_path}")

    print(f"\nStarting training: {args.dataset} | Model: {args.model} | Epochs: {args.epochs}")
    model = YOLO(args.model)

    model.train(
        data=str(yaml_path),
        epochs=args.epochs,
        batch=args.batch_size,
        imgsz=args.img_size,
        patience=args.patience,
        device=args.device,
        project=str(Path(work_dir) / "runs"),
        name=args.dataset,
        exist_ok=True,
        amp=True,
        workers=4,
        lr0=args.lr0,
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

    print("\nEvaluating...")
    metrics = model.val()
    print(f"\n  mAP50:    {metrics.box.map50:.3f}")
    print(f"  mAP50-95: {metrics.box.map:.3f}")

    print("\nExporting to TFLite INT8...")
    model.export(format="tflite", int8=True, imgsz=args.img_size)
    print("  TFLite INT8 exported")

    model.export(format="onnx", imgsz=args.img_size)
    print("  ONNX exported")

    print(f"\nDone! Results in: {work_dir}/runs/{args.dataset}/weights/")


if __name__ == "__main__":
    main()
