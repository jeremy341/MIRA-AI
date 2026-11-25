/**
 * Language-neutral data for the Package page: commands, flags, file names, sizes and scores.
 * Words (descriptions, notes, labels) live in src/i18n/package/{en,de}.ts. Every entry is copied
 * from the repository root, not invented:
 *   version         PyPI (https://pypi.org/pypi/mira-ai/json): the latest published release.
 *                   src/version.py in the repository is ahead of it and unreleased.
 *   python          PyPI metadata of the latest release (requires_python)
 *   extras          pyproject.toml
 *   commands        src/cli/*.py (argparse definitions, 16 registered subcommands)
 *   models          src/assets/models/detection/*.yaml, models/detection (file sizes),
 *                   results/experiments_log.md (metrics)
 *   thresholds      src/cli/inference.py, src/config.py, src/visualize.py, mira.yaml
 */

import { PYPI_LATEST_VERSION } from "$lib/site";

/** Latest release on PyPI. It matches src/version.py in the repository. */
export const PACKAGE_VERSION = PYPI_LATEST_VERSION;
/** requires_python of the latest PyPI release. The repository declares >=3.11,<3.13. */
export const PYTHON_REQUIREMENT = ">=3.11";
export const LICENSE_NAME = "MIT";

/* ------------------------------------------------------------------ */
/* Install and quickstart                                              */
/* ------------------------------------------------------------------ */

/** Windows PowerShell block is verbatim from README.md. */
export const INSTALL_POWERSHELL = [
  "py -3 -m venv .venv",
  ".venv\\Scripts\\Activate.ps1",
  "python -m pip install --upgrade pip",
  "python -m pip install mira-ai",
].join("\n");

/** Standard venv equivalent. Not documented in the repo, so the page says it is untested. */
export const INSTALL_UNIX = [
  "python3 -m venv .venv",
  "source .venv/bin/activate",
  "python -m pip install --upgrade pip",
  "python -m pip install mira-ai",
].join("\n");

/** The four quickstart commands, in order. Words for each step are in the copy files. */
export const QUICKSTART_COMMANDS = [
  "mira --version",
  "mira download --list",
  "mira doctor",
  "mira live --model mira_exp014.pt",
] as const;

/** Example for the thresholds section: --conf is the CLI default, 0.55 is reject_threshold in mira.yaml. */
export const THRESHOLD_EXAMPLE_COMMAND = "mira live --model mira_exp019.pt --conf 0.25 --reject 0.55";
export const THRESHOLD_CONF = 0.25;
export const THRESHOLD_REJECT = 0.55;

/* ------------------------------------------------------------------ */
/* Commands                                                            */
/* ------------------------------------------------------------------ */

/** A command line option. `value` is the choice list or positional values, `def` the default. */
export type CommandOption = {
  flag: string;
  value?: string;
  def?: string;
  required?: boolean;
};

export type CommandId =
  | "live"
  | "dashboard"
  | "models"
  | "download"
  | "doctor"
  | "config"
  | "evalYolo"
  | "benchmark"
  | "experiments"
  | "datasets"
  | "merge"
  | "validate"
  | "train"
  | "export"
  | "wizard"
  | "generate";

export type CommandRow = {
  /** Key into the copy's `commands.does`. */
  id: CommandId;
  /** What the user types, e.g. "mira live". */
  name: string;
  options: readonly CommandOption[];
};

export type CommandGroupId = "run" | "develop";

