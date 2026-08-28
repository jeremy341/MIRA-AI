# MIRA AI - Global Experiment Log
* **Project:** Machine Intelligence for Recycling Automation (MIRA)
* **Domain:** computer vision / edge ai
* **Target Hardware:** ESP32 / Raspberry Pi Zero 2W

---

## EXP-001: Baseline Custom CNN (3-Layer)
* **Date:** 2026-06-26
* **Commit Hash:** `04ef1f0`
* **Architecture:** 3x Conv2D (16/32/64) + Dropout(0.2) + Dense(128)
* **Dataset Size:** 126 images (highly restricted)
* **Dataset Source:** Hand-collected custom images (`data/classes/`), 4 classes only (no trash)
* **Training Platform:** n/a
* **Training Time:** ~70 seconds (20 epochs @ ~3.5s/epoch)

### Quantitative Metrics
* **Total Parameters:** 3,989,156 (15.22 MB)
* **Training Accuracy:** 73.61% | **Training Loss:** 0.9189
* **Validation Accuracy:** 61.00% | **Validation Loss:** 1.0633

### Class-Specific Performance
| Class | Precision | Recall | F1-Score | Support |
|---|---:|---:|---:|---:|
| glass | 0.92 | 0.77 | 0.84 | 43 |
| metal | 0.49 | 0.80 | 0.61 | 41 |
| paper | 0.50 | 0.07 | 0.12 | 42 |
| plastic | 0.56 | 0.85 | 0.67 | 33 |

---

## EXP-002: Transfer Learning (MobileNetV2 Frozen Base)
* **Date:** 2026-06-27
* **Commit Hash:** `366cd6c`
* **Architecture:** MobileNetV2 (weights: ImageNet, frozen) + Custom head [Dense(128) + Dropout(0.2)]
* **Dataset Size:** 796 images (fully scaled)
* **Dataset Source:** Hand-collected custom images (`data/classes/`), 4 classes only (no trash)
* **Training Platform:** n/a
* **Training Time:** ~165 seconds (20 epochs @ ~8s/epoch)

### Quantitative Metrics
* **Total Parameters:** 2,263,084 total (5,124 trainable, 2,257,984 non-trainable)
* **Training Accuracy:** 74.73% | **Training Loss:** 0.6917
* **Validation Accuracy:** 84.28% | **Validation Loss:** 0.5659

### Class-Specific Performance
| Class | Precision | Recall | F1-Score | Support |
|---|---:|---:|---:|---:|
| glass | 0.91 | 0.98 | 0.94 | 43 |
| metal | 0.86 | 0.76 | 0.81 | 41 |
| paper | 0.77 | 0.81 | 0.79 | 42 |
| plastic | 0.82 | 0.82 | 0.82 | 33 |

---

## EXP-003: Two-Stage Fine-Tuning (MobileNetV2 Unfrozen)
* **Date:** 2026-06-27
* **Commit Hash:** `n/a`
* **Architecture:** MobileNetV2 (unfrozen from layer 100) + Custom head [Dense(128) + Dropout(0.2)]
* **Dataset Size:** 796 images (fully scaled)
* **Dataset Source:** Hand-collected custom images (`data/classes/`), 4 classes only (no trash)
* **Training Platform:** n/a
* **Training Time:** ~177 seconds (15 epochs @ ~11s/epoch)

### Hyperparameters
* **Learning Rate (lr):** `1e-5` (Adam, Stage 2)

### Quantitative Metrics
* **Total Parameters:** 2,263,108 total (1,866,564 trainable, 396,544 non-trainable)
* **Training Accuracy:** 91.84% | **Training Loss:** 0.2575
* **Validation Accuracy:** 87.42% | **Validation Loss:** 0.3148

### Class-Specific Performance
| Class | Precision | Recall | F1-Score | Support |
|---|---:|---:|---:|---:|
| glass | 0.93 | 0.95 | 0.94 | 43 |
| metal | 0.77 | 0.98 | 0.86 | 41 |
| paper | 0.96 | 0.64 | 0.77 | 42 |
| plastic | 0.89 | 0.94 | 0.91 | 33 |

