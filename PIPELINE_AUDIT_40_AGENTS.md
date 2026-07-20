# MIRA Pipeline — 40-Agent Audit & Research Report

> Generated after 40 parallel agents completed:  
> 20 agents → code audit (bugs, severity, suggestions for each source file)  
> 10 agents → external waste detection pipeline research  
> 10 agents → pipeline design patterns & IDE tools research

---

## Part 1 — Code Audit Results (20 agents)

### 1. `src/config.py` (112 lines) — CRITICAL

| Issue | Severity | Detail |
|-------|----------|--------|
| Module-level `[]` key lookups crash on import | **CRITICAL** | `PROJECT_CONFIG["paths"]["reference"]` on line 21 raises `KeyError` if YAML key is missing. Since these run at module import, the entire application fails to start. No fallback or validation. |
| Mutable internal state exposed | **HIGH** | `get_project_config()` (line 54) returns `PROJECT_CONFIG` directly — callers can mutate global config |
| `DETECTION_MODEL_LABELS` hardcoded | **MEDIUM** | Adding a new model requires editing this dict. Each model has a `.pt` + `_int8.tflite` pair, both need entries. Proposal: replace with sidecar `.yaml` files auto-discovered by `ModelRegistry` |
| `get_tflite_imgsz()` creates full interpreter | **LOW** | Lines 64–98: Instantiates TFLite `Interpreter`, reads shape, then deletes it. For a trivial metadata read. Could use `Interpreter.get_signature_runner()` or parse from model filename convention |

**Fix:** Add validation with descriptive errors on lines 21–26; freeze config with `types.MappingProxyType`; replace DETECTION_MODEL_LABELS with sidecar YAML system.

---

### 2. `src/pipeline/models.py` (302 lines) — HIGH

| Issue | Severity | Detail |
|-------|----------|--------|
| `discover()` clears `_models` but NOT `_adapters` | **HIGH** | Line 210: `self._models.clear()`. But `_adapters` is never cleared during `discover()` — stale cached adapters persist after refresh |
| `list_models()` crashes on non-existent paths | **HIGH** | Lines 266–267: `.stat().st_size` raises `FileNotFoundError` if path was deleted between `discover()` and `list_models()`. The `.exists()` check on line 266 runs first, then `.stat()` on line 267 races |
| `_load_descriptor` uses `Path("")` fallback | **MEDIUM** | Line 249: `model_path = Path(data.get("model_file", ""))` — `Path("")` points to CWD, not "not found". Should warn and skip instead |
| No adapter caching refresh | **LOW** | `load_model()` returns cached adapter on line 279 if `_loaded` is True — but never re-validates that the underlying model file still exists |
| `ThirdPartyAdapter` silently returns empty results | **LOW** | Lines 199–200: If `predict()` fails and `_model` is `None`, returns `InferenceResult(detections=[])` with `latency_ms=0.0` — caller can't distinguish "no detections" from "model error" |

**Fix:** Clear `_adapters` in `discover()`; fix race condition with atomic path check/stat; handle `Path("")` fallback; add error flag to InferenceResult.

---

### 3. `src/pipeline/registry.py` (135 lines) — HIGH

| Issue | Severity | Detail |
|-------|----------|--------|
| Adapter registry is dead code | **HIGH** | `register_model_adapter` decorator (line 103) and `_MODEL_ADAPTERS` dict (line 100) are never consumed by `ModelRegistry.load_model()` — that method hardcodes `if/elif` chains for `yolo_pt`, `yolo_tflite`, `third_party` |
| `init_adapters()` called on every `get_model_adapters()` | **LOW** | Line 134: `init_adapters()` runs every time, re-registering the same adapters (harmless but unnecessary) |
| Decorator-based API inconsistent | **LOW** | Some registries use decorators (`register_command`), others are class-based (`ModelRegistry`). Mixing patterns confuses contributors |

**Fix:** Remove adapter registry dead code, or make `ModelRegistry.load_model()` consult `_MODEL_ADAPTERS` instead of hardcoded if/elif. Unify to one pattern.

---

### 4. `src/pipeline/benchmark.py` (283 lines) — HIGH

