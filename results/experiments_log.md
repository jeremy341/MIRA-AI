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
* **Dataset Source:** Hand-collected custom images (`data/classes/`), 4 classes only (no trash)

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
* **Dataset Source:** Hand-collected custom images (`data/classes/`), 4 classes only (no trash)

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
* **Dataset Source:** Hand-collected custom images (`data/classes/`), 4 classes only (no trash)
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

---

## EXP-004: Quantized TFLite Model (Full INT8)
* **Date:** July 2, 2026
* **Commit Hash:** `[your_commit_hash]`
* **Architecture:** MobileNetV2 (Quantized to 8-bit Integer Calibration)
* **Dataset Size:** 796 images (fully scaled)
* **Dataset Source:** Hand-collected custom images (`data/classes/`), 4 classes only (no trash)
* **Calibration Set:** 100 representative calibration samples

### Quantitative Metrics
* **Model Size on Disk:** 2.61 MB (Compressed from 23.48 MB Keras Binary)
* **Compression Ratio:** 9.0x smaller (70% smaller than standard FP32 TFLite)
* **Average CPU Latency:** 10.32 ms per image (Theoretical throughput: ~97 FPS)
* **Validation Accuracy:** 87.42% (0.8735)

### Classification Report (Val Set)
| Class | Precision | Recall | F1-Score | Support |
|---|---|---|---|---|
| glass | 0.93 | 0.93 | 0.93 | 43 |
| metal | 0.75 | 1.00 | 0.85 | 41 |
| paper | 1.00 | 0.64 | 0.78 | 42 |
| plastic | 0.91 | 0.94 | 0.93 | 33 |

---

## EXP-005: YOLOv8-Nano Object Detection
* **Date:** July 3, 2026
* **Architecture:** YOLOv8-Nano (PyTorch .pt)
* **Dataset Size:** ~3,300 images (Custom + TrashNet)
* **Dataset Source:** Hand-collected custom tabletop images + Stanford TrashNet (Canny-edge auto-labeled bounding boxes)
* **Target Classes:** glass, metal, paper, plastic, trash

### Quantitative Metrics
* **mAP50 (Overall):** 82.3%
* **mAP50-95:** 69.8%
* **Strongest Class:** Metal (0.941)
* **Weakest Class:** Trash (0.764)
* **Inference Latency (Cloud GPU):** 1.9 ms

### Observation
Transitioning to an object detector successfully enabled simultaneous detection of multiple items. Synthetic auto-labeling via Canny-Edge provided sufficient bounding box accuracy for model convergence.

## EXP-006: Stage B Object Detection Fusion
* **Date:** July 4, 2026
* **Architecture:** YOLOv8-Nano (PyTorch)
* **Cloud Platform:** Google Colab (T4 GPU)
* **Training Time:** 3.3 hours (100 Epochs)
* **Dataset Source:** Stanford TrashNet (clean background) + Roboflow Trash Detection Dataset (64 classes, outdoor/wild, remapped to 5 MIRA classes)

### Methodology
Transitioned from image classification (one label per image) to spatial object detection (bounding boxes). 
Fused TrashNet (clean background) with 64-class Roboflow "Wild Data" remapped to 5 MIRA classes: 
[Glass, Metal, Paper, Plastic, Trash].

### Quantitative Results
* **mAP50 (Global):** 39.4% (on highly complex wild data)
* **Real-time Performance (Tabletop):** Stable >90% confidence for Plastic and Metal
* **System Latency:** ~40.4 ms per frame on local CPU
* **Effective FPS:** ~15.6 FPS (sufficient for mechatronic sorting)

### Qualitative Observations
Model is highly robust against background textures (keyboard, laptop, white desk). 
Edge Case identified: "End-on" metal cans (opening facing camera) lead to detection drop-out.


---

## EXP-007: YOLOv8-Nano INT8 Quantization (LiteRT)
* **Date:** July 4, 2026
* **Architecture:** YOLOv8-Nano (TFLite INT8)
* **Base Model:** EXP-006 (`mira_detector_wild.pt`)

### Quantitative Metrics
* **Original Intermediate Graph Size:** 11.69 MB
* **Quantized INT8 Model Size:** 3.18 MB
* **Compression Ratio:** 3.7x smaller
* **Calibration Data:** `yolo_data/dataset.yaml`

### Observation
Static quantization (INT8 weights and activations) successfully applied using the Ultralytics LiteRT export pipeline via Google Colab (Linux environment). The model footprint of 3.18 MB is well within the memory constraints of the target edge hardware (Raspberry Pi).

---

## EXP-008: Specialized Tabletop YOLOv8-Nano (Data-Centric Optimization)
* **Date:** July 5, 2026
* **Commit Hash:** `[your_commit_hash]`
* **Architecture:** YOLOv8-Nano (PyTorch)
* **Dataset Size:** ~3,000 images (Custom Tabletop + Labeled TrashNet)
* **Dataset Source:** Hand-collected custom tabletop images + Stanford TrashNet (human-annotated bounding boxes, corrupted auto-labeled images removed)
* **Training Platform:** Google Colab (NVIDIA Tesla T4 GPU)
* **Training Time:** 1.661 hours (50 epochs)