---

## EXP-004: Quantized TFLite Model (Full INT8)
* **Date:** 2026-07-02
* **Commit Hash:** `93f32eb`
* **Architecture:** MobileNetV2 (Quantized to 8-bit Integer Calibration)
* **Dataset Size:** 796 images (fully scaled)
* **Dataset Source:** Hand-collected custom images (`data/classes/`), 4 classes only (no trash)
* **Calibration Set:** 100 representative calibration samples
* **Training Platform:** n/a
* **Training Time:** n/a

### Quantitative Metrics
* **Model Size on Disk:** 2.61 MB (Compressed from 23.48 MB Keras Binary)
* **Compression Ratio:** 9.0x smaller (70% smaller than standard FP32 TFLite)
* **Average CPU Latency:** 10.32 ms per image (Theoretical throughput: ~97 FPS)
* **Validation Accuracy:** 87.42% (0.8735)

### Class-Specific Performance
| Class | Precision | Recall | F1-Score | Support |
|---|---:|---:|---:|---:|
| glass | 0.93 | 0.93 | 0.93 | 43 |
| metal | 0.75 | 1.00 | 0.85 | 41 |
| paper | 1.00 | 0.64 | 0.78 | 42 |
| plastic | 0.91 | 0.94 | 0.93 | 33 |

---

## EXP-005: YOLOv8-Nano Object Detection
* **Date:** 2026-07-03
* **Commit Hash:** `n/a`
* **Architecture:** YOLOv8-Nano (PyTorch .pt)
* **Dataset Size:** ~3,300 images (Custom + TrashNet)
* **Dataset Source:** Hand-collected custom tabletop images + Stanford TrashNet (Canny-edge auto-labeled bounding boxes)
* **Target Classes:** glass, metal, paper, plastic, trash
* **Training Platform:** n/a
* **Training Time:** n/a

### Validation Metrics
| Metric | Value |
|---|---:|
| mAP50 (Overall) | 82.3% |
| mAP50-95 | 69.8% |
| Strongest Class | Metal (0.941) |
| Weakest Class | Trash (0.764) |

### Speed & Performance
* **Inference Latency (Cloud GPU):** 1.9 ms

### Observation
Transitioning to an object detector successfully enabled simultaneous detection of multiple items. Synthetic auto-labeling via Canny-Edge provided sufficient bounding box accuracy for model convergence.

---

## EXP-006: Stage B Object Detection Fusion
* **Date:** 2026-07-04
* **Commit Hash:** `n/a`
* **Architecture:** YOLOv8-Nano (PyTorch)
* **Dataset Size:** ~3,300 images (Custom + TrashNet + Roboflow)
* **Dataset Source:** Stanford TrashNet (clean background) + Roboflow Trash Detection Dataset (64 classes, outdoor/wild, remapped to 5 MIRA classes: glass, metal, paper, plastic, trash)
* **Training Platform:** Google Colab (T4 GPU)
* **Training Time:** 3.3 hours (100 epochs)

### Validation Metrics
| Metric | Value |
|---|---:|
| mAP50 (Global) | 39.4% (on highly complex wild data) |
| Real-time Performance (Tabletop) | Stable >90% confidence for Plastic and Metal |
| Effective FPS | ~15.6 FPS (sufficient for mechatronic sorting) |

### Speed & Performance
* **System Latency:** ~40.4 ms per frame on local CPU

### Observation
Model is highly robust against background textures (keyboard, laptop, white desk). Edge case identified: "End-on" metal cans (opening facing camera) lead to detection drop-out. Transitioned from image classification (one label per image) to spatial object detection (bounding boxes). Fused TrashNet (clean background) with 64-class Roboflow "Wild Data" remapped to 5 MIRA classes.

---

