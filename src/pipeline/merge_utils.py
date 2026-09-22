# Shared utilities for MIRA dataset merging.

import sys
import shutil
import random
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from src.config import CLASS_NAMES as _CLASS_NAMES_LIST, NUM_CLASSES

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tiff"}

CLASS_NAMES = {class_id: class_name for class_id, class_name in enumerate(_CLASS_NAMES_LIST)}
MIRA_CLASSES = list(CLASS_NAMES.values())


def remap_label_file(lbl_file, mapping):
    label_lines = lbl_file.read_text(encoding="utf-8").splitlines()
    remapped_lines = []
    skipped_count = 0
    for label_line in label_lines:
        fields = label_line.split()
        if not fields:
            continue
        if len(fields) < 5:
            skipped_count += 1
            continue
        try:
            original_class_id = int(fields[0])
            coordinates = [float(value) for value in fields[1:5]]
        except ValueError:
            skipped_count += 1
            continue
        valid_coordinates = all(0.0 <= coordinate <= 1.0 for coordinate in coordinates)
        if original_class_id not in mapping or not valid_coordinates:
            skipped_count += 1
            continue

        mapped_class_id = mapping[original_class_id]
        coordinate_text = " ".join(fields[1:])
        remapped_lines.append(f"{mapped_class_id} {coordinate_text}\n")
    if skipped_count > 0:
        print(f"Warning: {skipped_count} annotations skipped - no valid classes after remap", file=sys.stderr)
    return remapped_lines


def copy_passthrough(src_img_dir, src_lbl_dir, dst_img_dir, dst_lbl_dir):
    if not src_img_dir.exists() or not src_lbl_dir.exists():
        return 0, 0
    dst_img_dir.mkdir(parents=True, exist_ok=True)
    dst_lbl_dir.mkdir(parents=True, exist_ok=True)
    added = 0
    for image_path in src_img_dir.iterdir():
        if image_path.suffix.lower() in IMAGE_EXTENSIONS:
            destination_image = dst_img_dir / image_path.name
            shutil.copy2(image_path, destination_image)
            added += 1
    for label_path in src_lbl_dir.glob("*.txt"):
        destination_label = dst_lbl_dir / label_path.name
        shutil.copy2(label_path, destination_label)
    return added, 0


def copy_remapped_images(stems, src_img_dir, src_lbl_dir, dst_img_dir, dst_lbl_dir, mapping):
    dst_img_dir.mkdir(parents=True, exist_ok=True)
    dst_lbl_dir.mkdir(parents=True, exist_ok=True)
    added = 0
    skipped = 0
    for stem in stems:
        source_label_path = src_lbl_dir / f"{stem}.txt"
        if not source_label_path.exists():
            continue
        remapped_lines = remap_label_file(source_label_path, mapping)
        if not remapped_lines:
            skipped += 1
            print(f"  Warning: {stem} skipped - no valid classes after remap")
            continue

        source_image_path = None
        for candidate_path in src_img_dir.iterdir():
            matches_stem = candidate_path.stem == stem
            is_supported_image = candidate_path.suffix.lower() in IMAGE_EXTENSIONS
            if matches_stem and is_supported_image:
                source_image_path = candidate_path
                break

        if source_image_path is not None:
            destination_image_path = dst_img_dir / source_image_path.name
            shutil.copy2(source_image_path, destination_image_path)
            destination_label_path = dst_lbl_dir / source_label_path.name
            with open(destination_label_path, "w") as output_file:
                output_file.writelines(remapped_lines)
            added += 1
        else:
            skipped += 1
    return added, skipped


def create_split_from_train(src_img_dir, val_ratio=0.2, seed=42):
    image_stems = []
    for image_path in src_img_dir.iterdir():
        if image_path.suffix.lower() in IMAGE_EXTENSIONS:
            image_stems.append(image_path.stem)
    image_stems.sort()

    random_generator = random.Random(seed)
    random_generator.shuffle(image_stems)

    train_boundary = int(len(image_stems) * (1 - val_ratio))
    training_stems = image_stems[:train_boundary]
    validation_stems = image_stems[train_boundary:]
    return training_stems, validation_stems


def print_stats(output_dir, label):
    print(f"\n{'=' * 50}")
    class_counts = {class_id: 0 for class_id in range(NUM_CLASSES)}
    total_image_count = 0
    for split_name in ["train", "val"]:
        image_directory = output_dir / "images" / split_name
        label_directory = output_dir / "labels" / split_name
        split_image_count = sum(1 for _ in image_directory.glob("*"))
        total_image_count += split_image_count
        for label_path in label_directory.glob("*.txt"):
            label_lines = label_path.read_text().splitlines()
            for label_line in label_lines:
                if label_line.strip():
                    try:
                        class_id = int(label_line.split()[0])
                    except (ValueError, IndexError):
                        continue
                    class_counts[class_id] = class_counts.get(class_id, 0) + 1

    total_annotation_count = sum(class_counts.values())
    print(f"{label}")
    print(f"  Total: {total_image_count} images, {total_annotation_count} annotations")
    for class_id in range(NUM_CLASSES):
        if total_annotation_count:
            percentage = class_counts[class_id] / total_annotation_count * 100
        else:
            percentage = 0
        bar = "#" * int(percentage / 2)
        print(
            f"  {CLASS_NAMES[class_id]:8s}: {class_counts[class_id]:5d} "
            f"({percentage:5.1f}%) {bar}"
        )


def write_dataset_yaml(output_dir):
    yaml_content = f"train: images/train\nval: images/val\nnc: {NUM_CLASSES}\nnames: {MIRA_CLASSES}\n"
    (output_dir / "dataset.yaml").write_text(yaml_content, encoding="utf-8")
    print(f"\nSaved: {output_dir / 'dataset.yaml'}")