### Hyperparameters
* **Learning Rate (lr0):** 0.01 (Adam)
* **Image Size (imgsz):** 640 (Training) / 320 (Inference Target)
* **Batch Size:** 16
* **Loss Functions:** Complete IoU (box_loss), BCE (cls_loss), DFL (dfl_loss)

### Final Epoch Metrics (Epoch 50/50)
* **Box Loss:** 0.6241
* **Class Loss (cls_loss):** 0.7603
* **Distribution Focal Loss (dfl_loss):** 0.9023
* **Validation Accuracy (mAP50):** 39.6% (0.3960)
* **mAP50-95:** 32.9% (0.3290)

### Class-Specific Validation Performance (mAP50)
* **Glass:** 38.8% (0.3880)
* **Metal:** 51.0% (0.5100)
* **Paper:** 36.6% (0.3660)
* **Plastic:** 64.4% (0.6440)
* **Trash:** 7.1% (0.0711)

### Speed & Performance (GPU)
* **Preprocess:** 0.2 ms
* **Inference Latency:** 2.1 ms
* **Postprocess:** 3.1 ms

### Observation & Scientific Value
EXP-008 represents a Data-Centric AI optimization. By purging the corrupted auto-labeled custom images and training strictly on human-annotated, high-quality bounding boxes, the model converged to the exact same accuracy profile as the 100-epoch noisy model (EXP-006) in half the training time. The sharp contrast in classification confidence confirms that removing spatial label noise is more effective than brute-force longer training cycles.


---

## EXP-009: Pristine Tabletop YOLOv8-Nano (Verified Baseline)
* **Date:** July 5, 2026
* **Architecture:** YOLOv8-Nano (PyTorch .pt)
* **Dataset Size:** ~2,527 images (Pristine TrashNet, Auto-labeled via Canny Edge)
* **Dataset Source:** Stanford TrashNet only (clean white-background tabletop images, Canny-edge auto-labeled bounding boxes)
* **Training Platform:** Kaggle Notebooks (NVIDIA Tesla T4 GPU)
* **Training Time:** 0.309 hours (50 epochs)

### Quantitative Metrics
* **Total Parameters:** 3,006,623 (6.2 MB)
* **Overall mAP50:** 72.8%
* **mAP50-95:** 58.3%
* **Inference Latency (GPU):** 1.4 ms

### Class-Specific Validation Performance (mAP50)
* **Glass:** 72.9%
* **Metal:** 84.8%
* **Paper:** 77.7%
* **Plastic:** 64.5%
* **Trash:** 63.9%

### Observation
This run represents the final, verified baseline of MIRA's Stage B software. By purging all noisy custom desktop images that caused contour border leakage, overall mAP50 was raised from 39.6% to 72.8%. The massive improvements across the board (specifically paper and trash) validate our data-centric approach to model engineering.

---

## EXP-010: Quantized Wild YOLOv8-Nano (INT8 Calibration)
* **Date:** July 6, 2026
* **Architecture:** YOLOv8-Nano (TFLite INT8 / LiteRT)
* **Base Model:** EXP-006 (`mira_detector_wild.pt`)
* **Dataset Size:** ~3,300 images (Custom + TrashNet + Remapped Roboflow)
* **Dataset Source:** Hand-collected custom images + Stanford TrashNet + Roboflow Trash Detection Dataset (64 classes, outdoor/wild, remapped to 5 MIRA classes)
* **Calibration Set:** 100 representative samples from `mira_wild_data`

### Quantitative Metrics
* **Original Intermediate Graph Size:** 11.62 MB
* **Quantized INT8 Model Size:** 3.16 MB
* **Compression Ratio:** 3.7x smaller
* **Inference Speed (Cloud GPU):** 2.1 ms
* **Calibration Dataset Config:** `yolo_data/dataset.yaml` (5 classes)

### Observation
Static quantization (8-bit integer weights and activations) successfully applied using the Ultralytics LiteRT export pipeline in a Linux environment. The model footprint of 3.16 MB is fully optimized for CPU-only edge environments (Raspberry Pi), resolving the platform compiler conflicts encountered on Windows host systems.

---

## EXP-011: Tabletop-Excluded YOLOv8-Nano (Wild-Data Only)
* **Date:** July 6, 2026
* **Commit Hash:** `[your_commit_hash]`
* **Architecture:** YOLOv8-Nano (PyTorch .pt)
* **Dataset Size:** 3,365 images (Pristine TACO-remaped Wild Dataset)
* **Dataset Source:** TACO (Trash Annotations in Context) — outdoor/wild litter images, 60 COCO categories remapped to 5 MIRA classes
* **Training Platform:** Kaggle Notebooks (NVIDIA Tesla T4 GPU)
* **Training Time:** 0.309 hours (100 epochs)