## EXP-007: YOLOv8-Nano INT8 Quantization (LiteRT)
* **Date:** 2026-07-04
* **Commit Hash:** `n/a`
* **Architecture:** YOLOv8-Nano (TFLite INT8)
* **Dataset Size:** n/a (derived from EXP-006)
* **Dataset Source:** n/a (derived from EXP-006)
* **Base Model:** EXP-006 (`mira_exp006.pt`)
* **Training Platform:** Google Colab (Linux environment)
* **Training Time:** n/a

### Quantization
* **Original Intermediate Graph Size:** 11.69 MB
* **Quantized INT8 Model Size:** 3.18 MB
* **Compression Ratio:** 3.7x smaller
* **Calibration Data:** `yolo_data/dataset.yaml`

### Observation
Static quantization (INT8 weights and activations) successfully applied using the Ultralytics LiteRT export pipeline. The model footprint of 3.18 MB is well within the memory constraints of the target edge hardware (Raspberry Pi).

---

## EXP-008: Specialized Tabletop YOLOv8-Nano (Data-Centric Optimization)
* **Date:** 2026-07-05
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

### Validation Metrics
| Metric | Value |
|---|---:|
| Box Loss | 0.6241 |
| Class Loss (cls_loss) | 0.7603 |
| Distribution Focal Loss (dfl_loss) | 0.9023 |
| mAP50 | 39.6% (0.3960) |
| mAP50-95 | 32.9% (0.3290) |

### Class-Specific Performance
| Class | mAP50 |
|---|---:|
| Glass | 38.8% (0.3880) |
| Metal | 51.0% (0.5100) |
| Paper | 36.6% (0.3660) |
| Plastic | 64.4% (0.6440) |
| Trash | 7.1% (0.0711) |

### Speed & Performance
* **Preprocess:** 0.2 ms
* **Inference Latency:** 2.1 ms
* **Postprocess:** 3.1 ms

### Observation
Data-centric AI optimization. By purging the corrupted auto-labeled custom images and training strictly on human-annotated, high-quality bounding boxes, the model converged to the exact same accuracy profile as the 100-epoch noisy model (EXP-006) in half the training time.

---

## EXP-009: Pristine Tabletop YOLOv8-Nano (Verified Baseline)
* **Date:** 2026-07-05
* **Commit Hash:** `n/a`
* **Architecture:** YOLOv8-Nano (PyTorch .pt)
* **Dataset Size:** ~2,527 images (Pristine TrashNet, Auto-labeled via Canny Edge)
* **Dataset Source:** Stanford TrashNet only (clean white-background tabletop images, Canny-edge auto-labeled bounding boxes)
* **Training Platform:** Kaggle Notebooks (NVIDIA Tesla T4 GPU)
* **Training Time:** 0.309 hours (50 epochs)

### Model Summary
* **Total Parameters:** 3,006,623 (6.2 MB)

### Validation Metrics
| Metric | Value |
|---|---:|
| mAP50 (Overall) | 72.8% |
| mAP50-95 | 58.3% |

### Class-Specific Performance
| Class | mAP50 |
|---|---:|
| Glass | 72.9% |
| Metal | 84.8% |
| Paper | 77.7% |
| Plastic | 64.5% |
| Trash | 63.9% |

### Speed & Performance
* **Inference Latency (GPU):** 1.4 ms

### Observation
Verified baseline of MIRA's Stage B software. By purging all noisy custom desktop images that caused contour border leakage, overall mAP50 was raised from 39.6% to 72.8%.

---

## EXP-010: Quantized Wild YOLOv8-Nano (INT8 Calibration)
* **Date:** 2026-07-06
* **Commit Hash:** `n/a`
* **Architecture:** YOLOv8-Nano (TFLite INT8 / LiteRT)
* **Dataset Size:** ~3,300 images (Custom + TrashNet + Remapped Roboflow)
* **Dataset Source:** Hand-collected custom images + Stanford TrashNet + Roboflow Trash Detection Dataset (64 classes, outdoor/wild, remapped to 5 MIRA classes)
* **Base Model:** EXP-006 (`mira_exp006.pt`)
* **Calibration Set:** 100 representative samples from `mira_wild_data`
* **Training Platform:** n/a
* **Training Time:** n/a

