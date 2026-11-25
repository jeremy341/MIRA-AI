/**
 * The MIRA experiment record, typed.
 *
 * Source of truth: `results/experiments_log.md`, `results/field_benchmark_results.md`,
 * `README.md` and `experiments/exp020_yolo11n_roboflow_dominant.yaml` in the
 * repository root. Nothing here is estimated: a number that the log does not
 * record is `null`, and the UI shows it as "not recorded" instead of guessing.
 *
 * Conventions
 * - Every score is a percentage on a 0 to 100 scale, stored with the same
 *   digits the log prints (log "0.9058" is stored as 90.58, "0.607 (60.7%)" as 60.7).
 * - These are validation metrics on each experiment's own recorded split. They
 *   are NOT real-world sorting accuracy, and runs that used different
 *   validation splits are not like-for-like (see the `caveat` field).
 * - Stage A is whole-image classification (one label per image, metric: validation
 *   accuracy). Stage B is object detection with bounding boxes (metric: mAP50).
 */

import type { ClassId } from "./site";

/** Stage A: image classification. Stage B: object detection. */
export type Stage = "A" | "B";

/** `training` runs produce a score. `export` runs convert an earlier model (quantization). */
export type ExperimentKind = "training" | "export";

/** The headline metric each stage reports. */
export type MetricName = "validation accuracy" | "mAP50";

export type Metric = {
  name: MetricName;
  /** Percentage, 0 to 100. */
  value: number;
};

export type Evaluation = {
  /** Plain-language description of what the score was measured on. */
  split: string;
  /** Number of images in that split, or null when the log does not record it. */
  images: number | null;
};

export type Experiment = {
  /** Log identifier, e.g. "EXP-014". Unique. */
  id: string;
  stage: Stage;
  kind: ExperimentKind;
  /** ISO date from the log. */
  date: string;
  /** Short human title. */
  title: string;
  /** Architecture as recorded. */
  model: string;
  /** Dataset used (or, for exports, the dataset of the source model). */
  dataset: string;
  /** Dataset size as printed in the log, e.g. "6,802 images". Null when not recorded. */
  datasetSize: string | null;
  /** Headline score, or null for export runs that record only size. */
  result: Metric | null;
  /** mAP50-95 in percent (Stage B only), null when not recorded. */
  map5095: number | null;
  /** Mean precision in percent, null when not recorded. */
  precision: number | null;
  /** Mean recall in percent, null when not recorded. */
  recall: number | null;
  evaluation: Evaluation;
  /** Training time in hours when the log records it, else null. */
  trainingHours: number | null;
  /** Epochs when recorded. */
  epochs: number | null;
  /** Exported file size in MB (decimal) for export runs, else null. */
  modelSizeMb: number | null;
  /** For exports: the experiment whose weights were converted. */
  derivedFrom: string | null;
  /** One line on what the run showed. */
  note: string;
  /** Anything that limits how the number should be read. Null when the log has nothing to flag. */
  caveat: string | null;
};

const NOT_RECORDED_SIZE = "Validation split, size not recorded in the log";

/**
 * Every experiment from EXP-001 to EXP-019, in log order.
 * EXP-020 is planned and lives in {@link PLANNED_EXPERIMENT}, not here.
 */
