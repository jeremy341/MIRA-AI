/**
 * English documentation content.
 *
 * Every command, option, default and path below was checked against the repository code
 * (src/cli, src/config.py, src/dashboard/backend, src/pipeline, mira.yaml, pyproject.toml, scripts/).
 * Do not add a flag or a default here without checking it there first. The German twin is de.ts and
 * must keep the same structure. No em dashes or en dashes in any text.
 */

import { GITHUB_URL, HF_URL, PYPI_LATEST_VERSION, PYPI_URL, REPO_VERSION_UNRELEASED } from "../../lib/site";
import { code, h3, lines, list, note, output, p, table, warning } from "./helpers";
import { MIRA_YAML } from "./shared-code";
import type { DocPage } from "./types";

const quickstart: DocPage = {
  slug: "quickstart",
  title: "Quickstart",
  group: "start",
  summary: "Install mira-ai from PyPI, check the environment, and run live detection on a webcam.",
  lead: "Install the package, confirm the environment is healthy, and open a live detection window. The package ships three trained detectors.",
  sections: [
    {
      id: "install",
      title: "Install",
      blocks: [
        p(
          `MIRA needs Python 3.11 or 3.12 and, for live detection, a USB webcam. The [mira-ai package](${PYPI_URL}) installs the \`mira\` command and bundles the EXP-014, EXP-018 and EXP-019 detector weights. The newest release on PyPI is ${PYPI_LATEST_VERSION}.`,
        ),
        code(
          lines(
            "py -3 -m venv .venv",
            String.raw`.venv\Scripts\Activate.ps1`,
            "python -m pip install --upgrade pip",
            "python -m pip install mira-ai",
          ),
          "Windows PowerShell",
        ),
        code(
          lines(
            "python3 -m venv .venv",
            "source .venv/bin/activate",
            "python -m pip install --upgrade pip",
            "python -m pip install mira-ai",
          ),
          "macOS and Linux",
        ),
        p(
          "These commands come from the README and were run on Windows PowerShell. The macOS and Linux lines are standard venv commands that I have not run. Use a virtual environment: the package depends on PyTorch, OpenCV and Ultralytics, which are large and easy to conflict with other projects.",
        ),
        note(
          "Python version and release number",
          `The published package declares \`>=3.11\`. The repository declares \`>=3.11,<3.13\`, which is why this page says 3.11 or 3.12. The repository is at ${REPO_VERSION_UNRELEASED}, which is not released yet, so a source install prints ${REPO_VERSION_UNRELEASED} while the PyPI release is ${PYPI_LATEST_VERSION}.`,
        ),
      ],
    },
    {
      id: "check",
      title: "Check the environment",
      blocks: [
        code(lines("mira --version", "mira doctor", "mira models")),
        p(
          "`mira doctor` runs five checks: configuration, hardware, environment, models and datasets. It prints CUDA availability and a suggested model format for the machine. The last line is `Status: HEALTHY` unless the configuration is invalid or the environment check prints a warning, for example a missing library.",
        ),
        p(
          "On a plain PyPI install the datasets check reports that no dataset sources are available. That is expected and does not change the status. `mira models` lists the bundled weights with their type and size.",
        ),
      ],
    },
    {
      id: "live",
      title: "Start live detection",
      blocks: [
        code("mira live --model mira_exp014.pt"),
        p(
          "A window titled `MIRA Real-Time Multi-Object Detection` opens. Confident detections get a green box with the class and confidence, and a status line shows camera index, resolution, latency, FPS and frame skipping. Press `q` in the window to quit.",
        ),
        p(
          "Run `mira live` without `--model` to pick from an interactive list. EXP-014 is the default demo model because of how the live demo behaves, not because of its recorded mAP50. See [Models](/docs/models) for what each bundled model is.",
        ),
        note(
          "No camera found",
          "Try `--camera 1`. The command raises an error when camera index 0 cannot be opened, and stops after 30 consecutive failed frame reads. See [Run live inference](/docs/live-inference).",
        ),
      ],
    },
    {
      id: "source",
      title: "Install from source",
      blocks: [
        p(
          "Training, dataset merging and the experiment files live in the GitHub repository, not in the wheel. To use them, work from a clone.",
        ),
        code(
          lines(
            `git clone ${GITHUB_URL}.git`,
            "cd MIRA-AI",
            "py -3 -m venv .venv",
            String.raw`.venv\Scripts\Activate.ps1`,
            "pip install -e .",
          ),
          "Windows PowerShell",
        ),
        h3("extras", "Optional extras"),
        table(
          "Optional dependency groups declared in pyproject.toml",
          ["Extra", "Install", "Adds"],
          [
            [
              "`train`",
              '`pip install "mira-ai[train]"`',
              "TensorFlow, used by the classifier trainer and TFLite export.",
            ],
            [
              "`analysis`",
              '`pip install "mira-ai[analysis]"`',
              "matplotlib, pandas, scikit-learn and scipy for the plotting scripts.",
            ],
            ["`all`", '`pip install "mira-ai[all]"`', "Both of the above."],
          ],
        ),
      ],
    },
    {
      id: "next",
      title: "Where to go next",
      blocks: [
        list([
          "Tune thresholds and cameras in [Run live inference](/docs/live-inference).",
          "Watch detections in a browser with [Use the dashboard](/docs/dashboard).",
          "Rebuild or extend the training data in [Prepare datasets](/docs/datasets).",
          "Look up any flag in the [CLI commands](/docs/cli) reference.",
        ]),
      ],
    },
  ],
};

