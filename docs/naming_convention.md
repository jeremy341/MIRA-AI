# MIRA Naming Convention

## Dataset Folders (`datasets/`)

### Combined Datasets
| Folder | Composition | Train | Val | Used by |
|--------|-------------|-------|-----|---------|
| `mira_v2` | TACO + TrashNet | 3,219 | 705 | Field benchmarks, base for all merges |
| `mira_tnr` | TACO + TrashNet + **R**oboflow | — | — | Model 1 training (EXP-014) |
| `mira_tnw` | TACO + TrashNet + **W**aRP | — | — | Model 2 training (EXP-015) |
| `mira_all` | TACO + TrashNet + Roboflow + WaRP | — | — | Model 4 training (planned) |

### Raw Source Datasets (`*_raw`)
| Folder | Content | Format | Origin |
|--------|---------|--------|--------|
| `taco_raw` | Original TACO dataset | COCO annotations | GitHub: `TACO-master` |
| `roboflow_raw` | Roboflow Trash Detection | 64-class YOLO | Roboflow Universe |
| `mira_warp` | WaRP Waste Detection | 28-class YOLO (Warp-D) | Kaggle |
| `trashnet_labeled` | SAM-labeled TrashNet | 5-class YOLO (bbox) | Local SAM inference |

### Naming Rules
- **Combined:** `mira_<initials>` — short codes describing source datasets
- **Raw:** `<source>_raw` — raw, unprocessed source datasets
- **No** spaces, parentheses, or special characters except `_`

---

## Experiment Folders (`results/`)

| Folder | Model | Dataset | Experiment |
|--------|-------|---------|------------|
| `exp013_yolo11n_v2` | YOLO11n | mira_v2 (TACO+TrashNet) | EXP-013 |
| `exp014_yolo11n_tnr` | YOLO11n | mira_tnr | EXP-014 |
| `exp015_yolo11n_tnw` | YOLO11n | mira_tnw | EXP-015 |
| `exp016_yolo11n_warp` | YOLO11n | mira_warp_only | EXP-016 |

### Pattern
```
exp<NNN>_<arch>_<data>
```

- `<NNN>`: 3-digit experiment number (EXP-013 → exp013)
- `<arch>`: Model architecture (`yolo11n`, `yolov8n`, `mobilenetv2`)
- `<data>`: Dataset short code (matches dataset folder name)

---

## Model Files (`models/`)

| Pattern | Example | Description |
|---------|---------|-------------|
| `mira_exp<NNN>.pt` | `mira_exp014.pt` | Full precision PyTorch |
| `mira_exp<NNN>_int8.tflite` | `mira_exp014_int8.tflite` | INT8 quantized TFLite |
| `mira_classifier_<variant>.keras` | `mira_classifier_baseline.keras` | Stage A classification |
| `mira_classifier_<variant>.tflite` | `mira_classifier_int8.tflite` | Quantized classifier |

- Model filenames never change — the experiment log is the cross-reference
- Look up `mira_exp014.pt` → `exp014_yolo11n_tnr` → trained on `mira_tnr`
- INT8 variant always appends `_int8` before `.tflite` extension

---

## Version History

| Date | Change |
|------|--------|
| 2026-07-13 | Initial convention established |