### Quantization
* **Original Intermediate Graph Size:** 11.62 MB
* **Quantized INT8 Model Size:** 3.16 MB
* **Compression Ratio:** 3.7x smaller
* **Inference Speed (Cloud GPU):** 2.1 ms
* **Calibration Dataset Config:** `yolo_data/dataset.yaml` (5 classes)

### Observation
Static quantization (8-bit integer weights and activations) successfully applied using the Ultralytics LiteRT export pipeline in a Linux environment. The model footprint of 3.16 MB is fully optimized for CPU-only edge environments (Raspberry Pi).

---

## EXP-011: Tabletop-Excluded YOLOv8-Nano (Wild-Data Only)
* **Date:** 2026-07-06
* **Commit Hash:** `decb9d1`
* **Architecture:** YOLOv8-Nano (PyTorch .pt)
* **Dataset Size:** 3,365 images (Pristine TACO-remapped Wild Dataset)
* **Dataset Source:** TACO (Trash Annotations in Context) - outdoor/wild litter images, 60 COCO categories remapped to 5 MIRA classes
* **Training Platform:** Kaggle Notebooks (NVIDIA Tesla T4 GPU)
* **Training Time:** 0.309 hours (100 epochs)

### Hyperparameters
* **Learning Rate (lr0):** 0.01 (Adam)
* **Image Size (imgsz):** 640 (Training) / 320 (Inference Target)
* **Batch Size:** 16

### Validation Metrics
| Metric | Value |
|---|---:|
| mAP50 (Overall) | 35.0% (0.3500) |
| mAP50-95 | 29.0% (0.2900) |

### Class-Specific Performance
| Class | mAP50 |
|---|---:|
| Glass | 27.3% |
| Metal | 46.4% |
| Paper | 31.4% |
| Plastic | 62.3% |
| Trash | 7.5% |

### Speed & Performance
* **Inference Latency (GPU):** 1.8 ms

### Observation
Investigation into pure out-of-distribution generalization. By excluding local tabletop images and training exclusively on complex outdoor litter, global mAP50 dropped to 35.0% on the diverse test set.

---

## EXP-012: Quantized Wild-Only YOLOv8-Nano (INT8 Calibration)
* **Date:** 2026-07-06
* **Commit Hash:** `decb9d1`
* **Architecture:** YOLOv8-Nano (TFLite INT8 / LiteRT)
* **Dataset Size:** n/a (same as EXP-011, TACO only)
* **Dataset Source:** Same as EXP-011 (TACO only)
* **Base Model:** EXP-011 (`mira_exp011.pt`)
* **Calibration Dataset:** `wild_data/data.yaml`
* **Training Platform:** n/a
* **Training Time:** n/a

### Quantization
* **Original Model Size:** 11.62 MB (11.62 MiB)
* **Quantized INT8 Model Size:** 3.16 MB (3.16 MiB)
* **Compression Ratio:** 3.7x smaller (72.8% smaller footprint)
* **Inference Speed (Cloud GPU):** 2.1 ms

### Observation
Successfully quantized using the high-variance training distribution as the representative calibration set. The 3.16 MB footprint establishes the performance limits of complex background processing on low-power CPU architectures.

---

## EXP-013: YOLO11n on TACO + TrashNet (mira_v2 Fusion Dataset)
* **Date:** 2026-07-11
* **Commit Hash:** `n/a`
* **Architecture:** YOLO11n (PyTorch .pt -> TFLite INT8 / LiteRT)
* **Dataset Size:** 4,024 images (1,497 TACO wild + 2,527 TrashNet tabletop, full-image bbox)
* **Dataset Source:** TACO (Trash Annotations in Context, outdoor/wild) + Stanford TrashNet (clean tabletop), fused into mira_v2 dataset
* **Training Platform:** Kaggle Notebooks (NVIDIA Tesla T4 GPU)
* **Training Time:** 2.728 hours (120 epochs, best epoch 103)
* **Framework:** Ultralytics 8.4.92 | Python-3.12.13 | torch-2.10.0+cu128