const configuration: DocPage = {
  slug: "configuration",
  title: "Configuration",
  group: "start",
  summary: "How MIRA finds mira.yaml, which keys the code reads, and how to validate them.",
  lead: "`mira.yaml` holds the class list, training defaults and inference defaults. Only some keys are read by the code, so this page says which ones and where.",
  sections: [
    {
      id: "location",
      title: "Where MIRA looks",
      blocks: [
        p("The project root is the first of these that applies:"),
        list(
          [
            "The folder in the `MIRA_HOME` environment variable.",
            "The nearest folder, starting at the current directory and walking up, that contains `mira.yaml`.",
            "The current directory.",
          ],
          true,
        ),
        p(
          "If the root has no `mira.yaml`, the copy packaged inside the wheel is used. Model files are read from `<root>/models/detection`. If that folder contains no `.pt`, `.pth`, `.tflite` or `.onnx` file, the bundled weights are used instead.",
        ),
        warning(
          "A models folder hides the bundled models",
          "As soon as `models/detection` holds any model file, MIRA uses only that folder. The weights shipped in the package no longer appear in `mira models` or the dashboard until you remove or empty it.",
        ),
      ],
    },
    {
      id: "file",
      title: "The file",
      blocks: [p("This is the `mira.yaml` in the repository root."), code(MIRA_YAML, "mira.yaml")],
    },
    {
      id: "keys",
      title: "What each key does",
      blocks: [
        table(
          "mira.yaml keys and the code that reads them",
          ["Key", "Value", "Used by"],
          [
            [
              "`classes.names`, `classes.count`",
              "glass, metal, paper, plastic, trash; 5",
              "Class names for drawing boxes, and the class-id range check in `mira validate`. `count` must equal the number of names.",
            ],
            ["`paths.models`", "`models/`", "Where the `detection/` model folder is looked up."],
            [
              "`paths.datasets`, `paths.results`",
              "`datasets/`, `results/`",
              "Not read. Commands use `datasets/` and `results/` directly.",
            ],
            [
              "`training.default_model`",
              "`mira_exp014.pt`",
              "Default `model` of `mira train` and the wizard. Passed to Ultralytics as written, so use a real path or `yolo11n.pt` for a fresh run.",
            ],
            [
              "`training.default_epochs`, `default_batch_size`, `default_imgsz`, `default_lr`, `early_stopping_patience`",
              "120, 32, 640, 0.01, 30",
              "Defaults of `TrainConfig`, the wizard and the generated notebooks.",
            ],
            [
              "`training.augmentation`",
              "mapping",
              "Used only by `mira generate` notebooks and Docker files, when the experiment file has no `augmentation` of its own. `mira train` reads augmentation from the experiment file.",
            ],
            ["`inference.default_conf`", "0.5", "Default of `mira benchmark --conf` and of the model adapters."],
            ["`inference.default_iou`", "0.45", "NMS IoU for `mira live` and the model adapters."],
            [
              "`inference.reject_threshold`",
              "0.55",
              "Validated by `mira config --validate`, but no command reads it. `mira live` and the dashboard take the reject threshold from `--reject` and from the model settings.",
            ],
            ["`quantization.*`", "`int8`, `fp32`; 100", "Not read. Export formats come from `mira export --formats`."],
          ],
        ),
        note(
          "Live defaults are fixed in code",
          "`mira live` uses 0.25 for both `--conf` and `--reject`, and 1000 ms for `--target-latency`. These are constants in `src/config.py`, so editing `mira.yaml` does not change them. Pass the flag instead.",
        ),
      ],
    },
    {
      id: "validate",
      title: "Inspect and validate",
      blocks: [
        code(lines("mira config", "mira config --validate")),
        p(
          "`mira config` prints the effective configuration as JSON. `mira config --validate` checks the file and prints a short summary of classes, training defaults, datasets and model counts. It exits with status 1 and lists the errors if validation fails.",
        ),
        p("Validation requires:"),
        list([
          "the `classes`, `training` and `inference` sections to exist;",
          "`classes.names` to be a non-empty list of strings, and `classes.count` (if set) to equal its length;",
          "`default_epochs`, `default_batch_size`, `default_imgsz` and `early_stopping_patience` to be integers of at least 1, and `default_lr` to be above 0;",
          "`reject_threshold`, `default_conf` and `default_iou` to be numbers strictly between 0 and 1.",
        ]),
        p("Command-line flags override these defaults for a single run."),
      ],
    },
  ],
};

const architecture: DocPage = {
  slug: "architecture",
  title: "Architecture",
  group: "start",
  summary: "How a camera frame becomes a detection, and where each part lives in the repository.",
  lead: "Camera capture, inference, display and research tooling are separate modules, so each can be tested without the others.",
  sections: [
    {
      id: "flow",
      title: "From frame to detection",
      blocks: [
        {
          type: "flow",
          label: "MIRA runtime data flow",
          steps: [
            { title: "USB camera", detail: "OpenCV capture, MJPG, selectable resolution" },
            { title: "Frame buffer", detail: "A reader thread keeps only the newest frame" },
            { title: "YOLO inference", detail: "PyTorch .pt or TFLite, ByteTrack for .pt" },
            { title: "Output", detail: "OpenCV window, or dashboard over REST and WebSocket" },
          ],
        },
        p(
          "`USBCamera` in `src/hardware.py` runs a background thread that reads the camera about every 10 ms and overwrites a single-frame buffer. Inference always takes the latest frame, so a slow model skips frames instead of falling behind. The buffer also detects a frozen camera.",
        ),
        p(
          "`mira live` runs `InferenceEngine` and draws into an OpenCV window. `mira dashboard` runs a FastAPI service whose `CameraService` does the same capture and inference, then pushes JPEG frames, detections and metrics to the browser. A camera class for RTSP streams (`IPCamera`) exists in `src/hardware.py` but is not connected to the CLI or the dashboard, so only USB cameras are supported.",
        ),
      ],
    },
    {
      id: "modules",
      title: "Key modules",
      blocks: [
        table(
          "Where things live",
          ["Path", "Role"],
          [
            [
              "`src/cli/`",
              "One module per command group. Each command registers itself with `register_command`, and `src/cli/__init__.py` builds the `mira` parser from the registry.",
            ],
            [
              "`src/config.py`",
              "Finds and validates `mira.yaml`, resolves the model folder, defines the camera and inference defaults.",
            ],
            ["`src/hardware.py`", "Camera classes and the thread-safe frame buffer."],
            [
              "`src/inference_engine.py`",
              "Model loading, tracking, latency-based frame skipping and cleanup for `mira live`.",
            ],
            ["`src/visualize.py`", "Box drawing, including the confident and uncertain styles."],
            [
              "`src/dashboard/backend/`",
              "FastAPI app (`main.py`), `camera_service.py`, `command_service.py`, `websocket_handler.py` and the pydantic models.",
            ],
            [
              "`src/dashboard/frontend/`",
              "The dashboard page, `dashboard.html`, `dashboard.css` and `dashboard.js`, served by the backend.",
            ],
            [
              "`src/pipeline/`",
              "Dataset registry and merge, validators, training strategies, export, model registry and adapters, and the benchmark.",
            ],
            [
              "`src/serialization.py`",
              "Writes configs and results with `.bak` backups, plus reproducibility metadata.",
            ],
            ["`src/notebooks/`", "Generators for Kaggle and Colab notebooks and Docker training files."],
            ["`scripts/`", "Standalone scripts for evaluation, comparison, profiling and dataset building."],
          ],
        ),
      ],
    },
    {
      id: "models",
      title: "Model discovery",
      blocks: [
        p(
          "`ModelRegistry` scans the model folder. A YAML file next to a weight file is a sidecar that supplies the display name, class names, tags and recorded metrics. For a sidecar named `mira_exp019.yaml`, it also registers `mira_exp019_int8.tflite` and `mira_exp019.onnx` when those files exist. Files without a sidecar are registered by file name.",
        ),
        p(
          "Three adapters wrap the model types: `yolo_pt`, `yolo_tflite` and `third_party`. Training strategies are registered the same way, as `detection` (Ultralytics YOLO) and `classifier` (TensorFlow MobileNetV2 or a custom CNN).",
        ),
      ],
    },
    {
      id: "reproducibility",
      title: "Reproducibility records",
      blocks: [
        p(
          "A training run writes `config.yaml`, `results.json` and `metadata.json` into its run folder. The metadata records the command, arguments, git SHA, whether the working tree had uncommitted changes, the Python version and the platform. When a file already exists it is copied to `<name>.bak` before being replaced, so a rerun does not silently destroy earlier results.",
        ),
      ],
    },
  ],
};

