# MIRA — Machine Intelligence for Recycling Automation

**Jugend forscht 2027**

MIRA is my project for recognizing different types of waste with a camera. The
long-term idea is to use the detections to sort objects automatically.

- Project website: [mira-vision.vercel.app](https://mira-vision.vercel.app/)
- Python package: [mira-ai on PyPI](https://pypi.org/project/mira-ai/)

## Why I chose this problem

I wanted to work on a problem that was more challenging than training a model
on a fixed image dataset. Sorting waste combines computer vision, uncertain
predictions, real-time camera input, and eventually hardware. I also wanted to
build something that I could expand later, for example by connecting the
system to a robot or sorting arm.

The robot is not finished yet. My current focus is the part that has to work
first: reliably recognizing the objects.

## What I tried

I did not begin with YOLO. I started with a custom CNN to understand the basic
classification problem. I then tried MobileNetV2, YOLOv8n, and finally YOLO11n
for object detection.

I tested several datasets, including dmedhi, TACO, TrashNet, and Roboflow
waste-detection data. I initially assumed that adding more data would
automatically improve the model, but that was not true. Some larger dataset
combinations contained inconsistent image styles, labels, and object
arrangements.

The most important result was that a smaller, cleaner, balanced dataset worked
better than simply combining everything. The earlier EXP-014 run reached
60.7% mAP50, while the later clean-dataset YOLO11n experiments reached about
90.6% mAP50. EXP-019 repeated the result closely.

The full experiment history and charts are available on the
[project website](https://mira-vision.vercel.app/research.html).

## Current capabilities

- Detects glass, metal, paper, plastic, and trash
- Runs live webcam inference
- Includes a local development dashboard
- Provides dataset and evaluation tools
- Exports models to formats such as ONNX and TFLite

The current limitations and detailed documentation are covered on the
[website](https://mira-vision.vercel.app/).

## Install from PyPI

```powershell
py -3 -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install mira-ai
```

The PyPI package already includes the EXP-014, EXP-018, and EXP-019 detector
weights. No model download, account, or external model-hosting service is
needed after installation. EXP-014 is the default live-inference model for the
demo. Its selection is based on the current live-demo workflow, not on treating
the recorded mAP50 value as a real-time benchmark.

List the bundled models and start live detection:

```powershell
mira models
mira live --model mira_exp014.pt
```

To start the local dashboard:

```powershell
mira dashboard
```

## Development installation

For working on the source code instead of using the PyPI release:

```powershell
git clone https://github.com/jeremy341/MIRA-AI.git
cd MIRA-AI
py -3 -m venv .venv
.venv\Scripts\Activate.ps1
pip install -e .
```

## Data and limitations

The training datasets are not stored in Git. Their sources and license
information are listed in [`docs/DATASET_ORIGINS.md`](docs/DATASET_ORIGINS.md).

The models can struggle with crumpled paper, cans viewed from the opening,
overlapping objects, and unusual image conditions. The reported metrics come
from the project’s recorded evaluation setup and are not a guarantee of
real-world sorting performance.

## Transparency

I used AI tools for parts of coding and debugging. The problem choice, dataset
experiments, model comparisons, and decisions about what worked and failed are
part of my own project work.

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE).
