/**
 * English copy of the Package page. This file DEFINES the shape (`PackageCopy`); de.ts must match it key for key.
 *
 * Inline markup (rendered by components/ui-notebook/Rich.tsx): ==marker==, `code`, [label](href).
 * Placeholders look like {name}. No em dashes or en dashes anywhere.
 *
 * Language-neutral data (command names, flags, file names, sizes, scores) lives in
 * components/package/package-data.ts. Only words live here.
 */
export const packageEn = {
  header: {
    title: "The mira-ai package",
    lede: "`mira-ai` is the open-source Python package behind MIRA: three trained YOLO11n detectors and a `mira` command that runs them on your webcam. It finds glass, metal, paper, plastic and trash and draws a box around each.",
    installLabel: "Copy the install command",
    installNote: "That is the whole install. The steps below add a virtual environment.",
    factsLabel: "Package facts",
    facts: {
      pypi: "Latest on PyPI",
      python: "Python",
      pythonValue: "3.11 or 3.12",
      pythonNote: "PyPI declares {requires}. The repository caps it at <3.13, which is what the dependencies support.",
      licence: "Licence",
      bundled: "In the wheel",
      bundledValue: "3 detector weights, no model download",
    },
    versionNote:
      "The repository is already at {repoVersion}, which is not released. `pip install mira-ai` gives you {version}.",
    contentsLabel: "On this page",
  },
  contents: {
    install: "Install",
    quickstart: "Quickstart",
    judged: "How a detection is judged",
    commands: "Commands",
    models: "Models",
    requirements: "Requirements",
    status: "Status",
    links: "Links",
  },
  install: {
    title: "Install",
    p1: "You need Python 3.11 or 3.12 and a virtual environment. The package pulls in PyTorch and Ultralytics, so the first install is a large download.",
    windows: {
      label: "Windows PowerShell",
      copyLabel: "Copy the Windows PowerShell install commands",
      note: "These commands come from the project README and were run on Windows PowerShell.",
    },
    unix: {
      label: "macOS and Linux",
      copyLabel: "Copy the macOS and Linux install commands",
      note: "The same steps with the Unix activate script. They are standard venv commands that I have not run.",
    },
  },
  quickstart: {
    title: "Quickstart",
    intro: "Run these in the activated environment, in this order. Each step says what you should see.",
    youSee: "You should see",
    checkInstall: "Check your installation",
    steps: [
      {
        title: "Check that it installed",
        text: "Prints the version of your install.",
        copyLabel: "Copy the version command",
        expected: "One line: `MIRA` and the version number.",
      },
      {
        title: "List the bundled models",
        text: "The weights ship inside the package, so this only lists them. Nothing is downloaded.",
        copyLabel: "Copy the model list command",
        expected:
          "A list headed “Models bundled with mira-ai” with `mira_exp014.pt`, `mira_exp018.pt` and `mira_exp019.pt`, then “No model download is required.”",
      },
      {
        title: "Check the environment",
        text: "Runs five checks and ends with a one-line status.",
        copyLabel: "Copy the doctor command",
        expected:
          "Sections for configuration, hardware, environment, models and datasets, ending in `Status: HEALTHY`. A missing GPU or missing dataset folders are printed as notes and do not fail the check.",
      },
      {
        title: "Start live detection",
        text: "Opens your default camera (index 0) and draws a box on every detected object.",
        copyLabel: "Copy the live detection command",
        expected:
          "A window titled “MIRA Real-Time Multi-Object Detection” with a box, a class name and a confidence on each detected object. Press `q` to close it. Use `--camera 1` for a second camera.",
      },
    ],
    modelNote:
      "`mira_exp014.pt` is the demo default in the README. Swap in `mira_exp019.pt` for the model with the higher validation score, or leave out `--model` to pick from a list.",
    dashboard:
      "For a browser interface, run `mira dashboard` and open `http://127.0.0.1:8000`. The unreleased repository version also supports local JPEG and PNG detection.",
  },
  judged: {
    title: "How a detection is judged",
    p1: "Every box the model finds has a confidence between 0 and 1. `mira live` sorts each one into three outcomes with two thresholds, `--conf` and `--reject`.",
    p2: "Out of the box ==both thresholds are 0.25==, so the uncertain band is empty. Raise `--reject` to use it:",
    exampleCopyLabel: "Copy the example with both thresholds",
    figureCaption:
      "The three outcomes for `--conf 0.25 --reject 0.55`. The value 0.55 is the `reject_threshold` in `mira.yaml`, used here as an example. The command line default for both is 0.25.",
    scaleLabels: { hidden: "hidden", uncertain: "uncertain", labelled: "labelled" },
    tiers: [
      { name: "Below `--conf`", text: "The box is not drawn at all." },
      {
        name: "From `--conf` up to `--reject`",
        text: "The box is drawn and labelled “uncertain” with its confidence, in a different box colour.",
      },
      {
        name: "At or above `--reject`",
        text: "The box is drawn with the class name and its confidence, in the confident box colour.",
      },
    ],
  },
  commands: {
    title: "Command reference",
    intro:
      "The `mira` command has sixteen subcommands, taken from the code. Add `--help` to any of them for the full option list. `mira --version` prints the installed version, and `mira` alone prints the command list.",
    columns: { command: "Command", does: "What it does, and main options (defaults in brackets)" },
    required: "required",
    none: "no options",
    caption: "The sixteen subcommands of `mira`, read from `src/cli`.",
    groups: {
      run: { title: "Run and check", intro: "These work after a plain pip install." },
      develop: {
        title: "Evaluate, data and training",
        intro:
          "Written for a project folder with `datasets/` and `experiments/`, such as a git clone. I have not tried them from a plain pip install.",
      },
    },
    does: {
      live: "Real-time webcam detection in a window. Press q to quit. Without --model it opens an interactive picker.",
      dashboard: "Starts the local dashboard server.",
      models: "Lists the discovered model files with label, type and size.",
      download: "Lists the models bundled with the install. It downloads nothing.",
      doctor: "Checks configuration, hardware, libraries, models and dataset sources, then prints a status.",
      config: "Prints the effective mira.yaml settings.",
      evalYolo: "Validates a detector on a YOLO dataset.",
      benchmark: "Compares several models for accuracy and latency.",
      experiments: "Lists the experiment YAML files in experiments/.",
      datasets: "Lists registered dataset sources.",
      merge: "Merges registered sources into one YOLO dataset.",
      validate: "Checks the structure and labels of a YOLO dataset.",
      train: "Trains a YOLO detector or a classifier.",
      export: "Exports a trained .pt model to TFLite or ONNX.",
      wizard: "Interactive training setup.",
      generate: "Writes a Kaggle or Colab notebook, or Docker files, for a training run.",
    },
  },
  models: {
    title: "Models",
    p1: "Three weights ship inside the wheel: EXP-014, EXP-018 and EXP-019. The other files in the table are optional and come from [Hugging Face](https://huggingface.co/Jeremy341/MIRA-AI). I list them because the tools can read them, but pip does not install them. Run `mira models` to see what your install can load.",
    columns: { file: "File", format: "Format", size: "Size", map50: "mAP50", map5095: "mAP50-95" },
    notRecorded: "not recorded",
    groups: { bundled: "In the pip package", separate: "Optional files on Hugging Face" },
    notes: {
      exp014: "Default demo model in the README. Validated on a different split of 1,588 images.",
      exp018: "Clean, class-balanced data.",
      exp019: "Repeat of EXP-018 with the same setup.",
      exp019Int8320: "Float32 input and output, integer weights.",
    },
    tableLabel: "Scrolls sideways on small screens",
    caption:
      "The detector files. mAP50 scores how well the predicted boxes match the labelled ones (at least 50% overlap), and mAP50-95 uses stricter overlaps. Both are validation scores from the experiment log, not real-world accuracy. Sizes are file sizes in decimal megabytes.",
    splitNote:
      "EXP-018 and EXP-019 were scored on the same 415 images of the TrashNet tabletop split. EXP-014 used a different split of 1,588 images, so its 60.7% is not comparable to the others.",
  },
  requirements: {
    title: "Requirements and extras",
    requirementsTitle: "Requirements",
    items: {
      python: {
        label: "Python",
        text: "3.11 or 3.12. PyPI declares `>=3.11`, the repository caps it at `<3.13`, which is what the dependencies support, and its CI runs 3.11 and 3.12.",
      },
      camera: { label: "Camera", text: "A webcam for `mira live`. The other commands do not need one." },
      gpu: { label: "GPU", text: "Optional. `mira doctor` reports whether CUDA is found." },
      network: { label: "Network", text: "Only for the install." },
    },
    extrasTitle: "Extras",
    extras: {
      train: "TensorFlow 2.10 or newer, used by the training strategies.",
      analysis: "matplotlib, pandas, scikit-learn and scipy for analysing results.",
      all: "Both of the above.",
      dev: "All of the above plus pytest, ruff and mypy, for working on the package itself.",
    },
    extrasNote: "There is no separate dashboard extra: FastAPI and uvicorn are part of the base install.",
  },
  status: {
    title: "What works, and what is not tested",
    intro: "Nothing here is a claim about real-world accuracy.",
    worksTitle: "In the package today",
    works: [
      "Three detector weights (EXP-014, EXP-018, EXP-019) ship inside the package. No account and no model download.",
      "Live webcam detection with a confidence and a reject threshold you can set per run.",
      "A local dashboard served from your own machine. It is a development tool.",
      "Export of a trained model to TFLite or ONNX, and tools to build, validate and benchmark datasets.",
    ],
    openTitle: "Not tested or not built",
    open: [
      "Speed and accuracy on a Raspberry Pi are not measured. The INT8 TFLite file exists, but there are no numbers for it on that hardware.",
      "The robot or sorting arm is not built. The package detects objects and does not sort anything.",
      "There is no real-camera evaluation. The 1,375-image test split was not run for EXP-019.",
      "Plastic is the weak class (64.4% recall in EXP-019). Crumpled paper, cans seen from the opening and overlapping objects are known failure cases.",
      "The macOS and Linux install commands are standard venv steps that I have not run.",
      "The dashboard has unit tests, but I have not recorded an end-to-end check with a camera and a browser, and I have not tried it from an installed wheel.",
    ],
  },
  links: {
    title: "Links and downloads",
    downloads: {
      title: "Hugging Face downloads",
      allTime: "all time",
      last30: "{n} in the last 30 days",
      honest:
        "This counts file fetches from the model repository on Hugging Face, not unique people. PyPI installs are not included.",
      status: { checking: "checking", live: "live", cached: "cached", fallback: "built-in value" },
      statusLong: {
        checking: "Checking Hugging Face for the current count. Showing the last known value.",
        live: "Live count, fetched from Hugging Face just now.",
        cached: "Cached count. Hugging Face could not be reached, so this is the last known value.",
        fallback:
          "Built-in count. Hugging Face could not be reached and no earlier value was stored, so this is the number written into the site.",
      },
    },
    listTitle: "Where everything is",
    items: {
      pypi: { name: "PyPI", text: "Latest release: {version}." },
      github: { name: "GitHub", text: "Source code, tests, CI and issues." },
      huggingface: { name: "Hugging Face", text: "Optional model files and exports." },
      docs: { name: "Docs", text: "Commands and configuration in depth." },
      research: { name: "Research", text: "The experiments behind the models." },
      licence: { name: "MIT licence", text: "Free to use, change and share." },
    },
  },
};

export type PackageCopy = typeof packageEn;