const liveInference: DocPage = {
  slug: "live-inference",
  title: "Run live inference",
  group: "howto",
  summary: "Open a webcam detection window and tune the camera, thresholds and frame skipping.",
  sections: [
    {
      id: "run",
      title: "Run it",
      blocks: [
        code(
          lines(
            "mira live",
            "mira live --model mira_exp014.pt",
            "mira live --model mira_exp014.pt --camera 1 --resolution 1280x720",
            "mira live --model mira_exp014.pt --conf 0.4 --reject 0.6",
          ),
        ),
        p(
          "`--model` takes a file name from the model folder, not a path. Without it, an interactive picker lists the discovered models. Names containing `classifier` are rejected because live detection needs a detector. Press `q` in the window to quit.",
        ),
        p("The window draws a status line in this format. The numbers here are examples, not measurements."),
        output("Cam: 0 | 640x360 | Latency: 12.3ms (avg: 11.8ms) | FPS: 24.5 | Skip: OFF", "Status line"),
      ],
    },
    {
      id: "options",
      title: "Options",
      blocks: [
        table(
          "mira live options",
          ["Option", "Default", "Notes"],
          [
            ["`--model`", "picker", "Model file name."],
            ["`--camera`", "`0`", "Camera device index."],
            ["`--resolution`", "`640x360`", "One of `640x360`, `1280x720`, `1920x1080`."],
            ["`--conf`", "`0.25`", "Detections below this are not drawn."],
            ["`--reject`", "`0.25`", "Detections below this are labelled uncertain."],
            [
              "`--imgsz`",
              "`640`",
              "Inference size for PyTorch models. TFLite models use their own fixed size and ignore this with a warning.",
            ],
            ["`--target-latency`", "`1000`", "Milliseconds. See frame skipping below."],
          ],
        ),
      ],
    },
    {
      id: "tiers",
      title: "Confidence tiers",
      blocks: [
        table(
          "How a detection is drawn",
          ["Confidence", "Result"],
          [
            ["Below `--conf`", "Not drawn."],
            ["At or above `--conf`, below `--reject`", "Amber box labelled `uncertain` with the confidence."],
            ["At or above `--reject`", "Green box labelled with the class and confidence."],
          ],
        ),
        p(
          "Both thresholds default to 0.25, so by default nothing is labelled uncertain. Raise `--reject` above `--conf` to use the middle tier. The dashboard behaves differently: it drops detections below the larger of the two thresholds and has no uncertain tier.",
        ),
      ],
    },
    {
      id: "tracking",
      title: "Tracking and frame skipping",
      blocks: [
        p(
          "For `.pt` models MIRA runs Ultralytics tracking with the ByteTrack settings in `bytetrack.yaml`, so objects keep an ID between frames. The live window does not draw the IDs; the dashboard sends them as `track_id`. Tracking is turned off for every TFLite model.",
        ),
        p(
          "After each frame MIRA averages the model's inference time over the last 30 frames. If the average exceeds `--target-latency`, the next camera frame is skipped. With the default of 1000 ms this almost never triggers; lower it on slow hardware. The status line shows `Skip: ON` or `Skip: OFF`.",
        ),
      ],
    },
    {
      id: "problems",
      title: "When it does not start",
      blocks: [
        list([
          "`Failed to open USB camera index N`: another program holds the camera, or the index is wrong. Try `--camera 1`.",
          "`Camera N disconnected or frozen`: 30 frame reads in a row failed. Check the cable and reconnect.",
          "`Model '...' not found`: the error lists the available names. Run `mira models`.",
          "`is a classifier model, not a detector`: choose a detection model.",
        ]),
      ],
    },
  ],
};

const dashboard: DocPage = {
  slug: "dashboard",
  title: "Use the dashboard",
  group: "howto",
  summary: "Start the local FastAPI dashboard, configure a camera and model, and read the live statistics.",
  lead: "The dashboard is a local web page served by `mira dashboard`. Camera frames and detections stay on your computer. The page itself loads Chart.js from the jsDelivr CDN and its typefaces from Google Fonts, so the browser needs internet access for the charts and fonts. Fully offline use has not been tested.",
  sections: [
    {
      id: "start",
      title: "Start it",
      blocks: [
        code(lines("mira dashboard", "mira dashboard --port 8080", "mira dashboard --host 0.0.0.0")),
        p("The defaults are `--host 127.0.0.1` and `--port 8000`, so the page is at `http://127.0.0.1:8000`."),
        warning(
          "Binding to 0.0.0.0",
          "`--host 0.0.0.0` makes the dashboard reachable from your network. It has no login, and anyone who can reach it can start your camera. Keep the default unless you need remote access on a trusted network.",
        ),
      ],
    },
    {
      id: "stream",
      title: "Start a stream",
      blocks: [
        list(
          [
            "Open **Settings**. Under Camera Settings choose the camera index, resolution (`640x360`, `640x480` or `1280x720`), FPS, autofocus and auto exposure, then press **Apply**.",
            "Under Model Settings choose a model, confidence, reject and IoU thresholds, tracking and the target latency, then press **Apply**. The model is loaded when you apply.",
            "Open **Dashboard** and press **Start Stream**.",
          ],
          true,
        ),
        p(
          "The API refuses to start a stream until a camera and a model are ready. Camera and model changes are refused while a stream runs, so press **Stop** first.",
        ),
      ],
    },
    {
      id: "pages",
      title: "What it shows",
      blocks: [
        table(
          "Dashboard pages",
          ["Page", "Contents"],
          [
            [
              "Dashboard",
              "Live camera feed with FPS, latency, object count and confidence, the class distribution, and a list of recent detections.",
            ],
            [
              "Analytics",
              "Total detections, session duration, top class and average confidence, a detection trend, a class breakdown, and performance and system charts (FPS, latency, CPU, memory).",
            ],
            ["Settings", "Camera and model forms."],
          ],
        ),
      ],
    },
    {
      id: "behaviour",
      title: "Behaviour to know",
      blocks: [
        list([
          "The model list shows only `.pt` and `.tflite` files from the model folder. INT8 TFLite files are marked as recommended for small devices.",
          "Detections below the larger of the confidence and reject thresholds are discarded before they are counted or sent to the browser.",
          "For INT8 TFLite models the confidence threshold is capped at 0.25, and tracking is off for every TFLite model.",
          "The API defaults are 0.25 confidence, 0.25 reject, 0.45 IoU, tracking on and 1000 ms target latency. The Settings form starts with 0.50, 0.55 and 0.45 for the three thresholds, so check the sliders before applying.",
          "The backend keeps the last 1000 detections and the last 100 metric samples in memory. They are lost when the server stops.",
        ]),
        p(
          "Everything the page does is available over HTTP and WebSocket. See the [Dashboard API](/docs/dashboard-api).",
        ),
      ],
    },
  ],
};