### Hyperparameters
* **Learning Rate (lr0):** 0.01 (SGD auto)
* **Image Size (imgsz):** 640
* **Batch Size:** 32

### Model Summary
* **Total Parameters:** 2,583,127 (5.5 MB)
* **Layers:** 101 (fused)
* **FLOPs:** 6.3 GFLOPs

### Validation Metrics
| Metric | Value |
|---|---:|
| Train Box Loss | 0.3654 |
| Train Class Loss | 0.4173 |
| Train DFL Loss | 0.8878 |
| Val Box Loss | 0.5693 |
| Val Class Loss | 0.9511 |
| Val DFL Loss | 0.5637 |
| mAP50 (Best Epoch 103) | 55.1% (0.551) |
| mAP50-95 | 49.8% (0.498) |
| Mean Precision | 0.789 |
| Mean Recall | 0.468 |

### Class-Specific Performance
| Class | mAP50 |
|---|---:|
| Glass | 56.5% |
| Metal | 67.9% |
| Paper | 79.3% |
| Plastic | 55.6% |
| Trash | 15.6% |

### Speed & Performance
* **Preprocess:** 1.0 ms
* **Inference Latency:** 3.6 ms
* **Postprocess:** 0.9 ms

### Quantization
* **Original Model Size:** 10.14 MiB
* **Quantized INT8 Model Size:** 2.90 MiB
* **Compression Ratio:** 3.5x smaller
* **Export Time:** 598.4 s

### Observation
Upgrades from YOLOv8-Nano to YOLO11n (2.58M vs 3.01M params). Balanced 55.1% mAP50 is +20 pp over wild-only EXP-011 (35.0%). Paper strongest (79.3%) due to large surface area; trash weakest (15.6%) due to intra-class diversity.

---

## EXP-014: YOLO11n on TACO + TrashNet + Roboflow (Model 1 - mira_tnr)
* **Date:** 2026-07-12
* **Commit Hash:** `n/a`
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

### Validation Metrics
| Metric | Value |
|---|---:|
| Mean Precision | 0.662 |
| Mean Recall | 0.584 |
| mAP50 | 0.607 (60.7%) |
| mAP50-95 | 0.506 (50.6%) |
| Images | 1588 |
| Instances | 3126 |

### Class-Specific Performance
| Class | Precision | Recall | mAP50 | mAP50-95 | Instances |
|---|---:|---:|---:|---:|---:|
| Glass | 0.580 | 0.521 | 0.502 | 0.400 | 336 |
| Metal | 0.670 | 0.699 | 0.713 | 0.613 | 439 |
| Paper | 0.820 | 0.772 | 0.829 | 0.745 | 474 |
| Plastic | 0.715 | 0.699 | 0.721 | 0.601 | 1316 |
| Trash | 0.523 | 0.230 | 0.269 | 0.173 | 561 |

### Speed & Performance
* **Preprocess:** 0.2 ms
* **Inference:** 1.8 ms
* **Postprocess:** 1.3 ms

### Quantization
* **Original Model Size:** 10.14 MiB
* **Quantized INT8 Model Size:** 2.90 MiB
* **Compression Ratio:** 3.5x smaller
* **Export Time:** 1093.7 s

### Observation
First result from the 4-model comparison adding Roboflow. Overall mAP50 rises from 55.1% (EXP-013) to 60.7% (+5.6 pp). Trash gains +11.3 pp (15.6% -> 26.9%); glass drops -6.3 pp. Paper remains strongest (82.9%); trash weakest (26.9%).

---

## EXP-015: YOLO11n on TACO + TrashNet + WaRP (Model 2 - mira_tnw)
* **Date:** 2026-07-13
* **Commit Hash:** `n/a`
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