export const COMMAND_GROUPS: readonly { id: CommandGroupId; rows: readonly CommandRow[] }[] = [
  {
    id: "run",
    rows: [
      {
        id: "live",
        name: "mira live",
        options: [
          { flag: "--model" },
          { flag: "--camera", def: "0" },
          { flag: "--resolution", value: "640x360 | 1280x720 | 1920x1080", def: "640x360" },
          { flag: "--conf", def: "0.25" },
          { flag: "--reject", def: "0.25" },
          { flag: "--imgsz", def: "640" },
          { flag: "--target-latency", def: "1000 ms" },
        ],
      },
      {
        id: "dashboard",
        name: "mira dashboard",
        options: [
          { flag: "--host", def: "127.0.0.1" },
          { flag: "--port", def: "8000" },
        ],
      },
      { id: "models", name: "mira models", options: [] },
      {
        id: "download",
        name: "mira download",
        options: [{ flag: "model_name" }, { flag: "--list" }, { flag: "--all" }],
      },
      { id: "doctor", name: "mira doctor", options: [] },
      { id: "config", name: "mira config", options: [{ flag: "--validate" }] },
    ],
  },
  {
    id: "develop",
    rows: [
      { id: "evalYolo", name: "mira eval-yolo", options: [{ flag: "--model" }, { flag: "--data" }] },
      {
        id: "benchmark",
        name: "mira benchmark",
        options: [
          { flag: "--models", required: true },
          { flag: "--dataset" },
          { flag: "--conf" },
          { flag: "--max-images", def: "100" },
          { flag: "--output" },
        ],
      },
      { id: "experiments", name: "mira experiments", options: [] },
      { id: "datasets", name: "mira datasets", options: [] },
      {
        id: "merge",
        name: "mira merge",
        options: [
          { flag: "--sources", required: true },
          { flag: "--output", required: true },
          { flag: "--custom" },
          { flag: "--dry-run" },
        ],
      },
      { id: "validate", name: "mira validate", options: [{ flag: "--dataset", required: true }] },
      {
        id: "train",
        name: "mira train",
        options: [
          { flag: "--config" },
          { flag: "--model" },
          { flag: "--dataset" },
          { flag: "--epochs" },
          { flag: "--batch-size" },
          { flag: "--name" },
          { flag: "--device" },
          { flag: "--task", value: "detection | classifier", def: "detection" },
          { flag: "--auto" },
          { flag: "--dry-run" },
        ],
      },
      {
        id: "export",
        name: "mira export",
        options: [
          { flag: "--model", required: true },
          { flag: "--formats", value: "tflite_int8 | tflite_fp32 | onnx", def: "tflite_int8" },
          { flag: "--dataset" },
          { flag: "--dry-run" },
        ],
      },
      { id: "wizard", name: "mira wizard", options: [{ flag: "--auto-start" }] },
      {
        id: "generate",
        name: "mira generate",
        options: [
          { flag: "kaggle | colab | docker" },
          { flag: "--config", required: true },
          { flag: "--output" },
          { flag: "--project-root" },
        ],
      },
    ],
  },
];

/* ------------------------------------------------------------------ */
/* Models                                                              */
/* ------------------------------------------------------------------ */

export type ModelNoteId = "exp014" | "exp018" | "exp019" | "exp019Int8320";

export type ModelRow = {
  file: string;
  /** Not translated: it is a file format. */
  format: string;
  /** Decimal megabytes, two digits, from the file size on disk. */
  sizeMb: number;
  /** Validation scores in percent, or null when the log does not record them for this file. */
  map50: number | null;
  map5095: number | null;
  where: "bundled" | "separate";
  note?: ModelNoteId;
};

export const MODEL_ROWS: readonly ModelRow[] = [
  {
    file: "mira_exp014.pt",
    format: "YOLO11n, PyTorch FP32",
    sizeMb: 5.46,
    map50: 60.7,
    map5095: 50.6,
    where: "bundled",
    note: "exp014",
  },
  {
    file: "mira_exp018.pt",
    format: "YOLO11n, PyTorch FP32",
    sizeMb: 5.47,
    map50: 90.6,
    map5095: 82.2,
    where: "bundled",
    note: "exp018",
  },
  {
    file: "mira_exp019.pt",
    format: "YOLO11n, PyTorch FP32",
    sizeMb: 5.47,
    map50: 90.58,
    map5095: 82.15,
    where: "bundled",
    note: "exp019",
  },
  {
    file: "mira_exp019_int8_320.tflite",
    format: "TFLite INT8, 320 px",
    sizeMb: 3.02,
    map50: 86.2,
    map5095: 75.6,
    where: "separate",
    note: "exp019Int8320",
  },
  {
    file: "mira_exp019_int8_640.tflite",
    format: "TFLite INT8, 640 px",
    sizeMb: 3.04,
    map50: null,
    map5095: null,
    where: "separate",
  },
  { file: "mira_exp019.onnx", format: "ONNX", sizeMb: 10.61, map50: null, map5095: null, where: "separate" },
  {
    file: "mira_exp018_int8.tflite",
    format: "TFLite INT8",
    sizeMb: 3.04,
    map50: null,
    map5095: null,
    where: "separate",
  },
  { file: "mira_exp018.onnx", format: "ONNX", sizeMb: 10.61, map50: null, map5095: null, where: "separate" },
];

/* ------------------------------------------------------------------ */
/* Extras                                                              */
/* ------------------------------------------------------------------ */

export type ExtraId = "train" | "analysis" | "all" | "dev";

export const EXTRAS: readonly { id: ExtraId; command: string }[] = [
  { id: "train", command: 'pip install "mira-ai[train]"' },
  { id: "analysis", command: 'pip install "mira-ai[analysis]"' },
  { id: "all", command: 'pip install "mira-ai[all]"' },
  { id: "dev", command: 'pip install "mira-ai[dev]"' },
];