const datasets: DocPage = {
  slug: "datasets",
  title: "Prepare datasets",
  group: "howto",
  summary: "List registered dataset sources, merge them into one YOLO dataset, and validate the result.",
  lead: "Dataset files are not stored in Git, and the registry files and merge commands are in the GitHub repository rather than the PyPI package. Work from a clone.",
  sections: [
    {
      id: "registry",
      title: "Registered sources",
      blocks: [
        code("mira datasets"),
        p(
          "This reads `datasets/registry/*.yaml` and prints each source key, name, format and whether its folder exists. Each registry file records where the data lives, how its splits are laid out and, for sources with their own labels, a map to the five MIRA classes.",
        ),
        table(
          "Source keys in datasets/registry",
          ["Key", "Format", "Expected folder"],
          [
            ["`garbage_detection`", "YOLO", "`datasets/raw/garbage_detection`"],
            ["`recycle_trash`", "COCO", "`datasets/raw/recycle_trash`"],
            ["`roboflow`", "YOLO, remapped", "`datasets/roboflow_raw`"],
            ["`trashnet`", "YOLO, SAM-labelled", "`datasets/trashnet_labeled`"],
            ["`warp`", "YOLO", "`datasets/mira_warp`"],
          ],
        ),
      ],
    },
    {
      id: "merge",
      title: "Merge",
      blocks: [
        code(
          lines(
            "mira merge --sources roboflow trashnet --output datasets/mira_merged --dry-run",
            "mira merge --sources roboflow trashnet --output datasets/mira_merged",
          ),
        ),
        p(
          "`--dry-run` shows what would be merged without copying. The output folder must be inside the project directory. Sources whose labels use other class ids are remapped to the five MIRA classes, and an image is skipped when none of its labels map to one. `valid` and `test` splits are written to `val`, and a source with only a train split gets a 20% validation split carved out of it.",
        ),
        p(
          "The result is `images/train`, `images/val`, `labels/train`, `labels/val` and a `dataset.yaml`. The command prints how many images were added and skipped. Add your own YOLO-format data with `--custom PATH`.",
        ),
      ],
    },
    {
      id: "validate",
      title: "Validate",
      blocks: [
        code("mira validate --dataset datasets/mira_merged"),
        p(
          "The validator checks the `images/` and `labels/` folders for each split and reports orphaned labels and images, class ids outside the class range, coordinates outside 0 to 1 and boxes with no size. It prints the class distribution and exits with status 1 when the dataset is invalid.",
        ),
      ],
    },
    {
      id: "origins",
      title: "Where the data comes from",
      blocks: [
        p(
          "The final balanced dataset was built with `scripts/build_balanced_dataset.py` and written to `datasets/merged_mira_balanced`. It uses four sources.",
        ),
        table(
          "Final balanced dataset sources, from docs/DATASET_ORIGINS.md",
          ["Source", "Origin", "Notes"],
          [
            [
              "dmedhi",
              "[Hugging Face](https://huggingface.co/datasets/dmedhi/garbage-image-classification-detection)",
              "Object detection dataset.",
            ],
            ["TACO", "[GitHub](https://github.com/pedropro/TACO)", "Trash annotations in context."],
            [
              "Roboflow Trash Detection",
              "[Roboflow Universe](https://universe.roboflow.com/jerry-jukbu/trash-detection-1fjjc-uqlv1)",
              "Local export under CC BY 4.0, July 5, 2026.",
            ],
            ["TrashNet", "[GitHub](https://github.com/garythung/trashnet)", "Labelled locally with SAM for detection."],
          ],
        ),
        warning(
          "Check each license",
          "WaRP was used in earlier experiments and is excluded from the final dataset because it made results worse. It is also licensed for research use only. Read each source's terms before redistributing any data. The repository documents origins and does not include the datasets.",
        ),
      ],
    },
  ],
};

