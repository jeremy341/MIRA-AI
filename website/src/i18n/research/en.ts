/**
 * Research page copy, English. This file DEFINES the shape; de.ts must match it key for key
 * (`ResearchDictionary` is derived from it, so tsc fails on a missing or extra key).
 *
 * Inline markup is the same as in src/i18n/en.ts: ==marker==, `code`, [label](href).
 * Placeholders look like {name}. The page fills the shared ones from the experiment data, never retyped
 * (see `researchVars` in src/components/research/vars.ts).
 * No em dashes or en dashes anywhere.
 */

export type ExperimentCopy = {
  title: string;
  /** Model, data and size in one plain line. */
  setup: string;
  /** What the score was measured on (the image count is added from the data). */
  split: string;
  note: string;
  /** Empty array when the log has nothing to flag. */
  caveat: string[];
};

export const en = {
  meta: {
    title: "Research",
    description:
      "A student report on the MIRA waste detector: 19 experiments, the datasets, per-class results, real photos and failures, export for small devices and honest limits. Validation scores only.",
  },
  head: {
    eyebrow: "Research report",
    title: "Nineteen experiments on telling waste apart",
    subtitle: "What I tried, what worked, and what I still cannot say.",
    byline: "MIRA, a one-student project for Jugend forscht 2027. Experiments from June to July 2026.",
    abstractLabel: "Abstract",
    abstract:
      "I trained models to find glass, metal, paper, plastic and trash in camera images. Over 19 experiments, from a three-layer CNN to YOLO11n, the lesson was about data. Pooling three sources scored {exp014} mAP50 (EXP-014), and pooling all four {exp017} (EXP-017). A smaller, cleaned and class-balanced set scored {exp018} (EXP-018), and {exp019} when I repeated the run (EXP-019). Plastic is the weak class, with a recall of {plasticRecall}. All of this is validation scores on photos, not a test with a real camera, and the two runs used different validation splits. The model has not run on a Raspberry Pi, and the sorting robot does not exist yet.",
    contentsLabel: "Sections",
    contents: {
      question: "Question and setup",
      tried: "What I tried",
      results: "Results",
      runs: "All experiments",
      photos: "Real photos and failures",
      edge: "Export for small devices",
      limits: "Limits and next steps",
      data: "Data and reproducibility",
    },
  },
  question: {
    title: "Question and setup",
    p1: "The question behind MIRA is simple. Can a small model look at a camera image and tell glass, metal, paper, plastic and trash apart, well enough to be the eyes of a sorting robot?",
    classesLabel: "The five classes",
    note: "mAP50 scores how well the predicted boxes match the labelled ones (at least 50% overlap), averaged over the classes. 100% would be perfect.",
    p2: "The idea for the hardware is a Raspberry Pi Zero 2W with a camera that tells a robot arm what to pick up. Only the recognition step exists.",
    p3: "I worked on two kinds of task. In stage A, a classifier gives one label per photo and is scored by accuracy. In stage B, a detector draws a box around every object it finds and is scored by mAP50. Every score on this page is a validation score: it is measured on a recorded set of images that the model was not trained on.",
  },
  tried: {
    title: "What I tried",
    p1: "I started small on purpose. A three-layer CNN showed me the problem, MobileNetV2 showed what transfer learning adds, and only then did I move to detectors that draw boxes.",
    modelsCaption: "The four models, in the order I tried them.",
    modelsLabel: "Scrolls sideways on small screens",
    modelsColumns: { model: "Model", task: "Task", runs: "Runs", lesson: "What it taught me" },
    models: [
      {
        name: "Custom CNN",
        task: "Classifier, stage A",
        runs: "EXP-001",
        lesson: "I built it to understand the problem. Paper was almost never recognised.",
      },
      {
        name: "MobileNetV2",
        task: "Classifier, stage A",
        runs: "EXP-002 to EXP-004",
        lesson: "Transfer learning reached 87.42% accuracy on a larger hand-collected set. Still one label per photo.",
      },
      {
        name: "YOLOv8n",
        task: "Detector, stage B",
        runs: "EXP-005 to EXP-012",
        lesson: "Boxes allow several objects per frame. Adding outdoor photos dropped mAP50 to 39.4%.",
      },
      {
        name: "YOLO11n",
        task: "Detector, stage B",
        runs: "EXP-013 to EXP-019",
        lesson: "The model behind every headline number on this page.",
      },
    ],
    p2: "The training data turned out to be the bigger story. The final set uses four sources. A fifth, WaRP, I tried and dropped. SortWaste and Keremberke were excluded as well, and the log records the exclusion but not the reason.",
    datasetsCaption: "Where the training images come from.",
    datasetsLabel: "Scrolls sideways on small screens",
    datasetsColumns: { source: "Source", what: "What it is", status: "Status" },
    datasets: [
      { name: "dmedhi", what: "An object detection dataset from Hugging Face.", status: "In the final set" },
      { name: "TACO", what: "Trash Annotations in Context: litter photographed outdoors.", status: "In the final set" },
      {
        name: "Roboflow",
        what: "A Trash Detection export with 64 classes, remapped to my five. CC BY 4.0.",
        status: "In the final set",
      },
      {
        name: "TrashNet",
        what: "Tabletop photos of single items. I labelled them with SAM for detection.",
        status: "In the final set",
      },
      {
        name: "WaRP",
        what: "A waste dataset with a research-only licence and no trash class.",
        status: "Dropped, runs that used it scored lower",
      },
    ],
    p3: "More data did not help. EXP-014 pooled three sources (6,802 images) and scored {exp014} mAP50. Merging all four in EXP-017 gave the largest set, 9,774 images, and {exp017}. The clean set of EXP-018 has only {train} training images, with 1,621 to 1,982 boxes per class, and scored {exp018} in 2.7 hours instead of 4.7. The log concludes that dataset quality mattered far more than architecture or training length. My own reading is more careful, and I give it in section 7.",
    splitNote:
      "The clean set has 6,898 images and 12,832 boxes: {train} for training, {val} for validation and {test} for testing.",
  },
  results: {
    title: "Results",
    p1: "On the cleaned set, YOLO11n reached {exp018} mAP50 in EXP-018 and {exp019} when I repeated the run as EXP-019. The earlier pooled-data baseline, EXP-014, reached {exp014}.",
    chartAria: "Bar chart of mAP50: EXP-014 {exp014}, EXP-018 {exp018}, EXP-019 {exp019}.",
    chartRows: [
      { id: "EXP-014", note: "pooled sources" },
      { id: "EXP-018", note: "cleaned and balanced" },
      { id: "EXP-019", note: "repeat of EXP-018" },
    ],
    chartCaption:
      "mAP50 of EXP-014, EXP-018 and EXP-019. The outlined bar was scored on a different validation split (1,588 mixed images instead of {val} TrashNet tabletop images), so it compares two approaches, not two models on the same data.",
    statValue: "==90.58%==",
    statLabel: "mAP50 of EXP-019 on {val} validation images. The repeat matches EXP-018 almost exactly.",
    p2: "Table 3 breaks EXP-019 down by class. Plastic is the weak one. The detector finds {plasticRecall} of the plastic objects, so about one in three is missed. When it does say plastic, it is usually right (precision {plasticPrecision}).",
    marginRecall:
      "Recall is the share of the real objects of a class that the model finds. Precision is the share of its detections that are correct.",
    classTableCaption:
      "EXP-019 per class on the {val}-image validation split. The log prints the same per-class rows for EXP-018.",
    classTableLabel: "Scrolls sideways on small screens",
    classColumns: { cls: "Class", precision: "Precision", recall: "Recall", map50: "mAP50" },
    classAll: "All classes",
    classWeakMark: "weakest",
    p3: "Figure 2 puts the per-class mAP50 of the two approaches side by side. Every class improved. Trash moved most, from the weakest class ({trashBefore}) to the strongest ({trashAfter}). I do not trust that jump yet, and section 7 says why.",
    classChartAria: "Bar chart of per-class mAP50 for EXP-014 and EXP-018, five classes.",
    classChartCaption:
      "Per-class mAP50, EXP-014 (hatched) against EXP-018 (solid). Different validation splits, so the bars compare approaches, not like for like.",
    classChartBefore: "EXP-014",
    classChartAfter: "EXP-018",
  },
  runs: {
    title: "All experiments",
    p1: "Figure 3 shows the headline score of every scored run, and Table 4 lists all 19 with what each one showed. Each run was scored on its own validation split, so read the bars as a record, not a ranking. Three export runs have a file size and no score.",
    panelA: "A. Classifiers, validation accuracy",
    panelB: "B. Detectors, mAP50",
    chartAriaA: "Bar chart of validation accuracy for the four classifier runs.",
    chartAriaB: "Bar chart of mAP50 for the twelve scored detector runs.",
    chartCaption:
      "Headline score of every scored run. The dark bars are the clean-data runs, EXP-018 and EXP-019. Stage A runs used four classes without trash.",
    tableCaption: "All 19 recorded experiments, plus EXP-020, which is planned and has not run.",
    filterLabel: "Show",
    filters: { all: "All", A: "Stage A", B: "Stage B" },
    filterStatus: "Showing {shown} of {total} rows.",
    tableLabel: "Scrolls sideways on small screens",
    scrollHint: "Swipe the table sideways to see every column.",
    columns: { run: "Run", what: "What it was", score: "Score", note: "What it showed" },
    scoreMap: "mAP50",
    scoreAcc: "accuracy",
    sizeOnly: "size only",
    scoredOn: "Scored on",
    images: "{n} images",
    caveatLabel: "Caveat",
    planned: "planned, not run",
    plannedSetup: "YOLO11n. Roboflow 70%, TACO 20%, dmedhi 5%, TrashNet 5%.",
    plannedNote: "No result exists. Only the configuration is written (section 7).",
    plannedSplit: "Not evaluated yet",
    exportKind: "export",
    logLink: "Read the full experiment log on GitHub",
  },
  photos: {
    title: "Real photos and failures",
    unavailable: "This photo is not available in this build.",
    p1: "Numbers hide what a mistake looks like, so here are two. Both are public TrashNet photos, run through the EXP-019 model at a confidence threshold of 0.25.",
    note: "These photos are illustrations, not evidence. TrashNet is part of the training recipe, so I cannot say they were held out. They are shown at their original width of 512 pixels.",
    missed: "A miss. The photo shows a crushed plastic bottle. The model finds nothing at confidence {conf} or higher.",
    outOfScope:
      "Out of scope. The photo shows cardboard, and MIRA has no class for it. The model calls it {predicted} ({conf}).",
    wrong: "A mistake. The photo shows {trueClass}. The model calls it {predicted} ({conf}).",
    p2: "Both fit what Table 3 says. Plastic is the class the detector misses most, and anything outside the five classes gets forced into one of them. Most TrashNet photos show one object filling the frame, so the boxes are nearly full frame. A cluttered scene will look different.",
  },
  edge: {
    title: "Export for small devices",
    p1: "The Raspberry Pi Zero 2W is small, so I exported EXP-019 to smaller formats. Table 5 lists the files.",
    tableCaption: "The EXP-019 files and their size.",
    tableLabel: "Scrolls sideways on small screens",
    columns: { format: "Format", file: "File", size: "Size" },
    formats: {
      "mira_exp019.pt": "PyTorch, FP32",
      "mira_exp019_int8_320.tflite": "TFLite, 320 px, quantized weights",
      "mira_exp019_int8_640.tflite": "TFLite, 640 px, quantized weights",
      "mira_exp019.onnx": "ONNX",
    },
    sizeUnit: "MB",
    marginSize:
      "Sizes are exact byte counts from the log, in decimal MB. The log itself uses MB and MiB interchangeably.",
    p2: "Quantizing costs accuracy. The TFLite 320 export scores {tflite320} mAP50 against {exp019} for the original, about {drop} points lower. Both TFLite files keep FP32 input and output tensors, so they are reduced-size exports with quantized weights, not full-integer models. The log does not name the split of this local check.",
    p3: "What I have not measured is speed or accuracy on a Raspberry Pi. The only CPU timing of a detector in the log is about 40.4 ms per frame for EXP-006, a YOLOv8n model, on a local CPU. The log also gives about 15.6 FPS for the same run, which does not match (40.4 ms would be about 25 FPS). That is not a Pi and not the current model. The MobileNetV2 classifier EXP-004 has a CPU latency of 10.32 ms.",
    p4: "The July benchmark (image-level, no camera) scored 11 models on whether a class appears in a validation image at all (F1 at confidence {fieldConf}, not mAP50). EXP-014 ranked first at {fieldBest}, and its INT8 export fell to {fieldInt8}. EXP-018 and EXP-019 were not part of it.",
  },
  limits: {
    title: "Limits and next steps",
    limitsTitle: "Limits",
    limits: [
      "No real-camera evaluation. Every score is on a recorded split of photos. MIRA has not been tested with a camera over a real bin.",
      "The independent test split of {test} images was not run for EXP-019. A disk-full error stopped the notebook while saving, after training, validation and exports had finished.",
      "EXP-014 and EXP-018 were scored on different validation splits (1,588 mixed images against {val} TrashNet tabletop images). The jump from {exp014} to {exp018} compares two approaches. Some of it may come from scoring on a cleaner tabletop split, and the log cannot separate the two. These were not controlled ablations: data, split and sometimes the model changed together.",
      "Plastic recall is {plasticRecall}, and trash has the lowest precision ({trashPrecision}).",
      "Trash was the weakest class in every earlier detector run that recorded per-class results and has a trash class, and it is now the strongest at {trashAfter}. That reversal needs a check on real camera footage before anyone relies on it.",
      "Known failure cases are crumpled paper, cans seen from the opening and overlapping objects.",
      "Speed and accuracy on a Raspberry Pi are unmeasured, and the sorting robot is not built.",
    ],
    logTitle: "Inconsistencies in my own log",
    logIntro: "I found these while writing this page. I used each run's own numbers.",
    log: [
      "EXP-018: the all-class precision and recall in the log (90.4 and 82.5) are identical to its glass row, which looks like a transcription slip. Table 3 uses the all-class row of EXP-019.",
      "EXP-017: its comparison bullets quote the trash and plastic scores of EXP-014 differently from EXP-014's own table.",
      "EXP-001: the log lists 126 images, but the per-class support adds up to 159.",
      "EXP-004: the accuracy is printed as both 87.42% and 0.8735.",
    ],
    nextTitle: "Next steps",
    next: [
      "Evaluate on real camera footage, comparing recall and false positives, not confidence alone.",
      "Run the independent test split of {test} images.",
      "Measure speed and accuracy of the TFLite exports on a Raspberry Pi.",
    ],
    plannedTitle: "EXP-020: planned, not run",
    plannedIntro:
      "EXP-020 changes only how the sources are weighted. It uses the same architecture and the same recorded settings as EXP-019. It has a configuration file and no result.",
    plannedCaption: "The planned configuration of EXP-020. There is no score because it has not been trained.",
    plannedLabel: "Scrolls sideways on small screens",
    plannedRows: {
      model: "Model",
      mix: "Source mix",
      images: "Training images",
      settings: "Settings",
      validation: "Validation",
      camera: "Real camera",
      result: "Result",
      config: "Config file",
    },
    plannedMix: "Roboflow 70%, TACO 20%, dmedhi 5%, TrashNet 5%",
    plannedSettings:
      "{epochs} epochs, batch {batch}, {imgsz} px, {optimizer}, lr0 {lr0}, lrf {lrf}, weight decay {wd}, patience {patience}, seed {seed}",
    plannedValidation: "Mixed held-out source splits",
    plannedCamera: "Must be evaluated separately before deployment",
    plannedResult: "None. There is no score to report.",
  },
  data: {
    title: "Data and reproducibility",
    p1: "The datasets are not in the repository. [Dataset origins]({originsUrl}) lists where to download each one, with licences. All 19 experiments are in the [experiment log]({logUrl}) with their settings and limitations. The trained models are on [Hugging Face]({hfUrl}) and the code is on [GitHub]({githubUrl}). The [package](/package) ships the weights of EXP-014, EXP-018 and EXP-019.",
  },
  /** Copy for the bar charts and the index, keyed by experiment id. */
  experiments: {
    "EXP-001": {
      title: "Baseline custom CNN",
      setup: "Custom CNN, 3 conv layers. Hand-collected images, 4 classes (no trash). 126 images.",
      split: "Validation split, size not recorded",
      note: "A baseline to understand the problem. Paper was almost never recognised (recall 0.07).",
      caveat: [
        "The log lists 126 images, but the per-class support adds up to 159, so the validation size is not stated reliably.",
      ],
    },
    "EXP-002": {
      title: "MobileNetV2, frozen base",
      setup: "MobileNetV2 (ImageNet, frozen) + small head. Hand-collected images, 4 classes (no trash). 796 images.",
      split: "Validation split, size not recorded",
      note: "Transfer learning lifted accuracy by over 23 points on a larger hand-collected set.",
      caveat: [],
    },
    "EXP-003": {
      title: "MobileNetV2, fine-tuned",
      setup: "MobileNetV2 (unfrozen from layer 100) + small head. The same 796 hand-collected images, 4 classes.",
      split: "Validation split, size not recorded",
      note: "Two-stage fine-tuning gave the best classifier. It still labels one thing per image.",
      caveat: [],
    },
    "EXP-004": {
      title: "MobileNetV2, full INT8 TFLite",
      setup:
        "MobileNetV2 quantized (weights stored with smaller numbers) to 8-bit integers, from EXP-003. 796 images, 4 classes.",
      split: "Validation split, size not recorded",
      note: "Quantization shrank the model to 2.61 MB (9.0x smaller than the Keras binary) with no accuracy loss recorded.",
      caveat: ["The log prints the accuracy as both 87.42% and 0.8735."],
    },
    "EXP-005": {
      title: "First detector",
      setup: "YOLOv8n. Hand-collected tabletop images + TrashNet. About 3,300 images.",
      split: "Validation split, size not recorded",
      note: "Moving to boxes made several objects per frame possible.",
      caveat: ["Bounding boxes were auto-generated with Canny edge detection, not drawn by hand."],
    },
    "EXP-006": {
      title: "TrashNet + Roboflow outdoor data",
      setup: "YOLOv8n. Hand-collected + TrashNet + Roboflow (64 classes remapped to 5). About 3,300 images.",
      split: "Mixed validation data, mostly outdoor",
      note: "Adding outdoor data dropped mAP50 to 39.4%. The log gives about 40.4 ms per frame on a local CPU, and an FPS figure that does not match it.",
      caveat: ["Scored on mostly outdoor data, so it is not comparable with tabletop-only runs."],
    },
    "EXP-007": {
      title: "YOLOv8n INT8 export",
      setup: "YOLOv8n, TFLite INT8. Derived from EXP-006.",
      split: "Not evaluated, size only",
      note: "Static INT8 quantization: 11.69 MB down to 3.18 MB (3.7x smaller).",
      caveat: ["The log records the file size but no accuracy for the quantized model."],
    },
    "EXP-008": {
      title: "Tabletop, purged labels",
      setup: "YOLOv8n. Hand-collected tabletop + human-annotated TrashNet. About 3,000 images.",
      split: "Validation split, size not recorded",
      note: "Removing corrupted auto-labelled images matched the noisy 100-epoch run in half the epochs.",
      caveat: [],
    },
    "EXP-009": {
      title: "Pristine TrashNet baseline",
      setup: "YOLOv8n. TrashNet only, Canny-edge auto-labelled. About 2,527 images.",
      split: "Validation split, size not recorded",
      note: "Dropping the noisy custom images raised mAP50 from 39.6% to 72.8%.",
      caveat: [
        "Trained and validated on clean white-background TrashNet images. The log notes that this validation may overstate the score.",
      ],
    },
    "EXP-010": {
      title: "Outdoor-data INT8 export",
      setup: "YOLOv8n, TFLite INT8. Derived from EXP-006.",
      split: "Not evaluated, size only",
      note: "A second INT8 export of the EXP-006 model, calibrated on 100 outdoor samples: 3.16 MB.",
      caveat: ["The log records the file size but no accuracy for the quantized model."],
    },
    "EXP-011": {
      title: "Outdoor data only",
      setup: "YOLOv8n. TACO outdoor litter, 60 categories remapped to 5. 3,365 images.",
      split: "Diverse outdoor validation set",
      note: "A test of how well it generalises: tabletop images excluded, trash at 7.5% mAP50.",
      caveat: [],
    },
    "EXP-012": {
      title: "Outdoor-only INT8 export",
      setup: "YOLOv8n, TFLite INT8. Derived from EXP-011.",
      split: "Not evaluated, size only",
      note: "INT8 export of EXP-011: 11.62 MB down to 3.16 MB (3.7x smaller).",
      caveat: [
        "In the July benchmark (image-level, no camera) this export returned no detections at the default 0.5 confidence (INT8 shifts scores down). It works at 0.25.",
      ],
    },
    "EXP-013": {
      title: "YOLO11n on TACO + TrashNet",
      setup: "YOLO11n. TACO (1,497) + TrashNet (2,527), full-image boxes. 4,024 images.",
      split: "Validation split, size not recorded",
      note: "First YOLO11n run, 20 points above the outdoor-only EXP-011. Trash was the weakest class (15.6% mAP50).",
      caveat: ["Architecture and dataset changed together, so the gain is not attributable to the model alone."],
    },
    "EXP-014": {
      title: "TACO + TrashNet + Roboflow",
      setup: "YOLO11n. TACO + TrashNet + Roboflow (64 classes remapped to 5). 6,802 images.",
      split: "Own mixed validation split",
      note: "The pooled-data baseline. Adding Roboflow lifted mAP50 by 5.6 points over EXP-013.",
      caveat: ["Validated on its own mixed split, not the 415-image TrashNet split used by EXP-018 and EXP-019."],
    },
    "EXP-015": {
      title: "TACO + TrashNet + WaRP",
      setup: "YOLO11n. TACO + TrashNet + WaRP (28 classes remapped to 5). About 6,800 images.",
      split: "Own mixed validation split",
      note: "Swapping Roboflow for WaRP helped glass but cost metal, paper and trash. Trash recall fell to 0.087.",
      caveat: [],
    },
    "EXP-016": {
      title: "WaRP only",
      setup: "YOLO11n. WaRP only (28 classes remapped to 5). Image count not recorded.",
      split: "Validation split, size not recorded",
      note: "One clean source beat the mixed EXP-015 (56.0%) despite fewer classes.",
      caveat: ["WaRP has no trash class, so this model cannot detect trash at all."],
    },
    "EXP-017": {
      title: "All four sources merged",
      setup: "YOLO11n. TACO + TrashNet + Roboflow + WaRP. 9,774 images.",
      split: "Own mixed validation split",
      note: "The largest dataset scored lower than EXP-014. More data was not better data.",
      caveat: [
        "The log's comparison bullets quote EXP-014's trash and plastic scores differently from EXP-014's own table. This page uses each run's own table.",
      ],
    },
    "EXP-018": {
      title: "Clean, balanced dataset",
      setup:
        "YOLO11n. dmedhi + TACO + Roboflow + TrashNet (SAM-labelled). SortWaste and Keremberke excluded. 5,108 train, 415 validation, 1,375 test images.",
      split: "TrashNet tabletop validation split",
      note: "A smaller, class-balanced set (1,621 to 1,982 boxes per class) lifted mAP50 by 29.9 points.",
      caveat: [
        "The 415-image split differs from EXP-014's, so this compares approaches, not like for like.",
        "The all-class precision and recall in the log equal its glass row, which may be a transcription slip. No test-split result is recorded.",
      ],
    },
    "EXP-019": {
      title: "Repeat of EXP-018",
      setup: "YOLO11n. The same clean, balanced dataset and settings as EXP-018.",
      split: "TrashNet tabletop validation split",
      note: "Reproduces EXP-018 almost exactly, so the result is repeatable and not a lucky run.",
      caveat: ["The 1,375-image test split was not evaluated. A disk-full error stopped the notebook while saving."],
    },
  } as Record<string, ExperimentCopy>,
};

export type ResearchDictionary = typeof en;
