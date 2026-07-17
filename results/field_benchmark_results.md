# Field Benchmark Results — Image-Level Class-Presence F1

**Date:** July 13, 2026  
**Dataset:** mira_v2 (TACO + TrashNet, 805 validation images, 5 classes)  
**Confidence threshold:** 0.5  
**Models tested:** 11 detection models  
**Metric type:** Image-level class-presence F1 (binary: does the class exist in the image?), NOT detection mAP50

---

## Overall Comparison

> **Note:** These are image-level class-presence F1 scores (binary: does the class exist in the image?), NOT detection mAP50. Detection mAP50 is reported separately in experiments_log.md.

| Model | TP | FP | FN | Precision | Recall | F1 |
|---|---|---|---|---|---|---|
| **mira_exp014.pt** | 669 | 51 | 170 | **92.9%** | **79.7%** | **85.8%** |
| mira_exp014_int8.tflite | 492 | 20 | 347 | 96.1% | 58.6% | 72.8% |
| mira_exp015.pt | 572 | 68 | 267 | 89.4% | 68.2% | 77.3% |
| mira_exp015_int8.tflite | 579 | 67 | 260 | 89.6% | 69.0% | 78.0% |
| mira_exp013.pt | 589 | 82 | 250 | 87.8% | 70.2% | 78.0% |
| mira_exp013_int8.tflite | 475 | 30 | 364 | 94.1% | 56.6% | 70.7% |
| mira_exp011.pt | 624 | 94 | 215 | 86.9% | 74.4% | 80.2% |
| mira_exp011_int8.tflite | 0 | 0 | 839 | 0.0% | 0.0% | **0.0%** |
| mira_exp009_int8.tflite | 624 | 107 | 215 | 85.4% | 74.4% | 79.5% |
| mira_exp006.pt | 696 | 139 | 259 | 83.4% | 72.9% | 77.8% |
| mira_exp006_int8.tflite | 375 | 197 | 473 | 65.6% | 44.2% | 52.8% |

---

## Per-Class Breakdown (best model: mira_exp014.pt)

| Class | Precision | Recall | F1 |
|---|---|---|---|
| Glass | 93.0% | 86.9% | 89.9% |
| Metal | 89.2% | 81.1% | 84.9% |
| Paper | 94.6% | 87.2% | 90.7% |
| Plastic | 96.8% | 82.3% | 88.9% |
| Trash | 75.5% | 42.0% | 54.0% |

## Key Findings

> **Important:** The F1 scores in the table above measure image-level class-presence (binary: is the class present at all in the image?). This is a different metric from detection mAP50, which measures bounding-box localization quality. A model can have high class-presence F1 but low mAP50 if its detections are poorly localized.

1. **mira_exp014.pt (EXP-014) is the best model overall** with 85.8% F1 — highest on every metric.
2. **Trash is the weakest class** across all models (best: 54.0% F1 by EXP-014). Most models hover around 30-37%.
3. **mira_exp011_int8.tflite needs a lower confidence threshold** — at default conf=0.5 it produces 0 detections because INT8 quantization shifts scores downward. At conf=0.25 it performs normally (1.6 detections/image vs FP32's 1.9). The benchmark auto-caps INT8 models to conf=0.25 going forward.
4. **INT8 quantization costs ~13 pp F1** on average (85.8% → 72.8% for EXP-014).
5. **EXP-013 (TACO+TrashNet) and EXP-015 (+WaRP) are similar** at ~77-78% F1. Adding WaRP doesn't help on this dataset.
6. **EXP-009 (int8) at 79.5% F1** outperforms its reputation — though this benchmark uses mira_v2 which may differ from its inflated white-background validation.

---

## EXP-016 Results

**WaRP only — YOLO11n**

| Metric | Value |
|---|---|
| mAP50 | 58.8% |
| mAP50-95 | 43.2% |
| Precision | 62.1% |
| Recall | 55.9% |
| Training time | 1.07 hours (120 epochs, T4 GPU) |
| INT8 size | 2.90 MB |

**Per-class mAP50:**
- Glass: **77.7%** (strongest)
- Metal: 42.1%
- Paper: 42.2%
- Plastic: **73.1%**
- Trash: — (no trash in WaRP)

*Run `.\mira field-bench --dataset datasets/mira_warp_only` to get real precision/recall for this model.*
