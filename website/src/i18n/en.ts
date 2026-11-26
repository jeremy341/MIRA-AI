/**
 * English dictionary. This file DEFINES the shape: `Dictionary` is derived from it, and de.ts must
 * match it key for key, so a missing or extra key fails `tsc`.
 *
 * Inline markup in strings (rendered by components/ui-notebook/Rich.tsx):
 *   ==marked words==   highlighter marker
 *   `code`             monospace
 *   [label](href)      link ("/..." is an internal page and gets the language prefix)
 * Placeholders look like {name} and are filled by `fmt()` in src/i18n/format.ts.
 *
 * No em dashes or en dashes anywhere in the copy.
 */
export const en = {
  meta: {
    siteName: "MIRA",
    title: "MIRA: Machine Intelligence for Recycling Automation",
    description:
      "MIRA is an open-source detector for glass, metal, paper, plastic and trash in camera images, built by one student for Jugend forscht 2027. Experiments, honest limits and the mira-ai Python package.",
    ogTagline: "A waste detector, with its numbers and its limits",
    pages: {
      research: {
        title: "Research",
        description:
          "Every MIRA experiment with its numbers, datasets, charts and limits. Validation results only, no real-world accuracy claimed.",
      },
      package: {
        title: "Package",
        description:
          "The mira-ai Python package: install, bundled models, live webcam detection, dashboard and command reference.",
      },
      docs: {
        title: "Docs",
        description:
          "Guides and reference for the mira-ai package: install, live inference, the dashboard, datasets, training, export, CLI commands and the dashboard API.",
      },
    },
  },
  common: {
    skipToContent: "Skip to main content",
    opensInNewTab: "(opens in a new tab)",
    figure: "Figure",
    table: "Table",
    languageLabel: "Language",
    languageNames: { en: "English", de: "Deutsch" },
    switchTo: "Switch to {language}",
    copy: {
      copy: "Copy",
      copied: "Copied",
      failed: "Failed",
      labelFor: "Copy: {command}",
      copiedMessage: "Copied to clipboard",
      failedMessage: "Copy failed, select the command and copy it manually",
    },
    classes: {
      glass: "glass",
      metal: "metal",
      paper: "paper",
      plastic: "plastic",
      trash: "trash",
    },
  },
  nav: {
    label: "Primary",
    home: "Home",
    research: "Research",
    package: "Package",
    docs: "Docs",
    github: "GitHub",
  },
  header: {
    homeLabel: "MIRA, home",
  },
  footer: {
    blurb: "Machine Intelligence for Recycling Automation. A one-student project for Jugend forscht 2027.",
    pagesTitle: "Pages",
    projectTitle: "Elsewhere",
    licence: "MIT licence.",
    github: "GitHub",
    pypi: "PyPI",
    huggingface: "Hugging Face",
  },
  redirect: {
    title: "MIRA",
    message: "Choose a language",
    note: "You are being sent to the language your browser prefers.",
  },
  figures: {
    boxesToggle: "Detection boxes",
    boxesOn: "on",
    boxesOff: "off",
    altPrefix: "Photo with detections by the model.",
    altNone: "No detections.",
    altListIntro: "Detections:",
    altItem: "{cls}, confidence {conf}",
    placeholderTitle: "Detection photo not available yet",
    placeholderHint: "Expected file: {file}",
    unitConfidence: "confidence",
  },
  home: {
    hero: {
      title: "Waste detection with MIRA",
      lede: "MIRA draws boxes around glass, metal, paper, plastic, and general trash in a camera feed.",
      copyLabel: "Copy install command",
      tryCta: "Get started",
      resultsCta: "See the results",
      scrollCue: "Scroll to learn more",
      benchmark: "EXP-019 on {count} TrashNet tabletop validation images. Not real-world sorting accuracy.",
      benchmarkLink: "Read the benchmark and its limits",
    },
    what: {
      title: "What is MIRA?",
      lede: "An open-source detector for waste in camera images. Give it a photo or a webcam feed, and it draws a box around the objects it finds.",
      stepsLabel: "How a detection works",
      steps: [
        {
          title: "Give it a picture",
          text: "A photo or a webcam frame.",
        },
        {
          title: "MIRA looks for objects",
          text: "EXP-019 draws a box around what it finds and names one of five classes.",
        },
        { title: "You get the result", text: "A class, a confidence score and the box position for each object." },
      ],
    },
    problem: {
      title: "The problem, and what I tried",
      p1: "Sorting waste by hand is slow, and a machine can only sort what it can first recognise. So I started with the part that has to work first: a model that looks at a camera image and says what is in it.",
      note: "The long-term goal is a robot arm that sorts what the camera sees. This page is only about the recognition step.",
      p2: "I did not begin with YOLO. I built a custom CNN to understand the basic classification problem, then tried MobileNetV2, then YOLOv8n, and finally YOLO11n, which draws a box around every object it finds.",
      triedLabel: "Models I tried, in order",
      tried: [
        { name: "Custom CNN", text: "Classification, one label per image. To learn the problem." },
        { name: "MobileNetV2", text: "Classification with transfer learning." },
        { name: "YOLOv8n", text: "Detection: boxes around several objects." },
        { name: "YOLO11n", text: "Detection. The model behind every result below." },
      ],
      p3: "I also tried several datasets, including dmedhi, TACO, TrashNet and Roboflow waste-detection data. I assumed that more data would make the model better. It did not. Some of the larger mixes held inconsistent image styles, labels and object arrangements. I removed WaRP after it made the results worse, and its licence is research only.",
    },
    evidence: {
      title: "The evidence",
      subtitle: "Cleaner data beat more data.",
      p1: "The pooled-data baseline, EXP-014, reached 60.7% mAP50. After I cleaned and balanced the data, YOLO11n reached 90.6% in EXP-018, and 90.58% when I repeated the run as EXP-019.",
      mapNote:
        "mAP50 scores how well the predicted boxes match the labelled ones (at least 50% overlap), averaged over the classes. 100% would be perfect.",
      statValue: "==90.58%==",
      statLabel: "mAP50, EXP-019, on the validation split of 415 images",
      chartCaption:
        "mAP50 of EXP-014, EXP-018 and EXP-019, each on its own validation split (photos kept out of training and used only for scoring).",
      chartAria: "Bar chart of mAP50: EXP-014 60.7%, EXP-018 90.6%, EXP-019 90.58%.",
      chartRows: [
        { id: "EXP-014", note: "pooled sources" },
        { id: "EXP-018", note: "cleaned and balanced" },
        { id: "EXP-019", note: "repeat of EXP-018" },
      ],
      tableCaption: "EXP-018 and EXP-019 per class, validation split of 415 images.",
      tableAll: "EXP-019, all classes",
      tableColumns: { cls: "Class", precision: "Precision", recall: "Recall", map50: "mAP50" },
      plasticNote: "Plastic is the weak class. Recall is how many of the real plastic objects the model finds.",
      plastic:
        "The weak spot is plastic. The model finds only 64.4% of the plastic objects (recall), so about one in three is missed. Precision is 87.4%: when it says plastic, it is usually right.",
      caveatTitle: "What this does not show",
      caveat:
        "All of these numbers come from validation images, not from a real camera over a real bin. They say nothing about accuracy in real use. EXP-014 and EXP-018 were scored on different validation splits (1,588 mixed images against 415 TrashNet tabletop images), so the jump from 60.7% to 90.6% compares two approaches, not two models on the same data. I did not evaluate the independent test split of 1,375 images for EXP-019, and I have not yet evaluated MIRA on a real camera.",
    },
    landscape: {
      title: "The experiment landscape",
      lede: "All 19 documented experiments in one 3D bar chart. Column height is the recorded score.",
      ledeFlat: "All 19 documented experiments as bars. Bar length is the recorded score.",
      note: "Not a ranking: the runs were scored on different validation splits, so the heights are the recorded values and cannot be compared like for like.",
      caption: "EXP-014, EXP-018 and EXP-019 are highlighted: they are the three models that ship in the package.",
      hint: "Drag to rotate. The arrow keys move the focus from column to column.",
      hintFlat: "Shown as flat bars on this screen.",
      resetView: "Reset view",
      legendLabel: "Legend",
      stageA: "Stage A: classifiers",
      stageB: "Stage B: detectors",
      metricA: "validation accuracy",
      metricB: "mAP50",
      noScore: "no score recorded",
      noScoreShort: "no score",
      axisTick: "{n}%",
      highlighted: "ships in the package",
      chartLabel: "Experiment scores",
      tableSummary: "View as table",
      tableCaption: "All 19 experiments with the score the log records",
      columns: {
        experiment: "Experiment",
        stage: "Stage",
        metric: "Metric",
        value: "Value",
        split: "Validation split",
      },
      stageNames: { A: "A, classifier", B: "B, detector" },
      images: "{n} images",
      splits: {
        "Validation split, size not recorded in the log": "Validation split, size not recorded",
        "Mixed, wild-heavy validation data": "Mixed validation data, mostly outdoor",
        "Diverse outdoor validation set": "Diverse outdoor validation set",
        "Own mixed validation split": "Own mixed validation split",
        "TrashNet tabletop validation split": "TrashNet tabletop validation split",
        "Not evaluated, size only": "Not evaluated, file size only",
      },
      models: {
        "EXP-001": "Custom CNN",
        "EXP-002": "MobileNetV2, frozen base",
        "EXP-003": "MobileNetV2, fine-tuned",
        "EXP-004": "MobileNetV2, INT8 export of EXP-003",
        "EXP-005": "YOLOv8n, first detector",
        "EXP-006": "YOLOv8n, with Roboflow data",
        "EXP-007": "YOLOv8n, INT8 export of EXP-006",
        "EXP-008": "YOLOv8n, purged labels",
        "EXP-009": "YOLOv8n, TrashNet only",
        "EXP-010": "YOLOv8n, INT8 export of EXP-006",
        "EXP-011": "YOLOv8n, TACO only",
        "EXP-012": "YOLOv8n, INT8 export of EXP-011",
        "EXP-013": "YOLO11n, TACO and TrashNet",
        "EXP-014": "YOLO11n, TACO, TrashNet and Roboflow",
        "EXP-015": "YOLO11n, TACO, TrashNet and WaRP",
        "EXP-016": "YOLO11n, WaRP only",
        "EXP-017": "YOLO11n, four sources merged",
        "EXP-018": "YOLO11n, clean balanced data",
        "EXP-019": "YOLO11n, repeat of EXP-018",
      },
    },
    stats: {
      experiments: "documented experiments",
      classes: "waste classes",
    },
    tryit: {
      title: "Try it",
      p1: "The package already contains the weights of EXP-014, EXP-018 and EXP-019. Nothing else has to be downloaded.",
      steps: [
        { label: "Install", command: "pip install mira-ai" },
        { label: "List the bundled models", command: "mira models" },
        { label: "Start live detection on a webcam", command: "mira live --model mira_exp014.pt" },
        { label: "Open the local dashboard", command: "mira dashboard" },
      ],
      defaultNote:
        "EXP-014 is the default model for the live demo. I chose it for how it behaves in the live demo, not from its mAP50 value.",
      video: {
        title: "MIRA demo: live webcam detection with mira live",
        videoCaption: "Live webcam detection with `mira live`.",
        unsupported: "Your browser cannot play this video.",
        playLabel: "Play video",
        privacyNote: "The video loads from YouTube (youtube-nocookie.com) only when you press play.",
      },
      downloadsTitle: "Hugging Face downloads",
      downloadsAllTime: "all time",
      downloadsLast30: "{n} in the last 30 days",
      downloadsHonest:
        "This counts file fetches from the model repository on Hugging Face, not unique people. PyPI installs are not included.",
      status: {
        checking: "checking",
        live: "live",
        cached: "cached",
        fallback: "built-in value",
        checkingLong: "Checking Hugging Face for the current count. Showing the last known value.",
        liveLong: "Live count, fetched from Hugging Face just now.",
        cachedLong: "Cached count. Hugging Face could not be reached, so this is the last known value.",
        fallbackLong:
          "Built-in count. Hugging Face could not be reached and no earlier value was stored, so this is the number written into the site.",
      },
    },
    status: {
      title: "What works, what is open, who made it",
      worksTitle: "What works",
      works: [
        "Detects glass, metal, paper, plastic and trash in images and on a live webcam.",
        "Reaches 90.58% mAP50 on the 415-image validation split, confirmed by a second run (EXP-018, EXP-019).",
        "Runs from the command line, with a local dashboard and tools for datasets and evaluation.",
        "Exports to ONNX and TFLite.",
      ],
      openTitle: "What is open",
      open: [
        "Evaluation on a real camera. Not done.",
        "The 1,375-image test split for EXP-019. Not evaluated.",
        "Plastic recall of 64.4%. Weak.",
        "Speed on small hardware such as a Raspberry Pi. Not measured.",
        "The sorting robot. Not built.",
        "Known weak cases: crumpled paper, cans seen from the opening, overlapping objects and unusual image conditions.",
      ],
      planned:
        "EXP-020 is planned and has not run. It uses the same settings as EXP-019 but weights Roboflow images most (70% Roboflow, 20% TACO, 5% dmedhi, 5% TrashNet). There are no results yet.",
      whoTitle: "Who made it",
      who: "MIRA is a one-person project. I made it alone for Jugend forscht 2027.",
      transparency:
        "I used AI tools for parts of the coding and debugging. The choice of problem, the dataset experiments, the model comparisons and the decisions about what worked and what failed are my own project work.",
      licence: "MIT licence.",
      linksTitle: "Where everything is",
      links: {
        github: { name: "GitHub", text: "Source code, tests and CI." },
        pypi: { name: "PyPI", text: "Latest release: {version}." },
        huggingface: {
          name: "Hugging Face",
          text: "Most experiment models from EXP-006 to EXP-019 and the classifiers.",
        },
        datasets: { name: "Dataset origins", text: "Where each training dataset comes from, with licences." },
        log: { name: "Experiment log", text: "All experiments, with settings and limitations." },
      },
    },
  },
};

export type Dictionary = typeof en;
