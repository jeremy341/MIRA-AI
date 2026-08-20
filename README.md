# MIRA — Machine Intelligence for Recycling Automation

**Jugend forscht 2027**

MIRA is my project for recognizing different types of waste with a camera. The
long-term idea is to use the detections to sort objects automatically.

Project website: [mira-vision.vercel.app](https://mira-vision.vercel.app/)

## Why I chose this problem

I wanted to work on a problem that was more challenging than just training a
model on a fixed image dataset. Sorting waste combines computer vision,
uncertain predictions, real-time camera input, and eventually hardware. I also
wanted to build something that I could expand later, for example by connecting
the system to a robot or a sorting arm.

The robot is not finished yet. At the moment, my focus is the part that has to
work first: reliably recognizing the objects.

## What I tried

I did not begin with a YOLO model. I started with a custom CNN to understand
the basic classification problem. After that I tried MobileNetV2, YOLOv8n, and
finally YOLO11n for object detection.

I also tested several datasets, including dmedhi, TACO, TrashNet, and a
Roboflow waste-detection dataset. My first assumption was that adding more
data would automatically improve the model. That turned out not to be true.
Some of the larger combinations contained different image styles, labels, and
object arrangements that made the detector less consistent.

The most important result of the project so far was that a smaller, cleaner,
balanced dataset worked better than simply combining everything. After
removing unsuitable data and choosing the training examples more carefully,
the later YOLO11n experiments reached about 90.6% mAP50, compared with 60.7%
in the earlier EXP-014 run. EXP-019 repeated the result closely.

The detailed experiment history, charts, and limitations are on the
[project website](https://mira-vision.vercel.app/research.html).

## What works now

- Detection of glass, metal, paper, plastic, and trash
- Live webcam inference
- A local development dashboard
- Dataset merging and YOLO annotation validation
- Model evaluation, benchmarking, and export to formats such as TFLite

Raspberry Pi testing, a sorting mechanism, and complete robot integration are
still future work.

## Run MIRA locally

From the repository root:

```powershell
git clone https://github.com/jeremy341/MIRA-AI.git
cd MIRA-AI
py -3 -m venv .venv
.venv\Scripts\Activate.ps1
pip install -e .
```

Download a model and start live detection:

```powershell
mira download --list
mira download mira_exp019.pt
mira live --model mira_exp019.pt
```

To start the local dashboard:

```powershell
mira dashboard
```

It is available at `http://127.0.0.1:8000` by default. More setup and usage
guides are in the [website documentation](https://mira-vision.vercel.app/docs.html).

## Research commands

The main commands I use while working on the project are:

```powershell
mira datasets
mira merge --sources taco_trashnet roboflow --output datasets/mira_tnr
mira train --config experiments/exp014_yolo11n_multidataset.yaml
mira eval-yolo --model mira_exp019.pt
mira benchmark --models mira_exp019.pt mira_exp019_int8_640.tflite
```

The training datasets are not stored in Git. Their original sources and license
information are listed in [`docs/DATASET_ORIGINS.md`](docs/DATASET_ORIGINS.md).

## Project structure

- `src/` — the CLI, inference pipeline, training code, and dashboard backend
- `scripts/` — dataset preparation, evaluation, benchmarking, and training helpers
- `experiments/` — experiment configurations
- `models/` — model metadata and local model files
- `tests/` — automated tests
- `website/` — the public project website

## Honest limitations

The current system still has problems with crumpled paper, cans viewed from
the opening, and strongly overlapping objects. The reported results come from
my available validation and test data; I have not yet completed independent
Raspberry Pi benchmarks or end-to-end physical sorting tests.

## Transparency

I used AI tools for parts of coding and debugging. The problem choice, dataset
experiments, model comparisons, and decisions about what worked and failed are
part of my own project work.

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE).
