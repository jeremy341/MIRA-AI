# MIRA-AI Training Plan

> **Project:** Machine Intelligence for Recycling Automation  
> **Target:** Raspberry Pi Zero 2W → Tabletop robot arm sorting  
> **Current Best:** 60.7% mAP50 (EXP-014, YOLO11n INT8, ~2.9 MB)  
> **Deadline:** July 31, 2026  
> **Platform:** Marimo molab (Blackwell RTX Pro 6000, 96GB VRAM)

---

## Table of Contents

1. [Project Overview](#1-project-overview)
2. [Deployment Specs](#2-deployment-specs)
3. [Existing Open-Source Model Benchmark](#3-existing-open-source-model-benchmark)
4. [YOLO11n vs YOLO26n Comparison](#4-yolo11n-vs-yolo26n-comparison)
5. [Datasets](#5-datasets)
6. [Training Platform](#6-training-platform)
7. [Experiments](#7-experiments)
8. [Expected Results](#8-expected-results)
9. [Timeline](#9-timeline)
10. [Files to Create](#10-files-to-create)
11. [References & Links](#11-references--links)

---

## 1. Project Overview

MIRA-AI is a computer vision system for automated waste sorting, deployed on a **Raspberry Pi Zero 2W** (512 MB RAM, ARM CPU, no GPU). A robot arm picks trash from a bin, places it on a table, and the vision system identifies the material type so the arm can sort it into the correct category.

### Demo Setup
- Single item placed on a table by robot arm
- Top-down camera (same angle as SortWaste dataset)
- Varying lighting conditions
- Real-time inference required for arm coordination

### Domain Randomization Strategy
The model is trained on diverse outdoor/cluttered waste scenes (TACO, Recycle Trash outdoor samples) so it learns to **ignore background and lighting variations**. When deployed on a clean tabletop with controlled lighting, the model focuses purely on material type — making it highly robust to lighting changes.

### Class System (5-class)

| ID | Class | Description | Current Bottleneck |
|----|-------|-------------|-------------------|
| 0 | glass | Bottles, jars, containers | Recycle Trash + TACO cover this well |
| 1 | metal | Cans, tins, foil | SortWaste + Recycle Trash strong coverage |
| 2 | paper | Cardboard, paper, paper packs | SortWaste Cardboard + Recycle Trash Paper |
| 3 | plastic | Bottles, bags, rigid plastics, styrofoam | Largest class, many sub-types |
| 4 | trash | Organic waste, contaminated items, batteries | **Weakest class at 7.1% mAP50** — main target for improvement |

---

## 2. Deployment Specs

| Component | Spec |
|-----------|------|
| **Processor** | Raspberry Pi Zero 2W (ARM Cortex-A53, 1 GHz, 4 cores) |
| **RAM** | 512 MB (shared with GPU) |
| **GPU** | None — CPU-only inference |
| **Model format** | TFLite INT8 |
| **Target size** | ~2-3 MB on disk |
| **Camera** | Top-down mounted above table |
| **Task** | Single-object classification per frame |
| **Edge case** | Lighting may vary (domain randomization solves this) |

### From YOLO Docs: CPU Inference Benchmarks (ONNX, Intel Xeon @ 2.00 GHz)

| Model | CPU ms | Params | FLOPs | INT8 Est. Size |
|-------|--------|--------|-------|---------------|
| YOLO11n | 56.1 ± 0.8 | 2.6 M | 6.5 B | ~2.9 MB |
| **YOLO26n** | **38.9 ± 0.7** | **2.4 M** | **5.4 B** | **~2.5 MB** |

YOLO26n is **43% faster CPU inference** than YOLO11n and **NMS-free** (end-to-end), removing post-processing overhead on the Pi.

---

## 3. Existing Open-Source Model Benchmark

### 3.1 YOLO11n — Fine-Tuned for Waste Detection

| Model | Classes | mAP50 | mAP50-95 | Dataset | Training | Source |
|-------|---------|-------|----------|---------|----------|--------|
| **Tikusu** (2026) | 6 ** | **84.0%** | 65.7% | Recycle Trash subset (2,462 img) | 100 ep, partial backbone freeze | [GitHub](https://github.com/Tikusu/yolo11n-recycle-waste-detection) |
| **TrashMonkey** (2026) | 6 | **80.5%** val / 49.8% RealWaste | 66.3% / 39.5% | 5 merged public datasets | 100 ep, AdamW, full fine-tune | [GitHub](https://github.com/tr4m0ryp/TrashMonkey) |
| CBAM-Enhanced (2025) | 6 | **96.1%*** | 95.4%* | TrashNet (2,524 img) | 100 ep, CBAM attention added | IEEE ICITRI 2025 |
| Mobile Study (2025) | — | 66.9% | 48.3% | Waste classification dataset | 100 ep | IJSRA 2025 |
| **MIRA EXP-014** | **5** | **60.7%** | — | TACO + TrashNet + Roboflow (17k img) | 120 ep | This repo |
| Alope (HF) | 4 | — | — | Kaggle Trash Type | 30 ep, 320px | [HF](https://huggingface.co/Alope/trash-detection-yolo11n) |

*\*CBAM 96.1% is on TrashNet only — clean backgrounds, single items, not comparable to complex real-world scenes.*  
*\*\*Tikusu classes: plastic, paper, metal, glass, organic, cardboard — nearly identical to MIRA 5-class.*

### 3.2 Tikusu — Best Performing YOLO11n on Waste

Tikusu tested three layer-freezing strategies on the same data:

| Scenario | Precision | Recall | mAP50 | mAP50-95 |
|----------|-----------|--------|-------|-----------|
| Full backbone freeze (10 layers) | 0.797 | 0.684 | 0.785 | 0.565 |
| **Partial backbone freeze (5 layers)** | **0.823** | **0.767** | **0.840** | **0.657** |
| Full transfer learning (all unfrozen) | 0.813 | 0.716 | 0.815 | 0.624 |

**Best:** Partial backbone freeze (first 5 layers frozen).  
**Per-class performance:** Metal (0.970 mAP50) best, Organic (0.496 recall) worst, Plastic (transparency issues).  
**RPi5 benchmark:** 261 ms inference, 5.9 MB model.

**Reference:** [Paper DOI](https://doi.org/10.36341/rabit.v11i1.7323), [GitHub Repo](https://github.com/Tikusu/yolo11n-recycle-waste-detection)

### 3.3 TrashMonkey — Most Complete Open-Source Pipeline

TrashMonkey merges 5 public datasets and provides a full pipeline from download → train → eval → export.

| Metric | VAL | TEST-1 (RealWaste) | TEST-2 (degraded) |
|--------|-----|--------------------|--------------------|
| mAP50 | 0.805 | 0.498 | 0.43-0.50 |
| mAP50-95 | 0.663 | 0.395 | 0.33-0.40 |

- **Key insight:** ~30 point drop from validation to held-out RealWaste — this is the real generalization gap.
- Full fine-tune (all layers), AdamW, 100 epochs, 640 px, seed 42.
- "Rest" rejection threshold automatically tuned.

**Reference:** [GitHub Repo](https://github.com/tr4m0ryp/TrashMonkey)

### 3.4 YOLO26n — No Fine-Tuned Waste Models Exist

YOLO26 was released **January 2026** by Ultralytics. As of July 2026, **no publicly available fine-tuned waste detection weights** exist for YOLO26n. Only COCO-pretrained `yolo26n.pt` is available.

This means our MIRA YOLO26n models would be the **first open-source waste detection YOLO26n** — a significant contribution.

### 3.5 Coming From Our Experiments (EXP-014 best)

| Metric | Value |
|--------|-------|
| Model | YOLO11n INT8 |
| mAP50 | **60.7%** |
| Size | ~2.9 MB |
| Dataset | TACO + TrashNet + Roboflow (17k images) |
| Epochs | 120 |

---

## 4. YOLO11n vs YOLO26n Comparison

### 4.1 COCO Benchmarks (Ultralytics Official)

| Model | mAP50-95 | mAP50-95 (e2e) | CPU ONNX (ms) | T4 TensorRT (ms) | Params (M) | FLOPs (B) |
|-------|----------|----------------|---------------|-------------------|------------|-----------|
| YOLO11n | 39.5 | — | 56.1 ± 0.8 | 1.5 ± 0.0 | 2.6 | 6.5 |
| YOLO11s | 47.0 | — | 90.0 ± 1.2 | 2.5 ± 0.0 | 9.4 | 21.5 |
| YOLO11m | 51.5 | — | 183.2 ± 2.0 | 4.7 ± 0.1 | 20.1 | 68.0 |
| YOLO11l | 53.4 | — | 238.6 ± 1.4 | 6.2 ± 0.1 | 25.3 | 86.9 |
| YOLO11x | 54.7 | — | 462.8 ± 6.7 | 11.3 ± 0.2 | 56.9 | 194.9 |
| **YOLO26n** | **40.9** | **40.1** | **38.9 ± 0.7** | 1.7 ± 0.0 | **2.4** | **5.4** |
| YOLO26s | 48.6 | 47.8 | 87.2 ± 0.9 | 2.5 ± 0.0 | 9.5 | 20.7 |
| YOLO26m | 53.1 | 52.5 | 220.0 ± 1.4 | 4.7 ± 0.1 | 20.4 | 68.2 |
| YOLO26l | 55.0 | 54.4 | 286.2 ± 2.0 | 6.2 ± 0.2 | 24.8 | 86.4 |
| YOLO26x | 57.5 | 56.9 | 525.8 ± 4.0 | 11.8 ± 0.2 | 55.7 | 193.9 |

**Reference:** [YOLO11 docs](https://docs.ultralytics.com/models/yolo11/), [YOLO26 docs](https://docs.ultralytics.com/models/yolo26/)

### 4.2 Advantages of YOLO26n for RPi Zero 2W

| Feature | YOLO11n | YOLO26n | Benefit |
|---------|---------|---------|---------|
| CPU inference | 56.1 ms | **38.9 ms** | **43% faster** |
| Parameters | 2.6 M | **2.4 M** | Smaller memory |
| FLOPs | 6.5 B | **5.4 B** | Fewer compute |
| NMS | Required | **NMS-free** | No post-processing on Pi |
| DFL | Yes | **Removed** | Better INT8 quantization |
| Optimizer | AdamW | **MuSGD** | Faster convergence |

**Reference:** [YOLO11 vs YOLO26](https://docs.ultralytics.com/compare/yolo11-vs-yolo26/)

### 4.3 Edge Benchmarks (Jetson Orin Nano, TensorRT FP16)

| Model | FPS @ 640px | mAP50-95 | Params |
|-------|-------------|----------|--------|
| YOLOv8n | ~55 | 37.3 | 3.2 M |
| YOLO11n | ~58 | 39.5 | 2.6 M |
| **YOLO26n** | **~65** | **40.1** | **2.4 M** |

**Source:** [HemiHex comparison](https://hemihex.com/yolov8-vs-yolo11-vs-yolo26-comparison-2026/)

### 4.4 Cross-Domain Study (PPE Detection)

A controlled study on safety equipment detection showed scale-dependent behavior:

| Model | CHV mAP50 | CHV mAP50-95 | SHEL5K mAP50 | SH17 mAP50 |
|-------|-----------|--------------|--------------|------------|
| YOLO26n | 0.653 | 0.306 | 0.651 | 0.584 |
| YOLO11n | **0.704** | **0.369** | **0.683** | **0.620** |
| YOLO26s | 0.765 | 0.409 | 0.747 | 0.695 |
| YOLO11s | **0.779** | **0.427** | **0.762** | **0.708** |
| YOLO26m | **0.813** | **0.458** | **0.795** | **0.747** |
| YOLOv11m | 0.811 | 0.455 | 0.793 | 0.745 |
| YOLO26l | **0.826** | **0.473** | **0.812** | **0.767** |
| YOLOv11l | 0.818 | 0.461 | 0.807 | 0.758 |
| YOLO26x | **0.852** | **0.506** | **0.840** | **0.797** |
| YOLOv11x | 0.836 | 0.475 | 0.830 | 0.781 |

**Pattern:** YOLO11n beats YOLO26n at nano scale; YOLO26x beats YOLO11x at XL scale. Crossover at medium.

**Reference:** [MDPI Electronics 2026](https://www.mdpi.com/2079-9292/15/6/1146)

---

## 5. Datasets

### 5.1 Dataset Summary

| # | Dataset | Images | Boxes | Classes | Format | Size | Download | Role |
|---|---------|--------|-------|---------|--------|------|----------|------|
| 1 | **Recycle Trash** (NAVER) | 21,818 | 107,935 | 10 | COCO (convert) | ~120 GB | [GitHub](https://github.com/connectfoundation/naverconnect-dataset-trash) | Main source — **glass + trash** |
| 2 | **SortWaste** (WACV 2026) | 5,261 | 87,252 | 8 | YOLO split | ~3 GB | [sortwaste.di.ubi.pt](https://sortwaste.di.ubi.pt) | **Top-down** matches camera angle |
| 3 | **TACO** (existing) | ~3,000 | ~15,000 | 60 | Already YOLO | ~2 GB | In repo | **Domain randomization** outdoors |
| 4 | **TrashNet** (existing) | ~5,000 | ~8,000 | 6 | Already YOLO | ~3 GB | In repo | **Clean tabletop** simulation |
| 5 | **Garbage Detection** (Ultralytics Hub) | ~36,000 | 72,125 | 11 | YOLO | ~8 GB | [Ultralytics Platform](https://platform.ultralytics.com) | **Lighting + background diversity** |
| | **Total** | **~71,000** | **~267,000+** | | | **~136 GB** | | |

### 5.2 Detailed Dataset Breakdown

#### Recycle Trash (NAVER Connect Foundation)

- **Source:** [GitHub Repository](https://github.com/connectfoundation/naverconnect-dataset-trash)
- **License:** Creative Commons Attribution 4.0
- **Images:** 21,818 photos
- **Annotations:** 107,935 objects (bounding box + segmentation)
- **Format:** COCO JSON (44 batch folders × 500 images + json ea.)
- **Size:** ~120 GB compressed
- **Classes:**

| Class | Count | Ratio |
|-------|-------|-------|
| General trash | 18,117 | 16.79% |
| Plastic bag | 23,805 | 22.05% |
| Paper | 29,873 | 27.68% |
| Plastic | 14,098 | 13.06% |
| Styrofoam | 5,627 | 5.21% |
| Metal | 4,451 | 4.12% |
| Glass | 4,142 | 3.84% |
| Paper pack | 4,235 | 3.92% |
| Clothing | 2,091 | 1.94% |
| Battery | 738 | 0.68% |
| UNKNOWN | 758 | 0.70% |

**MIRA remap:**
- glass (0) → 4,142 samples
- metal (1) → 4,451 samples
- paper (2) → Paper + Paper pack = 34,108 samples
- plastic (3) → Plastic + Styrofoam + Plastic bag = 43,530 samples
- trash (4) → General trash + Clothing + Battery = 20,946 samples
- UNKNOWN → skip

#### SortWaste (WACV 2026 Workshop)

- **Source:** [sortwaste.di.ubi.pt](https://sortwaste.di.ubi.pt)
- **Paper:** [arXiv:2601.02299](https://arxiv.org/abs/2601.02299)
- **GitHub:** [sarainacio/SortWaste](https://github.com/sarainacio/SortWaste)
- **Images:** 5,261
- **Annotations:** 87,252 bounding boxes
- **Classes:** 8 industrial material types
- **Split:** Train 3,705 / Val 780 / Test 776

| Class | Train | Val | Test | Total |
|-------|-------|-----|------|-------|
| HDPE | 16,803 | 4,972 | 3,269 | 25,044 |
| ECAL | 13,649 | 2,552 | 3,026 | 19,227 |
| PET | 11,976 | 2,108 | 2,722 | 16,806 |
| Mixed Soft Plastic | 9,077 | 1,443 | 1,817 | 12,337 |
| Mixed Rigid Plastic | 7,066 | 1,120 | 1,230 | 9,416 |
| Cardboard | 1,524 | 425 | 207 | 2,156 |
| Metal | 945 | 277 | 215 | 1,437 |
| PET Oil | 802 | 168 | 132 | 1,102 |
| **Total** | **61,842** | **13,065** | **12,618** | **87,525** |

**MIRA remap:**
- metal (1) → Metal = 1,437 samples
- paper (2) → Cardboard = 2,156 samples
- plastic (3) → HDPE + ECAL + PET + PET Oil + Soft Plastic + Rigid Plastic = 83,932 samples
- glass (0), trash (4) → none → covered by Recycle Trash + TACO + TrashNet

**Download:** [Dataset splits (YOLO format)](https://sortwaste.di.ubi.pt/datasets/dataset.zip)

#### TACO (Trash Annotations in Context)

- **Source:** Already in repo (`datasets/`)
- **Images:** ~3,000
- **Classes:** 60 (subsampled to ~15 relevant)
- **Format:** Already YOLO format
- **Role:** Outdoor/context domain randomization

**MIRA remap:** Maps to all 5 classes, especially good for organic/trash class.

#### TrashNet

- **Source:** Already in repo (`datasets/`)
- **Original:** [garythung/trashnet](https://github.com/garythung/trashnet) (also on [HF](https://huggingface.co/datasets/garythung/trashnet))
- **Images:** ~5,000
- **Classes:** 6 (glass, paper, metal, plastic, cardboard, trash)
- **Format:** Already YOLO format
- **Role:** Clean tabletop single-item simulation (closest to demo setup)

#### Garbage Detection (Ultralytics Hub)

- **Source:** [Ultralytics Platform](https://platform.ultralytics.com)
- **Images:** ~36,000
- **Annotations:** 72,125 bounding boxes
- **Classes:** 11 (batteries, cardboard, plastic bottles, footwear, medical waste, organic, paper, metal, glass, etc.)
- **Format:** YOLO format (direct download)
- **Role:** Lighting + background diversity for domain randomization

### 5.3 Class Balance Strategy

After merge, target distribution should have:
- Each class ≥ 10% of total instances
- Trash class (currently 7.1% mAP50 weakest) needs extra representation
- Recycle Trash contributes 20,946 trash samples — this alone should fix the trash bottleneck

---

## 6. Training Platform

### 6.1 Marimo molab

- **URL:** [molab.marimo.io](https://molab.marimo.io)
- **GPU:** NVIDIA RTX Pro 6000 Blackwell — **96 GB VRAM**, 125 TFLOPS
- **CPU:** 4 cores, 32 GB RAM
- **Sessions:** Max 12 hours (supports resume), idle timeout 90 min
- **Storage:** Persistent R2 (survives session restarts)
- **Pricing:** Free (public preview, usage must be reasonable)
- **Access:** Browser-based marimo notebook editor
- **Deps:** `uv` package manager, PEP 723 notebook headers

**molab ToS — allowed:**
- Interactive model training ✓
- Long-running computations while you actively check ✓
- Dataset download and preprocessing ✓

**molab ToS — NOT allowed:**
- Non-interactive batch jobs ✗
- SSH/remote control ✗
- API serving or file hosting ✗
- Mining or reselling compute ✗

**Session management:**
- Training cells actively computing = not idle (no timeout while training runs)
- Check loss curves between epoch ends
- Save checkpoints before 12h hard kill
- Resume with `model.train(resume=True)` and `last.pt`

### 6.2 Why Not Kaggle?

| Factor | molab (Blackwell) | Kaggle (T4 x2) |
|--------|-------------------|----------------|
| VRAM | **96 GB** | 32 GB |
| Quota/week | **Unlimited** | 30 hours |
| YOLO11x @ 1280px | ✅ Batch 16 | ❌ Batch 4-6 (gradient ckpt) |
| Persistent storage | ✅ R2 | ❌ Dies on restart |
| Distillation overhead | ✅ Fits | ⚠️ Tight |

### 6.3 Distillation — Built-In Ultralytics

Ultralytics added native knowledge distillation in 2026. No custom code needed:

```python
from ultralytics import YOLO

student = YOLO("yolo26n.pt")
results = student.train(
    data="dataset.yaml",
    epochs=200,
    distill_model="runs/train/teacher/weights/best.pt",  # Teacher path
    dis=6.0,  # Distillation loss weight (default 6.0)
)
```

How it works internally (from [Ultralytics docs](https://docs.ultralytics.com/guides/knowledge-distillation/)):
1. Teacher model frozen in `eval` mode
2. Features extracted from both models at 3 neck layers feeding Detect head
3. Projector network (lightweight MLP) aligns student feature dimensions to teacher
4. Score-weighted L2 loss compares projected student features with teacher features
5. Combined with standard detection losses using `dis` weight
6. Expect ~1.2-1.5x slower training, ~1.1x more GPU memory

**Reference:** [Knowledge Distillation Guide](https://docs.ultralytics.com/guides/knowledge-distillation/), [DistillationModel API](https://docs.ultralytics.com/reference/nn/distill_model/)

---

## 7. Experiments

### 7.1 Phase 1 — Teacher Training

#### EXP-018: YOLO11x Teacher @ 1280px (Blackwell Advantage)

| Parameter | Value | Reasoning |
|-----------|-------|-----------|
| Model | `yolo11x.pt` | Largest YOLO11, 56.9 M params |
| imgsz | 1280 | **Only possible on 96 GB VRAM** — better small object detection |
| batch | 16 | Large batch = stable training |
| epochs | 200 | Full convergence |
| optimizer | AdamW | Best for large YOLO models |
| lr0 | 0.001 | Lower lr for fine-tuning large model |
| cos_lr | True | Cosine annealing schedule |
| close_mosaic | 10 | Disable mosaic in last 10 epochs |
| patience | 30 | Early stopping |
| amp | True | Mixed precision |
| data | `merged_dataset.yaml` | All 71k images |

**Expected time:** ~12 hours (1 full molab session)  
**Output:** `runs/train/teacher_yolo11x/weights/best.pt`

#### EXP-019: YOLO26x Teacher @ 640px

| Parameter | Value | Reasoning |
|-----------|-------|-----------|
| Model | `yolo26x.pt` | Largest YOLO26, 55.7 M params |
| imgsz | 640 | Native YOLO26 size |
| batch | 32 | Fits comfortably |
| epochs | 200 | Full convergence |
| optimizer | MuSGD | YOLO26's built-in optimizer |
| cos_lr | True | Cosine annealing |
| data | `merged_dataset.yaml` | Same dataset for fair comparison |

**Expected time:** ~8 hours  
**Output:** `runs/train/teacher_yolo26x/weights/best.pt`

### 7.2 Phase 2 — Student Distillation

#### EXP-020: Distilled YOLO26n (Primary Target)

| Parameter | Value |
|-----------|-------|
| Student | `yolo26n.pt` (2.4 M params) |
| Teacher | Best from Phase 1 |
| imgsz | 640 |
| batch | 32 |
| epochs | 200 |
| optimizer | MuSGD |
| distill_model | `teacher_best.pt` |
| dis | 6.0 (default) |
| close_mosaic | 10 |
| data | `merged_dataset.yaml` |

**Expected time:** ~12 hours  
**Output:** `runs/train/distill_yolo26n/weights/best.pt`  
**Expected mAP50:** 65-68%

#### EXP-021: Distilled YOLO11n

| Parameter | Value |
|-----------|-------|
| Student | `yolo11n.pt` (2.6 M params) |
| Teacher | Best from Phase 1 |
| imgsz | 640 |
| batch | 32 |
| epochs | 200 |
| optimizer | AdamW |
| distill_model | `teacher_best.pt` |
| dis | 6.0 |
| data | `merged_dataset.yaml` |

**Expected time:** ~12 hours  
**Output:** `runs/train/distill_yolo11n/weights/best.pt`  
**Expected mAP50:** 63-66%

### 7.3 Phase 3 — Baseline Controls

#### EXP-022: Baseline YOLO26n (No Distillation)

Same settings as EXP-020 but **without** `distill_model`. Measures how much the teacher helps.

**Expected mAP50:** 60-63% (compare to 65-68% with KD → confirms distillation gain)

#### EXP-023: Baseline YOLO11n (No Distillation)

Same settings as EXP-021 but **without** `distill_model`. Direct comparison to current best EXP-014 (60.7%) with the larger dataset.

**Expected mAP50:** 60-62% (same data, no KD → measure pure data scaling effect)

### 7.4 Phase 4 — Export & Evaluation

| Step | Format | Command |
|------|--------|---------|
| 1 | ONNX FP32 | `model.export(format="onnx")` |
| 2 | TFLite INT8 | `model.export(format="tflite", int8=True)` |
| 3 | Benchmark CPU | Time inference on molab CPU |
| 4 | RealWaste eval | Run val on held-out RealWaste dataset |
| 5 | Per-class analysis | Compare trash class mAP50 across all models |
| 6 | Upload to HF | Push best model to `jeremy341/MIRA-AI` |

---

## 8. Expected Results

### 8.1 Performance Projections

| EXP | Model | KD? | Expected mAP50 | Expected INT8 Size | Tabletop Demo |
|-----|-------|-----|---------------|-------------------|---------------|
| EXP-014 | YOLO11n | No | 60.7% (current) | ~2.9 MB | — |
| **EXP-020** | **YOLO26n** | **Yes** | **65-68%** | **~2.5 MB** | **>90%** |
| **EXP-021** | **YOLO11n** | **Yes** | **63-66%** | **~2.9 MB** | **>88%** |
| EXP-022 | YOLO26n | No | 60-63% | ~2.5 MB | ~85% |
| EXP-023 | YOLO11n | No | 60-62% | ~2.9 MB | ~83% |

### 8.2 Comparison to Published Work

| Model | Dataset Size | mAP50 | Notes |
|-------|-------------|-------|-------|
| Tikusu (2026) | 2,462 | 84.0% | 6-class, clean dataset, partial freeze |
| TrashMonkey (2026) | 5 merged | 80.5% val / 49.8% RealWaste | RealWaste shows generalization gap |
| **Ours (EXP-020)** | **~71,000** | **65-68%** | Larger dataset, harder scenes, 5-class |
| RealWaste expected | — | ~50-55% | Honest generalization estimate (similar to TrashMonkey's drop) |

### 8.3 Trash Class Improvement

| Model | Trash mAP50 (est.) |
|-------|-------------------|
| EXP-014 (current) | 7.1% |
| EXP-020 distilled YOLO26n | **~40-50%** |
| EXP-021 distilled YOLO11n | **~35-45%** |

18,000+ "General trash" samples from Recycle Trash dataset directly address this bottleneck.

---

## 9. Timeline

```
July 25 (Sat) ─ Day 0 ─ Setup: write mira_molab.py, push to GitHub          ~2h
July 26 (Sun) ─ Day 1 ─ S1: Download + convert + merge all datasets         ~8h
July 27 (Mon) ─ Day 2 ─ S2: YOLO11x teacher @ 1280px (Blackwell advantage)  ~12h
July 28 (Tue) ─ Day 3 ─ S3: YOLO26x teacher @ 640px + compare               ~8h
July 29 (Wed) ─ Day 4 ─ S4: EXP-020 distilled YOLO26n                       ~12h
July 30 (Thu) ─ Day 5 ─ S5: EXP-021 + EXP-022/023 baselines + export + eval ~12h
July 31 (Fri) ─ Day 6 ─ BUFFER: Extras / retries
```

**Total training time:** ~52 hours (max 8 × 12h sessions, but 4-5 productive sessions needed)

**molab session workflow per session:**
1. Open molab notebook from GitHub mirror
2. Toggle GPU on (notebook specs button)
3. Run cells sequentially (or resume from checkpoint)
4. Monitor loss curves between epochs
5. Before 12h kill: save checkpoint, optionally upload to HF
6. Next session: `model.train(resume=True)`

---

## 10. Files to Create

```
NEW  scripts/mira_molab.py                # Single marimo notebook driving everything
                                          # PEP 723 header, GPU spec, all cells
                                          # ~600-800 lines

NEW  experiments/exp018_teacher_yolo11x.yaml   # 1280px config
NEW  experiments/exp019_teacher_yolo26x.yaml   # 640px config
NEW  experiments/exp020_distill_yolo26n.yaml   # KD config
NEW  experiments/exp021_distill_yolo11n.yaml   # KD config
NEW  experiments/exp022_baseline_yolo26n.yaml  # No-KD control
NEW  experiments/exp023_baseline_yolo11n.yaml  # No-KD control

NEW  datasets/registry/sortwaste.yaml          # SortWaste dataset descriptor
NEW  datasets/registry/recycle_trash.yaml      # Recycle Trash dataset descriptor
NEW  datasets/registry/garbage_detection.yaml  # Garbage Detection dataset descriptor

MOD  results/experiments_log.md               # Append EXP-018 through EXP-023
```

**No modifications to `src/pipeline/strategies.py`** — built-in Ultralytics `distill_model` handles distillation without custom code.

---

## 11. References & Links

### 11.1 Open-Source Models

| Model | Source | Link |
|-------|--------|------|
| Tikusu YOLO11n (84% mAP50) | GitHub | https://github.com/Tikusu/yolo11n-recycle-waste-detection |
| TrashMonkey YOLO11n (80.5%) | GitHub | https://github.com/tr4m0ryp/TrashMonkey |
| Alope YOLO11n (4-class) | HuggingFace | https://huggingface.co/Alope/trash-detection-yolo11n |
| CBAM-Enhanced YOLO11n (96% TrashNet) | IEEE | https://doi.org/10.1109/icitri67507.2025.11232874 |

### 11.2 Datasets

| Dataset | URL |
|---------|-----|
| Recycle Trash (NAVER) | https://github.com/connectfoundation/naverconnect-dataset-trash |
| SortWaste (WACV 2026) | https://sortwaste.di.ubi.pt |
| SortWaste Paper | https://arxiv.org/abs/2601.02299 |
| TrashNet | https://github.com/garythung/trashnet |
| TACO | https://github.com/pedropro/TACO |
| Garbage Detection (Ultralytics) | https://platform.ultralytics.com |

### 11.3 YOLO Documentation

| Resource | URL |
|----------|-----|
| YOLO11 docs | https://docs.ultralytics.com/models/yolo11/ |
| YOLO26 docs | https://docs.ultralytics.com/models/yolo26/ |
| YOLO11 vs YOLO26 | https://docs.ultralytics.com/compare/yolo11-vs-yolo26/ |
| Knowledge Distillation Guide | https://docs.ultralytics.com/guides/knowledge-distillation/ |
| Training Modes | https://docs.ultralytics.com/modes/train/ |
| Callbacks | https://docs.ultralytics.com/usage/callbacks/ |
| DistillationModel API | https://docs.ultralytics.com/reference/nn/distill_model/ |
| Ultralytics GitHub | https://github.com/ultralytics/ultralytics |
| YOLO11 on HF | https://huggingface.co/Ultralytics/YOLO11 |
| YOLO26 on HF | https://huggingface.co/Ultralytics/YOLO26 |

### 11.4 Platform

| Resource | URL |
|----------|-----|
| Marimo molab | https://molab.marimo.io |
| Marimo docs | https://docs.marimo.io/guides/molab/ |
| Marimo GitHub | https://github.com/marimo-team/marimo |

### 11.5 Research Papers

| Paper | DOI / URL |
|-------|-----------|
| Tikusu — YOLO11n Transfer Learning for Waste | https://doi.org/10.36341/rabit.v11i1.7323 |
| CBAM-Enhanced YOLO11n for Solid Waste | https://doi.org/10.1109/icitri67507.2025.11232874 |
| SortWaste — Industrial Waste Dataset | https://arxiv.org/abs/2601.02299 |
| YOLO11 vs YOLO26 for PPE Detection | https://www.mdpi.com/2079-9292/15/6/1146 |
| Lightweight YOLO for PET/HDPE Sorting | https://pmc.ncbi.nlm.nih.gov/articles/PMC12823588/ |
| Mobile Waste Detection Comparison | https://ijsra.net/sites/default/files/fulltext_pdf/IJSRA-2025-1052.pdf |
| YOLOv11s Household Waste Detection | https://doi.org/10.1016/j.procs.2025.09.104 |
| YOLOv11 Multi-Object Waste Detection | https://doi.org/10.5281/zenodo.20118959 |

---

*Plan generated July 25, 2026. Experiment results will be appended to `results/experiments_log.md`.*