export const EXPERIMENTS: readonly Experiment[] = [
  {
    id: "EXP-001",
    stage: "A",
    kind: "training",
    date: "2026-06-26",
    title: "Baseline custom CNN",
    model: "Custom CNN, 3 conv layers",
    dataset: "Hand-collected images, 4 classes (no trash)",
    datasetSize: "126 images",
    result: { name: "validation accuracy", value: 61.0 },
    map5095: null,
    precision: null,
    recall: null,
    evaluation: { split: NOT_RECORDED_SIZE, images: null },
    trainingHours: null,
    epochs: 20,
    modelSizeMb: null,
    derivedFrom: null,
    note: "A baseline to understand the problem; paper was almost never recognized (recall 0.07).",
    caveat:
      "The log lists 126 images but the per-class support adds up to 159, so the validation size is not stated reliably.",
  },
  {
    id: "EXP-002",
    stage: "A",
    kind: "training",
    date: "2026-06-27",
    title: "MobileNetV2, frozen base",
    model: "MobileNetV2 (ImageNet, frozen) + small head",
    dataset: "Hand-collected images, 4 classes (no trash)",
    datasetSize: "796 images",
    result: { name: "validation accuracy", value: 84.28 },
    map5095: null,
    precision: null,
    recall: null,
    evaluation: { split: NOT_RECORDED_SIZE, images: null },
    trainingHours: null,
    epochs: 20,
    modelSizeMb: null,
    derivedFrom: null,
    note: "Transfer learning lifted accuracy by over 23 points on a larger hand-collected set.",
    caveat: null,
  },
  {
    id: "EXP-003",
    stage: "A",
    kind: "training",
    date: "2026-06-27",
    title: "MobileNetV2, fine-tuned",
    model: "MobileNetV2 (unfrozen from layer 100) + small head",
    dataset: "Hand-collected images, 4 classes (no trash)",
    datasetSize: "796 images",
    result: { name: "validation accuracy", value: 87.42 },
    map5095: null,
    precision: null,
    recall: null,
    evaluation: { split: NOT_RECORDED_SIZE, images: null },
    trainingHours: null,
    epochs: 15,
    modelSizeMb: null,
    derivedFrom: null,
    note: "Two-stage fine-tuning gave the best classifier. It still labels one thing per image.",
    caveat: null,
  },
  {
    id: "EXP-004",
    stage: "A",
    kind: "export",
    date: "2026-07-02",
    title: "MobileNetV2, full INT8 TFLite",
    model: "MobileNetV2, quantized to 8-bit integers",
    dataset: "Hand-collected images, 4 classes (no trash)",
    datasetSize: "796 images",
    result: { name: "validation accuracy", value: 87.42 },
    map5095: null,
    precision: null,
    recall: null,
    evaluation: { split: NOT_RECORDED_SIZE, images: null },
    trainingHours: null,
    epochs: null,
    modelSizeMb: 2.61,
    derivedFrom: "EXP-003",
    note: "Quantization shrank the model to 2.61 MB (9.0x smaller than the Keras binary) with no accuracy loss recorded.",
    caveat: "The log prints the accuracy as both 87.42% and 0.8735.",
  },
  {
    id: "EXP-005",
    stage: "B",
    kind: "training",
    date: "2026-07-03",
    title: "First detector",
    model: "YOLOv8n",
    dataset: "Hand-collected tabletop images + TrashNet",
    datasetSize: "~3,300 images",
    result: { name: "mAP50", value: 82.3 },
    map5095: 69.8,
    precision: null,
    recall: null,
    evaluation: { split: NOT_RECORDED_SIZE, images: null },
    trainingHours: null,
    epochs: null,
    modelSizeMb: null,
    derivedFrom: null,
    note: "Moving to boxes made several objects per frame possible.",
    caveat: "Bounding boxes were auto-generated with Canny edge detection, not drawn by hand.",
  },
  {
    id: "EXP-006",
    stage: "B",
    kind: "training",
    date: "2026-07-04",
    title: "TrashNet + Roboflow wild data",
    model: "YOLOv8n",
    dataset: "Hand-collected + TrashNet + Roboflow (64 classes remapped to 5)",
    datasetSize: "~3,300 images",
    result: { name: "mAP50", value: 39.4 },
    map5095: null,
    precision: null,
    recall: null,
    evaluation: { split: "Mixed, wild-heavy validation data", images: null },
    trainingHours: 3.3,
    epochs: 100,
    modelSizeMb: null,
    derivedFrom: null,
    note: "Adding outdoor wild data dropped mAP50 to 39.4%; the log records about 15.6 FPS on a local CPU.",
    caveat: "Scored on wild-heavy data, so it is not comparable with tabletop-only runs.",
  },
  {
    id: "EXP-007",
    stage: "B",
    kind: "export",
    date: "2026-07-04",
    title: "YOLOv8n INT8 LiteRT",
    model: "YOLOv8n, TFLite INT8",
    dataset: "Derived from EXP-006",
    datasetSize: null,
    result: null,
    map5095: null,
    precision: null,
    recall: null,
    evaluation: { split: "Not evaluated, size only", images: null },
    trainingHours: null,
    epochs: null,
    modelSizeMb: 3.18,
    derivedFrom: "EXP-006",
    note: "Static INT8 quantization: 11.69 MB down to 3.18 MB (3.7x smaller).",
    caveat: "The log records the file size but no accuracy for the quantized model.",
  },
  {
    id: "EXP-008",
    stage: "B",
    kind: "training",
    date: "2026-07-05",
    title: "Tabletop, purged labels",
    model: "YOLOv8n",
    dataset: "Hand-collected tabletop + human-annotated TrashNet",
    datasetSize: "~3,000 images",
    result: { name: "mAP50", value: 39.6 },
    map5095: 32.9,
    precision: null,
    recall: null,
    evaluation: { split: NOT_RECORDED_SIZE, images: null },
    trainingHours: 1.661,
    epochs: 50,
    modelSizeMb: null,
    derivedFrom: null,
    note: "Removing corrupted auto-labeled images matched the noisy 100-epoch run in half the epochs.",
    caveat: null,
  },
  {
    id: "EXP-009",
    stage: "B",
    kind: "training",
    date: "2026-07-05",
    title: "Pristine TrashNet baseline",
    model: "YOLOv8n",
    dataset: "TrashNet only, Canny-edge auto-labeled",
    datasetSize: "~2,527 images",
    result: { name: "mAP50", value: 72.8 },
    map5095: 58.3,
    precision: null,
    recall: null,
    evaluation: { split: NOT_RECORDED_SIZE, images: null },
    trainingHours: 0.309,
    epochs: 50,
    modelSizeMb: null,
    derivedFrom: null,
    note: "Dropping the noisy custom images raised mAP50 from 39.6% to 72.8%.",
    caveat:
      "Trained and validated on clean white-background TrashNet images; the log notes that this validation may overstate the score.",
  },
  {
    id: "EXP-010",
    stage: "B",
    kind: "export",
    date: "2026-07-06",
    title: "Wild-data INT8 export",
    model: "YOLOv8n, TFLite INT8",
    dataset: "Derived from EXP-006",
    datasetSize: null,
    result: null,
    map5095: null,
    precision: null,
    recall: null,
    evaluation: { split: "Not evaluated, size only", images: null },
    trainingHours: null,
    epochs: null,
    modelSizeMb: 3.16,
    derivedFrom: "EXP-006",
    note: "A second INT8 export of the EXP-006 model, calibrated on 100 wild samples: 3.16 MB.",
    caveat: "The log records the file size but no accuracy for the quantized model.",
  },
  {
    id: "EXP-011",
    stage: "B",
    kind: "training",
    date: "2026-07-06",
    title: "Wild data only",
    model: "YOLOv8n",
    dataset: "TACO outdoor litter, 60 categories remapped to 5",
    datasetSize: "3,365 images",
    result: { name: "mAP50", value: 35.0 },
    map5095: 29.0,
    precision: null,
    recall: null,
    evaluation: { split: "Diverse outdoor validation set", images: null },
    trainingHours: 0.309,
    epochs: 100,
    modelSizeMb: null,
    derivedFrom: null,
    note: "A test of out-of-distribution generalization: tabletop images excluded, trash at 7.5% mAP50.",
    caveat: null,
  },
  {
    id: "EXP-012",
    stage: "B",
    kind: "export",
    date: "2026-07-06",
    title: "Wild-only INT8 export",
    model: "YOLOv8n, TFLite INT8",
    dataset: "Derived from EXP-011",
    datasetSize: null,
    result: null,
    map5095: null,
    precision: null,
    recall: null,
    evaluation: { split: "Not evaluated, size only", images: null },
    trainingHours: null,
    epochs: null,
    modelSizeMb: 3.16,
    derivedFrom: "EXP-011",
    note: "INT8 export of EXP-011: 11.62 MB down to 3.16 MB (3.7x smaller).",
    caveat:
      "In the July benchmark (image-level, no camera) this export returned no detections at the default 0.5 confidence (INT8 shifts scores down); it works at 0.25.",
  },
  {
    id: "EXP-013",
    stage: "B",
    kind: "training",
    date: "2026-07-11",
    title: "YOLO11n on TACO + TrashNet",
    model: "YOLO11n",
    dataset: "TACO (1,497) + TrashNet (2,527), full-image boxes",
    datasetSize: "4,024 images",
    result: { name: "mAP50", value: 55.1 },
    map5095: 49.8,
    precision: 78.9,
    recall: 46.8,
    evaluation: { split: NOT_RECORDED_SIZE, images: null },
    trainingHours: 2.728,
    epochs: 120,
    modelSizeMb: null,
    derivedFrom: null,
    note: "First YOLO11n run, 20 points above wild-only EXP-011. Trash was the weakest class (15.6% mAP50).",
    caveat: "Architecture and dataset changed together, so the gain is not attributable to the model alone.",
  },
  {
    id: "EXP-014",
    stage: "B",
    kind: "training",
    date: "2026-07-12",
    title: "TACO + TrashNet + Roboflow",
    model: "YOLO11n",
    dataset: "TACO + TrashNet + Roboflow (64 classes remapped to 5)",
    datasetSize: "6,802 images",
    result: { name: "mAP50", value: 60.7 },
    map5095: 50.6,
    precision: 66.2,
    recall: 58.4,
    evaluation: { split: "Own mixed validation split", images: 1588 },
    trainingHours: 4.7,
    epochs: 120,
    modelSizeMb: null,
    derivedFrom: null,
    note: "The pooled-data baseline. Adding Roboflow lifted mAP50 by 5.6 points over EXP-013.",
    caveat:
      "Validated on its own 1,588-image mixed split, not the 415-image TrashNet split used by EXP-018 and EXP-019.",
  },
  {
    id: "EXP-015",
    stage: "B",
    kind: "training",
    date: "2026-07-13",
    title: "TACO + TrashNet + WaRP",
    model: "YOLO11n",
    dataset: "TACO + TrashNet + WaRP (28 classes remapped to 5)",
    datasetSize: "~6,800 images",
    result: { name: "mAP50", value: 56.0 },
    map5095: 45.1,
    precision: 72.3,
    recall: 47.7,
    evaluation: { split: "Own mixed validation split", images: 1816 },
    trainingHours: 3.707,
    epochs: 120,
    modelSizeMb: null,
    derivedFrom: null,
    note: "Swapping Roboflow for WaRP helped glass but cost metal, paper and trash; trash recall fell to 0.087.",
    caveat: null,
  },
  {
    id: "EXP-016",
    stage: "B",
    kind: "training",
    date: "2026-07-13",
    title: "WaRP only",
    model: "YOLO11n",
    dataset: "WaRP only (28 classes remapped to 5)",
    datasetSize: null,
    result: { name: "mAP50", value: 58.8 },
    map5095: 43.2,
    precision: 62.1,
    recall: 55.9,
    evaluation: { split: NOT_RECORDED_SIZE, images: null },
    trainingHours: 1.067,
    epochs: 120,
    modelSizeMb: null,
    derivedFrom: null,
    note: "One clean source beat the mixed EXP-015 (56.0%) despite fewer classes.",
    caveat: "WaRP has no trash class, so this model cannot detect trash at all.",
  },
  {
    id: "EXP-017",
    stage: "B",
    kind: "training",
    date: "2026-07-20",
    title: "All four sources merged",
    model: "YOLO11n",
    dataset: "TACO + TrashNet + Roboflow + WaRP",
    datasetSize: "9,774 images",
    result: { name: "mAP50", value: 59.3 },
    map5095: 46.5,
    precision: 63.9,
    recall: 54.9,
    evaluation: { split: "Own mixed validation split", images: 2599 },
    trainingHours: 6.01,
    epochs: 120,
    modelSizeMb: null,
    derivedFrom: null,
    note: "The largest dataset scored lower than EXP-014: more data was not better data.",
    caveat:
      "The log's comparison bullets quote EXP-014 trash and plastic differently from EXP-014's own table; this page uses each experiment's own table.",
  },
  {
    id: "EXP-018",
    stage: "B",
    kind: "training",
    date: "2026-07-30",
    title: "Clean, balanced dataset",
    model: "YOLO11n (yolo11n.pt)",
    dataset: "dmedhi + TACO + Roboflow + TrashNet (SAM-labeled); SortWaste and Keremberke excluded",
    datasetSize: "5,108 train, 415 val, 1,375 test",
    result: { name: "mAP50", value: 90.6 },
    map5095: 82.2,
    precision: 90.4,
    recall: 82.5,
    evaluation: { split: "TrashNet tabletop validation split", images: 415 },
    trainingHours: 2.705,
    epochs: 120,
    modelSizeMb: null,
    derivedFrom: null,
    note: "A smaller, class-balanced set (1,621 to 1,982 boxes per class) lifted mAP50 by 29.9 points.",
    caveat:
      "The 415-image split differs from EXP-014's, so this is a comparison of approaches, not like-for-like. The log's all-class precision and recall (0.904, 0.825) are identical to its glass row and may be a transcription slip. No test-split result is recorded.",
  },
  {
    id: "EXP-019",
    stage: "B",
    kind: "training",
    date: "2026-07-31",
    title: "Repeat of EXP-018",
    model: "YOLO11n (yolo11n.pt)",
    dataset: "Same clean, balanced dataset as EXP-018",
    datasetSize: "5,108 train, 415 val, 1,375 test",
    result: { name: "mAP50", value: 90.58 },
    map5095: 82.15,
    precision: 87.2,
    recall: 84.6,
    evaluation: { split: "TrashNet tabletop validation split", images: 415 },
    trainingHours: 2.672,
    epochs: 120,
    modelSizeMb: null,
    derivedFrom: null,
    note: "Reproduces EXP-018 almost exactly, so the result is repeatable rather than a lucky run.",
    caveat:
      "The 1,375-image independent test split was not evaluated. A disk-full error stopped the notebook while saving, after training, validation and exports had finished.",
  },
];

