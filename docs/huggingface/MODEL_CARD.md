---
license: mit
library_name: ultralytics
pipeline_tag: object-detection
base_model: Ultralytics/YOLO11
base_model_relation: finetune
language:
  - en
tags:
  - ultralytics
  - yolo
  - yolo11
  - yolo11n
  - yolov11
  - yolov11n
  - object-detection
  - computer-vision
  - waste-detection
  - trash-detection
  - garbage-detection
  - recycling
  - recycling-automation
  - waste-sorting
  - edge-ai
  - onnx
  - tflite
datasets:
  - dmedhi/garbage-image-classification-detection
  - garythung/trashnet
model-index:
  - name: MIRA EXP-019
    results:
      - task:
          type: object-detection
        dataset:
          name: MIRA clean balanced dataset, validation split (415 images)
          type: custom
        metrics:
          - {type: mAP50, value: 0.9058, name: mAP50}
          - {type: mAP50-95, value: 0.8215, name: mAP50-95}
          - {type: precision, value: 0.872, name: Precision}
          - {type: recall, value: 0.846, name: Recall}
---

# MIRA - YOLO11n Waste Detection for Recycling and Waste Sorting

MIRA is a custom YOLO11n object-detection project for waste detection,
recycling automation, and automated waste sorting.

The models detect five classes:

- glass
- metal
- paper
- plastic
- trash

This repository contains PyTorch, ONNX, and TFLite exports from the MIRA
experiments. The recommended reference model is `mira_exp019.pt`.

- GitHub: https://github.com/jeremy341/MIRA-AI
- Project website: https://mira-vision.vercel.app/
- PyPI package: https://pypi.org/project/mira-ai/ (`pip install mira-ai` bundles EXP-014, EXP-018 and EXP-019)

## EXP-019 performance

Validation split of the MIRA clean balanced dataset (415 images), FP32 PyTorch
weights, image size 640.

| Class | Precision | Recall | mAP50 | mAP50-95 |
|---|---:|---:|---:|---:|
| all | 0.872 | 0.846 | 0.9058 | 0.8215 |
| glass | 0.904 | 0.825 | 0.908 | 0.874 |
| metal | 0.914 | 0.960 | 0.948 | 0.827 |
| paper | 0.909 | 0.840 | 0.887 | 0.738 |
| plastic | 0.874 | 0.644 | 0.811 | 0.714 |
| trash | 0.761 | 0.963 | 0.975 | 0.955 |

| Training detail | Value |
|---|---|
| Base model | YOLO11n (`yolo11n.pt`), 2,583,127 parameters, 6.3 GFLOPs |
| Images | 5,108 train / 415 validation / 1,375 test |
| Epochs, batch, image size | 120, 32, 640 |
| Optimizer | AdamW, lr0 = 0.001, cosine schedule |
| Training time | 2.672 hours on one Kaggle T4 GPU |

The 1,375-image independent test split was **not evaluated** for EXP-019, so
these are validation numbers, not a measure of real-world accuracy.

The INT8 TFLite export at 320 px loses accuracy compared with FP32 (precision
0.797, recall 0.836, mAP50 0.862, mAP50-95 0.756, measured locally).

## Available model files

All detectors below are at the repository root and are mirrored under
`models/detection/`. Sizes are the actual file sizes in this repository.

