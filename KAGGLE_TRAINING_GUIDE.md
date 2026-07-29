# Kaggle Training Guide

## Uploads

### Notebook 1: YOLO11x Teacher

Add the dataset ZIP as a Kaggle input:

```text
merged_mira_balanced (2).zip
```

Paste and run `kaggle/notebook_1_teacher_yolo11x.py` as one cell.

Download the output:

```text
/kaggle/working/teacher_yolo11x.zip
```

### Notebook 2: YOLO26n Baseline

Add the same dataset ZIP:

```text
merged_mira_balanced (2).zip
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

Add two Kaggle inputs:

```text
merged_mira_balanced (2).zip
teacher_yolo11x.zip
```

Run:

```text
kaggle/notebook_3_distill_yolo26n.py
```

Download:

```text
/kaggle/working/distill_yolo26n_results.zip
```

## Training Settings

- 120 epochs
- No `patience` or early stopping
- Teacher time budget: 8.8 hours
- Baseline time budget: 8.8 hours
- Distillation time budget: 10.8 hours
- Total planned GPU usage: 28.4 hours

If a session ends before epoch 120, rerun the same cell. It resumes from `last.pt`.

## Important

The dataset ZIP contains a portable `dataset.yaml`, but each script rewrites it again after extraction so paths remain relative on Kaggle.

Do not run the old Phase 0 download pipeline. The dataset has already been prepared locally.