/** Look up a recorded experiment by id. Throws if the id is not in the log. */
export function getExperiment(id: string): Experiment {
  const found = EXPERIMENTS.find((e) => e.id === id);
  if (!found) throw new Error(`Unknown experiment ${id}`);
  return found;
}

/** Experiments of one stage, in log order. */
export function experimentsByStage(stage: Stage): Experiment[] {
  return EXPERIMENTS.filter((e) => e.stage === stage);
}

/** Experiments that report a headline score (excludes size-only export runs). */
export function scoredExperiments(stage: Stage): (Experiment & { result: Metric })[] {
  return EXPERIMENTS.filter((e): e is Experiment & { result: Metric } => e.stage === stage && e.result !== null);
}

/** Print a score with the digits the log uses: 61 becomes "61.0", 90.58 stays "90.58". */
export function formatScore(value: number): string {
  return Number.isInteger(value) ? value.toFixed(1) : String(value);
}

/* ------------------------------------------------------------------ */
/* Per-class results                                                   */
/* ------------------------------------------------------------------ */

export type ClassResult = {
  cls: ClassId;
  /** Percent. */
  precision: number;
  /** Percent. */
  recall: number;
  /** Percent. */
  map50: number;
  /** Percent. */
  map5095: number;
};

/**
 * EXP-014 per-class validation results (1,588 images, 3,126 instances).
 * Instance counts are the validation instances of each class.
 */
