"""Unified dataset merger for MIRA.

Combines any subset of available sources into one YOLO-format dataset with
5 classes: glass, metal, paper, plastic, trash.

Usage:
    py scripts/merge_dataset.py --sources taco_trashnet,roboflow,warp
    py scripts/merge_dataset.py --sources taco_trashnet,warp --output datasets/mira_tnw
    py scripts/merge_dataset.py --sources warp --output datasets/mira_warp_only
    py scripts/merge_dataset.py --sources taco_trashnet --custom my_data:my_mapping.json
    py scripts/merge_dataset.py --sources taco_trashnet,warp --dry-run
"""

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATASETS = ROOT / "datasets"

_scripts_dir = str(Path(__file__).resolve().parent)
if _scripts_dir not in sys.path:
    sys.path.insert(0, _scripts_dir)

from merge_utils import WARP_MAPPING, WARP_DIR


# ── Source registry ──────────────────────────────────────────────────
# Each source defines how to add its data to the output directory.


def _add_taco_trashnet(output_dir, dry_run=False):
    """Copy TACO + TrashNet (mira_v2) — already in 5-class MIRA format."""
    src = DATASETS / "mira_v2"
    if dry_run:
        print(f"  [DRY] TACO+TrashNet: {src}")
        return 0, 0
    print("  Copying TACO + TrashNet (mira_v2)...")
    from merge_utils import copy_passthrough

    added = 0
    for split in ["train", "val"]:
        a, _ = copy_passthrough(
            src / "images" / split,
            src / "labels" / split,
            output_dir / "images" / split,
            output_dir / "labels" / split,
        )
        added += a
    return added, 0


def _add_roboflow(output_dir, dry_run=False):
    """Add Roboflow Trash Detection with 64->5 class remapping."""
    from class_mappings import ROBOFLOW_MAPPING

    src = DATASETS / "roboflow_raw"
    if dry_run:
        print(f"  [DRY] Roboflow: {src}")
        return 0, 0
    print("  Adding Roboflow (64->5 remap)...")
    from merge_utils import copy_remapped_images

    roboflow_split_map = {"train": "train", "valid": "val", "test": "train"}
    added = 0
    skipped = 0
    for src_split, dst_split in roboflow_split_map.items():
        img_src = src / src_split / "images"
        lbl_src = src / src_split / "labels"
        if not lbl_src.exists():
            continue
        stems = [f.stem for f in lbl_src.glob("*.txt")]
        a, s = copy_remapped_images(
            stems,
            img_src,
            lbl_src,
            output_dir / "images" / dst_split,
            output_dir / "labels" / dst_split,
            ROBOFLOW_MAPPING,
        )
        added += a
        skipped += s
    return added, skipped


def _add_warp(output_dir, dry_run=False):
    """Add WaRP with 28->5 class remap, 80/20 split, train->val copy."""
    from merge_utils import copy_remapped_images, create_split_from_train

    warp_img_dir = WARP_DIR / "train" / "images"
    warp_lbl_dir = WARP_DIR / "train" / "labels"
    if dry_run:
        print(f"  [DRY] WaRP: {WARP_DIR}")
        return 0, 0
    print("  Creating WaRP split (80/20)...")
    train_stems, val_stems = create_split_from_train(warp_img_dir)
    print(f"    Train: {len(train_stems)} | Val: {len(val_stems)}")
    print("  Adding WaRP (28->5 remap)...")
    added = 0
    skipped = 0
    for dst_split, stems in [("train", train_stems), ("val", val_stems)]:
        a, s = copy_remapped_images(
            stems,
            warp_img_dir,
            warp_lbl_dir,
            output_dir / "images" / dst_split,
            output_dir / "labels" / dst_split,
            WARP_MAPPING,
        )
        added += a
        skipped += s
    return added, skipped


