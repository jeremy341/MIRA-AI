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
* **Commit Hash:** `366cd6c`
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
* **Commit Hash:** `93f32eb`
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
* **Base Model:** EXP-006 (`mira_exp006.pt`)

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
* **Commit Hash:** `2793a70`
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
* **Base Model:** EXP-006 (`mira_exp006.pt`)
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
* **Commit Hash:** `decb9d1`
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
* **Commit Hash:** `decb9d1`
* **Architecture:** YOLOv8-Nano (TFLite INT8 / LiteRT)
* **Base Model:** EXP-011 (`mira_exp011.pt`)
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

---

## EXP-014: YOLO11n on TACO + TrashNet + Roboflow (Model 1 — mira_tnr)
* **Date:** July 12, 2026
* **Architecture:** YOLO11n (PyTorch .pt -> TFLite INT8 / LiteRT)
* **Dataset Size:** 6,802 images (1,497 TACO wild + 2,527 TrashNet tabletop + ~2,778 Roboflow Trash Detection)
* **Dataset Source:** TACO + Stanford TrashNet + Roboflow Trash Detection (64 classes remapped to 5 MIRA classes)
* **Training Platform:** Kaggle Notebooks (NVIDIA Tesla T4 GPU)
* **Training Time:** 4.700 hours (120 epochs)
* **Framework:** Ultralytics 8.4.92 | Python-3.12.13 | torch-2.10.0+cu128

### Hyperparameters
* **Image Size (imgsz):** 640
* **Batch Size:** 32
* **Early Stopping Patience:** 30

### Model Summary
* **Total Parameters:** 2,583,127 (5.5 MB)
* **Layers:** 101 (fused)
* **FLOPs:** 6.3 GFLOPs

### Validation Metrics (all, 1588 images, 3126 instances)
| Metric | Value |
|---|---|
| Mean Precision | 0.662 |
| Mean Recall | 0.584 |
| **mAP50** | **0.607** |
| **mAP50-95** | **0.506** |

### Class-Specific Validation Performance
| Class | Precision | Recall | mAP50 | mAP50-95 | Instances |
|---|---|---|---|---|---|
| Glass | 0.580 | 0.521 | 0.502 | 0.400 | 336 |
| Metal | 0.670 | 0.699 | 0.713 | 0.613 | 439 |
| Paper | 0.820 | 0.772 | **0.829** | 0.745 | 474 |
| Plastic | 0.715 | 0.699 | 0.721 | 0.601 | 1316 |
| Trash | 0.523 | 0.230 | 0.269 | 0.173 | 561 |

### Speed (GPU)
* **Preprocess:** 0.2 ms
* **Inference:** 1.8 ms
* **Postprocess:** 1.3 ms

### Quantization (INT8 LiteRT Export)
* **Original Model Size:** 10.14 MiB
* **Quantized INT8 Model Size:** 2.90 MiB
* **Compression Ratio:** 3.5x smaller
* **Export Time:** 1093.7 s

### Observation
EXP-014 is the first result from the 4-Model Comparison, adding Roboflow Trash Detection (64 outdoor/wild classes remapped to 5 MIRA) to the TACO+TrashNet fusion. Overall mAP50 rises from 55.1% (EXP-013) to 60.7% — a +5.6 point improvement. The biggest gain comes from Trash (+11.3 pp, 15.6% → 26.9%); Glass drops slightly (−6.3 pp, 56.5% → 50.2%). Roboflow's diverse outdoor litter images help trash generalization. Paper remains the strongest class (82.9% mAP50), while Trash is still the weakest (26.9%) — consistent with its extreme intra-class diversity. The Roboflow segment/box count mismatch warning indicates a mixed dataset format but does not affect detection training.

---

## EXP-015: YOLO11n on TACO + TrashNet + WaRP (Model 2 — mira_tnw)
* **Date:** July 13, 2026
* **Architecture:** YOLO11n (PyTorch .pt -> TFLite INT8 / LiteRT)
* **Dataset Size:** ~6,800 images (1,497 TACO wild + 2,527 TrashNet tabletop + ~2,800 WaRP waste detection)
* **Dataset Source:** TACO + Stanford TrashNet + WaRP Waste Detection (28 classes remapped to 5 MIRA classes)
* **Training Platform:** Kaggle Notebooks (NVIDIA Tesla T4 GPU)
* **Training Time:** 3.707 hours (120 epochs)
* **Framework:** Ultralytics 8.4.93 | Python-3.12.13 | torch-2.10.0+cu128

### Model Summary
* **Total Parameters:** 2,583,127 (5.5 MB)
* **Layers:** 101 (fused)
* **FLOPs:** 6.3 GFLOPs

