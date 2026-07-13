# MIRA — Machine Intelligence for Recycling Automation

> **Jugend forscht 2026 — Category: Technology**  

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Ultralytics](https://img.shields.io/badge/YOLO-11n-%2300bcd4)](https://github.com/ultralytics/ultralytics)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Last Commit](https://img.shields.io/github/last-commit/jeremy341/MIRA-AI)](https://github.com/jeremy341/MIRA-AI/commits/main)

A lightweight, edge-AI-optimized computer vision system for automated recycling sorting — targeting deployment on resource-constrained hardware such as the Raspberry Pi Zero 2W. MIRA progresses from image classification (Stage A) to real-time object detection (Stage B), with a 4-model comparison to find the optimal training data mix for YOLO11n.

> **Quick start:** `.\mira live` → interactive model picker → live webcam detection

---

## Table of Contents

1. [Project Overview](#1-project-overview)
2. [Architecture & Research Stages](#2-architecture--research-stages)
3. [Directory Structure](#3-directory-structure)
4. [Model Guide](#4-model-guide)
5. [Experiment Results](#5-experiment-results)
6. [Setup & Installation](#6-setup--installation)
7. [CLI Reference](#7-cli-reference)
8. [Hardware Requirements](#8-hardware-requirements)
9. [Related Benchmarks](#9-related-benchmarks)
10. [Known Limitations](#10-known-limitations)
11. [Repository Notes](#11-repository-notes)

**Additional Resources:**
- **[Quick Start Guide](CLAUDE/QUICK_START.md)** — Get running in 3 minutes
- **[Troubleshooting Guide](CLAUDE/TROUBLESHOOTING.md)** — Common issues & solutions
- **[Deployment Guide](CLAUDE/DEPLOYMENT.md)** — Edge device setup (Raspberry Pi, Jetson)
- **[Contributing Guide](CLAUDE/CONTRIBUTING.md)** — How to contribute

---

## 1. Project Overview

MIRA is a five-class recycling classifier and detector trained to identify:

| Class | Description |
|---|---|
| **Glass** | Bottles, jars, glass containers |
| **Metal** | Cans, tins, aluminium packaging |
| **Paper** | Cardboard, paper sheets, packaging |
| **Plastic** | Bottles, bags, plastic containers |
| **Trash** | Residual waste / catch-all category |

The system was built and benchmarked in two stages:

- **Stage A** — Image classification using a custom CNN, then MobileNetV2 transfer learning and fine-tuning. The final INT8-quantized model achieves **87.42% accuracy at 2.61 MB**, running at ~97 FPS on CPU.
- **Stage B** — Real-time object detection using YOLOv8-Nano and YOLO11n with bounding box tracking. The current best model (EXP-014) achieves **60.7% mAP50 at 2.9 MB** (INT8 TFLite) using YOLO11n on a fused multi-dataset. An active 4-model comparison is underway to find the optimal training data mix.

---

## 2. Architecture & Research Stages

```
Webcam Input
     │
     ▼
┌─────────────────────────────────────────────────────┐
│  Stage A: Classification (single object per frame)  │
│                                                     │
│  Input (224×224) → MobileNetV2 → Dense(128) →       │
│  Dropout(0.2) → Softmax(5 classes)                  │
│                                                     │
│  Best model: mira_classifier_int8.tflite            │
│  Accuracy: 87.42% | Size: 2.61 MB | ~97 FPS CPU     │
└─────────────────────────────────────────────────────┘
     │
     ▼
┌─────────────────────────────────────────────────────┐
│  Stage B: Detection (multiple objects per frame)    │
│                                                     │
│  Input (640×640) → YOLO11n → NMS →              │
│  Bounding Boxes + Class Labels                      │
│                                                     │
│  Best model (EXP-014): YOLO11n 60.7% mAP50         │
│  Dataset: TACO + TrashNet + Roboflow (multi-source)│
└─────────────────────────────────────────────────────┘
```

---

## 3. Directory Structure

```text
MIRA-AI/
├── data/
│   └── classes/              # Manually collected Stage A webcam images
│       ├── glass/            # ~500 glass samples
│       ├── metal/            # ~500 metal/can samples
│       ├── paper/            # ~500 paper/cardboard samples
│       ├── plastic/          # ~500 plastic samples
│       └── trash/            # ~500 residual waste samples
│
├── datasets/                 # Detection datasets (gitignored)
│   ├── mira_v2/              # TACO + TrashNet (3,924 images)
│   ├── mira_tnr/             # Model 1: TACO+TrashNet+Roboflow
│   ├── mira_tnw/             # Model 2: TACO+TrashNet+WaRP
│   ├── mira_all/             # Model 4: all four combined
│   ├── taco_raw/             # Raw TACO source (COCO annotations)
│   ├── roboflow_raw/         # Raw Roboflow Trash Detection (64-class)
│   ├── mira_warp/            # Raw WaRP source (Warp-D, 28 classes)
│   └── trashnet_labeled/     # SAM-labeled TrashNet (bbox format)
│
├── models/                   # All trained model exports (ready to use)
│   ├── classifier/            # Stage A: image classification (Keras / TFLite)
│   │   ├── mira_classifier_baseline.keras
│   │   ├── mira_classifier_transfer.keras
│   │   ├── mira_classifier_tuned.keras
│   │   ├── mira_classifier_fp32.tflite
│   │   └── mira_classifier_int8.tflite      ← Best Stage A deployment model
│   └── detection/             # Stage B: object detection (YOLO .pt / .tflite)
│       ├── mira_exp006.pt                    ← Multi-dataset detection (YOLOv8n, EXP-006)
│       ├── mira_exp006_int8.tflite           ← Quantized wild model
│       ├── mira_exp009_int8.tflite           ← Tabletop model (EXP-009, inflated mAP)
│       ├── mira_exp011.pt                    ← TACO-only detection (YOLOv8n, EXP-011)
│       ├── mira_exp011_int8.tflite           ← Quantized TACO-only model (use conf ≤0.25)
│       ├── mira_exp013.pt                    ← YOLO11n on TACO+TrashNet (EXP-013)
│       ├── mira_exp013_int8.tflite           ← Quantized EXP-013
│       ├── mira_exp014.pt                    ← **CURRENT BEST** — YOLO11n +Roboflow (EXP-014)
│       ├── mira_exp014_int8.tflite           ← Quantized EXP-014
│       ├── mira_exp015.pt                    ← YOLO11n +WaRP (EXP-015)
│       ├── mira_exp015_int8.tflite           ← Quantized EXP-015
│       └── ... (place downloaded WaRP weights here)
│
├── reference/                # All training, evaluation, and quantization scripts
│   ├── build_detector_dataset.py
│   ├── evaluate_classifier.py
│   ├── evaluate_classifier_reference.py
│   ├── live_classifier.py
│   ├── prepare_detector_super_dataset.py
│   ├── quantize_classifier.py
│   ├── quantize_detector.py
│   ├── train_classifier_baseline.py
│   ├── train_classifier_finetune.py
│   ├── train_classifier_transfer.py
│   └── train_detector.py
│
├── results/                  # Experiment outputs, confusion matrices, and logs
│   ├── EXP-001_Baseline/
│   ├── EXP-002_MobileNetV2/
│   ├── EXP-003_FineTuning/
│   ├── EXP-004_Quantized_INT8/
│   ├── EXP-005_YOLOv8/
│   ├── EXP-006_YOLOv8_Super/
│   ├── EXP-008_Tabletop_Clean/
│   ├── EXP-009_Tabletop_INT8/
│   ├── EXP-010_Quantized_Wild/
│   ├── EXP-011_Wild_Only/
│   ├── EXP-012_Quantized_Wild_v2/
│   ├── exp013_yolo11n_v2/
│   ├── exp014_yolo11n_tnr/
│   ├── exp015_yolo11n_tnw/
│   ├── exp016_yolo11n_warp/
│   └── experiments_log.md    # Full quantitative metrics for all experiments
│
├── docs/                     # Project documentation
│   └── naming_convention.md  # Dataset, experiment, and model naming rules
│
├── scripts/                  # Dataset merge, training, and evaluation scripts
│   ├── add_trashnet_to_dataset.py
│   ├── build_raw_dataset.py
│   ├── check_detector_mapping.py
│   ├── convert_taco_to_yolo.py
│   ├── label_trashnet_with_sam.py
│   ├── merge_dataset_model1.py       # TACO + TrashNet + Roboflow → 6,802 images
│   ├── merge_dataset_model2.py       # TACO + TrashNet + WaRP → ~14,000 images
│   ├── merge_dataset_model3.py       # WaRP only → ~3,000 images
│   ├── merge_dataset_model4.py       # All datasets → ~17,000 images
│   ├── train_detector_kaggle.py      # Configurable Kaggle training (change DATASET_NAME per model)
│   └── warp_utils.py
│
├── src/                      # Runtime tools for demos and development
│   ├── capture_classifier_frames.py  # Webcam data collection tool (Stage A)
│   ├── cli.py                # Unified MIRA command-line interface
│   ├── config.py             # Shared paths, constants, and utility functions
│   ├── dashboard.py          # Streamlit web control center
│   ├── debug_detector.py     # Camera diagnostics for detection models
│   ├── field_benchmark.py    # Real-world model comparison on webcam images
│   ├── live_detector.py      # Real-time YOLOv8 detection and tracking
│   ├── model_picker.py       # Interactive arrow-key model selector
│   ├── visualize.py          # Shared bounding-box drawing utilities
│   └── visualize_classifier_dataset.py  # Dataset distribution and sample grid viewer
│
├── .gitignore
├── .gitattributes
├── LICENSE
├── mira.bat                  # Windows CLI launcher
├── README.md
└── requirements.txt          # Full Python dependency list
```

---

## 4. Model Guide

### Stage A — Classification

| Model | Val Accuracy | Size | Notes |
|---|---|---|---|
| `mira_classifier_baseline.keras` | 61.00% | 45.71 MB | 3-layer custom CNN — baseline only |
| `mira_classifier_transfer.keras` | 84.28% | 9.25 MB | MobileNetV2 frozen base, fast to train |
| `mira_classifier_tuned.keras` | 87.42% | 23.48 MB | MobileNetV2 fine-tuned, best Keras accuracy |
| `mira_classifier_fp32.tflite` | 87.42% | 8.49 MB | TFLite export, no quality loss |
| `mira_classifier_int8.tflite` | **87.42%** | **2.61 MB** | **Best for deployment** — INT8, ~97 FPS CPU |

### Stage B — Detection

| Model | mAP50 | Params | Size | Notes |
|---|---|---|---|---|
| `YOLO11n` (EXP-014) | **60.7%** | 2.58M | 2.9 MB | **CURRENT BEST** — YOLO11n on mira_tnr |
| `YOLO11n` (EXP-013) | 55.1% | 2.58M | 2.9 MB | YOLO11n on TACO+TrashNet (no Roboflow) |
| `mira_exp006.pt` (EXP-006) | 39.4% | 3.01M | 5.94 MB | Multi-dataset fusion, proven in live demos |
| `mira_exp009_int8.tflite` (EXP-009) | 72.8% | 3.01M | 3.18 MB | **WEAK** — Inflated from clean backgrounds, fails on real scenes |
| `YOLO11n` (EXP-016) | 58.8% | 2.58M | 2.9 MB | WaRP only — strong glass/plastic, no trash |

> **Note:** EXP-009's 72.8% mAP50 is inflated by clean white-background validation. EXP-014 (60.7% mAP50) is the most realistic for real-world deployment, with the added benefit of being the smallest (2.58M params, 2.9 MB INT8). EXP-016 (WaRP only) shows that a WaRP-only model can reach 58.8% mAP50 but cannot detect trash at all.

---

## 5. Experiment Results

### Stage A — Classification Summary

| Experiment | Architecture | Val Accuracy | Training Time |
|---|---|---|---|
| EXP-001 | Custom CNN (3-layer) | 61.00% | ~70 s |
| EXP-002 | MobileNetV2 (frozen) | 84.28% | ~165 s |
| EXP-003 | MobileNetV2 (fine-tuned) | 87.42% | ~177 s |
| EXP-004 | MobileNetV2 INT8 TFLite | 87.42% | — (quantization) |

### Stage B — Detection Summary

| Experiment | Model | Dataset | mAP50 | Platform |
|---|---|---|---|---|
| EXP-005 | YOLOv8n | Custom + TrashNet (~3,300 img) | 82.3% | Colab T4 |
| EXP-006 | YOLOv8n | Fused Wild + TrashNet | 39.4% | Colab T4 (3.3 h) |
| EXP-008 | YOLOv8n | Pruned Tabletop (~3,000 img) | 39.6% | Colab T4 (1.7 h) |
| EXP-009 | YOLOv8n | Pristine TrashNet (~2,527 img) | **72.8%** | Kaggle T4 (0.3 h) |
| EXP-010 | YOLOv8n INT8 | Wild + TrashNet (quantized) | 35.0% | — |
| EXP-011 | YOLOv8n | TACO only (3,365 img) | 35.0% | Kaggle T4 |
| EXP-012 | YOLOv8n INT8 | TACO only (quantized) | 35.0% | — |
| EXP-013 | **YOLO11n** | **TACO + TrashNet (4,024 img)** | **55.1%** | **Kaggle T4 (2.7 h)** |
| **EXP-014** | **YOLO11n** | **mira_tnr — TACO+TrashNet+Roboflow (6,802 img)** | **60.7%** | **Kaggle T4 (4.7 h)** |
| **EXP-015** | **YOLO11n** | **mira_tnw — TACO+TrashNet+WaRP (~6,800 img)** | **56.0%** | **Kaggle T4 (3.7 h)** |
| **EXP-016** | **YOLO11n** | **mira_warp_only — WaRP (~3,000 img)** | **58.8%** | **Kaggle T4 (1.1 h)** |

> **Key finding:** Roboflow (EXP-014) outperforms WaRP (EXP-015) by +4.7 pp mAP50. Roboflow helps Trash (+11.3 pp), while WaRP helps Glass (+24.8 pp) but hurts Trash (-12.6 pp) since WaRP has zero trash-class images. EXP-016 (WaRP only) shows strong Glass (77.7%) and Plastic (73.1%) but zero Trash detection.

### 4-Model Comparison (In Progress)

To find the optimal training data mix, we are training YOLO11n on 4 dataset combinations:

| Model | Datasets | ~Images | Script | Dataset folder | Status |
|---|---|---|---|---|---|
| Model 1 | TACO + TrashNet + Roboflow | 6,802 | `scripts/merge_dataset_model1.py` | `datasets/mira_tnr/` | **Done — 60.7% mAP50** |
| Model 2 | TACO + TrashNet + WaRP | ~14,000 | `scripts/merge_dataset_model2.py` | `datasets/mira_tnw/` | **Done — 56.0% mAP50** |
| Model 3 | WaRP only | ~3,000 | `scripts/merge_dataset_model3.py` | `datasets/mira_warp_only/` | **Done — 58.8% mAP50** |
| Model 4 | All four datasets | ~17,000 | `scripts/merge_dataset_model4.py` | `datasets/mira_all/` | Planned |

All models train with YOLO11n using `scripts/train_detector_kaggle.py` on Kaggle (free T4 GPU).

Full per-class metrics, confusion matrices, and training curves are in [`results/experiments_log.md`](results/experiments_log.md).

---

## 6. Setup & Installation

### Prerequisites

- Python **3.10 or 3.11** (TensorFlow 2.x requirement)
- A webcam (for live detection and data collection)
- Windows (Linux/macOS also work via `python src/cli.py` directly)

### Fresh Clone Setup (Windows)

```powershell
git clone https://github.com/jeremy341/MIRA-AI.git
cd MIRA-AI

# Create and activate a virtual environment
python -m venv .venv
.venv\Scripts\Activate.ps1

# Install all dependencies
pip install -r requirements.txt
```

### Kaggle Training

For training on Kaggle (free GPU), use `scripts/train_detector_kaggle.py`:

1. Upload the dataset ZIP to Kaggle
2. Run the notebook with argparse flags:

```bash
# Default (Model 1, YOLO11n, 120 epochs)
py scripts/train_detector_kaggle.py

# Model 2
py scripts/train_detector_kaggle.py --dataset mira_tnw

# Model 3 (WaRP only, fewer epochs)
py scripts/train_detector_kaggle.py --dataset mira_warp_only --epochs 80 --batch-size 16

# Model 4 (all data, longer training)
py scripts/train_detector_kaggle.py --dataset mira_all --epochs 200

# Different architecture
py scripts/train_detector_kaggle.py --model yolo8n.pt --dataset mira_tnr

# Custom learning rate
py scripts/train_detector_kaggle.py --lr0 0.005 --epochs 150
```

| Flag | Default | Description |
|---|---|---|
| `--dataset` | `mira_tnr` | Kaggle dataset name |
| `--model` | `yolo11n.pt` | Base model architecture |
| `--epochs` | `120` | Training epochs |
| `--batch-size` | `32` | Batch size |
| `--img-size` | `640` | Image size |
| `--patience` | `30` | Early stopping patience |
| `--device` | `0` | GPU device ID |
| `--lr0` | `0.01` | Initial learning rate |

### Dataset Merge Scripts

Each merge script combines datasets into YOLO format with class remapping:

```bash
# Model 1: TACO + TrashNet + Roboflow (output: datasets/mira_tnr)
py scripts/merge_dataset_model1.py
py scripts/merge_dataset_model1.py --output-dir datasets/MeinModell
py scripts/merge_dataset_model1.py --dry-run

# Model 2: TACO + TrashNet + WaRP (output: datasets/mira_tnw)
py scripts/merge_dataset_model2.py
py scripts/merge_dataset_model2.py --dry-run

# Model 3: WaRP only (output: datasets/mira_warp_only)
py scripts/merge_dataset_model3.py

# Model 4: All combined (output: datasets/mira_all)
py scripts/merge_dataset_model4.py
```

| Flag | Default | Description |
|---|---|---|
| `--output-dir` | `datasets/<dataset_name>` | Output dataset directory |
| `--dry-run` | `false` | Preview stats without copying files |

### Verify Installation

```powershell
.\mira live      # Should open a webcam window with live detection
```

### Collecting Your Own Training Data

`capture_classifier_frames.py` is a keyboard-driven frame capture tool for building your own Stage A dataset:

```powershell
.\mira data-viz       # First check the existing class distribution
python src/capture_classifier_frames.py   # Open the capture window
```

Controls inside the capture window:

| Key | Saves to |
|---|---|
| `1` | `data/classes/glass/` |
| `2` | `data/classes/metal/` |
| `3` | `data/classes/paper/` |
| `4` | `data/classes/plastic/` |
| `5` | `data/classes/trash/` |
| `q` | Quit |

The camera defaults to **640x360** to match the edge AI target hardware. Each frame is saved as a timestamped `.jpg`. After collecting, retrain with `.\mira train-tune`.

To capture at a different resolution (e.g. if your webcam doesn't support 640x360 natively or you want higher quality images):

```powershell
python src/capture_classifier_frames.py --resolution 1280x720
python src/capture_classifier_frames.py --camera 1 --resolution 1920x1080
```

> **Important:** If you collect data at a higher resolution and then train on it, make sure your inference resolution (`imgsz`) matches accordingly.

---

## 7. CLI Reference

MIRA uses a unified CLI launched via `mira.bat` (Windows) or `python src/cli.py` (cross-platform).

### Data Commands

| Command | Description |
|---|---|
| `.\mira data-viz` | Visualize dataset class distribution and sample grids |

### Training Commands

| Command | Description | Experiment |
|---|---|---|
| `.\mira train-baseline` | Train the 3-layer custom CNN | EXP-001 |
| `.\mira train-transfer` | Train MobileNetV2 with frozen base | EXP-002 |
| `.\mira train-tune` | Fine-tune MobileNetV2 from layer 100 | EXP-003 |
| `.\mira train-detection` | Run YOLOv8 detection training pipeline | EXP-005+ |

### Quantization Commands

| Command | Description |
|---|---|
| `.\mira quant-class` | Post-training INT8 quantization of the Keras classifier |
| `.\mira quant-yolo` | Export YOLOv8 model to INT8 TFLite |

### Benchmark Command

| Command | Description |
|---|---|
| `.\mira field-bench` | Capture webcam images with manual labels, run all models, compare real-world precision/recall |

### Evaluation Commands

```powershell
# Evaluate a classification model
.\mira eval-class --model mira_classifier_int8.tflite --exp EXP-004_Quantized_INT8

# Evaluate a YOLO detection model
.\mira eval-yolo --model mira_exp014.pt
.\mira eval-yolo --model mira_exp014.pt --data path/to/dataset.yaml

# For TFLite models, imgsz is auto-detected from the model's input tensor shape
.\mira eval-yolo --model mira_exp009_int8.tflite  # automatically uses imgsz=320
.\mira eval-yolo --model mira_exp011_int8.tflite   # automatically uses imgsz=320
```

### Deployment Commands

| Command | Description |
|---|---|
| `.\mira live` | Interactive model picker — arrow keys to choose, Enter to confirm |
| `.\mira live --model mira_exp014.pt` | Direct launch with a specific model |
| `.\mira live --model mira_exp009_int8.tflite` | INT8 edge deployment (smaller, lower accuracy) |
| `.\mira live --model mira_exp015.pt --resolution 1280x720` | Model 2 at 720p display |
| `.\mira live --camera 1` | Use a specific camera by index |
| `.\mira dashboard` | Launch the Streamlit web control center (model switchable via sidebar) |

Running `.\mira live` without `--model` opens an interactive picker:

```text
  Available models

    mira_exp006.pt
    → mira_exp014.pt          EXP-014 (YOLO11n, +Roboflow) BEST  <--
    mira_exp014_int8.tflite   EXP-014 INT8
    mira_exp015.pt            EXP-015 (YOLO11n, +WaRP)
    [Cancel]                  Exit without selecting

  ↑↓ navigate  |  Enter: select  |  Esc: cancel
```

> **Note:** `--resolution` controls the **camera capture resolution** (what you see on screen). The model always infers at `imgsz=640` internally regardless of this setting — so accuracy is unaffected. Use `640x360` when running on edge AI hardware, or a higher resolution for a cleaner display on a desktop.

**Dashboard features** (`.\ mira dashboard` opens a browser tab at `localhost:8501`):
- Live webcam feed with bounding boxes and confidence scores
- Sidebar controls for switching between any model in `models/`, adjusting confidence threshold, NMS IoU, and inference resolution on the fly
- Toggle ByteTrack object tracking on/off
- Real-time sorted inventory bar chart — counts each unique tracked object by material class
- FPS and latency metrics updated per frame

---

## 8. Hardware Requirements

| Use Case | Minimum Hardware | Recommended |
|---|---|---|
| Running inference | Any modern CPU | Intel i5 / Ryzen 5 or better |
| Live detection (`.\mira live`) | USB webcam at 640x360 | Any webcam supporting 640x360 |
| Retraining Stage A | CPU only is fine | GPU (CUDA) for speed |
| Retraining Stage B (YOLO) | GPU required | Google Colab / Kaggle T4 |
| Edge deployment target | Raspberry Pi Zero 2W | Raspberry Pi 4 |

> **Camera note:** All runtime scripts default to **640x360** to match the edge AI target hardware and model training resolution. Use `--resolution` to override for desktop use. The model inference resolution (`imgsz=640`) is always fixed internally by YOLO regardless of capture resolution.

### Camera Performance Optimizations

All three camera scripts (`live_detector.py`, `capture_classifier_frames.py`, `dashboard.py`) apply the following optimizations for stable, low-latency capture:

| Optimization | Setting | Effect |
|---|---|---|
| **MJPG codec** | `CAP_PROP_FOURCC = MJPG` | 3–5x faster frame decode vs. default YUY2; unlocks higher FPS at all resolutions |
| **DirectShow backend** | `cv2.CAP_DSHOW` | Windows-native driver with lower overhead than the default MSMF backend; correctly honours buffer size |
| **Buffer size 1** | `CAP_PROP_BUFFERSIZE = 1` | Prevents stale frames queuing up — always delivers the most recent frame |
| **Explicit 30 FPS** | `CAP_PROP_FPS = 30` | Some cameras silently default to 15 FPS without this |
| **Manual exposure** | `CAP_PROP_AUTO_EXPOSURE = 1` | Prevents per-frame brightness shifts that confuse the detector |
| **Autofocus off** | `CAP_PROP_AUTOFOCUS = 0` | Eliminates mid-inference blur from focus hunting |
| **Warmup frames** | 10 frames discarded on start | Lets auto-exposure settle so the first saved/detected frames aren't washed out |

`live_detector.py` additionally runs the camera capture in a **background thread** (`CameraStream` class). This decouples frame grabbing from inference: the main loop always processes the newest available frame instead of blocking on `cap.read()` while the model is busy, eliminating the lag that compounds over time in single-threaded loops.

---

## 9. Related Benchmarks

MIRA's YOLO11n models target a specific niche: **5-class recycling detection on edge hardware** (Raspberry Pi Zero 2W). No single public benchmark matches this exact setup, but several related works provide context:

| Work | Model | Classes | Dataset | mAP@0.5 | Notes |
|------|-------|---------|---------|---------|-------|
| Nasien et al. (2025) | YOLO11 | 5 (glass, plastic, metal, paper, biodegradable) | 10,464 custom images | ~94% accuracy | Accuracy metric, not mAP; biodegradable ≠ trash |
| Marwah & Chowanda (2025) | YOLO11s | household waste | TACO + custom (11,876 inst.) | 72.6% | After quantization; uses TACO like MIRA |
| Messai et al. (2025) | YOLO11-x | 8 recycling classes | Industrial recycling dataset | 62.8 | YOLO11-x (56.9M params) vs MIRA's YOLO11n (2.58M) |
| Lightweight YOLO for PET/HDPE (2025) | YOLO11n | 2 (PET, HDPE) | Drinking Waste + FORTH/RECLAIM | 99.2+ (99.9) | Binary classification, not comparable |
| **MIRA EXP-014 (this repo)** | **YOLO11n** | **5 (glass, metal, paper, plastic, trash)** | **mira_tnr — TACO+TrashNet+Roboflow** | **60.7%** | **2.9 MB INT8, edge-optimized** |

**Key takeaway:** Direct comparison is difficult because every study uses different class schemas, datasets, and evaluation protocols. MIRA's *trash* class (residual waste) is particularly challenging — most recycling datasets omit it entirely, which inflates their reported metrics.

> **Kaggle AI Credits:** You can use your credits to run a standardized benchmark of MIRA's models on the [TACO dataset](http://tacodataset.org/) or [Drinking Waste Classification](https://www.kaggle.com/datasets/arkadiyhacks/drinking-waste-classification) to produce a directly comparable published result. The training script `scripts/train_detector_kaggle.py` is already configured for this — just upload the dataset and run.

---

## 10. Known Limitations

- **End-on metal cans** — cans facing the camera opening-first cause frequent detection drop-outs due to a lack of representative training samples for this orientation.
- **Overlapping objects** — heavily stacked or occluded items reduce bounding box accuracy, particularly for paper and trash classes.
- **Trash class** — the catch-all "trash" class is the weakest performer across all experiments (as low as 7.1% mAP50 in EXP-008, 15.6% in EXP-013) due to its inherent visual diversity and limited training data.
- **Windows-only launcher** — `mira.bat` is Windows-specific. Linux/macOS users must call `python src/cli.py <command>` directly.

---

## 11. Repository Notes

- **Training data** (`data/classes/`) and **detection datasets** (`datasets/`) are excluded from the repository. The models are fully trained and ready to use without the raw images.
- **Documentation** (`doc/`) is excluded from the public repository.
- All model exports in `models/` are committed and ready for use.
- Confusion matrices and training curves are committed under `results/`.
- Dataset merge and training scripts are in `scripts/`.

---

## License

See [`LICENSE`](LICENSE) for details.