export const EXP014_CLASSES: readonly (ClassResult & { instances: number })[] = [
  { cls: "glass", precision: 58.0, recall: 52.1, map50: 50.2, map5095: 40.0, instances: 336 },
  { cls: "metal", precision: 67.0, recall: 69.9, map50: 71.3, map5095: 61.3, instances: 439 },
  { cls: "paper", precision: 82.0, recall: 77.2, map50: 82.9, map5095: 74.5, instances: 474 },
  { cls: "plastic", precision: 71.5, recall: 69.9, map50: 72.1, map5095: 60.1, instances: 1316 },
  { cls: "trash", precision: 52.3, recall: 23.0, map50: 26.9, map5095: 17.3, instances: 561 },
];

/**
 * Per-class validation results on the 415-image TrashNet tabletop split.
 * The log prints identical per-class rows for EXP-018 and EXP-019, so one table serves both.
 */
export const EXP018_019_CLASSES: readonly ClassResult[] = [
  { cls: "glass", precision: 90.4, recall: 82.5, map50: 90.8, map5095: 87.4 },
  { cls: "metal", precision: 91.4, recall: 96.0, map50: 94.8, map5095: 82.7 },
  { cls: "paper", precision: 90.9, recall: 84.0, map50: 88.7, map5095: 73.8 },
  { cls: "plastic", precision: 87.4, recall: 64.4, map50: 81.1, map5095: 71.4 },
  { cls: "trash", precision: 76.1, recall: 96.3, map50: 97.5, map5095: 95.5 },
];