### Hyperparameters
* **Learning Rate (lr0):** 0.01 (Adam)
* **Image Size (imgsz):** 640 (Training) / 320 (Inference Target)
* **Batch Size:** 16

### Final Epoch Validation Metrics (mAP50)
* **Overall mAP50:** 35.0% (0.3500)
* **mAP50-95:** 29.0% (0.2900)
* **Inference Latency (GPU):** 1.8 ms

### Class-Specific Validation Performance (mAP50)
* **Glass:** 27.3%
* **Metal:** 46.4%
* **Paper:** 31.4%
* **Plastic:** 62.3%
* **Trash:** 7.5%

### Observation
EXP-011 represents an investigation into pure out-of-distribution generalization. By excluding local tabletop images and training exclusively on complex outdoor packaging waste (litter), the global mAP50 dropped to 35.0% on the diverse test set. While overall precision remains lower due to extreme background occlusions, the model successfully generalized basic material geometries.

---

## EXP-012: Quantized Wild-Only YOLOv8-Nano (INT8 Calibration)
* **Date:** July 6, 2026
* **Commit Hash:** `[your_commit_hash]`
* **Architecture:** YOLOv8-Nano (TFLite INT8 / LiteRT)
* **Base Model:** EXP-011 (`mira_detector_wild_v2.pt`)
* **Dataset Source:** Same as EXP-011 (TACO only)
* **Calibration Dataset:** `wild_data/data.yaml`

### Quantitative Metrics
* **Original Model Size:** 11.62 MB (11.62 MiB)
* **Quantized INT8 Model Size:** 3.16 MB (3.16 MiB)
* **Compression Ratio:** 3.7x smaller (72.8% smaller footprint)
* **Inference Speed (Cloud GPU):** 2.1 ms

### Observation
The EXP-010 model was successfully quantized using its original high-variance training distribution as the representative calibration set. Unlike previous runs calibrated on clean white-background data, this run used the proper activation dynamic range. The successful compile of 3.16 MB establishes the performance limits of complex background processing on low-power CPU architectures.

---

## EXP-013: YOLO11n on TACO + TrashNet (mira_v2 Fusion Dataset)
* **Date:** July 11, 2026
* **Architecture:** YOLO11n (PyTorch .pt -> TFLite INT8 / LiteRT)
* **Dataset Size:** 4,024 images (1,497 TACO wild + 2,527 TrashNet tabletop, full-image bbox)
* **Dataset Source:** TACO (Trash Annotations in Context, outdoor/wild) + Stanford TrashNet (clean tabletop), fused into mira_v2 dataset
* **Training Platform:** Kaggle Notebooks (NVIDIA Tesla T4 GPU)
* **Training Time:** 2.728 hours (120 epochs, best epoch 103)

### Hyperparameters
* **Learning Rate (lr0):** 0.01 (SGD auto)
* **Image Size (imgsz):** 640
* **Batch Size:** 32
* **Framework:** Ultralytics 8.4.92 | Python-3.12.13 | torch-2.10.0+cu128

### Model Summary
* **Total Parameters:** 2,583,127 (5.5 MB)
* **Layers:** 101 (fused)
* **FLOPs:** 6.3 GFLOPs

### Final Epoch Metrics (Epoch 120/120)
* **Train Box Loss:** 0.3654
* **Train Class Loss:** 0.4173
* **Train DFL Loss:** 0.8878
* **Val Box Loss:** 0.5693
* **Val Class Loss:** 0.9511
* **Val DFL Loss:** 0.5637

### Best Epoch Validation (Epoch 103)
* **Overall mAP50:** 55.1% (0.551)
* **mAP50-95:** 49.8% (0.498)
* **Mean Precision:** 0.789
* **Mean Recall:** 0.468

### Class-Specific Validation Performance (mAP50)
| Class | mAP50 |
|---|---|
| Glass | 56.5% |
| Metal | 67.9% |
| Paper | 79.3% |
| Plastic | 55.6% |
| Trash | 15.6% |

### Speed & Performance (GPU)
* **Preprocess:** 1.0 ms
* **Inference Latency:** 3.6 ms
* **Postprocess:** 0.9 ms

### Quantization (INT8 LiteRT Export)
* **Original Model Size:** 10.14 MiB
* **Quantized INT8 Model Size:** 2.90 MiB
* **Compression Ratio:** 3.5x smaller
* **Export Time:** 598.4 s

### Observation
EXP-013 upgrades the architecture from YOLOv8-Nano to YOLO11n, which is both smaller (2.58M vs 3.01M parameters) and more efficient. Training on the fused mira_v2 dataset for 120 epochs yields a balanced 55.1% mAP50 -- a significant +20 point improvement over the wild-only baseline (EXP-011: 35.0%) while remaining realistic for cluttered scenes (unlike the inflated 72.8% tabletop-only EXP-009). Paper remains the strongest class (79.3% mAP50) due to large surface area and clear texture, while trash continues to struggle (15.6%) due to extreme intra-class diversity. The quantized 2.9 MB INT8 model is well-suited for Raspberry Pi edge deployment.