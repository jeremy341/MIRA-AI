# Related Work - Waste Detection with YOLO Variants

| Work | Model | Classes | Dataset | mAP@0.5 | Notes |
|---|---|---|---|---|---|
| Nasien et al. (2025) | YOLO11 | 5 | 10,464 custom | ~94% acc | Accuracy metric, not mAP |
| Marwah & Chowanda (2025) | YOLO11s | household | TACO + custom | 72.6% | After quantization |
| Messai et al. (2025) | YOLO11-x | 8 | Industrial | 62.8% | 56.9M params vs MIRA's 2.58M |
| **MIRA EXP-014** | **YOLO11n** | **5** | **TACO+TrashNet+Roboflow** | **60.7% FP32** | **Historical older-dataset result; INT8 size 2.90 MiB, INT8 mAP pending** |

> Direct comparison is difficult because every study uses different class schemas, datasets, and evaluation protocols. MIRA's *trash* class (residual waste) is particularly challenging - most recycling datasets omit it entirely.