### Validation Metrics
| Metric | Value |
|---|---:|
| Mean Precision | 0.723 |
| Mean Recall | 0.477 |
| mAP50 | 0.560 (56.0%) |
| mAP50-95 | 0.451 (45.1%) |
| Images | 1816 |
| Instances | 4845 |

### Class-Specific Performance
| Class | Precision | Recall | mAP50 | mAP50-95 | Instances |
|---|---:|---:|---:|---:|---:|
| Glass | 0.781 | 0.689 | 0.750 | 0.590 | 876 |
| Metal | 0.660 | 0.499 | 0.570 | 0.470 | 391 |
| Paper | 0.688 | 0.499 | 0.626 | 0.549 | 592 |
| Plastic | 0.778 | 0.608 | 0.712 | 0.544 | 2682 |
| Trash | 0.707 | 0.087 | 0.143 | 0.104 | 304 |

### Speed & Performance
* **Preprocess:** 0.1 ms
* **Inference:** 1.5 ms
* **Postprocess:** 1.3 ms

### Quantization
* **Original Model Size:** 10.14 MiB
* **Quantized INT8 Model Size:** 2.90 MiB
* **Compression Ratio:** 3.5x smaller
* **Export Time:** 1239.5 s

### Observation
Replaces Roboflow with WaRP. Overall mAP50 drops to 56.0% (-4.7 pp vs EXP-014). WaRP boosts glass (+24.8 pp) due to bottle-heavy data, but drags metal (-14.3 pp), paper (-20.3 pp), and trash (-12.6 pp). High trash precision (0.707) but low recall (0.087) indicates missed instances.

---

## EXP-016: WaRP Only - YOLO11n (dataset: mira_warp_only)
* **Date:** 2026-07-13
* **Commit Hash:** `0f90571`
* **Architecture:** YOLO11n (nano, 2.58M params)
* **Dataset Size:** n/a (WaRP only, 28 WaRP classes remapped to 5 MIRA classes)
* **Dataset Source:** WaRP only (28 WaRP classes remapped to 5 MIRA classes)
* **Training Platform:** Kaggle T4 GPU (1.067 hours / 120 epochs)
* **Training Time:** 1.067 hours (120 epochs)
* **Training Script:** `scripts/train_detector_kaggle.py --dataset mira_warp_only --epochs 120`

### Validation Metrics
| Metric | Value |
|---|---:|
| mAP50 | 0.588 (58.8%) |
| mAP50-95 | 0.432 (43.2%) |
| Precision | 0.621 |
| Recall | 0.559 |

### Class-Specific Performance
| Class | mAP50 |
|---|---:|
| Glass | 0.777 (77.7%) |
| Metal | 0.421 (42.1%) |
| Paper | 0.422 (42.2%) |
| Plastic | 0.731 (73.1%) |
| Trash | — (no trash in WaRP dataset) |

### Speed & Performance
* **Preprocess:** 0.1 ms
* **Inference:** 1.2 ms
* **Postprocess:** 1.3 ms

### Quantization
* **Original Model Size:** 10.14 MiB
* **Quantized INT8 Model Size:** 2.90 MiB
* **Compression Ratio:** 3.5x smaller
* **Export Time:** 702.3 s

### Observation
Trains exclusively on WaRP. Outperforms mixed EXP-015 (56.0%) despite no trash class. Glass (77.7%) and plastic (73.1%) strong; metal/paper weaker. No trash detection possible.

---

## EXP-017: YOLO11n on ALL 4 Sources (TACO + TrashNet + Roboflow + WaRP)
* **Date:** 2026-07-20
* **Commit Hash:** `n/a`
* **Architecture:** YOLO11n
* **Dataset Size:** 9,774 images (mira_all, 5 classes - all 4 sources merged)
* **Dataset Source:** TACO + TrashNet + Roboflow + WaRP (all 4 sources merged)
* **Training Platform:** Kaggle GPU (Tesla T4, 14GB VRAM)
* **Training Time:** 6.01 hours (120 epochs)