/** EXP-019 all-class row (the log's "all" line for that run). */
export const EXP019_ALL: Omit<ClassResult, "cls"> = {
  precision: 87.2,
  recall: 84.6,
  map50: 90.58,
  map5095: 82.15,
};

/* ------------------------------------------------------------------ */
/* Dataset composition                                                 */
/* ------------------------------------------------------------------ */

export const DATASET_SOURCES = ["TACO", "TrashNet", "Roboflow", "WaRP", "dmedhi"] as const;
export type DatasetSource = (typeof DATASET_SOURCES)[number];

export type DatasetRun = {
  /** Experiment id or ids, e.g. "EXP-013" or "EXP-018 and EXP-019". */
  label: string;
  /** Sources that contributed images. */
  sources: readonly DatasetSource[];
  /** Image count as printed in the log. */
  images: string;
  /** mAP50 in percent on that run's own validation split. */
  map50: number;
  /** Short note on what changed. */
  note: string;
};

/** How the training data was assembled in each YOLO11n run, with the score it produced. */
export const DATASET_RUNS: readonly DatasetRun[] = [
  {
    label: "EXP-013",
    sources: ["TACO", "TrashNet"],
    images: "4,024",
    map50: 55.1,
    note: "Wild plus tabletop.",
  },
  {
    label: "EXP-014",
    sources: ["TACO", "TrashNet", "Roboflow"],
    images: "6,802",
    map50: 60.7,
    note: "Added Roboflow.",
  },
  {
    label: "EXP-015",
    sources: ["TACO", "TrashNet", "WaRP"],
    images: "~6,800",
    map50: 56.0,
    note: "Swapped Roboflow for WaRP.",
  },
  {
    label: "EXP-016",
    sources: ["WaRP"],
    images: "not recorded",
    map50: 58.8,
    note: "WaRP alone, no trash class.",
  },
  {
    label: "EXP-017",
    sources: ["TACO", "TrashNet", "Roboflow", "WaRP"],
    images: "9,774",
    map50: 59.3,
    note: "Everything merged.",
  },
  {
    label: "EXP-018 and EXP-019",
    sources: ["TACO", "TrashNet", "Roboflow", "dmedhi"],
    images: "5,108 train",
    map50: 90.6,
    note: "Cleaned and balanced; SortWaste and Keremberke excluded. EXP-019 scored 90.58.",
  },
];