| Issue | Severity | Detail |
|-------|----------|--------|
| Bypasses `ModelRegistry` entirely | **HIGH** | Line 167: `model = YOLO(str(model_path), task=task_type)` — loads YOLO directly instead of using `ModelRegistry.load_model()` which would use `DetectionModel` adapters. `ThirdPartyAdapter` never gets invoked |
| Per-class TP/FP/FN uses set membership → loses double-counting | **HIGH** | Lines 196–199: `pred_classes = set(boxes.cls.int().tolist())` — if a model predicts TWO bottles of the same class, the set collapses them to one. Correct metric computation requires per-instance matching (IoU-based) |
| No mAP/mAP50 calculation | **MEDIUM** | The benchmark computes micro-averaged precision/recall/F1 per-image but never calculates mAP, which is the standard object detection metric |
| `max_images` divides dataset after loading | **LOW** | Line 155: Slices samples after loading the full dataset. For large datasets, this wastes time. Could skip early |
| `BenchmarkResult` passes model_type as file suffix | **LOW** | Line 174: `model_type=model_path.suffix` (`.pt`, `.tflite`) — inconsistent with `ModelRegistry` which uses `yolo_pt`, `yolo_tflite`, `third_party` |

**Fix:** Refactor to accept `DetectionModel` instances from `ModelRegistry.load_model()`; use IoU-based per-instance matching; add mAP computation; use consistent model type strings.

---

### 5. `src/pipeline/train.py` (311 lines) — CRITICAL

| Issue | Severity | Detail |
|-------|----------|--------|
| Augmentation defaults differ between `AugmentConfig` and `mira.yaml` | **CRITICAL** | `AugmentConfig.degrees=0.0` vs `mira.yaml` `degrees: 10.0`; `mixup: 0.0` vs `0.1`; `copy_paste: 0.0` vs `0.1`. Whichever path creates `TrainConfig` determines the augmentation used |
| `export_model()` re-instantiates YOLO from disk | **HIGH** | Line 191: `model = YOLO(model_path)` — the trained in-memory model is discarded and re-loaded from disk. Could fail if `best.pt` wasn't saved properly |
| `from_yaml()` never reads augmentation from config | **HIGH** | Lines 100–106: Always uses `data.pop("augmentation", {})` — if the YAML has no `augmentation` key, defaults silently override `mira.yaml` values |
| `TrainConfig` defaults read PROJECT_CONFIG at class definition time | **MEDIUM** | Lines 59–71: Default values like `PROJECT_CONFIG.get("training", {}).get("default_epochs", 120)` are evaluated once at import, not at instantiation. Dependency injection impossible |
| No training metrics returned from YOLO | **LOW** | Lines 168–170: Only reads `map50` and `map`. Ignores per-class metrics, precision, recall curves |

**Fix:** Make `AugmentConfig` defaults match `mira.yaml` exactly; have `from_yaml()` read augmentation from `mira.yaml` as fallback; pass in-memory model to `export_model()`; lazy-evaluate defaults.

---

### 6. `src/pipeline/dataset.py` (334 lines) — CRITICAL

| Issue | Severity | Detail |
|-------|----------|--------|
| Fragile root-path resolution via `yaml_path.parent.parent.parent` | **CRITICAL** | Line 65: `root = yaml_path.parent.parent.parent` — breaks if registry directory structure changes. A YAML file at `datasets/registry/foo.yaml` requires exactly this nesting |
| `sys.path` mutated at import time (line 31–33) | **CRITICAL** | `sys.path.insert(0, _SCRIPTS_DIR)` runs when the module is imported. Side effects at import time can cause hard-to-debug path shadowing |
| Dual competing dataset registries | **HIGH** | `_DATASET_SOURCES` in `registry.py` (decorator-based) and `sources` dict in `DatasetRegistry` (class-based) — two systems for the same purpose |
| `_merge_passthrough()` imports inside loop | **LOW** | `from merge_utils import copy_passthrough` inside a method called repeatedly — fine for a CLI tool but unnecessary |
| `_merge_remapped()` `valid`→`val` mapping | **LOW** | Hardcoded split-name normalization on line 257. Other datasets might use `test` or `eval` |

**Fix:** Use `ROOT_DIR` from `config.py` instead of parent traversal; move `sys.path` modification to a lazy import helper; unify DatasetRegistry with registry.py; move imports to module level.

---

### 7. `src/inference_engine.py` (155 lines) — HIGH