### Hyperparameters
* **Batch Size:** 32
* **Image Size (imgsz):** 640
* **Patience:** 30
* **Optimizer:** AdamW (lr0=0.01, lrf=0.01)
* **Augmentation:** mosaic=1.0, mixup=0.1, copy_paste=0.1, hsv_h=0.015, hsv_s=0.7, hsv_v=0.4, scale=0.5, fliplr=0.5

### Validation Metrics
| Class | Images | Instances | Precision | Recall | mAP50 | mAP50-95 |
|---|---:|---:|---:|---:|---:|---:|
| **All** | 2599 | 6424 | 0.639 | 0.549 | 0.593 | 0.465 |
| glass | 680 | 1027 | 0.675 | 0.685 | 0.706 | 0.531 |
| metal | 489 | 641 | 0.631 | 0.590 | 0.621 | 0.497 |
| paper | 644 | 777 | 0.660 | 0.614 | 0.686 | 0.583 |
| plastic | 1678 | 3418 | 0.713 | 0.677 | 0.727 | 0.566 |
| trash | 243 | 561 | 0.501 | 0.178 | 0.227 | 0.146 |

### Speed & Performance
* **Preprocess:** 0.7 ms
* **Inference:** 2.8 ms
* **Postprocess:** 0.9 ms

### Quantization
* **Original Model Size:** 10.14 MiB
* **Quantized INT8 Model Size:** 2.90 MiB
* **Compression Ratio:** 3.5x smaller
* **Export Time:** 176.95 ms

### Comparison
* **mAP50: 59.3%** - slightly lower than EXP-014 (60.7%)
* **Trash: 22.7% mAP50** - similar to EXP-014 (28.3%), remains worst class
* **Plastic: 72.7% mAP50** - best class, improves over EXP-014 (70.7%)
* **Paper: 68.6% mAP50** - best seen so far

### Observation
Merging all 4 sources (9,774 images) hurt overall mAP50 (60.7% -> 59.3%) vs EXP-014. Suggests label noise or distribution mismatch in WaRP degrades generalization despite larger dataset.

---

## EXP-018: YOLO11n Teacher on Clean Dataset (dmedhi + TACO + Roboflow + TrashNet)
* **Date:** 2026-07-30
* **Commit Hash:** `n/a`
* **Architecture:** YOLO11n (`yolo11n.pt`)
* **Dataset Size:** 5,108 train / 415 val / 1,375 test (12,832 boxes, `merged_mira_balanced_no_sortwaste.zip`)
* **Dataset Source:** dmedhi + TACO + Roboflow + TrashNet SAM-labeled (SortWaste and Keremberke excluded)
* **Classes:** glass (0), metal (1), paper (2), plastic (3), trash (4)
* **Training Platform:** Kaggle GPU (Tesla T4, 14.9 GB VRAM)
* **Training Time:** 2.705 hours (120 epochs)
* **Framework:** Ultralytics 8.4.112 | PyTorch 2.10.0+cu128 | Python 3.12.13

### Hyperparameters
* **Epochs:** 120
* **Batch Size:** 32
* **Image Size (imgsz):** 640
* **Optimizer:** AdamW, lr0=0.001, cos_lr=True
* **Parameters:** 2,583,127
* **GFLOPs:** 6.3

### Validation Metrics
| Class | Precision | Recall | mAP50 | mAP50-95 |
|---|---:|---:|---:|---:|
| all | 0.904 | 0.825 | 0.906 | 0.822 |
| glass | 0.904 | 0.825 | 0.908 | 0.874 |
| metal | 0.914 | 0.960 | 0.948 | 0.827 |
| paper | 0.909 | 0.840 | 0.887 | 0.738 |
| plastic | 0.874 | 0.644 | 0.811 | 0.714 |
| trash | 0.761 | 0.963 | 0.975 | 0.955 |

### Quantization
* **FP32 PT:** 5.5 MB stripped
* **INT8 TFLite:** 2.90 MB (3.5x smaller than original 10.14 MB)
* **ONNX:** 10.1 MB

