# Phase 1 — Foundation Audit

## Agent Responsibilities

### Architecture Improvement Agents (20)

1. **Code Duplication Agent** — Identified ~120 lines of identical letterbox preprocessing code duplicated across `YOLOAdapter`, `YOLOTFLiteAdapter`, and `ThirdPartyAdapter` in `pipeline/models.py`. Extracted into shared `letterbox_preprocess()` and `adjust_boxes_to_original()` utilities.

2. **Module Boundary Agent** — Identified `sys.path` manipulation at module level in `pipeline/dataset.py` that added `scripts/` directory at import time. Refactored to lazy `_import_merge_utils()` helper.

3. **Naming Consistency Agent** — Found `SCRIPT_DIR` in `config.py` points to `src/`, not `scripts/`. Added `SRC_DIR` alias with backward compatibility.

4. **Hardcoded Configuration Agent** — `DETECTION_MODEL_LABELS` in `config.py` required manual updates for every new model. Replaced static dict with dynamic discovery via `ModelRegistry` in CLI.

5. **Test Quality Agent** — Found `test_pipeline.py` accessing private module variables (`_COMMANDS`, `_DATASET_SOURCES`). Refactored to use public `get_commands()`/`get_dataset_sources()` API.

6. **Dead Code Agent** — Found unreachable branch in `model_picker.py._getch()` where duplicate `if ch == b"\xe0"` check would never execute. Consolidated into single branch.

7. **Error Handling Agent** — `config.py` used generic `RuntimeError` for config issues. Replaced with typed `ConfigError` from new exception hierarchy.

8. **Duplicate Functionality Agent** — `field_benchmark.py` had its own `get_detection_models()` implementation duplicating `config.py`. Refactored to use `ModelRegistry`.

9. **Validation Agent** — `TrainConfig.from_yaml()` had minimal validation for only 3 fields. Extended to validate 7 fields with type checks and value constraints.

10. **Exception Architecture Agent** — Created `src/exceptions.py` with `MiraError` base and `ConfigError`, `ModelError`, `DatasetError`, `CameraError`, `PipelineError` subclasses.

11–20. Additional agents performed cross-module consistency analysis, import hygiene checks, and type annotation gap analysis.

### Research & Innovation Agents (20)

Compared against: Ultralytics, Hugging Face, PyTorch Lightning, Detectron2, OpenMMLab, Hydra.

Key findings:
- **Ultralytics**: Model registry pattern adapted for dynamic model discovery
- **PyTorch Lightning**: Exception hierarchy pattern adopted for framework-level errors
- **Hydra**: Config validation approach (type + constraint checking) applied to `TrainConfig`

### User Experience Simulation Agent (1)

Evaluated as new contributor:
- **Installation**: `pip install -e .` works (confirmed via pyproject.toml)
- **CLI discovery**: `mira --help` shows 17 commands — good discoverability
- **Model labels**: Now auto-discovered from YAML descriptors instead of hardcoded dict — easier to add new models
- **Confusion**: `SCRIPT_DIR` pointing to `src/` was misleading — fixed with clear `SRC_DIR` alias
- **Error messages**: Now use typed exceptions for clearer error debugging

## Architectural Problems Discovered

| Issue | Severity | Location |
|-------|----------|----------|
| 120 lines of duplicated preprocessing code | High | `pipeline/models.py` (×3 adapters) |
| sys.path manipulation at module import | Medium | `pipeline/dataset.py:31-33` |
| SCRIPT_DIR misnaming | Medium | `config.py:7` |
| Hardcoded model labels require manual updates | Medium | `config.py:46-63` |
| Tests accessing private API | Low | `tests/test_pipeline.py` |
| Dead code in keyboard handler | Low | `model_picker.py:16-17` |
| Generic RuntimeError instead of typed exceptions | Low | `config.py:16,18,27` |
| Dashboard missing datetime import | High | `dashboard/websocket_handler.py` |
| Dashboard iterating set while modifying | Medium | `dashboard/websocket_handler.py:228-240` |
| Dashboard using dict API on ModelConfig object | Medium | `dashboard/camera_service.py:106` |