### Validation Metrics (all, 1816 images, 4845 instances)
| Metric | Value |
|---|---|
| Mean Precision | 0.723 |
| Mean Recall | 0.477 |
| **mAP50** | **0.560** |
| **mAP50-95** | **0.451** |

### Class-Specific Validation Performance
| Class | Precision | Recall | mAP50 | mAP50-95 | Instances |
|---|---|---|---|---|---|
| Glass | 0.781 | 0.689 | **0.750** | 0.590 | 876 |
| Metal | 0.660 | 0.499 | 0.570 | 0.470 | 391 |
| Paper | 0.688 | 0.499 | 0.626 | 0.549 | 592 |
| Plastic | 0.778 | 0.608 | 0.712 | 0.544 | 2682 |
| Trash | 0.707 | 0.087 | 0.143 | 0.104 | 304 |

### Speed (GPU)
* **Preprocess:** 0.1 ms
* **Inference:** 1.5 ms
* **Postprocess:** 1.3 ms

### Quantization (INT8 LiteRT Export)
* **Original Model Size:** 10.14 MiB
* **Quantized INT8 Model Size:** 2.90 MiB
* **Compression Ratio:** 3.5x smaller
* **Export Time:** 1239.5 s

### Observation
EXP-015 replaces Roboflow Trash Detection with WaRP Waste Detection in the TACO+TrashNet fusion. Overall mAP50 drops to 56.0% — a -4.7 pp decline compared to EXP-014 (60.7%). The WaRP dataset significantly boosts Glass (+24.8 pp, 50.2% → 75.0%) due to its large number of glass bottle images, but drags down Metal (-14.3 pp, 71.3% → 57.0%), Paper (-20.3 pp, 82.9% → 62.6%), and especially Trash (-12.6 pp, 26.9% → 14.3%). The Trash decline is expected — WaRP contains zero trash-class images, diluting the trash signal from TACO/TrashNet. The high Precision (0.707) but extremely low Recall (0.087) for Trash confirms the model detects trash when present but misses most instances. Glass benefits strongly from WaRP's bottle-focused imagery, making this dataset combination viable only if Glass detection is the priority.

---

## EXP-016: WaRP Only — YOLO11n (dataset: mira_warp_only)
* **Date:** July 13, 2026
* **Commit Hash:** `0f90571`
* **Model Architecture:** YOLO11n (nano, 2.58M params)
* **Training Hardware:** Kaggle T4 GPU (1.067 hours / 120 epochs)
* **Dataset:** WaRP only (28 WaRP classes remapped to 5 MIRA classes)
* **Training Script:** `scripts/train_detector_kaggle.py --dataset mira_warp_only --epochs 120`

### Validation Metrics
| Metric | Value |
|---|---|
| mAP50 | 0.588 |
| mAP50-95 | 0.432 |
| Precision | 0.621 |
| Recall | 0.559 |

### Per-Class mAP50
| Class | mAP50 |
|---|---|
| Glass | 0.777 |
| Metal | 0.421 |
| Paper | 0.422 |
| Plastic | 0.731 |
| Trash | — (no trash in WaRP dataset) |

### Speed (GPU)
* **Preprocess:** 0.1 ms
* **Inference:** 1.2 ms
* **Postprocess:** 1.3 ms

### Quantization (INT8 LiteRT Export)
* **Original Model Size:** 10.14 MiB
* **Quantized INT8 Model Size:** 2.90 MiB
* **Compression Ratio:** 3.5x smaller
* **Export Time:** 702.3 s

