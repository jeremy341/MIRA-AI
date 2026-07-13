# MIRA — Machine Intelligence for Recycling Automation

> **Jugend forscht 2026 — Category: Technology**  
> A lightweight, edge-AI-optimized computer vision system for automated recycling sorting. MIRA progresses through two research stages: image classification (Stage A) and real-time spatial object detection (Stage B), ultimately targeting deployment on resource-constrained hardware such as the Raspberry Pi Zero 2W.

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
9. [Known Limitations](#9-known-limitations)
10. [Repository Notes](#10-repository-notes)

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
├── datasets/                 # YOLO-format detection datasets (gitignored)
│   ├── mira_v2/              # TACO + TrashNet (current best, 4,024 images)
│   ├── TACO+TrashNet+Roboflow/  # Model 1: + Roboflow Trash Detection
│   ├── TACO+TrashNet+WaRP/      # Model 2: + WaRP waste detection
│   ├── WaRP_only/                # Model 3: WaRP only
│   └── All_TACO+TrashNet+Roboflow+WaRP/  # Model 4: all combined
│
├── models/                   # All trained model exports (ready to use)
│   ├── mira_classifier_baseline.keras
│   ├── mira_classifier_transfer.keras
│   ├── mira_classifier_tuned.keras
│   ├── mira_classifier_fp32.tflite
│   ├── mira_classifier_int8.tflite      ← Best Stage A deployment model
│   ├── mira_detector_wild.pt
│   ├── mira_detector_wild_v2.pt         ← Improved wild-world detection model
│   ├── mira_detector_tabletop_int8_320.tflite  ← Best Stage B deployment model
│   ├── mira_detector_wild_v2_int8_320.tflite   ← Quantized improved wild-world model
│   └── mira_yolo_int8_320.tflite
│
├── reference/                # All training, evaluation, and quantization scripts
│   ├── build_detection_dataset.py
│   ├── classify_archive.py
│   ├── evaluate.py
│   ├── evaluate_reference.py
│   ├── prepare_super_dataset.py
│   ├── quantize.py
│   ├── quantize_yolo.py
│   ├── train_baseline.py
│   ├── train_detection.py
│   ├── train_fine_tune.py
│   └── train_transfer.py
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
│   ├── EXP-013_YOLO11n_TACO+TrashNet/
│   └── experiments_log.md    # Full quantitative metrics for all experiments
│
├── scripts/                  # Dataset merge, training, and evaluation scripts
│   ├── kaggle_train.py       # Configurable Kaggle training (change DATASET_NAME per model)
│   ├── merge_model1.py       # TACO + TrashNet + Roboflow → 6,802 images
│   ├── merge_model2.py       # TACO + TrashNet + WaRP → ~14,000 images
│   ├── merge_model3.py       # WaRP only → ~3,000 images
│   └── merge_model4.py       # All datasets → ~17,000 images
│
├── src/                      # Runtime tools for demos and development
│   ├── cli.py                # Unified MIRA command-line interface
│   ├── capture_frame.py      # Webcam data collection tool (Stage A)
│   ├── dashboard.py          # Streamlit web control center
│   ├── debug_detection.py    # Camera diagnostics for detection models
│   ├── live_detection.py     # Real-time YOLOv8 detection and tracking
│   └── visualize_dataset.py  # Dataset distribution and sample grid viewer
│
├── .gitignore
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
| `YOLO11n` (EXP-014) | **60.7%** | 2.58M | 2.9 MB | **CURRENT BEST** — YOLO11n on TACO+TrashNet+Roboflow |
| `YOLO11n` (EXP-013) | 55.1% | 2.58M | 2.9 MB | YOLO11n on TACO+TrashNet (no Roboflow) |
| `mira_detector_wild.pt` (EXP-006) | 39.4% | 3.01M | 5.94 MB | Multi-dataset fusion, proven in live demos |
| `mira_detector_tabletop_int8_320.tflite` (EXP-009) | 72.8% | 3.01M | 3.18 MB | **WEAK** — Inflated from clean backgrounds, fails on real scenes |

> **Note:** EXP-009's 72.8% mAP50 is inflated by clean white-background validation. EXP-014 (60.7% mAP50) is the most realistic for real-world deployment, with the added benefit of being the smallest (2.58M params, 2.9 MB INT8).

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
| **EXP-014** | **YOLO11n** | **TACO + TrashNet + Roboflow (6,802 img)** | **60.7%** | **Kaggle T4 (4.7 h)** |
| **EXP-015** | **YOLO11n** | **TACO + TrashNet + WaRP (~6,800 img)** | **56.0%** | **Kaggle T4 (3.7 h)** |

> **Key finding:** Roboflow (EXP-014) outperforms WaRP (EXP-015) by +4.7 pp mAP50. Roboflow helps Trash (+11.3 pp), while WaRP helps Glass (+24.8 pp) but hurts Trash (-12.6 pp) since WaRP has zero trash-class images.

### 4-Model Comparison (In Progress)

To find the optimal training data mix, we are training YOLO11n on 4 dataset combinations:

| Model | Datasets | ~Images | Script | Status |
|---|---|---|---|---|
| Model 1 | TACO + TrashNet + Roboflow Trash Detection | 6,802 | `scripts/merge_model1.py` | **Done — 60.7% mAP50** |
| Model 2 | TACO + TrashNet + WaRP | ~14,000 | `scripts/merge_model2.py` | **Done — 56.0% mAP50** |
| Model 3 | WaRP only | ~3,000 | `scripts/merge_model3.py` | Pending |
| Model 4 | All four datasets | ~17,000 | `scripts/merge_model4.py` | Pending |

All models train with YOLO11n using `scripts/kaggle_train.py` on Kaggle.

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

For training on Kaggle (free GPU), use `scripts/kaggle_train.py`:

1. Upload the dataset ZIP to Kaggle
2. Run the notebook with argparse flags:

```bash
# Default (Model 1, YOLO11n, 120 epochs)
py scripts/kaggle_train.py

# Model 2
py scripts/kaggle_train.py --dataset TACO+TrashNet+WaRP

# Model 3 (WaRP only, fewer epochs)
py scripts/kaggle_train.py --dataset WaRP_only --epochs 80 --batch-size 16

# Model 4 (all data, longer training)
py scripts/kaggle_train.py --dataset All_TACO+TrashNet+Roboflow+WaRP --epochs 200

# Different architecture
py scripts/kaggle_train.py --model yolo8n.pt --dataset TACO+TrashNet+Roboflow

# Custom learning rate
py scripts/kaggle_train.py --lr0 0.005 --epochs 150
```

| Flag | Default | Description |
|---|---|---|
| `--dataset` | `TACO+TrashNet+Roboflow` | Kaggle dataset name |
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
# Model 1: TACO + TrashNet + Roboflow (6,802 images)
py scripts/merge_model1.py
py scripts/merge_model1.py --output-dir datasets/MeinModell
py scripts/merge_model1.py --dry-run

# Model 2: TACO + TrashNet + WaRP (~14,000 images)
py scripts/merge_model2.py
py scripts/merge_model2.py --dry-run

# Model 3: WaRP only (~3,000 images)
py scripts/merge_model3.py

# Model 4: All combined (~17,000 images)
py scripts/merge_model4.py
```

| Flag | Default | Description |
|---|---|---|
| `--output-dir` | `datasets/<model_name>` | Output dataset directory |
| `--dry-run` | `false` | Preview stats without copying files |

### Verify Installation

```powershell
.\mira live      # Should open a webcam window with live detection
```

### Collecting Your Own Training Data

`capture_frame.py` is a keyboard-driven frame capture tool for building your own Stage A dataset:

```powershell
.\mira data-viz       # First check the existing class distribution
python src/capture_frame.py   # Open the capture window
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
python src/capture_frame.py --resolution 1280x720
python src/capture_frame.py --camera 1 --resolution 1920x1080
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

### Evaluation Commands

```powershell
# Evaluate a classification model
.\mira eval-class --model mira_classifier_int8.tflite --exp EXP-004_Quantized_INT8

# Evaluate a YOLO detection model
.\mira eval-yolo --model mira_detector_wild.pt
.\mira eval-yolo --model mira_detector_wild.pt --data path/to/dataset.yaml

# For TFLite models, imgsz is auto-detected from the model's input tensor shape
.\mira eval-yolo --model mira_detector_tabletop_int8_320.tflite  # automatically uses imgsz=320
.\mira eval-yolo --model mira_detector_wild_v2_int8_320.tflite   # automatically uses imgsz=320
```

### Deployment Commands

| Command | Description |
|---|---|
| `.\mira live --model mira_detector_wild_v2.pt` | **RECOMMENDED** — Best accuracy, non-quantized detection |
| `.\mira live` | Live detection with default model (`mira_detector_wild.pt`) at 640x360 |
| `.\mira live --model mira_detector_tabletop_int8_320.tflite` | Edge deployment (smaller, faster but lower accuracy) |
| `.\mira live --model mira_detector_wild.pt --resolution 1280x720` | Wild model at 720p display |
| `.\mira live --camera 1` | Use a specific camera by index |
| `.\mira dashboard` | Launch the Streamlit web control center (model switchable via sidebar) |

On startup, `.\mira live` prints all available models with the selected one marked:

```
Available models in models/:
  mira_classifier_baseline.keras
  mira_classifier_int8.tflite
  mira_detector_tabletop_int8_320.tflite
  mira_detector_wild.pt          <-- selected
  mira_detector_wild_v2.pt
  mira_detector_wild_v2_int8_320.tflite
  mira_yolo_int8_320.tflite
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

All three camera scripts (`live_detection.py`, `capture_frame.py`, `dashboard.py`) apply the following optimizations for stable, low-latency capture:

| Optimization | Setting | Effect |
|---|---|---|
| **MJPG codec** | `CAP_PROP_FOURCC = MJPG` | 3–5x faster frame decode vs. default YUY2; unlocks higher FPS at all resolutions |
| **DirectShow backend** | `cv2.CAP_DSHOW` | Windows-native driver with lower overhead than the default MSMF backend; correctly honours buffer size |
| **Buffer size 1** | `CAP_PROP_BUFFERSIZE = 1` | Prevents stale frames queuing up — always delivers the most recent frame |
| **Explicit 30 FPS** | `CAP_PROP_FPS = 30` | Some cameras silently default to 15 FPS without this |
| **Manual exposure** | `CAP_PROP_AUTO_EXPOSURE = 1` | Prevents per-frame brightness shifts that confuse the detector |
| **Autofocus off** | `CAP_PROP_AUTOFOCUS = 0` | Eliminates mid-inference blur from focus hunting |
| **Warmup frames** | 10 frames discarded on start | Lets auto-exposure settle so the first saved/detected frames aren't washed out |

`live_detection.py` additionally runs the camera capture in a **background thread** (`CameraStream` class). This decouples frame grabbing from inference: the main loop always processes the newest available frame instead of blocking on `cap.read()` while the model is busy, eliminating the lag that compounds over time in single-threaded loops.

---

## 9. Known Limitations

- **End-on metal cans** — cans facing the camera opening-first cause frequent detection drop-outs due to a lack of representative training samples for this orientation.
- **Overlapping objects** — heavily stacked or occluded items reduce bounding box accuracy, particularly for paper and trash classes.
- **Trash class** — the catch-all "trash" class is the weakest performer across all experiments (as low as 7.1% mAP50 in EXP-008, 15.6% in EXP-013) due to its inherent visual diversity and limited training data.
- **Windows-only launcher** — `mira.bat` is Windows-specific. Linux/macOS users must call `python src/cli.py <command>` directly.

---

## 10. Repository Notes

- **Training data** (`data/classes/`) and **detection datasets** (`datasets/`) are excluded from the repository. The models are fully trained and ready to use without the raw images.
- **Documentation** (`doc/`) is excluded from the public repository.
- All model exports in `models/` are committed and ready for use.
- Confusion matrices and training curves are committed under `results/`.
- Dataset merge and training scripts are in `scripts/`.

---

## License

See [`LICENSE`](LICENSE) for details.
