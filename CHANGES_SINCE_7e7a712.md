# MIRA-AI — Changelog since `7e7a712`

> All changes after commit `7e7a71239c84c860d32abeac47172ae32692a119` (July 2026).
> 15 commits, ~2200 lines added, ~1000 lines removed.

---

## New Models (EXP-013 through EXP-016)

| EXP | Architecture | Dataset | mAP50 | mAP50-95 | INT8 Size | Training Time | Notes |
|-----|-------------|---------|-------|----------|-----------|---------------|-------|
| EXP-013 | YOLO11n | TACO + TrashNet (`mira_v2`, 4024 imgs) | 55.1% | 49.8% | 2.90 MB | 2.73h (120e) | First YOLO11n model, +20pp over EXP-011 |
| **EXP-014** | **YOLO11n** | **TACO + TrashNet + Roboflow (`mira_tnr`, 6802 imgs)** | **60.7%** | **50.6%** | **2.90 MB** | **4.70h (120e)** | **BEST MODEL — 85.8% F1 on field benchmark** |
| EXP-015 | YOLO11n | TACO + TrashNet + WaRP (`mira_tnw`, ~6800 imgs) | 56.0% | 45.1% | 2.90 MB | 3.71h (120e) | Glass +24.8pp, Trash -12.6pp vs EXP-014 |
| EXP-016 | YOLO11n | WaRP only (`mira_warp_only`) | 58.8% | 43.2% | 2.90 MB | 1.07h (120e) | No Trash class; specialized glass/plastic |

### Field Benchmark (real-world precision/recall on mira_v2 val)

| Model | Precision | Recall | F1 | Notes |
|-------|-----------|--------|----|-------|
| **mira_exp014.pt** | **92.9%** | **79.7%** | **85.8%** | **Best overall** |
| mira_exp014_int8.tflite | 96.1% | 58.6% | 72.8% | INT8 costs ~13pp F1 |
| mira_exp011_int8.tflite | 0.0% | 0.0% | 0.0% | Needs conf≤0.25 (was tested at 0.5) |
| mira_exp011.pt | 86.9% | 74.4% | 80.2% | TACO-only baseline |

### Model Naming Convention (established)
- `mira_exp<NNN>.pt` — full precision PyTorch
- `mira_exp<NNN>_int8.tflite` — INT8 quantized LiteRT

---

## New Files Created

| File | Purpose |
|------|---------|
| `src/config.py` | Shared paths (`ROOT_DIR`, `DETECTION_DIR`, `CLASS_NAMES`), `get_detection_models()`, `get_tflite_imgsz()` |
| `src/visualize.py` | Unified `draw_boxes()` — replaces 3 duplicates |
| `src/field_benchmark.py` | Runs all detection models on any YOLO val set, computes per-class TP/FP/FN/P/R/F1 |
| `src/model_picker.py` | Interactive arrow-key model selector for CLI |
| `scripts/warp_utils.py` | Shared WaRP class remapping logic (28→5 classes) |
| `scripts/merge_dataset_model2.py` | WaRP merge for `mira_tnw` (TACO+TrashNet+WaRP) |
| `scripts/merge_dataset_model3.py` | Roboflow-only merge (TACO+Roboflow) |
| `scripts/merge_dataset_model4.py` | Full merge for `mira_all` (TACO+TrashNet+Roboflow+WaRP) |
| `results/field_benchmark_results.md` | Field benchmark comparison table |
| `docs/naming_convention.md` | Dataset/experiment/model naming rules |
| `.gitattributes` | LF/CRLF line ending normalization |

---

## Refactored Files (shared modules eliminated duplication)

| File | Change |
|------|--------|
| `src/live_detector.py` | Imports `config`, `visualize`; removed inline `draw_boxes_corrected`, `CLASS_NAMES`, `DETECTION_MODEL_LABELS`, `MODELS_DIR` |
| `src/debug_detector.py` | Same imports; removed dead `--use-int8` flag, inline constants, inline `draw_boxes_optimized` |
| `src/dashboard.py` | Same imports; removed `draw_boxes_streamlit`, inline constants, deprecated `st.experimental_rerun`, unused `pathlib` import |
| `src/cli.py` | Imports `config`; added model validation (`ValueError` for missing `.pt`/`.tflite`), `mira.bat` wrapper |
| `src/capture_classifier_frames.py` | Imports `config.DATA_CLASSES_DIR` |
| `src/visualize_classifier_dataset.py` | Imports `config.DATA_CLASSES_DIR` |