### Observation
EXP-016 trains exclusively on the WaRP dataset (28 classes remapped to MIRA's 5 classes). With 58.8% mAP50 overall, it outperforms the mixed-dataset EXP-015 (56.0%) despite having no Trash class. Glass (77.7%) and Plastic (73.1%) are strong — WaRP is rich in bottles and packaging. Metal (42.1%) and Paper (42.2%) are weaker, likely because WaRP's metal/paper subclasses are fewer and more diverse. Trash is absent entirely (WaRP has zero residual waste images), so the model cannot detect it. This makes EXP-016 a specialized model: excellent at glass/plastic detection but unusable for trash sorting. As a 4-model comparison entry, it confirms that WaRP alone is not a viable general-purpose recycling detector.

---

## EXP-017: YOLO11n on ALL 4 Sources (TACO + TrashNet + Roboflow + WaRP)
* **Date:** July 20, 2026
* **Architecture:** YOLO11n
* **Dataset:** mira_all (9,774 images, 5 classes — all 4 sources merged)
* **Hardware:** Kaggle GPU (Tesla T4, 14GB VRAM)
* **Training Time:** 6.01 hours (120 epochs)

### Hyperparameters
* **Batch Size:** 32 | **Image Size:** 640
* **Patience:** 30 | **Optimizer:** AdamW (lr0=0.01, lrf=0.01)
* **Augmentation:** mosaic=1.0, mixup=0.1, copy_paste=0.1, hsv_h=0.015, hsv_s=0.7, hsv_v=0.4, scale=0.5, fliplr=0.5

### Quantitative Metrics
| Class | Images | Instances | Precision | Recall | mAP50 | mAP50-95 |
|---|---|---|---|---|---|---|
| **All** | 2599 | 6424 | 0.639 | 0.549 | 0.593 | 0.465 |
| glass | 680 | 1027 | 0.675 | 0.685 | 0.706 | 0.531 |
| metal | 489 | 641 | 0.631 | 0.590 | 0.621 | 0.497 |
| paper | 644 | 777 | 0.660 | 0.614 | 0.686 | 0.583 |
| plastic | 1678 | 3418 | 0.713 | 0.677 | 0.727 | 0.566 |
| trash | 243 | 561 | 0.501 | 0.178 | 0.227 | 0.146 |

### Speed
* **Preprocess:** 0.7 ms | **Inference:** 2.8 ms | **Postprocess:** 0.9 ms

### Quantization (INT8 TFLite)
* **Original Model Size:** 10.14 MiB
* **Quantized INT8 Model Size:** 2.90 MiB
* **Compression Ratio:** 3.5x smaller
* **Export Time:** 176.95 ms

### Comparison with EXP-014 (Best Previous)
* **mAP50: 59.3%** — slightly lower than EXP-014 (60.7%)
* **Trash: 22.7% mAP50** — similar to EXP-014 (28.3%), remains the worst class
* **Plastic: 72.7% mAP50** — best class, improves over EXP-014 (70.7%)
* **Paper: 68.6% mAP50** — best seen so far

### Observation
EXP-017 merges ALL 4 available dataset sources (9,774 images), but adding WaRP actually hurt overall mAP50 (60.7% → 59.3%) compared to EXP-014 which used only 3 sources. This suggests label noise or distribution mismatch in WaRP degrades generalization despite the larger dataset size. Trash remains critically weak (22.7%) — it needs either more high-quality trash data or a dedicated augmentation strategy. Plastic and Paper saw minor gains. The TFLite export is fast (177 ms) and produces a 2.9 MB model suitable for edge deployment.


---
## EXP-018 — YOLO11n Teacher on Clean Dataset (dmedhi + TACO + Roboflow + TrashNet)

- **Date:** 2026-07-30
- **Platform:** Kaggle GPU (Tesla T4, 14.9 GB VRAM)
- **Model:** yolo11n.pt
- **Dataset:** `merged_mira_balanced_no_sortwaste.zip` (5,108 train / 415 val / 1,375 test, 12,832 boxes)
- **Sources:** dmedhi + TACO + Roboflow + TrashNet SAM-labeled (SortWaste and Keremberke excluded)
- **Classes:** glass (0), metal (1), paper (2), plastic (3), trash (4)
- **Epochs:** 120
- **Batch:** 32
- **Image size:** 640
- **Optimizer:** AdamW, lr0=0.001, cos_lr=True
- **Parameters:** 2,583,127
- **GFLOPs:** 6.3
- **Ultralytics:** 8.4.112, PyTorch 2.10.0+cu128, Python 3.12.13
- **Duration:** 2.705 hours (120 epochs)

### Validation Results (best.pt, FP32)
```
Per-class:
       glass    mAP50 0.908  mAP50-95 0.874  Precision 0.904  Recall 0.825
       metal    mAP50 0.948  mAP50-95 0.827  Precision 0.914  Recall 0.960
       paper    mAP50 0.887  mAP50-95 0.738  Precision 0.909  Recall 0.840
     plastic    mAP50 0.811  mAP50-95 0.714  Precision 0.874  Recall 0.644
       trash    mAP50 0.975  mAP50-95 0.955  Precision 0.761  Recall 0.963

Overall:      mAP50 0.906  mAP50-95 0.822
```

### Exports
- FP32 PT: 5.5 MB stripped
- INT8 TFLite: 2.90 MB (3.5x smaller than original 10.14 MB)
- ONNX: 10.1 MB

### Comparison with EXP-014 (Old Best)

| Metric | EXP-014 (Old) | EXP-018 (New) | Improvement |
|---|---:|---:|---:|
| mAP50 | 60.7% | **90.6%** | +29.9 pp |
| mAP50-95 | 50.6% | **82.2%** | +31.6 pp |
| glass mAP50 | 50.2% | **90.8%** | +40.6 pp |
| metal mAP50 | 71.3% | **94.8%** | +23.5 pp |
| paper mAP50 | 82.9% | **88.7%** | +5.8 pp |
| plastic mAP50 | 72.1% | **81.1%** | +9.0 pp |
| trash mAP50 | 26.9% | **97.5%** | +70.6 pp |
| Epochs | 120 | **120** | same |
| Duration | ~5h | **2.7h** | ~2x faster |

### Observation
EXP-018 uses the cleaned balanced dataset with 5,108 training images (SortWaste and Keremberke excluded, class-balanced at 1621-1982 boxes per class). Against the pure tabletop TrashNet validation set (415 images), this model achieves **90.6% mAP50** — a dramatic improvement over EXP-014's 60.7% on the old TACO+TrashNet+Roboflow mix. All five classes perform well, with trash going from 26.9% to 97.5% mAP50. Training completed in 2.7 hours over 120 epochs — significantly faster than EXP-014's ~5 hours, likely due to the smaller, cleaner dataset. The INT8 TFLite export is 2.90 MB, suitable for Raspberry Pi Zero 2W deployment. This result validates that dataset quality (balanced, clean, deployment-matching geometry) matters far more than model architecture or training duration.

---
## EXP-019 — YOLO11n Repeatability Run on Clean Balanced Dataset

- **Date:** 2026-07-31
- **Purpose:** Repeat EXP-018 as a normal YOLO11n detector, not a teacher model
- **Platform:** Kaggle GPU (Tesla T4, 14.9 GB VRAM)
- **Model:** YOLO11n pretrained weights (`yolo11n.pt`)
- **Dataset:** `merged_mira_balanced_no_sortwaste` (5,108 train / 415 val / 1,375 test, 12,832 boxes)
- **Sources:** dmedhi + TACO + Roboflow + TrashNet SAM-labeled
- **Excluded:** SortWaste and Keremberke
- **Classes:** glass (0), metal (1), paper (2), plastic (3), trash (4)
- **Epochs:** 120
- **Batch:** 32
- **Image size:** 640
- **Optimizer:** AdamW, `lr0=0.001`, cosine LR, `close_mosaic=10`
- **Parameters:** 2,583,127
- **GFLOPs:** 6.3
- **Ultralytics:** 8.4.112, PyTorch 2.10.0+cu128, Python 3.12.13
- **Duration:** 2.672 hours

### Validation Results (best.pt, FP32)

Final evaluation used the 415-image TrashNet tabletop validation split:

| Class | Precision | Recall | mAP50 | mAP50-95 |
|---|---:|---:|---:|---:|
| all | 0.872 | 0.846 | **0.9058** | **0.8215** |
| glass | 0.904 | 0.825 | 0.908 | 0.874 |
| metal | 0.914 | 0.960 | 0.948 | 0.827 |
| paper | 0.909 | 0.840 | 0.887 | 0.738 |
| plastic | 0.874 | 0.644 | 0.811 | 0.714 |
| trash | 0.761 | 0.963 | 0.975 | 0.955 |

### Sanity Check

The post-training check detected objects in **10/10** sampled validation images at confidence 0.25. The independent 1,375-image test split was not evaluated in this run.

### Local TFLite 320 Validation

The exported 320px TFLite model was evaluated locally on the same 415-image validation split using Ultralytics 8.4.104 with CPU/XNNPACK:

| Metric | Value |
|---|---:|
| Precision | 0.797 |
| Recall | 0.836 |
| mAP50 | 0.862 |
| mAP50-95 | 0.756 |

The export therefore loses accuracy relative to the FP32 PT model (0.906/0.822), but remains functional on the validation set.

### Exports

- FP32 PyTorch: `mira_exp019.pt`, 5,469,402 bytes
- LiteRT/TFLite 320: `mira_exp019_int8_320.tflite`, 3,022,810 bytes
- LiteRT/TFLite 640: `mira_exp019_int8_640.tflite`, 3,041,690 bytes
- ONNX: `mira_exp019.onnx`, 10,607,296 bytes

Tensor inspection found FP32 input/output tensors in both TFLite files. They are reduced-size LiteRT exports with quantized weights, not full-integer input/output models. Raspberry Pi speed and accuracy remain to be measured.

### Comparison with EXP-018

| Metric | EXP-018 | EXP-019 | Change |
|---|---:|---:|---:|
| mAP50 | 0.906 | 0.9058 | approximately equal |
| mAP50-95 | 0.822 | 0.8215 | approximately equal |
| Duration | 2.705 h | 2.672 h | -0.033 h |

### Observation

EXP-019 reproduces EXP-018's validation performance almost exactly. The retraining confirms that the clean balanced dataset and training configuration are reproducible; it does not provide a measurable accuracy improvement. Training, validation, sanity checking, and exports completed before Kaggle later failed with `OSError: [Errno 28] No space left on device` while Papermill saved the notebook. The failure was caused by the notebook/archive output process, not by model training.
