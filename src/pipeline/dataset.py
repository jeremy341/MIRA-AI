"""Dataset registry for MIRA pipeline.

Discovers dataset sources from YAML descriptors in datasets/registry/
and provides a unified merge interface.

Usage:
    from pipeline.dataset import DatasetRegistry

    registry = DatasetRegistry()
    registry.discover()  # scans datasets/registry/*.yaml

    # List available sources
    for src in registry.list_sources():
        print(f"{src['key']}: {src['name']}")

    # Merge sources
    result = registry.merge(
        sources=["taco_trashnet", "roboflow"],
        output=Path("datasets/mira_merged"),
    )
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from ..logger import get_logger

logger = get_logger(__name__)


def _import_merge_utils():
    """Lazy-import merge_utils from scripts/ directory."""
    import importlib
    import sys

    scripts_dir = str(Path(__file__).resolve().parent.parent.parent / "scripts")
    if scripts_dir not in sys.path:
        sys.path.insert(0, scripts_dir)
    return importlib.import_module("merge_utils")


def _derive_label_path(img_rel: str) -> str:
    """Derive the label directory path from an image directory path.

    Handles common patterns: 'images/train' -> 'labels/train',
    'train/images' -> 'train/labels', etc.
    """
    parts = Path(img_rel).parts
    new_parts = []
    for part in parts:
        if part == "images":
            new_parts.append("labels")
        else:
            new_parts.append(part)
    return str(Path(*new_parts)) if new_parts else img_rel


@dataclass
class DatasetSource:
    """Represents a registered dataset source."""

    key: str
    name: str
    description: str
    source_format: str  # "yolo", "coco", "folder-per-class"
    input_path: Path
    splits: dict[str, str]  # split_name -> relative_path
    class_mapping: dict[int, int] | None  # source_id -> target_id
    stats: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_yaml(cls, yaml_path: Path) -> DatasetSource:
        """Load a dataset source from a YAML descriptor."""
        import yaml

        with open(yaml_path) as f:
            data = yaml.safe_load(f)

        required = ["key", "name", "source_format", "input_path"]
        missing = [f for f in required if f not in data]
        if missing:
            raise ValueError(f"Dataset descriptor {yaml_path.name} missing required fields: {missing}")

        if data["source_format"] not in ("yolo", "coco", "folder-per-class"):
            raise ValueError(f"Unknown source_format '{data['source_format']}' in {yaml_path.name}")

        root = yaml_path.parent.parent.parent  # datasets/registry/ -> project root
        input_path = root / data["input_path"]

        # Parse class_mapping (YAML dicts have string keys)
        class_mapping = None
        if data.get("class_mapping"):
            class_mapping = {int(k): int(v) for k, v in data["class_mapping"].items()}

        return cls(
            key=data["key"],
            name=data["name"],
            description=data.get("description", ""),
            source_format=data.get("source_format", "yolo"),
            input_path=input_path,
            splits=data.get("splits", {}),
            class_mapping=class_mapping,
            stats=data.get("stats", {}),
        )


@dataclass
class MergeResult:
    """Result of a dataset merge operation."""

    output_dir: Path
    total_added: int
    total_skipped: int
    sources_used: list[str]


class DatasetRegistry:
    """Discovers and manages dataset sources from YAML descriptors."""

    def __init__(self, registry_dir: Path | str | None = None):
        if registry_dir is None:
            registry_dir = Path(__file__).resolve().parent.parent.parent / "datasets" / "registry"
        self.registry_dir = Path(registry_dir)
        self.sources: dict[str, DatasetSource] = {}

    def discover(self) -> int:
        """Scan registry dir for *.yaml files. Returns count of sources found."""
        if not self.registry_dir.exists():
            return 0
        count = 0
        for yaml_file in sorted(self.registry_dir.glob("*.yaml")):
            try:
                source = DatasetSource.from_yaml(yaml_file)
                self.sources[source.key] = source
                count += 1
            except Exception as e:
                logger.warning("Failed to load %s: %s", yaml_file.name, e)
        return count

    def list_sources(self) -> list[dict]:
        """Return all registered sources with metadata."""
        return [
            {
                "key": s.key,
                "name": s.name,
                "description": s.description,
                "format": s.source_format,
                "path": str(s.input_path),
                "exists": s.input_path.exists(),
                "stats": s.stats,
            }
            for s in self.sources.values()
        ]

    def get_source(self, key: str) -> DatasetSource:
        """Get a specific source by key."""
        if key not in self.sources:
            available = ", ".join(self.sources.keys())
            raise KeyError(f"Unknown source '{key}'. Available: {available}")
        return self.sources[key]

    def merge(
        self,
        sources: list[str],
        output: Path,
        custom_path: Path | None = None,
        custom_mapping: dict[int, int] | None = None,
        dry_run: bool = False,
    ) -> MergeResult:
        """Merge registered sources + optional custom dataset."""
        mu = _import_merge_utils()

        # Validate and create output directory
        try:
            if not dry_run:
                output.mkdir(parents=True, exist_ok=True)
        except OSError as e:
            raise OSError(f"Cannot create output directory {output}: {e}") from e

        # Create output dirs
        if not dry_run:
            for split in ["train", "val"]:
                (output / "images" / split).mkdir(parents=True, exist_ok=True)
                (output / "labels" / split).mkdir(parents=True, exist_ok=True)

        total_added = 0
        total_skipped = 0
        sources_used = []

        # Process registered sources
        for key in sources:
            source = self.get_source(key)
            sources_used.append(key)
            logger.info("[%s]", source.name)

            if source.source_format == "yolo" and source.class_mapping is None:
                # Passthrough — already in MIRA format
                added = self._merge_passthrough(source, output, dry_run)
                total_added += added
            elif source.source_format == "yolo" and source.class_mapping:
                # Remap classes
                added, skipped = self._merge_remapped(source, output, dry_run)
                total_added += added
                total_skipped += skipped
            else:
                logger.warning("Unsupported format '%s' for %s", source.source_format, key)

        # Process custom dataset
        if custom_path:
            added, skipped = self._merge_custom(custom_path, custom_mapping, output, dry_run)
            total_added += added
            total_skipped += skipped
            sources_used.append(f"custom:{custom_path.name}")

        # Generate stats + YAML
        if not dry_run and (total_added > 0 or custom_path):
            if total_added > 0:
                mu.print_stats(output, f"Merged: {', '.join(sources_used)}")
                mu.write_dataset_yaml(output)
            elif total_added == 0:
                logger.warning("No images were added from any source.")

        return MergeResult(
            output_dir=output,
            total_added=total_added,
            total_skipped=total_skipped,
            sources_used=sources_used,
        )

    def _merge_passthrough(self, source: DatasetSource, output: Path, dry_run: bool) -> int:
        """Copy data that's already in MIRA 5-class format."""
        if dry_run:
            print(f"  [DRY] Passthrough: {source.input_path}")
            return 0

        mu = _import_merge_utils()
        print(f"  Copying {source.name} (passthrough)...")
        total = 0
        for split_name, split_rel in source.splits.items():
            img_src = source.input_path / split_rel
            lbl_src = source.input_path / _derive_label_path(split_rel)
            dst_split = "val" if split_name in ("valid", "test") else split_name
            if img_src.exists():
                a, _ = mu.copy_passthrough(
                    img_src,
                    lbl_src,
                    output / "images" / dst_split,
                    output / "labels" / dst_split,
                )
                total += a
        return total

    def _merge_remapped(self, source: DatasetSource, output: Path, dry_run: bool) -> tuple[int, int]:
        """Copy data with class ID remapping."""
        if dry_run:
            print(f"  [DRY] Remap: {source.input_path} ({len(source.class_mapping)} mappings)")
            return 0, 0

        mu = _import_merge_utils()
        print(f"  Adding {source.name} (remap {source.source_format})...")
        total_added = 0
        total_skipped = 0

        for split_name, split_rel in source.splits.items():
            img_src = source.input_path / split_rel
            lbl_src = source.input_path / _derive_label_path(split_rel)

            if not lbl_src.exists():
                continue

            dst_split = "val" if split_name in ("valid", "test") else split_name

            if split_name == "train" and "val" not in source.splits:
                train_stems, val_stems = mu.create_split_from_train(img_src)
                for ds, stems in [("train", train_stems), ("val", val_stems)]:
                    a, s = mu.copy_remapped_images(
                        stems,
                        img_src,
                        lbl_src,
                        output / "images" / ds,
                        output / "labels" / ds,
                        source.class_mapping,
                    )
                    total_added += a
                    total_skipped += s
            else:
                stems = [f.stem for f in lbl_src.glob("*.txt")]
                a, s = mu.copy_remapped_images(
                    stems,
                    img_src,
                    lbl_src,
                    output / "images" / dst_split,
                    output / "labels" / dst_split,
                    source.class_mapping,
                )
                total_added += a
                total_skipped += s

        return total_added, total_skipped

    def _merge_custom(
        self,
        path: Path,
        mapping: dict[int, int] | None,
        output: Path,
        dry_run: bool,
    ) -> tuple[int, int]:
        """Add a custom YOLO-format dataset."""
        mu = _import_merge_utils()
        path = Path(path)
        if not path.exists():
            print(f"  ERROR: Custom source not found: {path}")
            return 0, 0

        if dry_run:
            print(f"  [DRY] Custom: {path}")
            return 0, 0

        print(f"  Adding custom dataset: {path.name}...")
        added = 0
        skipped = 0
        for split in ["train", "val"]:
            img_src = path / "images" / split
            lbl_src = path / "labels" / split
            if not img_src.exists() or not lbl_src.exists():
                continue
            if mapping:
                stems = [f.stem for f in lbl_src.glob("*.txt")]
                a, s = mu.copy_remapped_images(
                    stems,
                    img_src,
                    lbl_src,
                    output / "images" / split,
                    output / "labels" / split,
                    mapping,
                )
            else:
                a, s = mu.copy_passthrough(
                    img_src,
                    lbl_src,
                    output / "images" / split,
                    output / "labels" / split,
                )
            added += a
            skipped += s
        return added, skipped
