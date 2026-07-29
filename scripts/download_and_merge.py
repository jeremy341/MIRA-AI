#!/usr/bin/env python3
"""Download all MIRA datasets and merge into 5-class YOLO format.

Usage:
  uv run scripts/download_and_merge.py                  # full pipeline
  uv run scripts/download_and_merge.py --skip-download   # merge only
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

MIRA_CLASSES = ["glass", "metal", "paper", "plastic", "trash"]
NUM_CLASSES = 5

RAW = ROOT / "datasets" / "raw"
MERGED = ROOT / "datasets" / "merged_mira"
RAW.mkdir(parents=True, exist_ok=True)

# ── Class mappings ───────────────────────────────────────────────────────────

SORTWASTE_MAP  = {0:3, 1:3, 2:3, 3:3, 4:3, 5:2, 6:1, 7:3}   # 8→5

KEREMBERKE_NAME_MAP = {                                        # category_name → MIRA
    "biodegradable":4, "cardboard":2, "glass":0,
    "metal":1, "paper":2, "plastic":3,
}

DMEDHI_NAME_MAP = {
    "Cardboard":2, "Garbage":4, "Glass":0,
    "Metal":1, "Paper":2, "Plastic":3, "Trash":4,
}

# Import TACO mapping from existing class_mappings module
sys.path.insert(0, str(ROOT / "scripts"))
from class_mappings import TACO_REMAP as _TACO_REMAP
TACO_REMAP = _TACO_REMAP

ROBOFLOW_MAP = {}
_rbf_path = ROOT / "datasets" / "registry" / "roboflow.yaml"
if _rbf_path.exists():
    import yaml as _yaml
    _rbf_cfg = _yaml.safe_load(_rbf_path.read_text())
    _raw_map = _rbf_cfg.get("class_mapping", {})
    ROBOFLOW_MAP = {int(k): int(v) for k, v in _raw_map.items()}

IMG_EXTS = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tiff"}

# ── Helpers ───────────────────────────────────────────────────────────────────

def banner(msg: str):
    print(f"\n{'='*50}\n  {msg}\n{'='*50}")

def ok(msg: str):
    print(f"  [OK] {msg}")

def warn(msg: str):
    print(f"  [WARN] {msg}")

def download(url: str, dest: Path) -> bool:
    import requests
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists() and dest.stat().st_size > 1000:
        ok(f"Already downloaded: {dest.name} ({dest.stat().st_size>>20} MB)")
        return True
    print(f"  Downloading {url} -> {dest.name} ...")
    try:
        resp = requests.get(url, stream=True, timeout=60)
        resp.raise_for_status()
        total = int(resp.headers.get("content-length", 0))
        downloaded = 0
        with open(dest, "wb") as f:
            for chunk in resp.iter_content(chunk_size=1024*1024):
                f.write(chunk)
                downloaded += len(chunk)
                if total:
                    pct = downloaded / total * 100
                    print(f"\r  {pct:.0f}% ({downloaded>>20}/{total>>20} MB)", end="")
        print()
        ok(f"Downloaded {dest.name} ({dest.stat().st_size>>20} MB)")
        return True
    except Exception as e:
        warn(f"Download failed: {e}")
        return False

def unzip(src: Path, dst: Path) -> bool:
    if not src.exists():
        warn(f"Zip not found: {src}")
        return False
    dst.mkdir(parents=True, exist_ok=True)
    print(f"  Extracting {src.name} ...")
    try:
        with zipfile.ZipFile(src, "r") as zf:
            zf.extractall(dst)
        ok(f"Extracted to {dst}")
        return True
    except Exception as e:
        warn(f"Extraction failed: {e}")
        return False

def count_images(d: Path) -> int:
    if not d.exists():
        return 0
    return sum(1 for _ in d.rglob("*") if _.suffix.lower() in IMG_EXTS)

# ── YOLO label remapping ─────────────────────────────────────────────────────

def remap_yolo_dir(src_img: Path, src_lbl: Path, dst_img: Path, dst_lbl: Path,
                    mapping: dict[int, int] | None = None) -> int:
    """Copy images + remapped YOLO labels. Returns count of copied images."""
    dst_img.mkdir(parents=True, exist_ok=True)
    dst_lbl.mkdir(parents=True, exist_ok=True)
    added = 0
    for img in src_img.iterdir():
        ext = img.suffix.lower()
        if ext not in IMG_EXTS:
            continue
        lbl_file = src_lbl / f"{img.stem}.txt"
        if not lbl_file.exists():
            continue

        if mapping is not None:
            new_lines = []
            for line in lbl_file.read_text().splitlines():
                p = line.strip().split()
                if not p:
                    continue
                try:
                    cid = int(p[0])
                except ValueError:
                    continue
                if cid in mapping:
                    new_lines.append(f"{mapping[cid]} {' '.join(p[1:])}\n")
            if not new_lines:
                continue
            shutil.copy2(img, dst_img / img.name)
            (dst_lbl / f"{img.stem}.txt").write_text("\n".join(new_lines))
        else:
            shutil.copy2(img, dst_img / img.name)
            shutil.copy2(lbl_file, dst_lbl / f"{img.stem}.txt")
        added += 1
    return added

# ── COCO → YOLO conversion ───────────────────────────────────────────────────

def coco_to_yolo(coco_json: Path, img_dir: Path, dst_img: Path, dst_lbl: Path,
                  name_map: dict[str, int] | None = None,
                  id_map: dict[int, int] | None = None) -> int:
    """Convert COCO dataset to YOLO format, optionally remapping classes."""
    try:
        from pycocotools.coco import COCO
    except ImportError:
        print("  Installing pycocotools ...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pycocotools"])
        from pycocotools.coco import COCO

    if not coco_json.exists():
        warn(f"No COCO JSON: {coco_json}")
        return 0

    coco = COCO(str(coco_json))
    dst_img.mkdir(parents=True, exist_ok=True)
    dst_lbl.mkdir(parents=True, exist_ok=True)

    # Build mapping from COCO category_id → MIRA id
    cat_map = {}
    cats = coco.loadCats(coco.getCatIds())
    for cat in cats:
        cid = cat["id"]
        name = cat["name"]
        if name_map:
            if name in name_map:
                cat_map[cid] = name_map[name]
        elif id_map:
            if cid in id_map:
                cat_map[cid] = id_map[cid]

    print(f"  COCO: {len(cats)} categories, {len(cat_map)} mapped to MIRA")

    count = 0
    for img_id in coco.getImgIds():
        info = coco.loadImgs(img_id)[0]
        fname = info["file_name"]
        src = img_dir / fname
        if not src.exists():
            continue
        anns = coco.loadAnns(coco.getAnnIds(imgIds=img_id))
        labels = []
        for ann in anns:
            cid = ann["category_id"]
            if cid not in cat_map:
                continue
            mc = cat_map[cid]
            x, y, w, h = ann["bbox"]
            labels.append(
                f"{mc} {(x + w/2)/info['width']:.6f} "
                f"{(y + h/2)/info['height']:.6f} "
                f"{w/info['width']:.6f} {h/info['height']:.6f}"
            )
        if not labels:
            continue
        stem = Path(fname).stem
        shutil.copy2(src, dst_img / f"{stem}.jpg")
        (dst_lbl / f"{stem}.txt").write_text("\n".join(labels))
        count += 1

    return count

# ── HuggingFace Parquet → YOLO ───────────────────────────────────────────────

def parquet_to_yolo(dataset_id: str, dst_img: Path, dst_lbl: Path,
                     name_map: dict[str, int]) -> int:
    """Download HuggingFace Parquet dataset and convert to YOLO."""
    try:
        from datasets import load_dataset
    except ImportError:
        print("  Installing datasets ...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "datasets"])
        from datasets import load_dataset

    dst_img.mkdir(parents=True, exist_ok=True)
    dst_lbl.mkdir(parents=True, exist_ok=True)

    print(f"  Loading dataset: {dataset_id} ...")
    try:
        ds = load_dataset(dataset_id, split="train")
    except Exception as e:
        warn(f"Failed to load dataset {dataset_id}: {e}. Dataset will be skipped.")
        return 0

    count = 0
    for row in ds:
        # Parquet has different schemas; try common patterns
        img = row.get("image")
        if img is None:
            continue
        # PIL image or encoded bytes
        if hasattr(img, "save"):
            img_path = dst_img / f"img_{count:06d}.jpg"
            img.save(img_path, "JPEG")
        elif isinstance(img, bytes):
            img_path = dst_img / f"img_{count:06d}.jpg"
            img_path.write_bytes(img)
        else:
            continue

        # Get bboxes — field name varies
        objs = row.get("objects", {})
        if not objs:
            bbox_list = row.get("bbox", [])
            cat_list = row.get("category", row.get("label", []))
        else:
            bbox_list = objs.get("bbox", [])
            cat_list = objs.get("category", objs.get("label", []))

        # Handle category info
        if isinstance(cat_list, list) and cat_list:
            cats = cat_list
        elif isinstance(row, dict):
            cats = [row.get("category_name")] if row.get("category_name") else []
        else:
            cats = []

        width = img.width if hasattr(img, "width") else 640
        height = img.height if hasattr(img, "height") else 640

        labels = []
        for idx, bbox in enumerate(bbox_list):
            if len(bbox) < 4:
                continue
            x, y, w, h = bbox[:4]
            cat_name = cats[idx] if idx < len(cats) else None
            if cat_name is None or cat_name not in name_map:
                continue
            mc = name_map[cat_name]
            labels.append(
                f"{mc} {(x + w/2)/width:.6f} {(y + h/2)/height:.6f} "
                f"{w/width:.6f} {h/height:.6f}"
            )
        if not labels:
            continue
        (dst_lbl / f"img_{count:06d}.txt").write_text("\n".join(labels))
        count += 1

    print(f"  {dataset_id}: {count} images converted")
    return count

# ── Dataset processors ───────────────────────────────────────────────────────

def process_sortwaste() -> int:
    banner("SortWaste (5,261 images, top-down camera)")

    # Downloaded as dataset.zip, extracted to datasets/raw/sortwaste/dataset/
    # Structure: dataset/dataset/splited_all_dataset/{split}/images/  (PNG images)
    #            dataset/dataset/splited_all_dataset_yolo/{split}/labels/  (YOLO labels)
    base = RAW / "sortwaste" / "dataset" / "dataset"
    yolo_base = base / "splited_all_dataset_yolo"
    img_base = base / "splited_all_dataset"

    total = 0
    for split in ("train", "val"):
        sw_img = img_base / split / "images"
        sw_lbl = yolo_base / split / "labels"
        if sw_lbl.exists() and sw_img.exists():
            n = remap_yolo_dir(sw_img, sw_lbl,
                               MERGED / "images" / "all",
                               MERGED / "labels" / "all",
                               SORTWASTE_MAP)
            ok(f"SortWaste {split}: {n} images")
            total += n
        else:
            ok(f"SortWaste {split}: labels exist={sw_lbl.exists()}, images exist={sw_img.exists()}")

    # test split has both images+labels in yolo_base, use as val bonus
    sw_test_img = yolo_base / "test" / "images"
    sw_test_lbl = yolo_base / "test" / "labels"
    if sw_test_lbl.exists() and sw_test_img.exists():
        n = remap_yolo_dir(sw_test_img, sw_test_lbl,
                           MERGED / "images" / "all",
                           MERGED / "labels" / "all",
                           SORTWASTE_MAP)
        ok(f"SortWaste test: {n} images")
        total += n

    return total

def process_keremberke() -> int:
    banner("keremberke/garbage-object-detection (10,464 images, COCO)")

    base = RAW / "keremberke" / "data"

    total = 0
    for split in ("train", "valid", "test"):
        split_dir = base / split
        if not split_dir.exists():
            continue
        # Find COCO JSON
        coco_json = split_dir / "_annotations.coco.json"
        if not coco_json.exists():
            coco_jsons = list(split_dir.glob("*coco*.json")) + list(split_dir.glob("*.json"))
            coco_json = coco_jsons[0] if coco_jsons else None
        if coco_json is None:
            warn(f"keremberke {split}: no COCO JSON found")
            continue
        n = coco_to_yolo(coco_json, split_dir,
                          MERGED / "images" / "all",
                          MERGED / "labels" / "all",
                          name_map=KEREMBERKE_NAME_MAP)
        ok(f"keremberke {split}: {n} images")
        total += n
    return total

def process_dmedhi() -> int:
    banner("dmedhi/garbage-image-classification-detection (3,490 images, Parquet)")

    try:
        from datasets import load_dataset
    except ImportError:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "datasets"])
        from datasets import load_dataset

    print("  Loading dmedhi/garbage-image-classification-detection ...")
    try:
        ds = load_dataset("dmedhi/garbage-image-classification-detection")
    except Exception as e:
        warn(f"Load failed: {e}")
        return 0

    # The dataset has train/val splits
    total = 0
    for split_name in ds:
        split = ds[split_name]
        print(f"  Processing split: {split_name} ({len(split)} rows)")
        for i, row in enumerate(split):
            img = row.get("image")
            if img is None:
                continue

            img_name = f"dmedhi_{split_name}_{i:06d}"
            img_path = MERGED / "images" / "all" / f"{img_name}.jpg"
            img_path.parent.mkdir(parents=True, exist_ok=True)

            if hasattr(img, "save"):
                img.save(img_path, "JPEG")
            elif isinstance(img, bytes):
                img_path.write_bytes(img)

            w = img.width if hasattr(img, "width") else row.get("width", 640)
            h = img.height if hasattr(img, "height") else row.get("height", 640)

            obj_data = row.get("objects", row)
            bboxes = obj_data.get("bbox", [])
            cats = obj_data.get("category", [])

            labels = []
            for bi, bbox in enumerate(bboxes):
                if not bbox or len(bbox) < 4:
                    continue
                x, y, bw, bh = bbox[:4]
                cat_name = cats[bi] if bi < len(cats) else None
                if cat_name is None or cat_name not in DMEDHI_NAME_MAP:
                    continue
                mc = DMEDHI_NAME_MAP[cat_name]
                labels.append(
                    f"{mc} {(x+bw/2)/w:.6f} {(y+bh/2)/h:.6f} "
                    f"{bw/w:.6f} {bh/h:.6f}"
                )
            if not labels:
                continue
            (MERGED / "labels" / "all" / f"{img_name}.txt").write_text("\n".join(labels))
            total += 1

    ok(f"dmedhi: {total} images")
    return total

def process_taco() -> int:
    banner("TACO (1,500 images, COCO, local)")

    taco_root = ROOT / "datasets" / "taco_raw" / "TACO-master" / "data"
    coco_json = taco_root / "annotations.json"
    img_dir = taco_root

    if not coco_json.exists():
        # Try unofficial annotations
        coco_json = taco_root / "annotations_unofficial.json"
    if not coco_json.exists():
        warn("TACO annotations not found, skipping")
        return 0

    # Build TACO name→id map from the string→int mapping
    taco_names = {k: v for k, v in TACO_REMAP.items() if isinstance(k, str)}

    n = coco_to_yolo(coco_json, img_dir,
                      MERGED / "images" / "all",
                      MERGED / "labels" / "all",
                      name_map=taco_names)
    ok(f"TACO: {n} images")
    return n

def process_roboflow() -> int:
    banner("Roboflow (2,783 images, YOLO, local)")

    rbf_root = ROOT / "datasets" / "roboflow_raw"
    total = 0

    for split in ("train", "valid", "test"):
        img_d = rbf_root / split / "images"
        lbl_d = rbf_root / split / "labels"
        if img_d.exists():
            n = remap_yolo_dir(img_d, lbl_d,
                               MERGED / "images" / "all",
                               MERGED / "labels" / "all",
                               ROBOFLOW_MAP)
            ok(f"Roboflow {split}: {n} images")
            total += n
    return total

# ── Merge & split ────────────────────────────────────────────────────────────

def create_train_val_split(val_ratio: float = 0.15, seed: int = 42):
    banner("Creating train/val split")

    import random
    all_img = MERGED / "images" / "all"
    all_lbl = MERGED / "labels" / "all"

    stems = sorted([
        f.stem for f in all_img.iterdir() if f.suffix.lower() in IMG_EXTS
    ])
    if not stems:
        warn("No images to split!")
        return

    random.seed(seed)
    random.shuffle(stems)
    split_idx = int(len(stems) * (1 - val_ratio))
    train_stems = set(stems[:split_idx])
    val_stems = set(stems[split_idx:])

    train_img = MERGED / "images" / "train"
    train_lbl = MERGED / "labels" / "train"
    val_img = MERGED / "images" / "val"
    val_lbl = MERGED / "labels" / "val"

    for d in [train_img, train_lbl, val_img, val_lbl]:
        d.mkdir(parents=True, exist_ok=True)
        for f in d.iterdir():
            f.unlink()

    for stem in train_stems:
        for ext in IMG_EXTS:
            src = all_img / f"{stem}{ext}"
            if src.exists():
                shutil.move(str(src), str(train_img / f"{stem}{ext}"))
                break
        lbl = all_lbl / f"{stem}.txt"
        if lbl.exists():
            shutil.move(str(lbl), str(train_lbl / f"{stem}.txt"))

    for stem in val_stems:
        for ext in IMG_EXTS:
            src = all_img / f"{stem}{ext}"
            if src.exists():
                shutil.move(str(src), str(val_img / f"{stem}{ext}"))
                break
        lbl = all_lbl / f"{stem}.txt"
        if lbl.exists():
            shutil.move(str(lbl), str(val_lbl / f"{stem}.txt"))

    ok(f"Train: {len(train_stems)} images, Val: {len(val_stems)} images")

def print_stats():
    banner("Dataset statistics")
    class_counts = {i: 0 for i in range(NUM_CLASSES)}
    total_imgs = 0
    for split in ("train", "val"):
        lbl_d = MERGED / "labels" / split
        img_d = MERGED / "images" / split
        total_imgs += count_images(img_d)
        for lbl in lbl_d.glob("*.txt"):
            for line in lbl.read_text().splitlines():
                if line.strip():
                    try:
                        cid = int(line.split()[0])
                        class_counts[cid] = class_counts.get(cid, 0) + 1
                    except (ValueError, IndexError):
                        pass

    total_ann = sum(class_counts.values())
    print(f"  Total: {total_imgs} images, {total_ann} annotations")
    for cid in range(NUM_CLASSES):
        pct = class_counts[cid] / total_ann * 100 if total_ann else 0
        bar = "#" * int(pct / 2)
        print(f"  {MIRA_CLASSES[cid]:8s}: {class_counts[cid]:5d} ({pct:5.1f}%) {bar}")

def write_yaml():
    (MERGED / "images" / "train").mkdir(parents=True, exist_ok=True)
    (MERGED / "images" / "val").mkdir(parents=True, exist_ok=True)
    yaml_content = f"""train: {MERGED / "images" / "train"}
