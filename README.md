# MIRA — Machine Intelligence for Recycling Automation

MIRA is a computer-vision research project for recycling automation. It combines YOLO object detection, dataset preparation, model evaluation, model export, webcam inference, and a development dashboard for the five configured classes: glass, metal, paper, plastic, and trash.

This project is being developed for Jugend forscht 2027, with Raspberry Pi deployment and tabletop robot integration as future goals.

> The detailed setup, CLI reference, research workflow, architecture, experiment history, and current status are documented below.

[![Jugend forscht](https://img.shields.io/badge/Jugend_forscht-2027-blue.svg)](https://www.jugend-forscht.de/)
[![Python 3.11](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/release/python-3110/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![CI](https://github.com/jeremy341/MIRA-AI/actions/workflows/ci.yml/badge.svg)](https://github.com/jeremy341/MIRA-AI/actions/workflows/ci.yml)
[![Last Commit](https://img.shields.io/github/last-commit/jeremy341/MIRA-AI)](https://github.com/jeremy341/MIRA-AI/commits/main)

A computer-vision research project for recycling detection, targeting eventual deployment on a Raspberry Pi Zero 2W and tabletop sorting robot. Detection models and historical experiments exist; Raspberry Pi benchmarking, robot integration, distillation, and end-to-end dashboard verification are pending.

> **Local demo:** `.\mira live` opens the model picker when compatible local model binaries are present.
> **Dashboard status:** an implementation exists under `src/dashboard/`, but end-to-end camera/model/browser integration has not yet been verified.

---

## Quick Start

### Installation

```bash
git clone https://github.com/jeremy341/MIRA-AI.git
cd MIRA-AI
python -m venv .venv
.venv\Scripts\Activate.ps1      # Windows PowerShell
pip install -r requirements.txt
```

> **Note:** Development dependencies (pytest, mypy, ruff) are included in `requirements.txt`. For a production-only install, install only the core packages listed at the top of the file.

> **Fresh-clone note:** datasets and trained model binaries are gitignored. Model binaries are published separately in the public [Hugging Face repository](https://huggingface.co/Jeremy341/MIRA-AI); the CLI downloads them into the local `models/detection/` directory.

### Live Detection

> **Platform note:** On Windows, use `.\mira` (PowerShell) or `launchers\mira.bat` (CMD). On Linux/macOS, use `python -m src` or `./launchers/mira.sh`.

```bash
.\mira live                                    # Interactive model picker
.\mira live --model mira_exp014.pt             # Direct launch
.\mira live --model mira_exp014.pt --conf 0.25 --reject 0.55 --resolution 1280x720
```

### Dashboard

```bash
.\mira dashboard                           # Opens at http://127.0.0.1:8000
.\mira dashboard --port 8080               # Custom port
.\mira dashboard --host 0.0.0.0            # Listen on all interfaces
```

> **Note:** The dashboard implementation is retained for development. Camera, model loading, streaming, and browser UI have not yet been verified end to end.

### Research Pipeline

```bash
.\mira datasets                            # List available dataset sources
.\mira merge --sources taco_trashnet roboflow --output datasets/mira_tnr
.\mira train --config experiments/exp014_yolo11n_multidataset.yaml
.\mira export --model models/detection/mira_exp014.pt --formats tflite_int8
.\mira benchmark --models mira_exp014.pt mira_exp014_int8.tflite
.\mira models                               # List discovered models
```

<details open>
<summary><strong>All CLI Commands</strong></summary>

| Command | Description |
|---|---|
| `.\mira live` | Interactive model picker — arrow keys to choose, Enter to confirm |
| `.\mira live --model <file>` | Bypass picker — launch directly with a specific model |
| `.\mira dashboard` | Start the unverified dashboard implementation for development |
| `.\mira train` | Train a YOLO detection model via the research pipeline |
| `.\mira train --config <file>` | Train from experiment YAML |
| `.\mira eval-yolo --model <file>` | Evaluate a YOLO detection model on test set |
| `.\mira benchmark --models <file1> <file2> ...` | Compare models by accuracy and latency |
| `.\mira export --model <file> --formats tflite_int8` | Export trained `.pt` to TFLite / ONNX |
| `.\mira merge --sources taco_trashnet roboflow --output <dir>` | Merge registered datasets into unified YOLO dataset |
| `.\mira datasets` | List registered dataset sources from `datasets/registry/*.yaml` |
| `.\mira validate` | Validate a YOLO-format dataset's annotation structure |
| `.\mira download` | Download pretrained models from Hugging Face Hub |
| `.\mira models` | List all discovered model files in `models/` |
| `.\mira experiments` | List all experiment YAML configs in `experiments/` |
| `.\mira doctor` | Run comprehensive environment and project health check |
| `.\mira diagnostics` | Check hardware capabilities (GPU, NPU, TPU) |
| `.\mira config` | Display current project configuration |
| `.\mira generate kaggle --config <file>` | Generate cloud training scripts (Kaggle, Colab, Docker) |
| `.\mira wizard` | Interactive training setup wizard |

</details>

<details>
<summary><strong>Live Command Flags</strong></summary>

| Flag | Default | Description |
|---|---|---|
| `--model` | Interactive picker | Model filename (omit for arrow-key picker) |
| `--camera` | `0` | Camera device index |
| `--resolution` | `640x360` | Capture resolution: `640x360`, `1280x720`, `1920x1080` |
| `--conf` | `0.25` | Confidence threshold |
| `--reject` | `0.25` | Reject threshold (detections below this labeled "unsicher") |
| `--target-latency` | `1000` | Target latency in ms (prevents automatic frame skipping) |

</details>

---

## Installation Troubleshooting

| Issue | Solution |
|-------|----------|
| `ai_edge_litert` import error | Windows-only: install via `pip install ai-edge-litert`. Not needed on Raspberry Pi (use `tflite-runtime`). |
| CUDA out of memory | Use `--imgsz 320` instead of 640, or close other GPU applications. |
| Camera not opening (Windows) | Ensure no other app is using the webcam. Try `--camera 1` to switch device index. |
| `No module named 'ultralytics'` | Run `pip install ultralytics>=8.3.0` |

---

## Configuration

MIRA uses `mira.yaml` as the single source of truth for project-wide settings. All scripts, CLI commands, and the pipeline read from this file.

```yaml
# mira.yaml — key settings
classes:
  names: ["glass", "metal", "paper", "plastic", "trash"]
  count: 5

training:
  default_model: yolo11n.pt
  default_epochs: 120
  default_batch_size: 32
  default_imgsz: 640

inference:
  reject_threshold: 0.55
  default_conf: 0.5
  default_iou: 0.7
```

CLI flags override `mira.yaml` defaults:
```bash
.\mira train --epochs 200 --batch-size 16    # Override training defaults
.\mira live --conf 0.25 --reject 0.60       # Override inference defaults
```

---

## Architecture

```
Webcam Input
     │
     ▼
┌─────────────────────────────────────────────────────┐
│  Stage A: Classification (single object per frame)  │
│  Input (224×224) → MobileNetV2 → Dense(128) →       │
│  Dropout(0.2) → Softmax(4 classes)                  │
│  Best: mira_classifier_int8.tflite — 87.42% | 2.61 MB │
└─────────────────────────────────────────────────────┘
     │
     ▼
┌─────────────────────────────────────────────────────┐
│  Stage B: Detection (multiple objects per frame)    │
│  Input (640×640) → YOLO11n → NMS →              │
│  Bounding Boxes + Class Labels + ByteTrack IDs      │
│  Best: mira_exp019.pt — 90.6% mAP50 | 5.47 MB     │
└─────────────────────────────────────────────────────┘
     │
     ▼
┌─────────────────────────────────────────────────────┐
│  Stage C: Robotic Sorting (planned)                 │
│  USB Serial → ESP32-S3 → 3-DOF Servo Arm →         │
│  Pick-and-place into sorted bins                    │
└─────────────────────────────────────────────────────┘
```

> **Note:** Stage A classifiers were trained on 4 classes (glass, metal, paper, plastic) without the trash class. Stage B detectors operate on all 5 classes including trash. Stage C and target-hardware deployment remain pending.

### Confidence Reject System

| Tier | Confidence Range | Visual | Behavior |
|---|---|---|---|
| **Rejected** | conf < 0.25 | Not drawn | Ignored entirely |
| **Uncertain** | 0.25 ≤ conf < reject_threshold | Yellow box, "unsicher" | Shown but not counted in inventory |
| **Confident** | conf ≥ reject_threshold | Green box, class label | Counted in inventory |

---

## Models

### Stage A — Classification

| Model | Val Accuracy | Size | Speed | Notes |
|---|---|---|---|---|
| `mira_classifier_int8.tflite` | **87.42%** | **2.61 MB** | **~97 FPS** | Compact INT8 export; target-hardware validation pending |

### Stage B — Detection

| Model | mAP50 | Size | Notes |
|---|---|---|---|
| `mira_exp019.pt` | **90.6%** | 5.47 MB | **Current recommended** — clean balanced dataset, repeatability run |
| `mira_exp019_int8_640.tflite` | 86.2% | 2.90 MiB | INT8 quantized; target-hardware validation pending |
| `mira_exp014.pt` | 60.7% | 5.21 MB | Historical FP32 result on older dataset |
| `mira_exp006.pt` | 39.4% | 5.94 MB | YOLOv8n multi-dataset, proven in demos |

> **Status:** EXP-019 PT is the current best measured detector on the clean balanced validation split. Raspberry Pi suitability still requires target-hardware evaluation.

<details>
<summary><strong>Full experiment history (EXP-001 through EXP-019)</strong></summary>

| Exp | Model | Dataset | mAP50 | Platform |
|---|---|---|---|---|
| EXP-001 | Custom CNN | 796 images | 61.00% acc | — |
| EXP-002 | MobileNetV2 (frozen) | 796 images | 84.28% acc | — |
| EXP-003 | MobileNetV2 (fine-tuned) | 796 images | 87.42% acc | — |
| EXP-004 | MobileNetV2 INT8 | 796 images | 87.42% acc | — |
| EXP-005 | YOLOv8n | Custom + TrashNet | 82.3% | Colab T4 |
| EXP-006 | YOLOv8n | Fused Wild + TrashNet | 39.4% | Colab T4 |
| EXP-008 | YOLOv8n | Pruned Tabletop | 39.6% | Colab T4 |
| EXP-009 | YOLOv8n | Pristine TrashNet | 72.8% | Kaggle T4 |
| EXP-011 | YOLOv8n | TACO only | 35.0% | Kaggle T4 |
| EXP-013 | YOLO11n | TACO + TrashNet | 55.1% | Kaggle T4 |
| **EXP-014** | **YOLO11n** | **mira_tnr (6,802 img)** | **60.7%** | **Kaggle T4** |
| EXP-015 | YOLO11n | mira_tnw | 56.0% | Kaggle T4 |
| EXP-016 | YOLO11n | mira_warp_only | 58.8% | Kaggle T4 |
| EXP-017 | YOLO11n | mira_all (9,774 img) | 59.3% | Kaggle T4 |
| **EXP-018** | **YOLO11n** | **Clean balanced dataset** | **90.6%** | **Kaggle T4** |
| **EXP-019** | **YOLO11n** | **Clean balanced (repeatability)** | **90.6%** | **Kaggle T4** |

> EXP-007 was an exploratory attempt and is excluded. Full per-class metrics, confusion matrices, and training curves: [`results/experiments_log.md`](results/experiments_log.md)

</details>

---

## Dataset

Training datasets are not included in Git. The current build uses:

| Dataset | Images | Format | License |
|---|---|---|---|
| [dmedhi garbage classification](https://huggingface.co/datasets/dmedhi/garbage-image-classification-detection) | ~800 | Classification | — |
| [TACO](https://github.com/pedropro/TACO) | 1,500 | COCO | CC-BY-4.0 |
| [TrashNet](https://github.com/garythung/trashnet) | 2,527 | Classification | MIT-0 |
| [Roboflow Trash Detection](https://universe.roboflow.com/jerry-jukbu/trash-detection-1fjjc-uqlv1/dataset/dataset) | ~3,300 | YOLO | CC BY 4.0 |

All datasets are remapped to 5 unified classes: **glass, metal, paper, plastic, trash**.

`scripts/build_balanced_dataset.py` documents the expected local directories, remapping, deterministic TACO split, balancing, and manifest generation. The canonical source list is in [`docs/DATASET_ORIGINS.md`](docs/DATASET_ORIGINS.md).

---

## Training on Kaggle

All detection models train with YOLO11n using `scripts/train_detector_kaggle.py` on Kaggle (free T4 GPU).

```bash
py scripts/train_detector_kaggle.py --dataset mira_tnr
py scripts/train_detector_kaggle.py --dataset mira_all --epochs 200
.\mira generate kaggle --config experiments/exp014_yolo11n_multidataset.yaml
```

---

## Hardware Requirements

| Use Case | Minimum | Recommended |
|---|---|---|
| Running inference | Any modern CPU | Intel i5 / Ryzen 5 or better |
| Live detection | USB webcam at 640x360 | Any webcam |
| Training Stage B (YOLO) | GPU required | Google Colab / Kaggle T4 |
| Edge deployment target | Raspberry Pi Zero 2W | Raspberry Pi 4 |

---

## Known Limitations

- **Crumpled paper** — white crumpled paper is misclassified as plastic with 80–90% confidence. The reject threshold cannot help here (too confident). Needs more training data.
- **End-on metal cans** — cans facing the camera opening-first cause detection drop-outs due to limited training samples for this orientation.
- **Overlapping objects** — heavily stacked or occluded items reduce bounding box accuracy, particularly for paper and trash.
- **Trash class** — the catch-all "trash" class is the weakest performer across all experiments (as low as 7.1% mAP50) due to its inherent visual diversity.
- **No RPi or robot integration benchmark** — target-hardware latency, memory, and end-to-end sorting remain pending.
- **Dashboard integration unverified** — components and unit tests exist, but no tracked end-to-end camera/model/browser verification artifact exists.

---

## Reproducibility

### Random Seeds

All scripts use fixed random seeds for deterministic results:
- **TensorFlow/Keras:** `seed=123`
- **NumPy / Python random:** `seed=42`

### Model Availability

Trained model binaries are local, gitignored files. Public detector artifacts are available from [Jeremy341/MIRA-AI](https://huggingface.co/Jeremy341/MIRA-AI), and `mira download` places them under `models/detection/`.

---

## Citation

```bibtex
@misc{mira2027,
  title={MIRA: Machine Intelligence for Recycling Automation},
  author={Jeremy Darko},
  year={2027},
  howpublished={Jugend forscht 2027},
  note={Gymnasium Broich, Mülheim an der Ruhr}
}
```

---

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Adding a New CLI Command

Use the plugin registry to add commands without editing existing files:

```python
# src/cli/my_module.py
from pipeline.registry import register_command

@register_command("my-command", "Description of what it does")
def cmd_my_command(args):
    print("Hello from my command!")

def setup(parser):
    parser.add_argument("--flag", help="Custom flag")
```

Then import the module in `src/cli/__init__.py` to activate it.

---

## License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.

---

## Acknowledgments

- **Supervising Teacher** — Jugend Forscht project guidance
- **Kaggle** — free T4 GPU for model training
- **Ultralytics** — YOLO framework
- **OpenCode** — development assistance and code review
- **TACO Dataset** — Trash Annotations in Context
- **Roboflow** — community waste detection dataset

---

<div align="center">

**MIRA** — Machine Intelligence for Recycling Automation

Jugend forscht 2027 · Gymnasium Broich · Mülheim an der Ruhr

</div>
