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
- **Stage B** — Real-time object detection using YOLOv8-Nano with bounding box tracking. The final deployment model achieves **72.8% mAP50 at 3.18 MB** with ~15 FPS on local CPU.

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
│  Input (640×640) → YOLOv8-Nano → NMS →              │
│  Bounding Boxes + Class Labels                      │
│                                                     │
│  Best model (accuracy): mira_detector_wild_v2.pt    │
│  Best model (edge): mira_detector_tabletop_int8_320 │
│  Trade-off: PyTorch is more accurate but needs more │
│  resources; quantized models are smaller/faster     │
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
│   └── experiments_log.md    # Full quantitative metrics for all experiments
│
├── src/                      # Runtime tools for demos and development
│   ├── cli.py                # Unified MIRA command-line interface
│   ├── capture_frame.py      # Webcam data collection tool (Stage A)
│   ├── dashboard.py          # Streamlit web control center
│   ├── debug_detection.py    # Camera diagnostics for detection models
│   ├── live_detection.py     # Real-time YOLOv8 detection and tracking
│   └── visualize_dataset.py  # Dataset distribution and sample grid viewer
│
├── yolo_data/
│   └── dataset.yaml          # YOLO class names and dataset split paths
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

| Model | mAP50 | Size | Notes |
|---|---|---|---|
| `mira_detector_wild_v2.pt` | 35.0% | 6.23 MB | **BEST** — Most robust real-world detector |
| `mira_detector_wild.pt` | 39.4% | 5.94 MB | **STRONG** — Wild-world baseline, proven in live demos |
| `mira_detector_wild_v2_int8_320.tflite` | 35.0% | 3.31 MB | Quantized wild, lower accuracy than .pt, low confidence issues |
| `mira_detector_tabletop_int8_320.tflite` | 72.8% | 3.18 MB | **WEAK** — Inflated mAP from clean backgrounds, fails on real scenes |
| `mira_yolo_int8_320.tflite` | 72.8% | 3.16 MB | **WEAK** — Legacy quantized, same problems as tabletop |

> **Note:** The `.pt` PyTorch wild models are the strongest detectors despite lower mAP50 scores. The tabletop INT8 models have high mAP50 (72.8%) because they were validated on clean white-background data — but they perform poorly in real-world scenes with complex backgrounds. The wild models were trained on diverse environments and generalize much better. For live detection, always use the `.pt` models.

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

| Experiment | Dataset | mAP50 | Platform |
|---|---|---|---|
| EXP-005 | Custom + TrashNet (~3 300 img) | 82.3% | Colab T4 |
| EXP-006 | Fused Wild + TrashNet | 39.4% | Colab T4 (3.3 h) |
| EXP-008 | Pruned Tabletop (~3 000 img) | 39.6% | Colab T4 (1.7 h) |
| EXP-009 | Pristine TrashNet (~2 527 img) | **72.8%** | Kaggle T4 (0.3 h) |

> **Key finding:** Removing noisy auto-labeled custom images (EXP-008 → EXP-009) raised mAP50 from 39.6% to **72.8%** in one-fifth of the training time — a clear demonstration of the data-centric AI approach.

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
| `.\mira data-build` | Build the pristine tabletop YOLO dataset from raw images |
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
- **Tabletop-optimized models** — the best deployment models (`EXP-009`) were trained on clean tabletop images. Performance degrades on cluttered, real-world backgrounds.
- **Trash class** — the catch-all "trash" class is the weakest performer across all experiments (as low as 63.9% mAP50) due to its inherent visual diversity.
- **Windows-only launcher** — `mira.bat` is Windows-specific. Linux/macOS users must call `python src/cli.py <command>` directly.

---

## 10. Repository Notes

- **Training data** (`data/classes/`) is excluded from the repository. The models are fully trained and ready to use without the raw images.
- **YOLO training data** (`yolo_data/images/`, `yolo_data/labels/`) is also excluded — only the dataset manifest (`yolo_data/dataset.yaml`) is tracked.
- **Documentation** (`doc/`) is excluded from the public repository.
- All model exports in `models/` are committed and ready for use.
- Confusion matrices and training curves are committed under `results/`.

---

## License

See [`LICENSE`](LICENSE) for details.