const trainEvaluate: DocPage = {
  slug: "train-evaluate",
  title: "Train and evaluate",
  group: "howto",
  summary: "Train a YOLO detector from an experiment file, then evaluate and benchmark it.",
  lead: 'Training needs a clone of the repository, a prepared dataset and, for a GPU run, a CUDA build of PyTorch. Install with `pip install -e ".[train]"`.',
  sections: [
    {
      id: "train",
      title: "Train",
      blocks: [
        code(
          lines(
            "mira train --config experiments/exp014_yolo11n_multidataset.yaml --dry-run",
            "mira train --config experiments/exp014_yolo11n_multidataset.yaml",
            "mira train --model yolo11n.pt --dataset datasets/mira_merged/dataset.yaml --epochs 120 --name exp_local",
          ),
        ),
        p(
          "`--dry-run` validates the configuration and prints the model, dataset, epochs, batch size and image size without training. The experiment files in `experiments/` record the model, dataset, image size, epochs, batch size, optimiser settings and augmentation.",
        ),
        table(
          "Defaults when nothing else is set",
          ["Setting", "Default"],
          [
            ["Epochs, batch size, image size", "120, 32, 640"],
            ["Device", "`0` (first GPU). Use `cpu`, or ids such as `0,1`."],
            ["Run name", "A UTC timestamp, written under `runs/`."],
            ["Dataset", "The first `datasets/*/dataset.yaml` found, when `--dataset` is omitted."],
          ],
        ),
        p(
          "A run writes `runs/<name>/weights/best.pt` and `last.pt`, plus `config.yaml`, `results.json` and `metadata.json`. In an experiment file, keys that `mira train` does not know about, such as `augmentation` and `optimizer`, are kept and passed to Ultralytics when it accepts them. An `export` block is ignored by `mira train` and used only by `mira generate`.",
        ),
        warning(
          "Set the base model yourself",
          "The default `training.default_model` is `mira_exp014.pt`, which Ultralytics will not find by name. With `--auto` and no `--model`, MIRA picks the last `.pt` file it discovers, which is one of its own trained weights. Pass `--model yolo11n.pt` to start from the pretrained base.",
        ),
        h3("wizard", "Guided setup"),
        p(
          "`mira wizard` asks for the task (detection or classifier), a dataset key, base model, epochs, batch size and export formats, shows a summary, then calls `mira train`. `--auto-start` skips the confirmation. `mira train --task classifier` trains the MobileNetV2 or custom CNN classifier on a folder per class.",
        ),
      ],
    },
    {
      id: "evaluate",
      title: "Evaluate",
      blocks: [
        code(
          lines(
            "mira eval-yolo --model mira_exp019.pt --data datasets/mira_merged/dataset.yaml",
            "mira benchmark --models mira_exp019.pt mira_exp019_int8_640.tflite --dataset datasets/mira_merged/dataset.yaml --output results/benchmark.json",
          ),
        ),
        p(
          "`mira eval-yolo` runs the Ultralytics validator on a model from the model folder, at 640 px or the fixed input size of a TFLite file. `mira benchmark` runs your own evaluation loop and prints a table of images, precision, recall, F1, mAP50 and mean latency per model, sorted by F1. `--output` also writes the full result, including per-class metrics, as JSON.",
        ),
        warning(
          "Benchmark numbers are not comparable to the headline mAP50",
          "`mira benchmark` evaluates only the first 100 images of the dataset by default (`--max-images`) and uses `--conf 0.5`. The recorded 90.58% mAP50 comes from Ultralytics validation on the 415-image split. Do not put the two side by side.",
        ),
      ],
    },
    {
      id: "scripts",
      title: "Scripts",
      blocks: [
        code(
          lines(
            "python scripts/evaluate.py --model mira_exp019.pt",
            "python scripts/compare.py --models mira_exp018.pt mira_exp019.pt --data datasets/mira_merged/dataset.yaml",
            "python scripts/profile.py --model mira_exp019.pt",
          ),
        ),
        list([
          "`evaluate.py` writes plots and metrics to `results/eval_<timestamp>/` (`--conf` defaults to 0.25).",
          "`compare.py` needs at least two models and can save a markdown report with `--output`.",
          "`profile.py` measures FPS, latency and memory over 500 iterations after 50 warmup runs; set `--iterations`, `--warmup` and `--batch-size` to change that.",
          "`evaluate.py` and `compare.py` need the `analysis` extra for matplotlib.",
        ]),
      ],
    },
    {
      id: "cloud",
      title: "Train in the cloud",
      blocks: [
        code(
          lines(
            "mira generate kaggle --config experiments/exp014_yolo11n_multidataset.yaml",
            "mira generate colab --config experiments/exp014_yolo11n_multidataset.yaml",
            "mira generate docker --config experiments/exp014_yolo11n_multidataset.yaml",
          ),
        ),
        p(
          "The Kaggle and Colab commands write `<name>_kaggle.ipynb` or `<name>_colab.ipynb` in the current folder. The Docker command writes a `docker_<name>` folder with `Dockerfile`, `docker-compose.yml`, `train.py` and `entrypoint.sh`. Use `--output` to choose another path. The Kaggle notebook looks for an attached dataset under `/kaggle/input` and expects `images/train` and `images/val` inside it. Export formats come from the experiment file's `export.formats`.",
        ),
        p(
          "`docs/EXP020_RUNBOOK.md` describes EXP-020, which keeps the EXP-019 architecture but weights Roboflow data at 70%. Run `py -3 scripts/run_exp020.py --prepare-only` to build the dataset, or `--train` to build, train and export. No result for EXP-020 is recorded yet.",
        ),
      ],
    },
  ],
};

const exportEdge: DocPage = {
  slug: "export-edge",
  title: "Export for edge devices",
  group: "howto",
  summary:
    "Convert a PyTorch model to INT8 TFLite or ONNX and check it before using it on an edge device, a small computer such as a Raspberry Pi.",
  sections: [
    {
      id: "export",
      title: "Export",
      blocks: [
        code(
          lines(
            "mira export --model models/detection/mira_exp019.pt --dry-run",
            "mira export --model models/detection/mira_exp019.pt --formats tflite_int8 onnx",
            "mira export --model models/detection/mira_exp019.pt --formats tflite_int8 --dataset datasets/mira_merged/dataset.yaml",
          ),
        ),
        table(
          "mira export --formats values",
          ["Value", "Output"],
          [
            ["`tflite_int8`", "TFLite with INT8 weights (default)."],
            ["`tflite_fp32`", "TFLite without quantisation."],
            ["`onnx`", "ONNX."],
          ],
        ),
        p(
          "`--dataset` points at a dataset YAML used to calibrate INT8 quantisation. `--dry-run` only checks that the model exists. The command prints the path of each exported file. Unknown format names are skipped with a warning.",
        ),
      ],
    },
    {
      id: "use",
      title: "Use the exported model",
      blocks: [
        p(
          "Copy the exported file into `models/detection/`. Keep `int8` in the file name: MIRA treats a `.tflite` file as INT8 when its name contains `int8`, which caps the dashboard confidence threshold at 0.25 and marks the file as recommended in the dashboard model list. TFLite models have a fixed input size, which `mira live` reads from the file, and tracking is off.",
        ),
        code("mira live --model mira_exp019_int8_640.tflite"),
        p(
          "On a Raspberry Pi, install a TFLite runtime first. `mira doctor` warns when a Pi has neither `tflite-runtime` nor TensorFlow, and prints a suggested format for the machine, for example `tflite_int8` on a Pi with a TFLite runtime or `pt` when CUDA is available.",
        ),
      ],
    },
    {
      id: "check",
      title: "Check what you exported",
      blocks: [
        p(
          "Quantisation (storing the weights with smaller numbers) costs accuracy. For EXP-019, the 640 px PyTorch model reached 0.906 mAP50 on the validation split, and the 320 px INT8 TFLite export reached 0.862. Both TFLite exports keep FP32 input and output tensors, so they are smaller files with quantised weights, not full-integer models.",
        ),
        code(
          "mira benchmark --models mira_exp019.pt mira_exp019_int8_640.tflite mira_exp019_int8_320.tflite --dataset datasets/mira_merged/dataset.yaml",
        ),
        warning(
          "Not measured on a Raspberry Pi yet",
          "The TFLite files are included, but latency and memory on Raspberry Pi hardware have not been measured. The model metadata marks deployment as pending target-hardware validation.",
        ),
      ],
    },
  ],
};