### Comparison
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
Uses cleaned balanced dataset (5,108 training images, class-balanced 1621-1982 boxes per class). Achieves 90.6% mAP50 on TrashNet tabletop validation (415 images) - dramatic improvement over EXP-014's 60.7%. Validates that dataset quality matters far more than architecture or duration. INT8 TFLite 2.90 MB suitable for Raspberry Pi Zero 2W.

---

## EXP-019: YOLO11n Repeatability Run on Clean Balanced Dataset
* **Date:** 2026-07-31
* **Commit Hash:** `n/a`
* **Architecture:** YOLO11n pretrained weights (`yolo11n.pt`)
* **Dataset Size:** 5,108 train / 415 val / 1,375 test (12,832 boxes, `merged_mira_balanced_no_sortwaste`)
* **Dataset Source:** dmedhi + TACO + Roboflow + TrashNet SAM-labeled (SortWaste and Keremberke excluded)
* **Classes:** glass (0), metal (1), paper (2), plastic (3), trash (4)
* **Purpose:** Repeat EXP-018 as a normal YOLO11n detector, not a teacher model
* **Training Platform:** Kaggle GPU (Tesla T4, 14.9 GB VRAM)
* **Training Time:** 2.672 hours (120 epochs)
* **Framework:** Ultralytics 8.4.112 | PyTorch 2.10.0+cu128 | Python 3.12.13

### Hyperparameters
* **Epochs:** 120
* **Batch Size:** 32
* **Image Size (imgsz):** 640
* **Optimizer:** AdamW, lr0=0.001, cosine LR, close_mosaic=10
* **Parameters:** 2,583,127
* **GFLOPs:** 6.3

### Validation Metrics
| Class | Precision | Recall | mAP50 | mAP50-95 |
|---|---:|---:|---:|---:|
| all | 0.872 | 0.846 | 0.9058 | 0.8215 |
| glass | 0.904 | 0.825 | 0.908 | 0.874 |
| metal | 0.914 | 0.960 | 0.948 | 0.827 |
| paper | 0.909 | 0.840 | 0.887 | 0.738 |
| plastic | 0.874 | 0.644 | 0.811 | 0.714 |
| trash | 0.761 | 0.963 | 0.975 | 0.955 |

### Sanity Check
* **Post-training check:** Detected objects in 10/10 sampled validation images at confidence 0.25
* **Independent test split (1,375 images):** Not evaluated in this run

### Local TFLite 320 Validation
| Metric | Value |
|---|---:|
| Precision | 0.797 |
| Recall | 0.836 |
| mAP50 | 0.862 |
| mAP50-95 | 0.756 |

Export loses accuracy vs FP32 PT (0.906/0.822) but remains functional.

### Quantization
* **FP32 PyTorch:** `mira_exp019.pt`, 5,469,402 bytes
* **LiteRT/TFLite 320:** `mira_exp019_int8_320.tflite`, 3,022,810 bytes
* **LiteRT/TFLite 640:** `mira_exp019_int8_640.tflite`, 3,041,690 bytes
* **ONNX:** `mira_exp019.onnx`, 10,607,296 bytes
* **Note:** FP32 input/output tensors in both TFLite files - reduced-size LiteRT exports with quantized weights, not full-integer I/O. Raspberry Pi speed/accuracy to be measured.

### Comparison
| Metric | EXP-018 | EXP-019 | Change |
|---|---:|---:|---:|
| mAP50 | 0.906 | 0.9058 | approximately equal |
| mAP50-95 | 0.822 | 0.8215 | approximately equal |
| Duration | 2.705 h | 2.672 h | -0.033 h |

### Observation
Reproduces EXP-018's validation performance almost exactly. Confirms clean balanced dataset and training configuration are reproducible; no measurable accuracy improvement. Training, validation, sanity checking, and exports completed before Kaggle Papermill failed with `OSError: [Errno 28] No space left on device` during notebook save (not model training).
