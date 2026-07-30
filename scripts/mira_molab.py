# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "marimo>=0.9.0",
#     "ultralytics>=8.3.0",
#     "pycocotools>=2.0.7",
#     "requests>=2.31.0",
#     "tqdm>=4.66.0",
#     "huggingface-hub>=0.24.0",
#     "pyyaml>=6.0",
# ]
# ///
"""MIRA-AI: Full Training Pipeline for Marimo molab.

Interactive:
  marimo run scripts/mira_molab.py

Headless (batch):
  uv run scripts/mira_molab.py --phase 0   # download + merge
  uv run scripts/mira_molab.py --phase 1   # train teachers
  uv run scripts/mira_molab.py --phase 2   # distill students
  uv run scripts/mira_molab.py --phase 3   # baselines
  uv run scripts/mira_molab.py --phase 4   # export + eval
  uv run scripts/mira_molab.py --phase -1  # all

Platform: molab.marimo.io (Blackwell RTX Pro 6000, 96 GB VRAM)
Target: RPi Zero 2W TFLite INT8 deployment
"""

from __future__ import annotations

import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

import marimo

__generated_with = "0.10.0"
app = marimo.App()

# -- Constants ----------------------------------------------------------------
ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "datasets" / "raw"
MERGED = ROOT / "datasets" / "merged_mira"
RUNS = ROOT / "runs"
MIRA_CLASSES = ["glass", "metal", "paper", "plastic", "trash"]
NUM_CLASSES = 5

RAW_SORTWASTE = RAW / "sortwaste"
RAW_RECYCLE = RAW / "recycle_trash"
RAW_GARBAGE = RAW / "garbage_detection"

# -- Helpers ------------------------------------------------------------------


def ok(msg: str):
    print(f"  [OK] {msg}")


def warn(msg: str):
    print(f"  [!] {msg}")


def info(msg: str):
    print(f"  [i] {msg}")


def step(n, total, label: str):
    print(f"\n{'=' * 60}")
    print(f"  STEP {n}/{total}: {label}")
    print(f"{'=' * 60}")