const models: DocPage = {
  slug: "models",
  title: "Models",
  group: "reference",
  summary: "The bundled detector weights, their recorded metrics, and how MIRA discovers model files.",
  lead: "All numbers are validation metrics on the TrashNet tabletop split, not real-world sorting accuracy.",
  sections: [
    {
      id: "bundled",
      title: "Bundled detectors",
      blocks: [
        p(
          `The PyPI package ships these three weights, each with a metadata sidecar. More experiment models and exports are on [Hugging Face](${HF_URL}); they are optional and nothing in MIRA depends on that site.`,
        ),
        table(
          "Weights included in the mira-ai wheel",
          ["File", "Experiment", "mAP50", "mAP50-95"],
          [
            ["`mira_exp014.pt`", "EXP-014, earlier multi-dataset run", "60.7%", "50.6%"],
            ["`mira_exp018.pt`", "EXP-018, clean balanced dataset", "90.6%", "82.2%"],
            ["`mira_exp019.pt`", "EXP-019, repeat of EXP-018", "90.58%", "82.15%"],
          ],
        ),
        p(
          "EXP-019 was trained for 120 epochs at 640 px, batch 32, AdamW with a learning rate of 0.001, on a Tesla T4 in 2.67 hours. Its precision is 87.2% and recall 84.6%. The architecture is YOLO11n with 2,583,127 parameters. The training split has 5,108 images and the validation split 415.",
        ),
      ],
    },
    {
      id: "classes",
      title: "Classes",
      blocks: [
        p("The detector predicts five classes, in this index order."),
        { type: "classes" },
        table(
          "EXP-019 per-class validation mAP50",
          ["Class", "mAP50"],
          [
            ["glass", "90.8%"],
            ["metal", "94.8%"],
            ["paper", "88.7%"],
            ["plastic", "81.1%"],
            ["trash", "97.5%"],
          ],
        ),
        p(
          "Plastic has the lowest recall of the five at 64.4%. The high trash score reflects the tabletop validation set and should not be read as a general ability to detect arbitrary trash.",
        ),
      ],
    },
    {
      id: "files",
      title: "File sizes and exports",
      blocks: [
        table(
          "EXP-019 files from the experiment log",
          ["File", "Size", "Notes"],
          [
            ["`mira_exp019.pt`", "5.47 MB", "PyTorch weights, 640 px input."],
            ["`mira_exp019_int8_640.tflite`", "3.04 MB", "INT8 weights, FP32 input and output."],
            ["`mira_exp019_int8_320.tflite`", "3.02 MB", "320 px export, 0.862 validation mAP50."],
            ["`mira_exp019.onnx`", "10.6 MB", "ONNX export."],
          ],
        ),
        p(
          "The TFLite and ONNX files are not in the wheel. Create them with [Export for edge devices](/docs/export-edge) or take them from Hugging Face.",
        ),
      ],
    },
    {
      id: "discovery",
      title: "How models are found",
      blocks: [
        p(
          "`mira models` lists everything `ModelRegistry` finds in the model folder, with label, type (`yolo_pt`, `yolo_tflite` or `yolo_onnx`) and size. `mira download` does not download anything. It lists the bundled models, or reports whether a named file is available. See [Configuration](/docs/configuration) for how the model folder is chosen.",
        ),
      ],
    },
  ],
};