/** Splits of the clean, balanced dataset used by EXP-018 and EXP-019 (6,898 images in total). */
export const DATASET_SPLIT = {
  train: 5108,
  val: 415,
  test: 1375,
  /** Bounding boxes across the dataset. */
  boxes: 12832,
  /** Boxes per class were balanced within this range. */
  boxesPerClassMin: 1621,
  boxesPerClassMax: 1982,
} as const;

/* ------------------------------------------------------------------ */
/* Edge exports                                                        */
/* ------------------------------------------------------------------ */

export type ExportFile = {
  format: string;
  file: string;
  /** Exact size in bytes as printed in the log. */
  bytes: number;
};

/** Files exported from EXP-019. */
export const EXP019_EXPORTS: readonly ExportFile[] = [
  { format: "PyTorch FP32", file: "mira_exp019.pt", bytes: 5_469_402 },
  { format: "TFLite 320, quantized weights", file: "mira_exp019_int8_320.tflite", bytes: 3_022_810 },
  { format: "TFLite 640, quantized weights", file: "mira_exp019_int8_640.tflite", bytes: 3_041_690 },
  { format: "ONNX", file: "mira_exp019.onnx", bytes: 10_607_296 },
];

/** Decimal megabytes with two decimals, e.g. 3_022_810 becomes "3.02". */
export function bytesToMb(bytes: number): string {
  return (bytes / 1_000_000).toFixed(2);
}