| Issue | Severity | Detail |
|-------|----------|--------|
| CameraStream race: `ret`/`frame` not updated atomically | **HIGH** | `_reader()` (line 44–47): Writes `self.ret` then `self.frame` in two separate assignments under lock. Under non-GIL Python implementations (or C extension threads), `read()` could see a stale `ret` with a fresh `frame` or vice-versa |
| `_load_model()` duplicates model scanning logic | **MEDIUM** | Lines 34–36: Scans `DETECTION_DIR` glob — duplicates `get_detection_models()` from `config.py` |
| Skip-frame logic inverted | **LOW** | Line 129–130: `self.skip_frame = avg_latency > self.target_latency_ms` — skip is enabled when average latency exceeds target. But `skip_frame` is only consumed once, then reset to False (line 104). So every other frame is skipped, halving FPS regardless |
| Hardcoded model format list | **LOW** | Line 34: Only `.pt`, `.tflite`, `.keras` considered. Third-party adapters ignored |

**Fix:** Use `dataclass` for frame pair updates; deduplicate with `get_detection_models()`; review skip-frame logic (should use a counter or timer).

---

### 8. `src/cli.py` (275 lines) — MEDIUM

| Issue | Severity | Detail |
|-------|----------|--------|
| `benchmark` command circumvents ModelRegistry | **HIGH** | Lines 195–197: Calls `registry.get_model(name)` for path resolution but then passes raw paths to `ModelBenchmark`, which loads YOLO directly. No `DetectionModel` adapter path used |
| Deprecated commands still registered | **LOW** | `cmd_data_build`, `cmd_train_detection`, `cmd_quant_class`, `cmd_quant_yolo`, etc. remain but print deprecation messages |
| `eval-yolo` imports YOLO inside function | **LOW** | Line 112: `from ultralytics import YOLO` inside function — delayed import is intentional for startup speed but not consistent |

---

### 9. `src/model_picker.py` (86 lines) — HIGH

| Issue | Severity | Detail |
|-------|----------|--------|
| Windows `UnicodeDecodeError` on function keys | **HIGH** | Line 18: `return ch.decode()` — if `msvcrt.getch()` returns bytes not decodable as UTF-8 (e.g., function keys F1–F12 send multi-byte escape sequences), `decode()` raises `UnicodeDecodeError` |
| Unix reads only 2 bytes for escape sequences | **MEDIUM** | Lines 37–38: `sys.stdin.read(2)` assumes escape sequences are exactly 2 bytes after `\x1b`. VT100 sequences can be longer (e.g., `\x1b[15~` for F5) |
| No `__future__` annotations | **LOW** | Missing `from __future__ import annotations` unlike other modules |
| Hardcoded `cls`/`clear` | **LOW** | Line 53: `os.system("cls" if sys.platform == "win32" else "clear")` — works but flashes screen. Alternative: ANSI escape codes or `curses` |

**Fix:** Use `ch.decode("utf-8", errors="replace")` for Windows; buffer multi-byte escape sequences on Unix.

---

### 10. `src/visualize.py` (58 lines) — LOW

| Issue | Severity | Detail |
|-------|----------|--------|
| No `__future__` annotations | **LOW** | Missing `from __future__ import annotations` |
| Color-blind unfriendly | **LOW** | Green/yellow scheme is hard for deuteranopia. Use shapes or patterns |
| `reject_threshold` param unused | **LOW** | Line 13: parameter `reject_threshold` accepted but logic on line 40 uses `conf >= reject_threshold` literally — it IS used, but could have clearer semantics |
| No empty-result guard annotation | **LOW** | Returns raw frame when no detections — fine, but no visual indicator that inference ran and found nothing |

---

### 11. `src/dashboard/main.py` (190 lines) — CRITICAL

| Issue | Severity | Detail |
|-------|----------|--------|
| CORS `allow_origins=["*"]` with `allow_credentials=True` | **CRITICAL** | Line 67–72: CORS spec says `Access-Control-Allow-Origin: *` MUST NOT be used with `Access-Control-Allow-Credentials: true`. Browsers will reject the response |
| Binds to 0.0.0.0 with no authentication | **HIGH** | Line 166: `host="0.0.0.0"` — accessible to anyone on the network. No auth middleware on any endpoint |
| Path traversal in model loading via `model_name` | **MEDIUM** | `camera_service.load_model(model_config.name, ...)` — if `model_config.name` contains `../`, could load arbitrary files |
| Missing input validation on camera config | **MEDIUM** | `CameraConfig` fields not validated — negative resolution values, extreme FPS, etc. not rejected |
| WebSocket control has no rate limiting | **LOW** | Control WebSocket accepts unlimited commands — potential DoS vector |
| Deprecated `Config.dict()` calls | **LOW** | Lines 84, 93, 130, 141: `.dict()` is deprecated in Pydantic v2 in favor of `.model_dump()` |