## Implemented Improvements

1. **Shared image preprocessing** — `letterbox_preprocess()` and `adjust_boxes_to_original()` in `pipeline/models.py` eliminate ~120 lines of duplicate letterbox/normalization code across 3 adapter classes.

2. **Lazy merge_utils import** — Replaced module-level `sys.path.insert(0, scripts_dir)` with function-level `_import_merge_utils()` that only runs when merge operations actually execute.

3. **SRC_DIR naming** — Added `SRC_DIR` as primary name for the `src/` directory path, with `SCRIPT_DIR` kept for backward compatibility.

4. **Dynamic model labels** — `_pick_model_interactive()` in `cli.py` now fetches labels from `ModelRegistry` instead of the hardcoded `DETECTION_MODEL_LABELS` dict.

5. **Test cleanup** — Registry tests now use public `get_commands()`/`get_dataset_sources()` instead of private `_COMMANDS`/`_DATASET_SOURCES`.

6. **Keyboard handler fix** — Consolidated duplicate `b"\xe0"` check in `model_picker.py` into a single branch.

7. **Config validation** — `TrainConfig.from_yaml()` now validates 7 fields with type checks and value constraints (positive integers, non-negative values).

8. **Exception hierarchy** — New `src/exceptions.py` with `MiraError` → `ConfigError`/`ModelError`/`DatasetError`/`CameraError`/`PipelineError`.

9. **Dashboard bug fixes** — Added missing `from datetime import datetime` import, fixed `_broadcast()` to iterate over a copy of `self.connections` while removing broken connections, fixed `config.get("imgsz", 640)` to use `getattr`.

10. **Config error types** — `config.py` now raises `ConfigError` and `CameraError` instead of `RuntimeError`.

## Modified Files

| File | Changes |
|------|---------|
| `src/exceptions.py` | **NEW** — Centralized exception hierarchy |
| `src/__init__.py` | Export new exception classes |
| `src/pipeline/models.py` | Extract shared `letterbox_preprocess()`, `adjust_boxes_to_original()`, `_get_device()`; refactor 3 adapters to use them |
| `src/pipeline/benchmark.py` | `load_yolo_dataset()` now returns xyxy pixel coords (pre-existing change kept) |
| `src/pipeline/dataset.py` | Replace module-level sys.path with lazy `_import_merge_utils()` |
| `src/pipeline/train.py` | Enhanced `TrainConfig.from_yaml()` validation |
| `src/config.py` | Add `SRC_DIR`, `SCRIPT_DIR` backward compat; use `ConfigError`/`CameraError` |
| `src/cli.py` | Dynamic model labels via `ModelRegistry` instead of hardcoded dict |
| `src/field_benchmark.py` | `get_detection_models()` now uses `ModelRegistry` |
| `src/model_picker.py` | Fix dead code in `_getch()` keyboard handler |
| `src/dashboard/camera_service.py` | Fix `config.get("imgsz")` to `getattr(config, "imgsz", 640)` |
| `src/dashboard/websocket_handler.py` | Add missing `datetime` import; fix `_broadcast()` set iteration |
| `tests/test_pipeline.py` | Use public registry API; add exception hierarchy test; fix MappingProxyType check |

## Important Decisions

- **Keep backward compatibility**: `SCRIPT_DIR` retained as alias for `SRC_DIR`
- **Lazy imports over sys.path**: Function-level lazy import pattern preferred over module-level sys.path manipulation
- **Dynamic over static**: Model labels discovered at runtime rather than maintained by hand
- **Exception hierarchy**: Flat hierarchy under `MiraError` for simplicity; can be deepened as needed

## Remaining Issues

- `pipeline/benchmark.py` and `field_benchmark.py` still have substantial overlap — full consolidation deferred to Phase 2
- Dashboard `camera_service.py` has hardcoded class names duplicated from `config.py` — needs deduplication
- `DETECTION_MODEL_LABELS` in `config.py` could be fully deprecated but kept for non-CLI use cases
- No integration tests for CLI commands or dashboard endpoints
- `reference/` directory scripts may contain dead code — needs audit