def _add_custom(source_path, mapping_path, output_dir, dry_run=False):
    """Add a custom YOLO-format dataset with optional class remapping.

    Args:
        source_path: Path to dataset root (must have images/ and labels/ with train/val splits)
        mapping_path: Optional JSON file mapping old class IDs to new IDs (0-4)
    """
    src = Path(source_path)
    if not src.exists():
        print(f"  ERROR: Custom source not found: {src}")
        return 0, 0

    mapping = {}
    if mapping_path:
        with open(mapping_path) as f:
            mapping = {int(k): int(v) for k, v in json.load(f).items()}

    if dry_run:
        print(f"  [DRY] Custom: {src} (mapping: {len(mapping)} entries)")
        return 0, 0

    print(f"  Adding custom dataset: {src.name}...")
    added = 0
    skipped = 0
    for split in ["train", "val"]:
        img_src = src / "images" / split
        lbl_src = src / "labels" / split
        if not img_src.exists() or not lbl_src.exists():
            print(f"    Skipping {split} (not found)")
            continue
        if mapping:
            from merge_utils import copy_remapped_images

            stems = [f.stem for f in lbl_src.glob("*.txt")]
            a, s = copy_remapped_images(
                stems,
                img_src,
                lbl_src,
                output_dir / "images" / split,
                output_dir / "labels" / split,
                mapping,
            )
        else:
            from merge_utils import copy_passthrough

            a, s = copy_passthrough(
                img_src,
                lbl_src,
                output_dir / "images" / split,
                output_dir / "labels" / split,
            )
        added += a
        skipped += s
    return added, skipped


# ── CLI ──────────────────────────────────────────────────────────────
SOURCES = {
    "taco_trashnet": ("TACO + TrashNet (mira_v2)", _add_taco_trashnet),
    "roboflow": ("Roboflow Trash Detection", _add_roboflow),
    "warp": ("WaRP", _add_warp),
}


def parse_args():
    p = argparse.ArgumentParser(
        description="Unified MIRA dataset merger",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --sources taco_trashnet,roboflow,warp
  %(prog)s --sources taco_trashnet,warp --output datasets/mira_tnw
  %(prog)s --sources warp --output datasets/mira_warp_only
  %(prog)s --sources taco_trashnet --custom my_data:my_mapping.json
  %(prog)s --sources taco_trashnet,warp --dry-run
        """,
    )
    p.add_argument("--sources", type=str, required=True, help="Comma-separated sources: " + ", ".join(SOURCES.keys()))
    p.add_argument("--output", type=Path, default=None, help="Output dataset directory (default: auto-named)")
    p.add_argument("--custom", type=str, default=None, help="Custom dataset as path or path:mapping.json")
    p.add_argument("--dry-run", action="store_true", help="Preview stats without copying files")
    return p.parse_args()


def main():
    args = parse_args()
    source_keys = [s.strip() for s in args.sources.split(",")]
    for s in source_keys:
        if s not in SOURCES:
            print(f"Unknown source: {s}")
            print(f"Available: {', '.join(SOURCES.keys())}")
            return

    if args.output:
        output_dir = args.output
    else:
        name = "_".join(sorted(source_keys))
        if args.custom:
            custom_name = Path(args.custom.split(":")[0]).stem
            name = f"{name}_{custom_name}"
        output_dir = DATASETS / f"mira_{name}"

    # Ensure output directories exist
    for split in ("train", "val"):
        (output_dir / "images" / split).mkdir(parents=True, exist_ok=True)
        (output_dir / "labels" / split).mkdir(parents=True, exist_ok=True)

    print("MIRA Dataset Merger")
    print(f"  Sources: {', '.join(source_keys)}")
    if args.custom:
        print(f"  Custom:  {args.custom}")
    print(f"  Output:  {output_dir}")
    print()

    if args.dry_run:
        print("[DRY RUN] No files will be copied.\n")

    # Process sources
    total_added = 0
    total_skipped = 0
    for source_key in source_keys:
        label, add_fn = SOURCES[source_key]
        print(f"[{label}]")
        a, s = add_fn(output_dir, dry_run=args.dry_run)
        total_added += a
        total_skipped += s
        if not args.dry_run:
            print(f"  Added: {a} images | Skipped: {s}")
        print()

    # Process custom dataset
    if args.custom:
        parts = args.custom.split(":")
        custom_path = parts[0]
        custom_mapping = parts[1] if len(parts) > 1 else None
        print(f"[Custom: {Path(custom_path).name}]")
        a, s = _add_custom(custom_path, custom_mapping, output_dir, dry_run=args.dry_run)
        total_added += a
        total_skipped += s
        if not args.dry_run:
            print(f"  Added: {a} images | Skipped: {s}")
        print()

    if not args.dry_run:
        from merge_utils import print_stats, write_dataset_yaml

        print_stats(output_dir, f"Merged: {', '.join(source_keys)}")
        write_dataset_yaml(output_dir)

    print("\nDone!")


if __name__ == "__main__":
    main()