**Fix:** Remove `allow_credentials=True` or restrict origins; add auth middleware; validate and sanitize model_name; use Pydantic field validators.

---

### 12. `src/dashboard/camera_service.py` — HIGH

| Issue | Severity | Detail |
|-------|----------|--------|
| No error recovery on camera disconnect | **HIGH** | If camera disconnects mid-stream, no auto-reconnect logic |
| Duplicate model scanning logic | **MEDIUM** | Duplicates `get_detection_models()` pattern |
| No timeout on camera operations | **MEDIUM** | `cv2.VideoCapture.read()` can block indefinitely on corrupted streams |

---

### 13. `src/dashboard/websocket_handler.py` — MEDIUM

| Issue | Severity | Detail |
|-------|----------|--------|
| No backpressure handling | **MEDIUM** | If client is slow, frames queue in memory unbounded |
| WebSocket frame send errors ignored | **MEDIUM** | `await websocket.send_bytes(frame)` can raise on disconnected clients |

---

## Part 2 — External Pipeline Research (10 agents)

### Compared Open-Source Waste Detection Projects

| Project | Stars | Approach | Relevant Features | MIRA Comparison |
|---------|-------|----------|-------------------|-----------------|
| **TrashMonkey** (Tacobotics) | ~20 | YOLO11n, Makefile-driven pipeline, ONNX/TensorRT export | Split Makefiles for train/export/benchmark; ONNX export; Raspberry Pi deployment | MIRA has more structured Python pipeline (CLI + registry pattern); TrashMonkey has better ONNX workflow |
| **TACO** (Pedro F. Proença) | 742 | Dataset toolkit + Mask R-CNN baseline | Rich dataset annotation tools; COCO evaluation; active maintenance | MIRA's dataset merger is more automated; TACO has better annotation tooling |
| **dgozos/waste- detection** | ~15 | Single Jupyter notebook, ROS node | ROS integration; end-to-end training notebook | MIRA is more production-ready with CLI + dashboard |
| **Waste-Detector** (shubham401) | ~10 | TACO-only, YOLOv5 | 1K training images, simple structure | MIRA uses 4 merged datasets (9,774 images) — significantly more data |
| **Trash Detection YOLO** (yasser-123) | ~10 | Gradio interface, 2.7K TACO images | Web UI for testing; single script | MIRA has real-time inference engine + WebSocket dashboard |
| **YOLO-Waste** (niconatali) | ~5 | Flask app, TrashNet + MobileNet | Real-time Flask web server; class-based sorting | MIRA uses FastAPI + YOLO — better detection architecture |
| **RealWaste** | 74 | Dataset + ML pipeline (no detection) | Real-world waste dataset; not detection-ready | MIRA already has working detection pipeline |

### MIRA's Rating vs. External Projects

| Dimension | MIRA | Best External | MIRA Advantage? |
|-----------|------|---------------|-----------------|
| **Pipeline automation** | CLI commands + registry pattern | TrashMonkey (Makefile) | Yes — Python CLI more flexible than Makefiles |
| **Dataset sources** | 4 merged (9,774 images) | TACO (742 stars, bigger community) | No — TACO has more community resources |
| **Model formats** | PT + TFLite (INT8/FP32) + ONNX | TrashMonkey (ONNX + TensorRT) | No — missing TensorRT |
| **Real-time inference** | CameraStream + tracking | TrashMonkey (basic) | Yes — threaded reader + ByteTrack |
| **Dashboard** | FastAPI + WebSocket | YOLO-Waste (Flask) | Yes — modern WebSocket architecture |
| **Evaluation** | Per-class TP/FP/FN + F1 | TACO (standard COCO mAP) | No — missing mAP in pipeline benchmark |
| **Deployment target** | Raspberry Pi 4 | TrashMonkey (RPi) | Comparable — both target RPi |

### External Weights Available for Benchmarking