const cli: DocPage = {
  slug: "cli",
  title: "CLI commands",
  group: "reference",
  summary: "Every mira subcommand with its options and defaults.",
  lead: "`mira --version` prints the installed version, and `mira` alone prints help. A command that fails exits with status 1, an interrupted one with 130.",
  sections: [
    {
      id: "live",
      title: "mira live",
      blocks: [
        p("Start real-time webcam detection. See [Run live inference](/docs/live-inference)."),
        code(
          "mira live [--model NAME] [--camera N] [--resolution WxH] [--conf X] [--reject X] [--imgsz N] [--target-latency MS]",
        ),
        table(
          "Options",
          ["Option", "Default", "Description"],
          [
            ["`--model`", "picker", "Model file name."],
            ["`--camera`", "`0`", "Camera index."],
            ["`--resolution`", "`640x360`", "`640x360`, `1280x720` or `1920x1080`."],
            ["`--conf`", "`0.25`", "Confidence threshold."],
            ["`--reject`", "`0.25`", "Detections below this are labelled uncertain."],
            ["`--imgsz`", "`640`", "Inference size for PyTorch models."],
            ["`--target-latency`", "`1000`", "Target latency in ms."],
          ],
        ),
      ],
    },
    {
      id: "dashboard",
      title: "mira dashboard",
      blocks: [
        p("Launch the dashboard server. See [Use the dashboard](/docs/dashboard)."),
        code("mira dashboard [--host ADDRESS] [--port N]"),
        table(
          "Options",
          ["Option", "Default", "Description"],
          [
            ["`--host`", "`127.0.0.1`", "Bind address."],
            ["`--port`", "`8000`", "Port."],
          ],
        ),
      ],
    },
    {
      id: "models",
      title: "mira models and mira download",
      blocks: [
        p("`mira models` lists discovered model files. It takes no options."),
        p("`mira download` lists the models bundled with the installation. It does not download anything."),
        code("mira download [NAME] [--list] [--all]"),
        table(
          "Arguments",
          ["Argument", "Description"],
          [
            ["`NAME`", "A bundled file name. Reports where it is, or fails if it is not available."],
            ["`--list`, `--all`", "List the bundled models."],
          ],
        ),
      ],
    },
    {
      id: "datasets",
      title: "mira datasets",
      blocks: [
        p("List dataset sources from `datasets/registry/*.yaml` and whether each folder exists. It takes no options."),
      ],
    },
    {
      id: "merge",
      title: "mira merge",
      blocks: [
        p("Merge registered sources into one YOLO dataset. See [Prepare datasets](/docs/datasets)."),
        code("mira merge --sources KEY [KEY ...] --output DIR [--custom PATH] [--dry-run]"),
        table(
          "Options",
          ["Option", "Default", "Description"],
          [
            ["`--sources`", "required", "One or more registry keys."],
            ["`--output`", "required", "Output folder, inside the project directory."],
            ["`--custom`", "none", "Extra YOLO-format dataset to include."],
            ["`--dry-run`", "off", "Show the plan without copying."],
          ],
        ),
      ],
    },
    {
      id: "validate",
      title: "mira validate",
      blocks: [
        p("Check a YOLO dataset folder. Exits with status 1 if it is invalid."),
        code("mira validate --dataset DIR"),
      ],
    },
    {
      id: "train",
      title: "mira train",
      blocks: [
        p("Train a detector or classifier. See [Train and evaluate](/docs/train-evaluate)."),
        code(
          "mira train [--config FILE] [--model NAME] [--dataset YAML] [--epochs N] [--batch-size N] [--name NAME] [--device D] [--auto] [--dry-run]",
        ),
        table(
          "Options",
          ["Option", "Default", "Description"],
          [
            ["`--config`", "none", "Experiment YAML. Other flags override its values."],
            ["`--model`", "`mira.yaml` default", "Base model name or path. Use `yolo11n.pt` for a fresh run."],
            ["`--dataset`", "auto", "Dataset YAML. Falls back to the first `datasets/*/dataset.yaml`."],
            ["`--epochs`", "`120`", "Training epochs."],
            ["`--batch-size`", "`32`", "Batch size."],
            ["`--name`", "timestamp", "Run name. Letters, numbers, hyphens and underscores only."],
            ["`--device`", "`0`", "`cpu`, or GPU ids such as `0` or `0,1`."],
            ["`--auto`", "off", "Detect hardware: GPU with batch 32, otherwise CPU with batch 8."],
            ["`--task`", "`detection`", "`detection` or `classifier`."],
            ["`--data-dir`", "`data/classes`", "Image folder for classifier training."],
            ["`--base-model`", "`mobilenetv2`", "`mobilenetv2` or `custom_cnn`, classifier only."],
            ["`--fine-tune`", "off", "Fine-tune the classifier."],
            ["`--dry-run`", "off", "Validate and print the settings, then stop."],
          ],
        ),
      ],
    },
    {
      id: "wizard",
      title: "mira wizard",
      blocks: [p("Interactive training setup that ends by running `mira train`."), code("mira wizard [--auto-start]")],
    },
    {
      id: "eval-yolo",
      title: "mira eval-yolo",
      blocks: [
        p("Run the Ultralytics validator on a model."),
        code("mira eval-yolo [--model NAME] [--data YAML]"),
        p("`--model` opens the picker when omitted. `--data` falls back to the first `datasets/*/dataset.yaml`."),
      ],
    },
    {
      id: "benchmark",
      title: "mira benchmark",
      blocks: [
        p("Compare models on accuracy and latency."),
        code("mira benchmark --models NAME [NAME ...] [--dataset YAML] [--conf X] [--max-images N] [--output FILE]"),
        table(
          "Options",
          ["Option", "Default", "Description"],
          [
            ["`--models`", "required", "Model file names from the model folder."],
            ["`--dataset`", "auto", "Dataset YAML."],
            ["`--conf`", "`0.5`", "Confidence threshold, from `inference.default_conf`."],
            ["`--max-images`", "`100`", "Images to evaluate. Must be at least 1."],
            ["`--output`", "none", "Write the full result as JSON."],
          ],
        ),
      ],
    },
    {
      id: "export",
      title: "mira export",
      blocks: [
        p("Export a `.pt` model. See [Export for edge devices](/docs/export-edge)."),
        code("mira export --model PATH [--formats F [F ...]] [--dataset YAML] [--dry-run]"),
        table(
          "Options",
          ["Option", "Default", "Description"],
          [
            ["`--model`", "required", "Path to the `.pt` file, relative to the project root."],
            ["`--formats`", "`tflite_int8`", "`tflite_int8`, `tflite_fp32` or `onnx`."],
            ["`--dataset`", "none", "Dataset YAML for INT8 calibration."],
            ["`--dry-run`", "off", "Check the model path only."],
          ],
        ),
      ],
    },
    {
      id: "generate",
      title: "mira generate",
      blocks: [
        p("Generate cloud training files from an experiment YAML."),
        code("mira generate {kaggle|colab|docker} --config FILE [--output PATH] [--project-root DIR]"),
        p(
          "`kaggle` and `colab` write a notebook. `docker` writes a folder of files. Without a target the command prints its help.",
        ),
      ],
    },
    {
      id: "experiments",
      title: "mira experiments",
      blocks: [p("List the YAML files in `experiments/` with their `name` or `model`. It takes no options.")],
    },
    {
      id: "doctor",
      title: "mira doctor and mira config",
      blocks: [
        p(
          "`mira doctor` checks configuration, hardware, environment, models and datasets. See [Quickstart](/docs/quickstart).",
        ),
        code("mira config [--validate]"),
        p(
          "`mira config` prints the effective configuration as JSON. `--validate` checks it and exits with status 1 on errors. See [Configuration](/docs/configuration).",
        ),
      ],
    },
  ],
};

