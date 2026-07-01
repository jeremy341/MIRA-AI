# MIRA AI — Global Experiment Log
**Project:** Machine Intelligence for Recycling Automation (MIRA)
**Domain:** computer vision / edge ai
**Target Hardware:** ESP32 / Raspberry Pi Zero 2W

---

## EXP-001: Baseline Custom CNN (3-Layer)
* **Date:** June 26, 2026
* **Commit Hash:** `04ef1f0`
* **Architecture:** 3x Conv2D (16/32/64) + Dropout(0.2) + Dense(128)
* **Dataset Size:** 126 images (highly restricted)

### Quantitative Metrics
* **Total Parameters:** 3,989,156 (15.22 MB)
* **Training Time:** ~70 seconds (20 epochs @ ~3.5s/epoch)
* **Training Accuracy:** 73.61% | **Training Loss:** 0.9189
* **Validation Accuracy:** 61.00% | **Validation Loss:** 1.0633

### Classification Report (Val Set)
| Class | Precision | Recall | F1-Score | Support |
|---|---|---|---|---|
| glass | 0.92 | 0.77 | 0.84 | 43 |
| metal | 0.49 | 0.80 | 0.61 | 41 |
| paper | 0.50 | 0.07 | 0.12 | 42 |
| plastic | 0.56 | 0.85 | 0.67 | 33 |

---

## EXP-002: Transfer Learning (MobileNetV2 Frozen Base)
* **Date:** June 27, 2026
* **Commit Hash:** `[your_commit_hash]`
* **Architecture:** MobileNetV2 (weights: ImageNet, frozen) + Custom head [Dense(128) + Dropout(0.2)]
* **Dataset Size:** 796 images (fully scaled)

### Quantitative Metrics
* **Total Parameters:** 2,263,084 total (5,124 trainable, 2,257,984 non-trainable)
* **Training Time:** ~165 seconds (20 epochs @ ~8s/epoch)
* **Training Accuracy:** 74.73% | **Training Loss:** 0.6917
* **Validation Accuracy:** 84.28% | **Validation Loss:** 0.5659

### Classification Report (Val Set)
| Class | Precision | Recall | F1-Score | Support |
|---|---|---|---|---|
| glass | 0.91 | 0.98 | 0.94 | 43 |
| metal | 0.86 | 0.76 | 0.81 | 41 |
| paper | 0.77 | 0.81 | 0.79 | 42 |
| plastic | 0.82 | 0.82 | 0.82 | 33 |

---

## EXP-003: Two-Stage Fine-Tuning (MobileNetV2 Unfrozen)
* **Date:** June 27, 2026
* **Commit Hash:** `[your_commit_hash]`
* **Architecture:** MobileNetV2 (unfrozen from layer 100) + Custom head [Dense(128) + Dropout(0.2)]
* **Dataset Size:** 796 images (fully scaled)
* **Hyperparameters:** Stage 2 learning_rate = `1e-5` (Adam)

### Quantitative Metrics
* **Total Parameters:** 2,263,108 total (1,866,564 trainable, 396,544 non-trainable)
* **Training Time:** ~177 seconds (15 epochs @ ~11s/epoch)
* **Training Accuracy:** 91.84% | **Training Loss:** 0.2575
* **Validation Accuracy:** 87.42% | **Validation Loss:** 0.3148

### Classification Report (Val Set)
| Class | Precision | Recall | F1-Score | Support |
|---|---|---|---|---|
| glass | 0.93 | 0.95 | 0.94 | 43 |
| metal | 0.77 | 0.98 | 0.86 | 41 |
| paper | 0.96 | 0.64 | 0.77 | 42 |
| plastic | 0.89 | 0.94 | 0.91 | 33 |