| Source | Model | Classes | How to Load | Status |
|--------|-------|---------|-------------|--------|
| **gianlucasposito** | YOLOv8n | 5-class waste (glass, metal, paper, plastic, trash) | Direct download `best_model.pt` from GitHub releases | ✅ Direct download available |
| **kendrickfff** | YOLOv8 | 12-class (battery, glass, metal, paper, plastic, etc.) | `YOLO("kendrickfff/yolov8_waste_detection")` | ✅ HuggingFace auto-load |
| **TrashMonkey** | YOLO11n | Multi-class | `best.pt` saved after training | ❌ No pre-trained weights published |
| **dgozos** | YOLOv8 | N/A | No weights in repo | ❌ No weights published |

### Literature References

- **"Campus-Scale Smart Waste Classification" (2026):** YOLOv8n on RPi 5 achieved mAP50 0.990 on 5-class waste (paper, plastic, can, glass, biodegradable) with 2,000 images — unrealistically high, likely overfitted
- **"Edge-Enabled Real-Time Waste Detection" (2025):** Lightweight backbones (MobileNetV3 + attention) reduced inference from 480ms to 350ms on RPi 4B; mAP50 ~0.85
- **"Deep Learning for Waste Classification" (2024):** Survey of 50+ papers; ensemble methods consistently outperform single models by 3–7% mAP
- **"Optimizing YOLO for Edge Deployment" (2025):** YOLOv8n INT8 quantization reduces model size 75% with < 2% mAP drop; recommended for RPi deployment

---

## Part 3 — Pipeline Design Patterns & IDE Research (10 agents)

### Recommended Design Patterns

| Pattern | Source | Recommendation |
|---------|--------|---------------|
| **MMDetection-style Registry** | MMDetection docs | Replace hardcoded `if/elif` in `ModelRegistry.load_model()` with decorator-based adapter registration. Already partially implemented in `registry.py` but never consumed |
| **Sidecar metadata files** | Kubernetes / MLflow convention | Each model file gets a `.yaml` sidecar with `class_names`, `input_size`, `description`, `recommended_for`. Replaces `DETECTION_MODEL_LABELS` dict |
| **Hydra-style config composition** | Facebook Hydra | `AugmentConfig` should compose from `mira.yaml` + experiment override, not exist independently |
| **Plugin discovery** | HuggingFace Hub / setuptools | `ModelRegistry.discover()` should scan for sidecar YAMLs, not hardcode model types |
| **Strategy pattern** | GoF | `TrainingPipeline` should use pluggable strategies per task (detection vs classifier), not `if task == "classifier"` |
| **Repository pattern** | DDD | Dataset access should go through one `DatasetRegistry`, not two competing systems (`_DATASET_SOURCES` + `DatasetRegistry.sources`) |

### Recommended IDE / DevTools

| Tool | When to Use |
|------|-------------|
| **FastAPI Swagger UI** | Already available at `/docs` — use for dashboard API testing |
| **Pydantic V2 validators** | For `CameraConfig` and `ModelConfig` input validation |
| **Hydra config composition** | If experiment configurations grow beyond 10+ YAML files |
| **MLflow** | For experiment tracking (currently manual logging to `results/experiments_log.md`) |
| **Great Expectations** | For dataset quality checks before merging sources |
| **DVC** | For dataset versioning (currently managing 4 sources manually) |
| **Cookie Cutter Data Science** | If restructuring the repo layout |

### GitHub / VS Code Integration

- **VS Code Launch Configs** recommended for: `mira live`, `mira dashboard`, `mira train`, individual pytest files
- **GitHub Actions** for: training CI (trigger re-training on dataset changes), benchmark comparison across PRs
- **pre-commit hooks** already configured in `.pre-commit-config.yaml`

---

## Part 4 — Proposed Architecture: Sidecar Metadata System

### Current (Broken) Design
```
DETECTION_MODEL_LABELS = {
    "mira_exp014.pt": "EXP-014 (YOLO11n, +Roboflow)",
    "mira_exp014_int8.tflite": "EXP-014 INT8 (YOLO11n, +Roboflow)",
    ...
}
```
- Hardcoded in `config.py`, requires editing source to add models
- No way to store class_names, input_size, or training metadata per model
- Duplicate entries for .pt + _int8.tflite pairs

### Proposed Design
```
models/detection/
  mira_exp014.pt
  mira_exp014.yaml          # sidecar
  mira_exp014_int8.tflite
  mira_exp014_int8.yaml     # sidecar (can reference parent)
  example_third_party.yaml  # already exists
```