const dashboardApi: DocPage = {
  slug: "dashboard-api",
  title: "Dashboard API",
  group: "reference",
  summary: "REST and WebSocket endpoints of the local FastAPI dashboard, with request and message shapes.",
  lead: "The dashboard is a FastAPI app titled MIRA Control Center API. FastAPI also serves its generated reference at `/docs` and the schema at `/openapi.json` on the same server. There is no authentication.",
  sections: [
    {
      id: "endpoints",
      title: "Endpoints",
      blocks: [
        {
          type: "endpoints",
          items: [
            { method: "GET", path: "/api/status", text: "Stream state and readiness." },
            { method: "GET", path: "/api/models", text: "Model files the dashboard can load." },
            { method: "POST", path: "/api/camera/initialize", text: "Open a camera with the given settings." },
            { method: "POST", path: "/api/model/load", text: "Load a model with the given thresholds." },
            { method: "POST", path: "/api/stream/start", text: "Begin capture and inference." },
            { method: "POST", path: "/api/stream/stop", text: "Stop the stream." },
            { method: "POST", path: "/api/detect/image", text: "Detect objects in an uploaded image without adding to session history." },
            { method: "GET", path: "/api/statistics", text: "Class counts and mean confidence for a recent period." },
            { method: "GET", path: "/api/metrics/history", text: "Recent FPS, latency, CPU and memory samples." },
            { method: "GET", path: "/api/detections/recent", text: "Recent detection records." },
            { method: "WS", path: "/ws/video", text: "Frames, detections, metrics and status events." },
            {
              method: "WS",
              path: "/ws/control",
              text: "The same control commands as the REST endpoints, plus status and statistics queries.",
            },
          ],
        },
        p("The server also serves the page at `/`, plus `/dashboard.css` and `/dashboard.js`."),
      ],
    },
    {
      id: "rest",
      title: "REST requests",
      blocks: [
        h3("status", "Status"),
        p(
          "`GET /api/status` returns `status` (`idle`, `initializing`, `running`, `paused` or `error`), `message`, `camera_initialized`, `model_loaded`, `streaming` and a `timestamp`.",
        ),
        h3("camera-body", "Camera body"),
        table(
          "POST /api/camera/initialize",
          ["Field", "Default", "Limits"],
          [
            ["`index`", "`0`", "0 or more."],
            ["`width`, `height`", "`640`, `360`", "1 to 8192."],
            ["`fps`", "`30`", "1 to 240."],
            ["`autofocus`", "`false`", "Boolean."],
            ["`auto_exposure`", "`true`", "Boolean."],
          ],
        ),
        h3("model-body", "Model body"),
        table(
          "POST /api/model/load",
          ["Field", "Default", "Limits"],
          [
            ["`name`", "required", "A bare file name from the model folder. Paths are rejected."],
            ["`conf_threshold`", "`0.25`", "0 to 1."],
            ["`reject_threshold`", "`0.25`", "0 to 1."],
            ["`iou_threshold`", "`0.45`", "0 to 1."],
            ["`enable_tracking`", "`true`", "Ignored for TFLite models."],
            ["`target_latency_ms`", "`1000`", "Above 0."],
          ],
        ),
        h3("errors", "Errors"),
        list([
          "`409` on camera initialize or model load while a stream is running. Stop it first.",
          "`409` on `stream/start` with `{ message, missing }` when `missing` lists `camera` or `model`.",
          "`500` when the camera or model fails to open, or the stream cannot start.",
          "`400` for `period` outside 1 to 86400, and for `limit` outside 1 to 1000.",
        ]),
        h3("queries", "Queries"),
        list([
          "`GET /api/statistics?period=60` returns `statistics` (period start and end, `total_detections`, `class_counts`, `avg_confidence`, `average_confidence`) and `period_seconds`.",
          "`GET /api/metrics/history?limit=100` returns `metrics`, `count` and `timestamp`. The server keeps at most 100 samples.",
          "`GET /api/detections/recent?limit=50` returns `detections`, `count` and `timestamp`. The server keeps at most 1000 detections.",
        ]),
      ],
    },
    {
      id: "websockets",
      title: "WebSockets",
      blocks: [
        h3("video", "/ws/video"),
        p(
          "The server sends JSON messages and ignores everything except the text `ping`, which it answers with `pong`. On connect it sends a `status` message, then the latest frame if one exists.",
        ),
        table(
          "Messages from /ws/video",
          ["type", "Fields"],
          [
            ["`status`", "`status`, `message`, `timestamp`"],
            ["`frame`", "`frame_id`, `frame` (base64 JPEG, quality 85), `detections`, `timestamp`"],
            [
              "`metrics`",
              "`fps`, `inference_latency_ms`, `avg_latency_ms`, `cpu_percent`, `memory_percent`, `temperature_celsius`, `detections_per_second`, `skip_frames`, `timestamp`",
            ],
          ],
        ),
        p(
          "Each detection is `{ class, confidence, bbox: [x1, y1, x2, y2], track_id, timestamp }`. The broadcast queue holds 32 messages; when it is full the oldest frame is dropped so the view stays current.",
        ),
        h3("control", "/ws/control"),
        p('Send `{ "command": NAME, "params": { ... } }`.'),
        table(
          "Control commands",
          ["command", "params", "Reply"],
          [
            ["`set_camera_config`", "Camera body", "`response`"],
            ["`load_model`", "Model body", "`response`"],
            ["`start_stream`, `stop_stream`", "none", "`response`"],
            ["`get_status`", "none", "`status`, with the fields of `/api/status`"],
            ["`get_statistics`", "`{ period }`, default 60", "`statistics`"],
          ],
        ),
        p(
          'A `response` has `command`, `success`, `message` and `missing`. An unknown command returns `{ type: "error", message }`.',
        ),
      ],
    },
    {
      id: "example",
      title: "Example",
      blocks: [
        p("Start the server with `mira dashboard`, then drive it from Python without extra packages."),
        code(
          lines(
            "import json",
            "import urllib.request",
            "",
            'BASE = "http://127.0.0.1:8000"',
            "",
            "def post(path, body=None):",
            "    request = urllib.request.Request(",
            "        BASE + path,",
            "        data=json.dumps(body or {}).encode(),",
            '        headers={"Content-Type": "application/json"},',
            '        method="POST",',
            "    )",
            "    with urllib.request.urlopen(request) as response:",
            "        return json.load(response)",
            "",
            'print(post("/api/camera/initialize", {"index": 0}))',
            'print(post("/api/model/load", {"name": "mira_exp014.pt", "conf_threshold": 0.4}))',
            'print(post("/api/stream/start"))',
          ),
          "Python",
        ),
      ],
    },
  ],
};

const limitations: DocPage = {
  slug: "limitations",
  title: "Limitations",
  group: "reference",
  summary: "What MIRA does not do yet, where the models fail, and how far the numbers can be trusted.",
  lead: "The results are validation metrics from a controlled setup. They are not evidence that MIRA sorts waste reliably in the real world.",
  sections: [
    {
      id: "models",
      title: "Model limits",
      blocks: [
        list([
          "The models can struggle with crumpled paper, cans seen from the opening, overlapping objects and unusual image conditions.",
          "The recorded mAP50 comes from the 415-image TrashNet tabletop validation split. EXP-019 did not evaluate its independent 1,375-image test split.",
          "Plastic recall is 64.4% for EXP-019, and trash was the weakest class in the July benchmark of earlier models (image-level, no camera).",
          "A smaller, cleaner, balanced dataset beat simply combining every source. More data is not automatically better.",
        ]),
      ],
    },
    {
      id: "system",
      title: "System limits",
      blocks: [
        list([
          "The sorting robot is not built. MIRA detects and labels objects; it does not move anything.",
          "Latency and memory on a Raspberry Pi and other small devices have not been measured.",
          "Only USB cameras are connected to the CLI and dashboard.",
          "The dashboard has unit tests but no recorded end-to-end run with a real camera and browser.",
          "The dashboard has no authentication. Keep it on `127.0.0.1` unless you trust the network.",
          "The dashboard page loads Chart.js and its fonts from the internet. Offline use has not been tested.",
          "Python 3.11 and 3.12 are the intended versions. The published package declares `>=3.11`, the repository declares `>=3.11,<3.13`.",
        ]),
      ],
    },
    {
      id: "tooling",
      title: "Tooling notes",
      blocks: [
        list([
          "`mira live` takes its confidence and reject defaults from constants in code, not from `mira.yaml`.",
          "`inference.reject_threshold`, `paths.datasets`, `paths.results` and the `quantization` block of `mira.yaml` are not read by any command.",
          "A `models/detection` folder with any model file hides the weights bundled in the package.",
          "`mira download` lists bundled models and never downloads.",
        ]),
        p(`If something here is wrong or out of date, please open an issue on [GitHub](${GITHUB_URL}/issues).`),
      ],
    },
  ],
};

export const EN_PAGES: readonly DocPage[] = [
  quickstart,
  configuration,
  architecture,
  liveInference,
  dashboard,
  datasets,
  trainEvaluate,
  exportEdge,
  models,
  cli,
  dashboardApi,
  limitations,
];