| File | Format | Size | Description |
|---|---|---:|---|
| `mira_exp006.pt` | PyTorch | 6.2 MB | EXP-006: YOLOv8n, fused Wild + TrashNet |
| `mira_exp006_int8.tflite` | TFLite INT8 | 3.3 MB | EXP-006: YOLOv8n, fused Wild + TrashNet |
| `mira_exp009_int8.tflite` | TFLite INT8 | 3.3 MB | EXP-009: YOLOv8n, TrashNet |
| `mira_exp010_int8.tflite` | TFLite INT8 | 3.3 MB | EXP-010: INT8 export of EXP-006, wild-data calibration |
| `mira_exp011.pt` | PyTorch | 6.2 MB | EXP-011: YOLOv8n, TACO |
| `mira_exp011_int8.tflite` | TFLite INT8 | 3.3 MB | EXP-011: YOLOv8n, TACO |
| `mira_exp013.pt` | PyTorch | 5.5 MB | EXP-013: YOLO11n, TACO + TrashNet |
| `mira_exp013_int8.tflite` | TFLite INT8 | 3.0 MB | EXP-013: YOLO11n, TACO + TrashNet |
| `mira_exp014.pt` | PyTorch | 5.5 MB | EXP-014: YOLO11n, combined dataset |
| `mira_exp014_int8.tflite` | TFLite INT8 | 3.0 MB | EXP-014: YOLO11n, combined dataset |
| `mira_exp015.pt` | PyTorch | 5.5 MB | EXP-015: YOLO11n, combined dataset with WaRP |
| `mira_exp015_int8.tflite` | TFLite INT8 | 3.0 MB | EXP-015: YOLO11n, combined dataset with WaRP |
| `mira_exp016.pt` | PyTorch | 5.5 MB | EXP-016: YOLO11n, WaRP-focused dataset |
| `mira_exp016_int8.tflite` | TFLite INT8 | 3.0 MB | EXP-016: YOLO11n, WaRP-focused dataset |
| `mira_exp017.onnx` | ONNX | 10.6 MB | EXP-017: YOLO11n, larger combined dataset |
| `mira_exp017.pt` | PyTorch | 5.5 MB | EXP-017: YOLO11n, larger combined dataset |
| `mira_exp017_int8.tflite` | TFLite INT8 | 3.0 MB | EXP-017: YOLO11n, larger combined dataset |
| `mira_exp018.onnx` | ONNX | 10.6 MB | EXP-018: YOLO11n, clean balanced dataset |
| `mira_exp018.pt` | PyTorch | 5.5 MB | EXP-018: YOLO11n, clean balanced dataset |
| `mira_exp018_int8.tflite` | TFLite INT8 | 3.0 MB | EXP-018: YOLO11n, clean balanced dataset |
| `mira_exp019.onnx` | ONNX | 10.6 MB | EXP-019: YOLO11n, clean balanced repeatability run (recommended) |
| `mira_exp019.pt` | PyTorch | 5.5 MB | EXP-019: YOLO11n, clean balanced repeatability run (recommended) |
| `mira_exp019_int8_320.tflite` | TFLite INT8 | 3.0 MB | EXP-019: YOLO11n, clean balanced repeatability run (recommended), 320 px |
| `mira_exp019_int8_640.tflite` | TFLite INT8 | 3.0 MB | EXP-019: YOLO11n, clean balanced repeatability run (recommended), 640 px |

Each `.yaml` next to a model (`mira_exp014`, `017`, `018`, `019`) records its
class names and training metadata.

### Earlier classifier experiments

`models/classifier/` holds the whole-image classifiers from the first MIRA
experiments (EXP-001 to EXP-004), before the project moved to object detection:

| File | Format | Size |
|---|---|---:|
| `models/classifier/mira_classifier_baseline.keras` | Keras | 47.9 MB |
| `models/classifier/mira_classifier_fp32.tflite` | TFLite | 8.9 MB |
| `models/classifier/mira_classifier_int8.tflite` | TFLite | 2.7 MB |
| `models/classifier/mira_classifier_transfer.keras` | Keras | 9.7 MB |
| `models/classifier/mira_classifier_tuned.keras` | Keras | 24.6 MB |