**Sidecar schema (mira_exp014.yaml):**
```yaml
name: mira_exp014
display_name: "EXP-014 (YOLO11n, +Roboflow)"
model_type: yolo_pt
task: detect
input_size: 640
class_names: ["glass", "metal", "paper", "plastic", "trash"]
training:
  dataset: taco+trashnet+roboflow
  epochs: 120
  date: 2025-01-15
metrics:
  map50: 0.607
  map50_95: 0.455
tags: ["yolo11n", "multidataset", "best-so-far"]
recommended_for: "raspberry_pi"
```

**Discovery logic (ModelRegistry.discover() v2):**
```python
def discover(self) -> int:
    self._models.clear()
    self._adapters.clear()
    count = 0
    for p in sorted(self.detection_dir.iterdir()):
        if p.suffix == ".yaml" and not p.name.startswith("example"):
            info = self._load_sidecar(p)
            self._models[info["name"]] = info
            count += 1
        elif p.suffix in (".pt", ".pth", ".tflite"):
            sidecar = p.with_suffix(".yaml")
            if not sidecar.exists():
                # auto-register with inferred type
                self._register_inferred(p)
                count += 1
    return count
```

### CLI Filtering (Post-Sidecar)
```bash
mira models                          # all models
mira models --type yolo_pt           # only PyTorch models
mira models --tag best-so-far        # tagged models
mira models --recommended rpi        # Raspberry Pi suitable
mira benchmark --best                # best model by mAP50
mira models --latest                 # most recent by training date
```

---

## Part 5 — Actionable Priority Queue

### P0 — Fix Now (Blocks Correctness)
1. **Config.py:** Add key validation + fallbacks for `PROJECT_CONFIG` lookups (line 21+)
2. **Train.py:** Sync `AugmentConfig` defaults with `mira.yaml` (degrees: 10.0, mixup: 0.1, copy_paste: 0.1)
3. **Benchmark.py:** Refactor to use `ModelRegistry.load_model()` — currently bypasses all adapter logic
4. **Dataset.py:** Replace `yaml_path.parent.parent.parent` with `ROOT_DIR / data["input_path"]`

### P1 — Fix Soon (Important for Correctness)
5. **Benchmark.py:** Replace per-class set-based TP/FP/FN with IoU-based per-instance matching
6. **Dashboard/main.py:** Fix CORS `allow_origins=["*"]` + `allow_credentials=True`
7. **Models.py:** Fix `_load_descriptor` empty-path fallback
8. **Inference_engine.py:** Fix CameraStream race condition with atomic frame update
9. **Dashboard/main.py:** Add auth middleware for 0.0.0.0 binding

### P2 — Refactor (Architecture)
10. **Implement sidecar metadata system** — replace `DETECTION_MODEL_LABELS`
11. **Remove dead adapter registry** from `registry.py` or wire it into `ModelRegistry`
12. **Unify `DatasetRegistry`** (dataset.py) with `_DATASET_SOURCES` (registry.py)
13. **Remove sys.path mutation** from dataset.py

### P3 — Enhance (Features)
14. Add mAP calculation to benchmark (currently micro-F1 only)
15. Download gianlucasposito `best_model.pt` for comparison
16. Auto-load kendrickfff from HuggingFace
17. Add TensorRT export option
18. Add ONNX export to export_model()
19. Fix model_picker.py Windows UnicodeDecodeError

### P4 — Polish
20. Add VS Code launch configs for pipeline commands
21. Add dataset tests with Great Expectations
22. Add DVC for dataset versioning
23. Add GitHub Actions workflow for benchmark comparison
24. Ensure all files use `from __future__ import annotations`

---

**Report generated from 40 parallel agent results**  
Files audited: config.py, models.py, registry.py, benchmark.py, train.py, dataset.py, cli.py, inference_engine.py, model_picker.py, visualize.py, dashboard/main.py, dashboard/camera_service.py, dashboard/models.py, dashboard/websocket_handler.py  
Projects researched: TrashMonkey, TACO, dgozos, Waste-Detector, Trash Detection YOLO, YOLO-Waste, RealWaste  
Patterns researched: MMDetection Registry, HuggingFace Hub, MLflow, sidecar metadata, Hydra, DVC, Cookie Cutter DS