val: {MERGED / "images" / "val"}
nc: {NUM_CLASSES}
names: {MIRA_CLASSES}
"""
    (MERGED / "dataset.yaml").write_text(yaml_content)
    ok(f"Written {MERGED / 'dataset.yaml'}")

# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Download and merge MIRA datasets")
    parser.add_argument("--skip-download", action="store_true",
                        help="Skip downloading, only merge existing raw data")
    args = parser.parse_args()

    # Clean old merge output
    old_all = MERGED / "images" / "all"
    if old_all.exists():
        shutil.rmtree(old_all)
    old_lbl = MERGED / "labels" / "all"
    if old_lbl.exists():
        shutil.rmtree(old_lbl)
    MERGED.mkdir(parents=True, exist_ok=True)
    (MERGED / "images" / "all").mkdir(parents=True, exist_ok=True)
    (MERGED / "labels" / "all").mkdir(parents=True, exist_ok=True)
    (MERGED / "images" / "train").mkdir(parents=True, exist_ok=True)
    (MERGED / "labels" / "train").mkdir(parents=True, exist_ok=True)
    (MERGED / "images" / "val").mkdir(parents=True, exist_ok=True)
    (MERGED / "labels" / "val").mkdir(parents=True, exist_ok=True)

    total = 0

    total += process_sortwaste()
    total += process_keremberke()
    total += process_dmedhi()

    total += process_taco()
    total += process_roboflow()

    banner(f"Grand total merged: {total} images")

    create_train_val_split()
    print_stats()
    write_yaml()

    print(f"\n  Dataset ready at: {MERGED}")
    print(f"  Config: {MERGED / 'dataset.yaml'}")
    print(f"  Next: run training on molab with --data {MERGED / 'dataset.yaml'}")

if __name__ == "__main__":
    main()