### Before vs After
```
BEFORE: 3× draw_boxes() + 3× CLASS_NAMES + 2× DETECTION_MODEL_LABELS + 2× MODELS_DIR
AFTER:  1× draw_boxes() (src/visualize.py) + 1× constants (src/config.py)
```

---

## Bug Fixes

### 1. Tracker Swap (Critical)
- **Files:** `src/live_detector.py`, `src/debug_detector.py`
- **Bug:** Tracker init order was `BoTSSORT → ByteTrack` — both failed because `BoTSSORT` requires `boxmot` package
- **Fix:** Swapped to `BYTETracker → BoTSSORT` (ByteTrack as first choice, BoTSSORT as fallback)
- **Impact:** Live detection and debug commands now work without `boxmot` installed

### 2. Double Confidence Filtering
- **Files:** `src/live_detector.py`, `src/debug_detector.py`
- **Bug:** `model.predict()` had `conf=conf_threshold` AND post-loop filter `if conf > conf_threshold` — double filtering
- **Fix:** Removed `conf` param from `model.predict()`, kept only post-loop filter
- **Impact:** All detections were being aggressively filtered

### 3. No Model Type Validation
- **File:** `src/cli.py`
- **Bug:** CLI accepted `.pt` for INT8 and `.tflite` for FP32 without complaint
- **Fix:** Added validation that raises `ValueError` for mismatched model types
- **Impact:** Prevents silent failures from wrong model format

### 4. INT8 Confidence Threshold
- **File:** `src/field_benchmark.py`
- **Bug:** INT8 models tested at `conf=0.5` — INT8 quantization shifts scores down, so `mira_exp011_int8.tflite` produced 0 detections
- **Fix:** Auto-caps to `min(conf, 0.25)` for INT8 models
- **Impact:** EXP-011 INT8 now shows real performance (1.6 det/img vs 0)

### 5. Model Picker Arrow Keys
- **File:** `src/model_picker.py`
- **Bug:** Arrow keys not responding in interactive model selector
- **Fix:** Fixed keyboard input handling

---

## Renamed Files

### Model Files (`models/`)
```
BEFORE → AFTER
models/EXP-006.pt → models/detection/mira_exp006.pt
models/EXP-006_int8.tflite → models/detection/mira_exp006_int8.tflite
models/EXP-009_int8.tflite → models/detection/mira_exp009_int8.tflite
models/EXP-011.pt → models/detection/mira_exp011.pt
models/EXP-011_int8.tflite → models/detection/mira_exp011_int8.tflite
models/classifier/* → models/classifier/*  (split into subfolder)
```

### Scripts (`scripts/`)
```
build_dataset.py → build_raw_dataset.py
convert_taco.py → convert_taco_to_yolo.py
label_trashnet.py → label_trashnet_with_sam.py
add_trashnet.py → add_trashnet_to_dataset.py
merge_mira_v3.py → merge_dataset_mira_v3.py
merge_model1.py → merge_dataset_model1.py
kaggle_train.py → train_detector_kaggle.py
```

### Results (`results/`)
```
EXP-006_YOLOv8_Super → exp006_yolov8n_super
(all other EXP- folders → exp* convention)
```

### Reference Scripts
```
reference/evaluate.py → reference/evaluate_classifier.py
reference/inference.py → reference/evaluate_classifier_reference.py
reference/classify_archive.py → reference/live_classifier.py
reference/prepare_dataset.py → reference/prepare_detector_super_dataset.py
reference/quantize.py → reference/quantize_classifier.py
reference/quantize_yolo.py → reference/quantize_detector.py
reference/train_baseline.py → reference/train_classifier_baseline.py
reference/train_fine_tune.py → reference/train_classifier_finetune.py
reference/train_transfer.py → reference/train_classifier_transfer.py
reference/train_detection.py → reference/train_detector.py
```