See the [experiment log](https://github.com/jeremy341/MIRA-AI/blob/main/results/experiments_log.md)
for how they were trained and evaluated.

### Third-party reference model

`models/detection/gianlucasposito_yolov8n.pt` is a third-party YOLOv8n model
included only as a comparison baseline. It was not trained by MIRA and is not
covered by this repository's license.

## Experiment results

| Experiment | Model | Dataset | mAP50 | Weights here |
|---|---|---|---:|---|
| EXP-005 | YOLOv8n | Custom + TrashNet | 82.3% | not published |
| EXP-006 | YOLOv8n | Fused Wild + TrashNet | 39.4% | yes |
| EXP-007 | YOLOv8n INT8 | Quantized EXP-006 | not recorded | `mira_exp006_int8.tflite` |
| EXP-008 | YOLOv8n | Tabletop, human-annotated labels | 39.6% | not published |
| EXP-009 | YOLOv8n | TrashNet | 72.8% | TFLite only |
| EXP-010 | YOLOv8n INT8 | EXP-006 quantized with wild-data calibration | not recorded | `mira_exp010_int8.tflite` |
| EXP-011 | YOLOv8n | TACO | 35.0% | yes |
| EXP-012 | YOLOv8n INT8 | Quantized EXP-011 | not recorded | `mira_exp011_int8.tflite` |
| EXP-013 | YOLO11n | TACO + TrashNet | 55.1% | yes |
| EXP-014 | YOLO11n | Combined dataset | 60.7% | yes |
| EXP-015 | YOLO11n | Combined dataset with WaRP | 56.0% | yes |
| EXP-016 | YOLO11n | WaRP-focused dataset | 58.8% | yes |
| EXP-017 | YOLO11n | Larger combined dataset | 59.3% | yes |
| EXP-018 | YOLO11n | Clean balanced dataset | 90.6% | yes |
| EXP-019 | YOLO11n | Clean balanced repeatability run | 90.58% | yes |

EXP-007, EXP-010 and EXP-012 are INT8 quantizations of other runs, so they have no
training results of their own. EXP-007 and EXP-012 are the files
`mira_exp006_int8.tflite` and `mira_exp011_int8.tflite`. EXP-005 and EXP-008
were trained, but their weights are not currently available and are not published.

The main lesson was that adding more data did not automatically improve the
model. Removing inconsistent examples and building a cleaner, more balanced
dataset led to the strongest results in EXP-018 and EXP-019.

## Quick start

Install the required packages:

```bash
pip install ultralytics huggingface_hub
```

Download the recommended model directly from Hugging Face:

```python
from huggingface_hub import hf_hub_download
from ultralytics import YOLO

model_path = hf_hub_download(
    repo_id="Jeremy341/MIRA-AI",
    filename="mira_exp019.pt",
)

model = YOLO(model_path)

results = model.predict(
    "image.jpg",
    conf=0.25,
    save=True,
)

results[0].show()
```

For validation, provide a compatible YOLO dataset configuration:

```python
results = model.val(data="dataset.yaml")
```

## Intended use

MIRA is intended for research and prototyping in:

- waste detection
- recycling automation
- waste sorting
- computer-vision research
- edge-AI object detection
- robotic sorting experiments

The models are not presented as a finished production recycling system.

## Datasets

The models were trained using combinations of:

- [dmedhi garbage image classification/detection](https://huggingface.co/datasets/dmedhi/garbage-image-classification-detection)
- [TACO](https://github.com/pedropro/TACO)
- [TrashNet](https://github.com/garythung/trashnet)
- [Roboflow Trash Detection](https://universe.roboflow.com/jerry-jukbu/trash-detection-1fjjc-uqlv1)

The datasets were remapped to the five MIRA classes. Each dataset remains
subject to its original license and usage terms.

## Limitations

The models can struggle with:

- white crumpled paper
- cans viewed from the opening
- strongly overlapping objects
- unusual lighting
- unusual viewing angles
- waste objects outside the training distribution

The reported results do not guarantee the same performance on completely
independent real-world images.

## License

The model files are provided under the MIT License where applicable. Dataset
licenses remain subject to their original terms.
