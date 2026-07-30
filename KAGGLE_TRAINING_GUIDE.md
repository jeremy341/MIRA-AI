# Kaggle Training Guide

## Prepare The Dataset

From the repository root, build and archive the dataset:

```powershell
py scripts/build_balanced_dataset.py
Compress-Archive -Path datasets\merged_mira_balanced -DestinationPath merged_mira_balanced.zip -Force
```

The generated `dataset.yaml` uses `images/train`, `images/val`, and
`images/test` relative to the YAML file.

## Upload And Run

### Notebook 1: YOLO11n Exploratory/Reference Teacher

YOLO11n is intentionally retained because it was selected under the limited
Kaggle quota. It is an exploratory/reference teacher for this run, not a
high-capacity teacher. Any comparison must account for that limitation.

Add the dataset ZIP as a Kaggle input:

```text
merged_mira_balanced.zip
```

Paste and run `kaggle/notebook_1_teacher_yolo11n.py` as one cell.

Download the output:

```text
/kaggle/working/teacher_yolo11n.zip
```

### Notebook 2: YOLO26n Baseline

Add the same dataset ZIP:

```text
merged_mira_balanced.zip
```

Run this notebook in parallel with Notebook 1:

```text
kaggle/notebook_2_baseline_yolo26n.py
```

Download the output:

```text
/kaggle/working/baseline_yolo26n.zip
```

### Notebook 3: Distilled YOLO26n

After Notebook 1 has produced its artifact, add exactly these two Kaggle inputs:

```text
merged_mira_balanced.zip
teacher_yolo11n.zip
```

Run:

```text
kaggle/notebook_3_distill_yolo26n.py
```

At startup, Notebook 3 installs Ultralytics in the same way as Notebooks 1 and 2
and immediately validates support for `distill_model`, `dis`, and `MuSGD`. This
compatibility check runs before dataset extraction or training. Distillation is
only expected to start if the installed release passes the check; otherwise the
notebook fails with the installed version and the unsupported capability. Do not
assume that an arbitrary current or preinstalled Ultralytics release supports
this training interface.

If compatibility validation and training complete, download:

```text
/kaggle/working/distill_yolo26n_results.zip
```

## Training Settings

- 120 epochs
- No `patience` or early stopping
- Exploratory/reference YOLO11n teacher time budget: 8.8 hours
- Baseline time budget: 8.8 hours
- Distillation time budget: 10.8 hours
- Total planned GPU usage: 28.4 hours

Automatic resume works only while the same Kaggle session still has `last.pt` in
`/kaggle/working`. To resume in a new session, attach the ZIP produced by the
interrupted run as an additional Kaggle input, then run the same script:

```text
Notebook 1: teacher_yolo11n.zip
Notebook 2: baseline_yolo26n.zip
Notebook 3: distill_yolo26n_results.zip (plus teacher_yolo11n.zip)
```

The scripts restore the attached run's `last.pt`. They fail if multiple matching
dataset, checkpoint, or teacher artifacts are attached.

Notebook 3 also refuses to begin a new long run when its installed Ultralytics
release lacks the required distillation arguments or optimizer support.

## Important

The dataset ZIP contains a portable `dataset.yaml` whose split paths are relative
to the YAML location. Each Kaggle script rewrites those split paths as absolute
paths after extraction.

Do not run the old Phase 0 download pipeline. The dataset has already been prepared locally.