def check_gpu() -> str:
    try:
        out = subprocess.run(
            ["nvidia-smi", "--query-gpu=name,memory.total,driver_version", "--format=csv,noheader"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        if out.returncode == 0:
            return out.stdout.strip()
    except Exception:
        pass
    return "No GPU detected"


def download_file(url: str, dest: Path, desc: str = "") -> bool:
    import requests
    from tqdm import tqdm

    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists() and dest.stat().st_size > 1000:
        info(f"{desc} already exists ({dest.stat().st_size >> 20} MB), skip")
        return True

    info(f"Downloading {desc} from {url}")
    try:
        resp = requests.get(url, stream=True, timeout=30, allow_redirects=True)
        resp.raise_for_status()
        total = int(resp.headers.get("content-length", 0))
        with (
            open(dest, "wb") as f,
            tqdm(
                desc=desc,
                total=total,
                unit="B",
                unit_scale=True,
            ) as pbar,
        ):
            for chunk in resp.iter_content(chunk_size=8192):
                f.write(chunk)
                pbar.update(len(chunk))
        ok(f"Downloaded {dest.name} ({dest.stat().st_size >> 20} MB)")
        return True
    except Exception as e:
        warn(f"Download failed: {e}")
        return False


def unzip_file(src: Path, dst: Path) -> bool:
    if not src.exists():
        warn(f"Zip not found: {src}")
        return False
    dst.mkdir(parents=True, exist_ok=True)
    info(f"Extracting {src.name} -> {dst}")
    try:
        with zipfile.ZipFile(src, "r") as zf:
            zf.extractall(dst)
        ok(f"Extracted to {dst}")
        return True
    except Exception as e:
        warn(f"Extraction failed: {e}")
        return False


def write_yaml(path: Path, data: dict):
    import yaml

    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        yaml.dump(data, f, default_flow_style=False)
    ok(f"Saved: {path.relative_to(ROOT)}")


def print_stats(img_dir: Path, lbl_dir: Path, label: str):
    class_counts = {i: 0 for i in range(NUM_CLASSES)}
    total_imgs = sum(1 for _ in img_dir.glob("*.*"))
    for lbl in lbl_dir.glob("*.txt"):
        for line in lbl.read_text().splitlines():
            line = line.strip()
            if line:
                try:
                    cid = int(line.split()[0])
                    class_counts[cid] = class_counts.get(cid, 0) + 1
                except (ValueError, IndexError):
                    pass
    total_ann = sum(class_counts.values())
    print(f"\n  {label}: {total_imgs} images, {total_ann} annotations")
    for cid in range(NUM_CLASSES):
        pct = class_counts[cid] / total_ann * 100 if total_ann else 0
        bar = "#" * int(pct / 2)
        print(f"    {MIRA_CLASSES[cid]:8s}: {class_counts[cid]:5d} ({pct:5.1f}%) {bar}")


# ==============================================================================
# CELLS
# ==============================================================================


@app.cell
def setup_cell():
    import marimo as mo

    gpu_info = check_gpu()
    print(f"GPU: {gpu_info}")
    print(f"Root: {ROOT}")
    print(f"Python: {sys.version}")

    for d in [RAW_SORTWASTE, RAW_RECYCLE, RAW_GARBAGE]:
        d.mkdir(parents=True, exist_ok=True)

    img_exts = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tiff"}
    return mo, img_exts


@app.cell
def download_sortwaste():
    step(1, 7, "Download SortWaste (WACV 2026)")

    url = "https://sortwaste.di.ubi.pt/datasets/dataset.zip"
    dest = RAW_SORTWASTE / "dataset.zip"
    extracted = RAW_SORTWASTE / "dataset"

    if extracted.exists() and len(list(extracted.rglob("*.jpg"))) > 100:
        ok(f"SortWaste extracted ({len(list(extracted.rglob('*.jpg')))} images)")
        return

    if download_file(url, dest, "SortWaste"):
        unzip_file(dest, extracted)

    n = len(list(extracted.rglob("*.jpg"))) if extracted.exists() else 0
    if n > 0:
        ok(f"SortWaste: {n} images")
    else:
        warn("SortWaste download failed")


@app.cell
def download_recycle_trash():
    step(2, 7, "Download Recycle Trash / TADA (NAVER/Korea)")

    extracted = RAW_RECYCLE / "trash_dataset"
    partial = RAW_RECYCLE / "boostcamp_subset"

    if extracted.exists() and len(list(extracted.rglob("*.jpg"))) > 1000:
        ok(f"Recycle Trash extracted ({len(list(extracted.rglob('*.jpg')))} images)")
        return

    # Option A: Official NAVER dataset (requires access application, 120 GB)
    info("Option A: Official NAVER Recycle Trash")
    info("  Requires access: https://github.com/connectfoundation/naverconnect-dataset-trash")
    info("  Download manually to: datasets/raw/recycle_trash/trash_dataset/")
    info("  Then re-run this cell.")

    # Option B: Kaggle download (if Kaggle API is set up)
    info("Option B: Kaggle Garbage Classification (4133 images, 7 classes)")
    try:
        r = subprocess.run(
            [
                "kaggle",
                "datasets",
                "download",
                "-d",
                "karansolanki01/garbage-classification",
                "-p",
                str(RAW_RECYCLE / "kaggle"),
            ],
            capture_output=True,
            text=True,
            timeout=300,
        )
        if r.returncode == 0:
            n = len(list((RAW_RECYCLE / "kaggle").rglob("*.jpg")))
            ok(f"Kaggle subset: {n} images")
        else:
            warn(f"Kaggle download failed (not configured?): {r.stderr[:200]}")
    except Exception as e:
        warn(f"Option B failed: {e}")

    # Option C: TADA dataset (Zenodo, 4977 images, 10 classes, open access)
    info("Option C: TADA dataset from Zenodo (4977 images, 10 classes)")
    tada_url = "https://zenodo.org/record/4607158/files/TADA.zip"
    tada_dest = RAW_RECYCLE / "tada.zip"
    if download_file(tada_url, tada_dest, "TADA dataset"):
        unzip_file(tada_dest, RAW_RECYCLE / "tada")

    # Count what we got
    n = 0
    for src_dir in [partial, RAW_RECYCLE / "kaggle", RAW_RECYCLE / "tada"]:
        if src_dir.exists():
            n += len(list(src_dir.rglob("*.jpg")))
    if n > 100:
        ok(f"Total Recycle Trash / alternatives: {n} images")
    else:
        warn("No Recycle Trash or alternative data available. Will train without it.")


@app.cell
def download_garbage_detection():
    step(3, 7, "Download Garbage Detection (Ultralytics Hub)")

    extracted = RAW_GARBAGE / "dataset"

    if extracted.exists() and len(list(extracted.rglob("*.jpg"))) > 1000:
        ok(f"Garbage Detection extracted ({len(list(extracted.rglob('*.jpg')))} images)")
        return

    warn("Garbage Detection requires Ultralytics Platform API key.")
    info("Download from https://platform.ultralytics.com and place in:")
    info(f"  {RAW_GARBAGE}")
    info("Then re-run this cell.")

    present = False
    alt = "https://github.com/NawanolT/Garbage-Dataset/archive/refs/heads/main.zip"
    dest = RAW_GARBAGE / "garbage_alt.zip"
    if download_file(alt, dest, "Garbage Alt (15k images)"):
        unzip_file(dest, RAW_GARBAGE / "alt")
        n = len(list((RAW_GARBAGE / "alt").rglob("*.jpg")))
        if n > 100:
            ok(f"Alt garbage dataset: {n} images")
            present = True

    if not present:
        warn("Garbage Detection: not available")


@app.cell
def convert_and_merge(img_exts):
    step(4, 7, "Convert & Merge All Datasets to MIRA 5-class")

    mira_map = {"glass": 0, "metal": 1, "paper": 2, "plastic": 3, "trash": 4}

    # -- Recycle Trash: COCO to YOLO ------------------------------------------
    recycle_map = {
        0: 4,
        1: 3,
        2: 2,
        3: 3,
        4: 3,
        5: 1,
        6: 0,
        7: 2,
        8: 4,
        9: 4,
    }

    def coco_to_yolo(coco_path: Path, out_dir: Path, mapping: dict) -> int:
        from pycocotools.coco import COCO

        if not coco_path.exists():
            return 0
        coco = COCO(str(coco_path))
        img_dir = coco_path.parent
        out_img = out_dir / "images"
        out_lbl = out_dir / "labels"
        out_img.mkdir(parents=True, exist_ok=True)
        out_lbl.mkdir(parents=True, exist_ok=True)

        count = 0
        for img_id in coco.getImgIds():
            info = coco.loadImgs(img_id)[0]
            src = img_dir / info["file_name"]
            if not src.exists():
                continue
            anns = coco.loadAnns(coco.getAnnIds(imgIds=img_id))
            labels = []
            for ann in anns:
                cid = ann["category_id"]
                if cid not in mapping:
                    continue
                mc = mapping[cid]
                x, y, w, h = ann["bbox"]
                labels.append(
                    f"{mc} {(x + w / 2) / info['width']:.6f} "
                    f"{(y + h / 2) / info['height']:.6f} "
                    f"{w / info['width']:.6f} {h / info['height']:.6f}"
                )
            if not labels:
                continue
            stem = Path(info["file_name"]).stem
            shutil.copy2(src, out_img / f"{stem}.jpg")
            (out_lbl / f"{stem}.txt").write_text("\n".join(labels))
            count += 1
        return count

    # -- SortWaste: remap YOLO labels -----------------------------------------
    sw_map = {0: 3, 1: 3, 2: 3, 3: 3, 4: 3, 5: 2, 6: 1, 7: 3}

    def process_sortwaste(src: Path, dst: Path) -> int:
        total = 0
        for split in ["train", "val"]:
            img_src = src / split / "images"
            lbl_src = src / split / "labels"
            if not img_src.exists():
                continue
            for img in img_src.glob("*.*"):
                if img.suffix.lower() not in img_exts:
                    continue
                lbl = lbl_src / f"{img.stem}.txt"
                if not lbl.exists():
                    continue
                new = []
                for line in lbl.read_text().splitlines():
                    parts = line.strip().split()
                    if not parts:
                        continue
                    try:
                        old = int(parts[0])
                    except ValueError:
                        continue
                    if old in sw_map:
                        new.append(f"{sw_map[old]} " + " ".join(parts[1:]))
                if not new:
                    continue
                (dst / "images" / split).mkdir(parents=True, exist_ok=True)
                (dst / "labels" / split).mkdir(parents=True, exist_ok=True)
                shutil.copy2(img, dst / "images" / split / img.name)
                (dst / "labels" / split / f"{img.stem}.txt").write_text("\n".join(new))
                total += 1
        return total

    # -- Garbage Detection: remap YOLO ----------------------------------------
    gd_map = {0: 4, 1: 2, 2: 4, 3: 0, 4: 4, 5: 1, 6: 4, 7: 2, 8: 3, 9: 4, 10: 4}

    def process_gd(src: Path, dst: Path) -> int:
        total = 0
        for split in ["train", "val"]:
            img_src = src / split / "images"
            lbl_src = src / split / "labels"
            if not img_src.exists():
                continue
            for img in img_src.glob("*.*"):
                if img.suffix.lower() not in img_exts:
                    continue
                lbl = lbl_src / f"{img.stem}.txt"
                if not lbl.exists():
                    continue
                new = []
                for line in lbl.read_text().splitlines():
                    parts = line.strip().split()
                    if not parts:
                        continue
                    try:
                        old = int(parts[0])
                    except ValueError:
                        continue
                    if old in gd_map:
                        new.append(f"{gd_map[old]} " + " ".join(parts[1:]))
                if not new:
                    continue
                (dst / "images" / split).mkdir(parents=True, exist_ok=True)
                (dst / "labels" / split).mkdir(parents=True, exist_ok=True)
                shutil.copy2(img, dst / "images" / split / img.name)
                (dst / "labels" / split / f"{img.stem}.txt").write_text("\n".join(new))
                total += 1
        return total

    # -- TADA COCO remap ----------------------------------------------------
    tada_map = {  # noqa: F841
        0: 3,  # Plastic
        1: 2,  # Paper
        2: 4,  # General trash
        3: 4,  # Clothing
        4: 0,  # Glass
        5: 1,  # Metal
        6: 3,  # Styrofoam
        7: 3,  # Plastic bag
        8: 2,  # Paper pack
        9: 4,  # Battery
    }

    # -- Execute --------------------------------------------------------------
    total = 0

    n = process_sortwaste(RAW_SORTWASTE / "dataset", MERGED)
    ok(f"SortWaste: {n} images")
    total += n

    for src_dir in [RAW_RECYCLE / "boostcamp_subset", RAW_RECYCLE / "tada"]:
        for jp in src_dir.rglob("*.json"):
            if "train" in jp.name or "test" in jp.name or "val" in jp.name:
                sn = "val" if "test" in jp.stem or "val" in jp.stem else "train"
                n = coco_to_yolo(jp, MERGED / sn, recycle_map)
                ok(f"COCO source ({jp.parent.name}/{jp.name}): {n} images")
                total += n

    for src in [RAW_GARBAGE / "dataset", RAW_GARBAGE / "alt"]:
        if src.exists():
            n = process_gd(src, MERGED)
            ok(f"Garbage Detection: {n} images")
            total += n

    ok(f"Total merged: {total} images")

    for split in ["train", "val"]:
        img_d = MERGED / "images" / split
        lbl_d = MERGED / "labels" / split
        if img_d.exists():
            print_stats(img_d, lbl_d, split.capitalize())

    return (coco_to_yolo, sw_map, gd_map, recycle_map, mira_map)


@app.cell
def create_merged_yaml():
    step(5, 7, "Create Merged Dataset YAML")

    data = {
        "train": str(MERGED / "images" / "train"),
        "val": str(MERGED / "images" / "val"),
        "nc": NUM_CLASSES,
        "names": MIRA_CLASSES,
    }
    write_yaml(MERGED / "dataset.yaml", data)
    ok(f"Dataset ready at {MERGED / 'dataset.yaml'}")


@app.cell
def train_teacher_yolo11x():
    step(6, 7, "EXP-018: YOLO11x Teacher @ 1280px")

    from ultralytics import YOLO

    yaml_path = MERGED / "dataset.yaml"
    if not yaml_path.exists():
        warn("Merge dataset first (step 4+5)")
        return

    out = RUNS / "teachers" / "yolo11x_1280"
    if (out / "weights" / "best.pt").exists():
        ok("YOLO11x teacher exists, skip")
        return

    model = YOLO("yolo11x.pt")
    model.train(
        data=str(yaml_path),
        epochs=200,
        batch=16,
        imgsz=1280,
        optimizer="AdamW",
        lr0=0.001,
        cos_lr=True,
        close_mosaic=10,
        patience=30,
        amp=True,
        device=0,
        workers=8,
        project="runs/teachers",
        name="yolo11x_1280",
        exist_ok=True,
        hsv_h=0.015,
        hsv_s=0.7,
        hsv_v=0.4,
        degrees=0,
        translate=0.1,
        scale=0.5,
        shear=0,
        flipud=0,
        fliplr=0.5,
        mosaic=1.0,
    )
    ok("EXP-018 done")


@app.cell
def train_teacher_yolo26x():
    step(7, 7, "EXP-019: YOLO26x Teacher @ 640px")

    from ultralytics import YOLO

    yaml_path = MERGED / "dataset.yaml"
    if not yaml_path.exists():
        warn("Merge dataset first")
        return

    out = RUNS / "teachers" / "yolo26x_640"
    if (out / "weights" / "best.pt").exists():
        ok("YOLO26x teacher exists, skip")
        return

    model = YOLO("yolo26x.pt")
    model.train(
        data=str(yaml_path),
        epochs=200,
        batch=32,
        imgsz=640,
        optimizer="MuSGD",
        lr0=0.01,
        cos_lr=True,
        close_mosaic=10,
        patience=30,
        amp=True,
        device=0,
        workers=8,
        project="runs/teachers",
        name="yolo26x_640",
        exist_ok=True,
        hsv_h=0.015,
        hsv_s=0.7,
        hsv_v=0.4,
        degrees=0,
        translate=0.1,
        scale=0.5,
        shear=0,
        flipud=0,
        fliplr=0.5,
        mosaic=1.0,
    )
    ok("EXP-019 done")


@app.cell
def distill_yolo26n():
    step(8, 11, "EXP-020: Distilled YOLO26n (Primary RPi Target)")

    from ultralytics import YOLO

    yaml_path = MERGED / "dataset.yaml"
    if not yaml_path.exists():
        warn("Merge dataset first")
        return

    teachers = list((RUNS / "teachers").rglob("weights/best.pt"))
    if not teachers:
        warn("Train teachers first (step 6+7)")
        return
    teacher = str(teachers[0])
    info(f"Teacher: {teacher}")

    out = RUNS / "students" / "distill_yolo26n"
    if (out / "weights" / "best.pt").exists():
        ok("Distilled YOLO26n exists, skip")
        return

    student = YOLO("yolo26n.pt")
    student.train(
        data=str(yaml_path),
        epochs=200,
        batch=32,
        imgsz=640,
        optimizer="MuSGD",
        lr0=0.01,
        cos_lr=True,
        close_mosaic=10,
        patience=30,
        amp=True,
        device=0,
        workers=8,
        project="runs/students",
        name="distill_yolo26n",
        exist_ok=True,
        distill_model=teacher,
        dis=6.0,
        hsv_h=0.015,
        hsv_s=0.7,
        hsv_v=0.4,
        degrees=0,
        translate=0.1,
        scale=0.5,
        shear=0,
        flipud=0,
        fliplr=0.5,
        mosaic=1.0,
    )
    ok("EXP-020 done")


@app.cell
def distill_yolo11n():
    step(9, 11, "EXP-021: Distilled YOLO11n")

    from ultralytics import YOLO

    yaml_path = MERGED / "dataset.yaml"
    if not yaml_path.exists():
        warn("Merge dataset first")
        return

    teachers = list((RUNS / "teachers").rglob("weights/best.pt"))
    if not teachers:
        warn("Train teachers first")
        return
    teacher = str(teachers[0])

    out = RUNS / "students" / "distill_yolo11n"
    if (out / "weights" / "best.pt").exists():
        ok("Distilled YOLO11n exists, skip")
        return

    student = YOLO("yolo11n.pt")
    student.train(
        data=str(yaml_path),
        epochs=200,
        batch=32,
        imgsz=640,
        optimizer="AdamW",
        lr0=0.01,
        cos_lr=True,
        close_mosaic=10,
        patience=30,
        amp=True,
        device=0,
        workers=8,
        project="runs/students",
        name="distill_yolo11n",
        exist_ok=True,
        distill_model=teacher,
        dis=6.0,
        hsv_h=0.015,
        hsv_s=0.7,
        hsv_v=0.4,
        degrees=0,
        translate=0.1,
        scale=0.5,
        shear=0,
        flipud=0,
        fliplr=0.5,
        mosaic=1.0,
    )
    ok("EXP-021 done")


@app.cell
def baseline_yolo26n():
    step(10, 11, "EXP-022: Baseline YOLO26n (No KD)")

    from ultralytics import YOLO

    yaml_path = MERGED / "dataset.yaml"
    if not yaml_path.exists():
        warn("Merge dataset first")
        return

    out = RUNS / "baselines" / "baseline_yolo26n"
    if (out / "weights" / "best.pt").exists():
        ok("Baseline YOLO26n exists, skip")
        return

    model = YOLO("yolo26n.pt")
    model.train(
        data=str(yaml_path),
        epochs=200,
        batch=32,
        imgsz=640,
        optimizer="MuSGD",
        lr0=0.01,
        cos_lr=True,
        close_mosaic=10,
        patience=30,
        amp=True,
        device=0,
        workers=8,
        project="runs/baselines",
        name="baseline_yolo26n",
        exist_ok=True,
        hsv_h=0.015,
        hsv_s=0.7,
        hsv_v=0.4,
        degrees=0,
        translate=0.1,
        scale=0.5,
        shear=0,
        flipud=0,
        fliplr=0.5,
        mosaic=1.0,
    )
    ok("EXP-022 done")


@app.cell
def baseline_yolo11n():
    step(11, 11, "EXP-023: Baseline YOLO11n (No KD)")

    from ultralytics import YOLO

    yaml_path = MERGED / "dataset.yaml"
    if not yaml_path.exists():
        warn("Merge dataset first")
        return

    out = RUNS / "baselines" / "baseline_yolo11n"
    if (out / "weights" / "best.pt").exists():
        ok("Baseline YOLO11n exists, skip")
        return

    model = YOLO("yolo11n.pt")
    model.train(
        data=str(yaml_path),
        epochs=200,
        batch=32,
        imgsz=640,
        optimizer="AdamW",
        lr0=0.01,
        cos_lr=True,
        close_mosaic=10,
        patience=30,
        amp=True,
        device=0,
        workers=8,
        project="runs/baselines",
        name="baseline_yolo11n",
        exist_ok=True,
        hsv_h=0.015,
        hsv_s=0.7,
        hsv_v=0.4,
        degrees=0,
        translate=0.1,
        scale=0.5,
        shear=0,
        flipud=0,
        fliplr=0.5,
        mosaic=1.0,
    )
    ok("EXP-023 done")


@app.cell
def export_models():
    step(12, 13, "Export ONNX + TFLite INT8")

    from ultralytics import YOLO

    models = [
        ("distill_yolo26n", RUNS / "students" / "distill_yolo26n"),
        ("distill_yolo11n", RUNS / "students" / "distill_yolo11n"),
        ("baseline_yolo26n", RUNS / "baselines" / "baseline_yolo26n"),
        ("baseline_yolo11n", RUNS / "baselines" / "baseline_yolo11n"),
    ]

    for name, run_dir in models:
        pt = run_dir / "weights" / "best.pt"
        if not pt.exists():
            warn(f"{name}: no weights")
            continue
        info(f"Exporting {name}...")
        model = YOLO(str(pt))
        for fmt in [("onnx", {}), ("tflite", {"int8": True})]:
            out = run_dir / f"best_{fmt[0]}.{'tflite' if fmt[1].get('int8') else 'onnx'}"
            if out.exists():
                ok(f"{name}: {out.name} exists")
                continue
            try:
                model.export(format=fmt[0], imgsz=640, **fmt[1])
                ok(f"{name}: {out.name} done")
            except Exception as e:
                warn(f"{name}: {fmt[0]} failed: {e}")


@app.cell
def evaluate_models():
    step(13, 13, "Evaluate All Models")

    from ultralytics import YOLO

    yaml_path = MERGED / "dataset.yaml"
    if not yaml_path.exists():
        warn("No merged dataset")
        return

    models = [
        ("EXP-020 YOLO26n KD", RUNS / "students" / "distill_yolo26n"),
        ("EXP-021 YOLO11n KD", RUNS / "students" / "distill_yolo11n"),
        ("EXP-022 YOLO26n base", RUNS / "baselines" / "baseline_yolo26n"),
        ("EXP-023 YOLO11n base", RUNS / "baselines" / "baseline_yolo11n"),
        ("EXP-018 YOLO11x tchr", RUNS / "teachers" / "yolo11x_1280"),
        ("EXP-019 YOLO26x tchr", RUNS / "teachers" / "yolo26x_640"),
    ]

    results = []
    for name, run_dir in models:
        pt = run_dir / "weights" / "best.pt"
        if not pt.exists():
            warn(f"{name}: no weights")
            continue
        info(f"Eval {name}...")
        try:
            m = YOLO(str(pt))
            val = m.val(data=str(yaml_path), imgsz=640, device=0, half=True)
            results.append(
                {
                    "name": name,
                    "mAP50": val.box.map50,
                    "mAP50-95": val.box.map,
                    "P": val.box.mp,
                    "R": val.box.mr,
                }
            )
            ok(f"{name}: mAP50={val.box.map50:.3f}, mAP50-95={val.box.map:.3f}")
        except Exception as e:
            warn(f"{name}: eval failed: {e}")

    if results:
        print(f"\n{'=' * 70}")
        print(f"  {'Model':<22s} {'mAP50':>8s} {'mAP50-95':>10s} {'P':>8s} {'R':>8s}")
        print(f"{'=' * 70}")
        for r in sorted(results, key=lambda x: x["mAP50"], reverse=True):
            print(f"  {r['name']:<22s} {r['mAP50']:>8.3f} {r['mAP50-95']:>10.3f} {r['P']:>8.3f} {r['R']:>8.3f}")
        print(f"{'=' * 70}")


@app.cell
def upload_to_hf():
    step(14, 14, "Upload Best Model to HuggingFace")

    from huggingface_hub import HfApi

    repo_id = "jeremy341/MIRA-AI"
    api = HfApi()

    for run_dir in [RUNS / "students" / "distill_yolo26n", RUNS / "students" / "distill_yolo11n"]:
        tflite = list(run_dir.rglob("*.tflite"))
        onnx = list(run_dir.rglob("*.onnx"))
        pt = run_dir / "weights" / "best.pt"

        if not any([tflite, onnx, pt.exists()]):
            warn(f"Nothing to upload for {run_dir.name}")
            continue

        try:
            if pt.exists():
                api.upload_file(
                    path_or_fileobj=str(pt),
                    path_in_repo=f"models/{run_dir.name}/best.pt",
                    repo_id=repo_id,
                )
            for f in onnx + tflite:
                api.upload_file(
                    path_or_fileobj=str(f),
                    path_in_repo=f"models/{run_dir.name}/{f.name}",
                    repo_id=repo_id,
                )
            ok(f"Uploaded {run_dir.name}")
        except Exception as e:
            warn(f"Upload {run_dir.name} failed: {e}")

    ok("Uploaded to https://huggingface.co/jeremy341/MIRA-AI")


# ==============================================================================
# HEADLESS MODE
# ==============================================================================
# When run as `uv run mira_molab.py --phase N`, marimo is not needed.
# We import mock `mo` and call cell functions directly.

if __name__ == "__main__":
    import argparse

    # Provide a dummy `mo` module for cells that import it
    if "marimo" in sys.modules:
        _mo = sys.modules["marimo"]
    else:

        class _MockMo:
            def __getattr__(self, _):
                return lambda *a, **kw: None

        _mo = _MockMo()
        sys.modules["marimo"] = _mo

    parser = argparse.ArgumentParser(description="MIRA-AI Training Pipeline")
    parser.add_argument(
        "--phase",
        type=int,
        default=-1,
        help="Phase: 0=download, 1=teachers, 2=distill, 3=baselines, 4=export+eval, -1=all",
    )
    args = parser.parse_args()

    phases = {
        0: [
            download_sortwaste,
            download_recycle_trash,
            download_garbage_detection,
            lambda: convert_and_merge({".jpg", ".jpeg", ".png"}),
            create_merged_yaml,
        ],
        1: [train_teacher_yolo11x, train_teacher_yolo26x],
        2: [distill_yolo26n, distill_yolo11n],
        3: [baseline_yolo26n, baseline_yolo11n],
        4: [export_models, evaluate_models],
    }

    def run_phase(n):
        for fn in phases[n]:
            fn()

    if args.phase == -1:
        for n in range(5):
            run_phase(n)
    elif args.phase in phases:
        run_phase(args.phase)
    else:
        parser.print_help()
