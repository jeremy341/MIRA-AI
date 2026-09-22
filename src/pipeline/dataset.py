"""Dataset registry and dataset merging functionality for MIRA."""

from __future__ import annotations

from dataclasses import dataclass, field
import shutil
from pathlib import Path
from typing import Any

from ..config import ROOT_DIR
from ..logger import get_logger
from . import merge_utils as mu

logger = get_logger(__name__)


def _derive_label_path(img_rel: str) -> str:
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
        """Load a dataset source descriptor from a YAML file."""
        import yaml

        with open(yaml_path, encoding="utf-8") as f:
            data = yaml.safe_load(f)

        required = ["key", "name", "source_format", "input_path"]
        missing = []
        for field_name in required:
            if field_name not in data:
                missing.append(field_name)
        if missing:
            raise ValueError(f"Dataset descriptor {yaml_path.name} missing required fields: {missing}")

        if data["source_format"] not in ("yolo", "coco"):
            raise ValueError(f"Unknown source_format '{data['source_format']}' in {yaml_path.name}")

        registry_dir = yaml_path.parent
        if registry_dir.name == "registry" and registry_dir.parent.name == "datasets":
            root = registry_dir.parent.parent
        else:
            root = registry_dir.parent
        input_path = (root / data["input_path"]).resolve()
        try:
            input_path.relative_to(root.resolve())
        except ValueError:
            raise ValueError(f"input_path '{data['input_path']}' escapes project root in {yaml_path.name}") from None

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
            registry_dir = ROOT_DIR / "datasets" / "registry"
        self.registry_dir = Path(registry_dir)
        self.sources: dict[str, DatasetSource] = {}

    def discover(self) -> int:
        # Scan registry dir for *.yaml files. Returns count of sources found.
        self.sources.clear()
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
        source_rows = []
        for source in self.sources.values():
            source_rows.append(
                {
                    "key": source.key,
                    "name": source.name,
                    "description": source.description,
                    "format": source.source_format,
                    "path": str(source.input_path),
                    "exists": source.input_path.exists(),
                    "stats": source.stats,
                }
            )
        return source_rows

    def get_source(self, key: str) -> DatasetSource:
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
        # Merge registered sources + optional custom dataset.
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

            has_mapping = bool(source.class_mapping)
            if source.source_format == "yolo" and not has_mapping:
                added = self._merge_passthrough(source, output, dry_run)
                skipped = 0
            elif source.source_format == "yolo":
                added, skipped = self._merge_remapped(source, output, dry_run)
            elif source.source_format == "coco":
                added, skipped = self._merge_coco(source, output, dry_run)
            else:
                raise ValueError(f"Unsupported dataset format: {source.source_format}")
            total_added += added
            total_skipped += skipped

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
        # Copy data that's already in MIRA 5-class format.
        if dry_run:
            print(f"  [DRY] Passthrough: {source.input_path}")
            return 0

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
        if dry_run:
            if source.class_mapping is not None and len(source.class_mapping) > 0:
                print(f"  [DRY] Remap: {source.input_path} ({len(source.class_mapping)} mappings)")
            return 0, 0

        print(f"  Adding {source.name} (remap {source.source_format})...")
        total_added = 0
        total_skipped = 0

        for split_name, split_rel in source.splits.items():
            img_src = source.input_path / split_rel
            lbl_src = source.input_path / _derive_label_path(split_rel)

            if not img_src.exists() or not lbl_src.exists():
                continue

            dst_split = "val" if split_name in ("valid", "test") else split_name

            if split_name == "train" and "val" not in source.splits:
                train_stems, val_stems = mu.create_split_from_train(img_src)
                split_stems = [("train", train_stems), ("val", val_stems)]
                for output_split, stems in split_stems:
                    a, s = mu.copy_remapped_images(
                        stems,
                        img_src,
                        lbl_src,
                        output / "images" / output_split,
                        output / "labels" / output_split,
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

    @staticmethod
    def _find_coco_image(
        source_path: Path,
        split_name: str,
        image_filename: str,
    ) -> Path | None:
        image_name = Path(image_filename).name
        image_candidates = [source_path / image_filename]
        image_candidates.append(source_path / "images" / image_name)
        image_candidates.append(source_path / "images" / split_name / image_name)
        source_root = source_path.resolve()
        for candidate_path in image_candidates:
            candidate = candidate_path.resolve()
            try:
                candidate.relative_to(source_root)
            except ValueError:
                continue
            if candidate.exists():
                return candidate
        return None

    @staticmethod
    def _coco_annotations_to_yolo_lines(
        annotations: list[dict],
        class_mapping: dict[int, int] | None,
        image_width: int,
        image_height: int,
    ) -> list[str]:
        yolo_lines: list[str] = []
        for annotation in annotations:
            category_id = annotation["category_id"]
            if class_mapping:
                if category_id not in class_mapping:
                    continue
                target_category_id = class_mapping[category_id]
            else:
                target_category_id = category_id

            x, y, box_width, box_height = annotation["bbox"]
            center_x = (x + box_width / 2.0) / image_width
            center_y = (y + box_height / 2.0) / image_height
            normalized_width = box_width / image_width
            normalized_height = box_height / image_height
            yolo_lines.append(
                f"{target_category_id} {center_x:.6f} {center_y:.6f} "
                f"{normalized_width:.6f} {normalized_height:.6f}\n"
            )
        return yolo_lines

    @staticmethod
    def _write_coco_image(
        output: Path,
        source_key: str,
        split_name: str,
        image_id: int,
        image_filename: str,
        image_path: Path,
        yolo_lines: list[str],
        destination_split: str,
    ) -> None:
        destination_image_dir = output / "images" / destination_split
        destination_label_dir = output / "labels" / destination_split
        destination_image_dir.mkdir(parents=True, exist_ok=True)
        destination_label_dir.mkdir(parents=True, exist_ok=True)

        output_stem = f"{source_key}_{split_name}_{image_id}_{Path(image_filename).stem}"
        destination_image = destination_image_dir / f"{output_stem}{image_path.suffix.lower()}"
        shutil.copy2(image_path, destination_image)

        label_path = destination_label_dir / f"{output_stem}.txt"
        with open(label_path, "w", encoding="utf-8") as label_file:
            label_file.writelines(yolo_lines)

    def _merge_coco(
        self,
        source: DatasetSource,
        output: Path,
        dry_run: bool,
    ) -> tuple[int, int]:
        # Convert COCO annotations to YOLO format and merge.
        if dry_run:
            print(f"  [DRY] COCO convert: {source.input_path}")
            return 0, 0

        try:
            from pycocotools.coco import COCO
        except ImportError:
            logger.warning(
                "Cannot process COCO source '%s': pycocotools is not installed. "
                "Install it with: pip install pycocotools",
                source.key,
            )
            return 0, 0

        print(f"  Converting {source.name} (COCO -> YOLO)...")
        total_added = 0
        total_skipped = 0

        for split_name, split_rel in source.splits.items():
            ann_file = source.input_path / split_rel
            if not ann_file.exists():
                logger.warning("  COCO annotation file not found: %s", ann_file)
                continue

            coco = COCO(str(ann_file))
            img_ids = coco.getImgIds()
            if not img_ids:
                logger.warning("  No images found in COCO annotations: %s", ann_file)
                continue

            dst_split = "val" if split_name in ("valid", "test") else split_name

            for img_id in img_ids:
                img_info = coco.loadImgs(img_id)[0]
                ann_ids = coco.getAnnIds(imgIds=img_id)
                anns = coco.loadAnns(ann_ids)

                if not anns:
                    total_skipped += 1
                    continue

                img_filename = img_info["file_name"]
                img_path = self._find_coco_image(
                    source.input_path,
                    split_name,
                    img_filename,
                )
                if img_path is None:
                    logger.debug("  Image not found for annotation: %s", img_filename)
                    total_skipped += 1
                    continue

                image_width = img_info["width"]
                image_height = img_info["height"]
                if image_width <= 0 or image_height <= 0:
                    total_skipped += 1
                    continue
                yolo_lines = self._coco_annotations_to_yolo_lines(
                    anns,
                    source.class_mapping,
                    image_width,
                    image_height,
                )

                if yolo_lines:
                    self._write_coco_image(
                        output,
                        source.key,
                        split_name,
                        img_id,
                        img_filename,
                        img_path,
                        yolo_lines,
                        dst_split,
                    )

                    total_added += 1
                else:
                    total_skipped += 1

        return total_added, total_skipped

    def _merge_custom(
        self,
        path: Path,
        mapping: dict[int, int] | None,
        output: Path,
        dry_run: bool,
    ) -> tuple[int, int]:
        # Add a custom YOLO-format dataset.
        path = Path(path)
        if not path.exists():
            logger.error("Custom source not found: %s", path)
            return 0, 0

        if dry_run:
            print(f"  [DRY] Custom: {path}")
            return 0, 0

        print(f"  Adding custom dataset: {path.name}...")
        added = 0
        skipped = 0
        for split in ("train", "val"):
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
