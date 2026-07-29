"""CLI commands for merging, listing, and validating YOLO-format datasets."""

import sys
from pathlib import Path

from src.config import ROOT_DIR
from src.pipeline.registry import register_command


def _add_merge_args(parser):
    parser.add_argument("--sources", type=str, nargs="+", required=True, help="Registered source keys to merge.")
    parser.add_argument("--output", type=str, required=True, help="Output directory for merged dataset.")
    parser.add_argument("--custom", type=str, default=None, help="Optional path to a custom YOLO-format dataset.")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be merged without copying files.")


@register_command("merge", "Merge registered dataset sources into a unified YOLO dataset", add_args=_add_merge_args)
def cmd_merge(args):
    from src.pipeline.dataset import DatasetRegistry

    registry = DatasetRegistry()
    n = registry.discover()
    print(f"Discovered {n} dataset sources.")
    output_path = Path(args.output).resolve()
    try:
        is_rel = output_path.is_relative_to(ROOT_DIR.resolve())
    except AttributeError:
        is_rel = str(output_path.resolve()).startswith(str(ROOT_DIR.resolve()))
    if not is_rel:
        print("Error: Output path must be within the project directory.")
        sys.exit(1)
    result = registry.merge(
        sources=args.sources,
        output=output_path,
        custom_path=Path(args.custom) if args.custom else None,
        dry_run=args.dry_run,
    )
    print(f"\nMerge complete: {result.total_added} added, {result.total_skipped} skipped")
    print(f"Output: {result.output_dir}")


@register_command("datasets", "List registered dataset sources from datasets/registry/*.yaml")
def cmd_datasets(args):
    from src.pipeline.dataset import DatasetRegistry

    registry = DatasetRegistry()
    registry.discover()
    sources = registry.list_sources()
    if not sources:
        print("No dataset sources found in datasets/registry/")
        return
    print(f"{'Key':<24} {'Name':<32} {'Format':<12} {'Exists':<8}")
    print("-" * 76)
    for s in sources:
        exists = "yes" if s["exists"] else "NO"
        print(f"{s['key']:<24} {s['name']:<32} {s['format']:<12} {exists:<8}")


def _add_validate_args(parser):
    parser.add_argument("--dataset", type=str, required=True, help="Path to dataset directory to validate.")


@register_command("validate", "Validate a YOLO-format dataset", add_args=_add_validate_args)
def cmd_validate(args):
    from src.pipeline.validators import validate_yolo_dataset

    result = validate_yolo_dataset(args.dataset)
    print(f"\n  Dataset validation: {args.dataset}")
    print(f"  {'=' * 50}")
    print(f"  Valid:          {'YES' if result.is_valid else 'NO'}")
    print(f"  Images:         {result.total_images}")
    print(f"  Labels:         {result.total_labels}")

    if result.class_counts:
        print("\n  Class distribution:")
        for cls_id, count in sorted(result.class_counts.items()):
            print(f"    class {cls_id}: {count} instances")

    if result.warnings:
        print("\n  Warnings:")
        for w in result.warnings:
            print(f"    ! {w}")

    if result.errors:
        print("\n  Errors:")
        for e in result.errors:
            print(f"    ! {e}")

    if result.orphaned_labels:
        print(f"\n  Orphaned labels ({len(result.orphaned_labels)}):")
        for p in result.orphaned_labels[:5]:
            print(f"    {p}")
        if len(result.orphaned_labels) > 5:
            print(f"    ... and {len(result.orphaned_labels) - 5} more")

        print()

    if not result.is_valid:
        sys.exit(1)

