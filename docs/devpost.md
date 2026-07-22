# MIRA — Machine Intelligence for Recycling Automation

**Tagline:** An edge-AI computer vision system that sorts recycling in real-time — running on a Raspberry Pi.

## Elevator Pitch

MIRA is a lightweight, edge-optimized computer vision system for automated recycling sorting. After 17 systematic experiments comparing YOLOv8n vs YOLO11n across 4 dataset combinations (TACO, TrashNet, Roboflow, WaRP), our best model achieves **60.7% mAP50** at just **2.9 MB** (INT8 quantized) — small enough for a Raspberry Pi Zero 2W.

## Inspiration

Recycling rates are stagnating worldwide. Manual sorting is expensive, error-prone, and unsafe. Existing AI solutions require cloud GPUs — but what if the sorting could happen *at the bin*, with no internet needed? That's the question MIRA answers.

## What it does

MIRA takes a live webcam feed (or video file), runs YOLO11n inference, and draws bounding boxes with:
- **3-tier confidence coloring** — green (confident), yellow (uncertain), red (rejected)
- **ByteTrack object tracking** — persistent IDs across frames
- **Real-time inventory counting** — tracks sorted materials in a Chart.js dashboard

Two main modes:
- **Live CLI** — arrow-key model picker → instant detection stream
- **Dashboard** — FastAPI+WebSocket web UI with clean light theme, model selector, confidence sliders, and live chart

## How we built it

**Research-first approach:** 17 controlled experiments, each logged with full quantitative metrics.

| Phase | What | Result |
|---|---|---|
| Stage A | Custom CNN → MobileNetV2 transfer learning | 87.42% classification accuracy, 2.6 MB |
| Stage B | 4-model 4-dataset comparison on YOLO11n | EXP-014: 60.7% mAP50, 2.9 MB INT8 |
| Pipeline | YAML-driven research framework | Plugin CLI, dataset registry, model adapters |
| Dashboard | FastAPI + WebSocket + Chart.js | Real-time detection with interactive controls |

**Tech stack:** Python, YOLO11n (Ultralytics), TensorFlow/Keras, FastAPI, WebSocket, Chart.js, ONNX/TFLite export, psutil, OpenCV, scikit-learn.

**Experiments conducted on:** Kaggle T4 GPUs (NVIDIA Tesla T4), with local testing on Intel i7.

## Challenges we ran into

1. **The trash class is hard.** Catch-all "trash" hits as low as 7.1% mAP50 — it's visually diverse by definition.
2. **Transfer learning ≠ instant results.** YOLOv8n on pristine datasets hit 72.8% mAP50, but that was inflated by clean backgrounds. Real-world performance was ~39%.
3. **Dataset noise.** Merging 4 sources (TACO, TrashNet, Roboflow, WaRP) with different annotation styles took careful class mapping — WaRP has 28 classes, we map 5.
4. **Crumpled paper looks like plastic.** 80-90% confidence misclassification. Needs more training data.
5. **PyTorch CPU vs optional GPU.** We made torch/tensorflow fully optional imports so MIRA runs on stock Python without forcing users to install CUDA.

## Accomplishments that we're proud of

- **17 experiments, 99 passing tests, 0 lint errors.** Full diagnostic audit cleaned ~100 issues.
- **Smallest detection model: 2.9 MB INT8.** Fits on a Raspberry Pi Zero 2W with room to spare.
- **Third-party model support.** Drop any `.pt`/`.tflite`/`.pth` into `models/detection/` with a YAML descriptor — instant benchmarking.
- **CLI with 17 subcommands** — from `live` to `doctor` to `generate` (Kaggle/Colab/Docker).
- **Clean codebase.** Ruff lint clean, ruff format clean, mypy-clean in progress.

## What we learned

- Dataset quality > dataset size. Roboflow's focused 6,802 images (EXP-014) beat all 17,000 images from 4 sources combined (EXP-017: 59.3%).
- YOLO11n is dramatically better than YOLOv8n for edge deployment — same accuracy at 14% fewer parameters.
- A good CLI matters for research velocity. The plugin registry made adding new experiments trivial.
- Cross-platform is hard. Windows `mira.bat`, Linux `mira.sh`, optional CUDA, graceful fallbacks everywhere.

## What's next

- **Raspberry Pi Zero 2W benchmarks** — real-world FPS/latency on the target hardware
- **Robotic arm integration** — ESP32-S3 servo control via USB serial
- **More trash-class data** — targeted collection to fix the weakest class
- **NPU acceleration** — Coral Edge TPU / NVIDIA Jetson support

## Built With

- Python 3.11+
- Ultralytics YOLO11n / YOLOv8n
- TensorFlow 2.x / Keras
- FastAPI + WebSocket + Chart.js
- OpenCV (cv2)
- ONNX / TFLite
- psutil, scikit-learn
- Git LFS (model storage)
- Ruff (linting), pytest (testing), mypy (typing)

## Try it out

**GitHub:** https://github.com/jeremy341/MIRA-AI

```bash
git clone https://github.com/jeremy341/MIRA-AI.git
cd MIRA-AI
python -m venv .venv
# Windows: .venv\Scripts\Activate.ps1
pip install -r requirements.txt
.\mira doctor          # Health check
.\mira live            # Interactive detection
.\mira dashboard       # Web UI
```

**Models on Hugging Face:** https://huggingface.co/Jeremy341