### Dead Files Removed
```
scripts/merge_model2.py → deleted (replaced by scripts/merge_dataset_model2.py)
scripts/merge_model3.py → deleted (replaced by scripts/merge_dataset_model3.py)
scripts/merge_model4.py → deleted (replaced by scripts/merge_dataset_model4.py)
scripts/merge_mira_v3.py → deleted (unused)
```

---

## Dataset Changes

| Dataset | Source Files | Composition |
|---------|-------------|-------------|
| `mira_v2` | TACO + TrashNet | 1497 wild + 2527 tabletop |
| `mira_tnr` | TACO + TrashNet + Roboflow | + ~2778 Roboflow Trash Detection |
| `mira_tnw` | TACO + TrashNet + WaRP | + ~2800 WaRP Waste Detection |
| `mira_all` | All four | Planned (Model 4 training pending) |

### Naming Convention
- Combined datasets: `mira_<initials>` (v2, tnr, tnw, all)
- Raw source datasets: `<source>_raw` (taco_raw, roboflow_raw, mira_warp, trashnet_labeled)

---

## Documentation

| File | Change |
|------|--------|
| `README.md` | Full sync: directory tree updated (added `docs/`, `config.py`, `visualize.py`; removed `merge_dataset_mira_v3.py`), 4-model table, EXP-011 INT8 note, scripts list |
| `results/experiments_log.md` | Added EXP-013, EXP-014, EXP-015, EXP-016 entries with full metrics |
| `results/field_benchmark_results.md` | Corrected EXP-011 INT8 finding ("broken" → "needs conf≤0.25") |
| `src/__init__.py` | Populated with docstring |

---

## Configuration Changes

- `requirements.txt` — Updated encoding, pinned ultralytics version
- `.gitattributes` — Added LF/CRLF normalization for `.py`, `.md`, `.yaml`, `.txt`, `.tex`, `.bib`
- Removed deprecated `st.experimental_rerun` from `dashboard.py`
- Removed dead `--use-int8` CLI flag from `debug_detector.py`

---

## Git History

```
ce2c180 docs: sync README to current structure; cleanup dead code
d1d1771 refactor: shared config/visualize modules; fix INT8 conf auto-cap in field_benchmark; rename results to exp* convention
ff6d2ac fix: EXP-016 result structure, cleanup temp artifacts
7d489a1 feat: EXP-016 weights, field benchmark results
b3487cf refactor: models/ split into classifier/ + detection/; feat: EXP-016 WaRP only results
0f90571 refactor: field_benchmark now runs on existing YOLO val datasets instead of manual capture
8772396 feat: field_benchmark.py — real-world model comparison on webcam images
e84ee03 docs: badges, model picker docs, benchmarks section, renumber sections
e5310ee fix: arrow keys in model picker, rename legacy train_detector.py
e741376 feat: interactive model picker for live/eval-yolo commands
ab066e5 refactor: rename models to mira_exp<NNN> scheme, rename all scripts consistently
489d147 feat: add EXP-014/015 models and results (Model 1 & 2)
62f71b8 docs: add EXP-015 results (Model 2 — 56.0% mAP50)
6fc505d docs: add EXP-014 results (Model 1 — 60.7% mAP50)
f693b2f refactor: extract shared WaRP logic, add __init__.py, improve dashboard
9757362 fix: requirements.txt encoding, ultralytics version, remove dead CLI command
```

---

## Key Decisions

1. **YOLO11n over YOLOv8n** — 14% fewer parameters (2.58M vs 3.01M), faster inference, better mAP50
2. **TACO+TrashNet+Roboflow as primary dataset** (`mira_tnr`) — EXP-014 achieves best field benchmark
3. **INT8 confidence rule** — Always use `conf ≤ 0.25` for quantized models
4. **No dataset zipping** — Keep datasets uncompressed for fast training access
5. **Kaggle as primary training platform** — T4 GPU, ~$0 cost, 30h/week quota

---

## What's Pending

- [ ] Folder cleanup (17.3 GB → <500 MB) — purge duplicates, git history, fix `.gitignore`
- [ ] Model 4 training (`mira_all`) — blocked on Kaggle quota exhaustion
- [ ] Missing JuFo figures (EXP-014/015/016 confusion matrices, field benchmark chart)
- [ ] Missing JUFO citations (7 academic refs)
- [ ] Git push — repo too large; needs cleanup first