/** Local validation of the TFLite 320 export of EXP-019, in percent. The log does not name the split. */
export const EXP019_TFLITE_320 = {
  precision: 79.7,
  recall: 83.6,
  map50: 86.2,
  map5095: 75.6,
} as const;

/**
 * The July 13 benchmark (image-level, no camera): class-presence F1 (does the class
 * appear in the image at all?), NOT detection mAP50. EXP-018 and EXP-019 were
 * not among the 11 models tested.
 */
export const FIELD_BENCHMARK = {
  date: "2026-07-13",
  dataset: "mira_v2 (TACO + TrashNet), 805 validation images",
  confidence: 0.5,
  modelsTested: 11,
  bestModel: "mira_exp014.pt",
  bestF1: 85.8,
  bestPrecision: 92.9,
  bestRecall: 79.7,
  bestInt8Model: "mira_exp014_int8.tflite",
  bestInt8F1: 72.8,
  weakestClass: "trash",
  weakestClassF1: 54.0,
} as const;

/* ------------------------------------------------------------------ */
/* Planned work                                                        */
/* ------------------------------------------------------------------ */

/**
 * EXP-020 is planned, not run. It has a config file but no results, so it is
 * kept apart from {@link EXPERIMENTS} and must never be shown with a score.
 * Source: `experiments/exp020_yolo11n_roboflow_dominant.yaml`.
 */
export const PLANNED_EXPERIMENT = {
  id: "EXP-020",
  status: "planned" as const,
  title: "Roboflow-dominant source mix",
  model: "YOLO11n (yolo11n.pt)",
  configFile: "experiments/exp020_yolo11n_roboflow_dominant.yaml",
  /** Share of training images by source, percent. Sums to 100. */
  sourceMix: [
    { source: "Roboflow", share: 70 },
    { source: "TACO", share: 20 },
    { source: "dmedhi", share: 5 },
    { source: "TrashNet", share: 5 },
  ],
  trainImages: 6000,
  epochs: 120,
  batchSize: 32,
  imageSize: 640,
  optimizer: "AdamW",
  lr0: 0.001,
  lrf: 0.01,
  weightDecay: 0.0005,
  patience: 30,
  seed: 2026,
  validation: "Mixed held-out source splits",
  realCamera: "Must be evaluated separately before deployment",
  summary:
    "Same architecture and the same recorded training settings as EXP-019 (120 epochs, batch 32, 640 px, AdamW, lr0 0.001). It changes only how the sources are weighted.",
} as const;
