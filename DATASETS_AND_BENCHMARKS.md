# MIRA-AI: Datasets & Benchmarks

## Training Datasets

### Primary training sources

| # | Dataset | Images | Classes | Size | License | URL | Notes |
|---|---------|--------|---------|------|---------|-----|-------|
| 1 | **SortWaste** (WACV 2026) | 5,261 | 8→5 remap | ~12.4 GB | Research | `https://sortwaste.di.ubi.pt/datasets/dataset.zip` | Top-down camera, matches deployment geometry |
| 2 | **dmedhi/garbage-image-classification-detection** | 3,491 | 7→5 remap | ~300 MB | CC-BY-4.0 | `https://huggingface.co/datasets/dmedhi/garbage-image-classification-detection` | Has explicit Trash/Garbage boxes; strong glass source |

### Existing (local, already in repo)

| # | Dataset | Images | Classes | Size | License | Notes |
|---|---------|--------|---------|------|---------|-------|
| 3 | **TACO** | 1,500 | 60→5 remap | ~2.6 GB | MIT | Outdoor litter — domain randomization |
| 4 | **Roboflow Raw** | 2,783 | 64→5 remap | ~2.6 GB | CC-BY | Diverse scraped sources — domain randomization |
| 5 | **TrashNet SAM-labeled** | 2,527 | Already 5-class | Local | Existing project data | Clean tabletop examples; held-out val used as tabletop test |

SortWaste is capped during training to prevent its plastic-heavy annotations from dominating. The final training target is approximately balanced by annotation count; validation and test retain their natural source distributions.

**Excluded:**
- mira_warp (user preference)
- TrashNet (classification only, no bounding boxes)
- keremberke/garbage-object-detection (biodegradable→trash creates 45k trash boxes and overwhelms the primary mix)
- alexNova/MRS-Trash-Detection (unknown class names, can't verify trash content)
- ZeroWaste (inaccessible download link)
- Recycle Trash NAVER (120 GB + access-gated)
- WaRP (no public download)

### Target Classes (MIRA)

| ID | Class | Priority |
|----|-------|----------|
| 0 | glass | Normal |
| 1 | metal | Normal |
| 2 | paper | Normal |
| 3 | plastic | Normal |
| 4 | trash | **Weakest (7.1% mAP50) — main improvement target** |

---

## Benchmark Models

Pre-trained YOLO11n/YOLOv8n models for comparison against our distilled model.

| # | Model | Architecture | mAP50 | License | Size | Has Weights | Use |
|---|-------|-------------|-------|---------|------|-------------|-----|
| 1 | **Tikusu** | YOLO11n | **0.840** | MIT | 5.9 MB | ✅ | Best documented, 6-class recyclables |
| 2 | **Alope/trash-detection-yolo11n** | YOLO11n | not reported | AGPL-3.0 | 5.43 MB | ✅ | 4-class, easy HF download |
| 3 | **benl4212/trash-bot-models** | YOLO11n box+seg | not reported | AGPL-3.0 | unknown | ✅ | Has Edge-TPU .tflite for edge comparison |

### Download Links

- Tikusu: `https://github.com/Tikusu/yolo11n-recycle-waste-detection/raw/main/models/backbone-partial-freeze/best.pt`
- Alope: `https://huggingface.co/Alope/trash-detection-yolo11n/resolve/main/best.pt`
- benl4212: `https://github.com/benl4212/trash-bot-models`

### Note on TrashMonkey

TrashMonkey (YOLO11n, 0.805 val mAP50 / 0.498 RealWaste) is well documented but **no public weights**. Useful as a reference number only, not for direct benchmarking.

---

## Reference

- MIRA EXP-014 (current best): YOLO11n INT8, 60.7% mAP50, ~2.9 MB
- Target: distilled YOLO26n INT8, 65-68% mAP50, ~2.5 MB
- Deployment: RPi Zero 2W, 512 MB RAM, TFLite INT8
