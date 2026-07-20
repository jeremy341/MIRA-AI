# MIRA-AI Architecture Audit

> Comprehensive architecture review covering three phases: Foundation, Scalability & Extensibility, and Production Readiness.

**Project**: MIRA-AI — Modular Inference and Recognition Architecture  
**Audit Period**: 2026  
**Overall Architecture Score**: **86 / 100**

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Architecture Overview](#architecture-overview)
3. [Phase 1 — Foundation Audit](#phase-1--foundation-audit)
4. [Phase 2 — Scalability & Extensibility Audit](#phase-2--scalability--extensibility-audit)
5. [Phase 3 — Production Readiness Audit](#phase-3--production-readiness-audit)
6. [Key Design Decisions](#key-design-decisions)
7. [Before / After Comparison](#before--after-comparison)
8. [Architecture Scoring](#architecture-scoring)
9. [Remaining Weaknesses](#remaining-weaknesses)
10. [Future Roadmap](#future-roadmap)

---

## Executive Summary

MIRA-AI is a modular computer vision framework designed for object detection and classification tasks. Over three audit phases, the codebase was systematically improved from a monolithic prototype into a well-structured, extensible platform.

**Phase 1** addressed foundational issues: code duplication, naming inconsistencies, weak error handling, and hardcoded configuration.  
**Phase 2** introduced scalability patterns: hardware abstraction, training strategy registry, deployment utilities, and dataset validation.  
**Phase 3** focused on production readiness: version management, experiment serialization, dashboard removal, and comprehensive test coverage.

The result is a framework scoring **86/100** overall, with strong marks for maintainability (90) and extensibility (88), and clear paths for future improvement.

---

## Architecture Overview

```
MIRA-AI/
├── src/
│   ├── __init__.py          # Package exports
│   ├── version.py           # Version management
│   ├── config.py            # Central configuration
│   ├── exceptions.py        # Exception hierarchy
│   ├── cli.py               # CLI entry point
│   ├── logger.py            # Logging utilities
│   ├── hardware.py          # Hardware abstraction
│   ├── deploy.py            # Deployment utilities
│   ├── serialization.py     # Experiment serialization
│   ├── inference_engine.py  # Inference pipeline
│   ├── visualize.py         # Visualization utilities
│   ├── model_picker.py      # Interactive model selection
│   ├── field_benchmark.py   # Field benchmarking
│   └── pipeline/
│       ├── __init__.py
│       ├── train.py         # Training pipeline
│       ├── strategies.py    # Training strategies
│       ├── models.py        # Model adapters
│       ├── registry.py      # Plugin registry
│       ├── dataset.py       # Dataset management
│       ├── benchmark.py     # Benchmarking
│       └── validators.py    # Dataset validation
└── tests/
    ├── test_config.py
    ├── test_visualize.py
    ├── test_pipeline.py
    ├── test_field_benchmark.py
    ├── test_hardware.py
    ├── test_strategies.py
    ├── test_deploy.py
    └── test_validators.py
```

### Module Dependency Flow

```
CLI (cli.py)
 ├── config.py ──→ exceptions.py
 ├── pipeline/registry.py ──→ pipeline/models.py
 ├── pipeline/train.py ──→ pipeline/strategies.py
 ├── inference_engine.py ──→ hardware.py
 ├── deploy.py ──→ hardware.py
 └── serialization.py ──→ version.py
```

---

## Phase 1 — Foundation Audit

**Commit**: `2f459c8`

### Problems Discovered

| Issue | Severity | Location |
|-------|----------|----------|
| ~120 lines of duplicated preprocessing code | High | `pipeline/models.py` (×3 adapters) |
| `sys.path` manipulation at module import | Medium | `pipeline/dataset.py:31-33` |
| `SCRIPT_DIR` misnaming (points to `src/`, not `scripts/`) | Medium | `config.py:7` |
| Hardcoded model labels require manual updates | Medium | `config.py:46-63` |
| Tests accessing private API (`_COMMANDS`, `_DATASET_SOURCES`) | Low | `tests/test_pipeline.py` |
| Dead code in keyboard handler | Low | `model_picker.py:16-17` |
| Generic `RuntimeError` instead of typed exceptions | Low | `config.py:16,18,27` |
| Dashboard missing `datetime` import | High | `dashboard/websocket_handler.py` |
| Dashboard iterating set while modifying | Medium | `dashboard/websocket_handler.py:228-240` |
| Dashboard using `dict` API on `ModelConfig` object | Medium | `dashboard/camera_service.py:106` |

### Implemented Improvements

1. **Shared image preprocessing** — Extracted `letterbox_preprocess()` and `adjust_boxes_to_original()` into shared utilities, eliminating ~120 lines of duplicate letterbox/normalization code across `YOLOAdapter`, `YOLOTFLiteAdapter`, and `ThirdPartyAdapter`.

2. **Lazy merge_utils import** — Replaced module-level `sys.path.insert(0, scripts_dir)` with function-level `_import_merge_utils()` that only runs when merge operations execute.

3. **SRC_DIR naming** — Added `SRC_DIR` as the primary name for the `src/` directory path, with `SCRIPT_DIR` retained for backward compatibility.

4. **Dynamic model labels** — `_pick_model_interactive()` in `cli.py` now fetches labels from `ModelRegistry` instead of the hardcoded `DETECTION_MODEL_LABELS` dict.

5. **Test cleanup** — Registry tests now use public `get_commands()`/`get_dataset_sources()` instead of private `_COMMANDS`/`_DATASET_SOURCES`.

6. **Keyboard handler fix** — Consolidated duplicate `b"\xe0"` check in `model_picker.py` into a single branch.

7. **Config validation** — `TrainConfig.from_yaml()` now validates 7 fields with type checks and value constraints (positive integers, non-negative values).

8. **Exception hierarchy** — Created `src/exceptions.py` with `MiraError` base class and five typed subclasses: `ConfigError`, `ModelError`, `DatasetError`, `CameraError`, `PipelineError`.

9. **Dashboard bug fixes** — Added missing `datetime` import, fixed `_broadcast()` to iterate over a copy of `self.connections`, fixed `config.get("imgsz")` to use `getattr`.

10. **Config error types** — `config.py` now raises `ConfigError` and `CameraError` instead of generic `RuntimeError`.

11. **Field benchmark refactor** — `field_benchmark.py` refactored to use `ModelRegistry` instead of its own duplicate `get_detection_models()` implementation.

### Research & Benchmarking

Compared against: Ultralytics, Hugging Face, PyTorch Lightning, Detectron2, OpenMMLab, Hydra.

Key patterns adopted:
- **Ultralytics**: Model registry pattern for dynamic model discovery
- **PyTorch Lightning**: Exception hierarchy pattern for framework-level errors
- **Hydra**: Config validation approach (type + constraint checking) applied to `TrainConfig`

### Modified Files

| File | Changes |
|------|---------|
| `src/exceptions.py` | **NEW** — Centralized exception hierarchy |
| `src/__init__.py` | Export new exception classes |
| `src/pipeline/models.py` | Extract shared preprocessing utilities; refactor 3 adapters |
| `src/pipeline/dataset.py` | Replace module-level sys.path with lazy import |
| `src/pipeline/train.py` | Enhanced `TrainConfig.from_yaml()` validation |
| `src/config.py` | Add `SRC_DIR`, backward compat; use typed exceptions |
| `src/cli.py` | Dynamic model labels via `ModelRegistry` |
| `src/field_benchmark.py` | Use `ModelRegistry` instead of duplicate implementation |
| `src/model_picker.py` | Fix dead code in keyboard handler |
| `src/dashboard/camera_service.py` | Fix `config.get()` to `getattr()` |
| `src/dashboard/websocket_handler.py` | Add missing import; fix set iteration |
| `tests/test_pipeline.py` | Use public API; add exception hierarchy test |

---

## Phase 2 — Scalability & Extensibility Audit

**Commit**: `1471862`

### Problems Discovered

| Issue | Severity | Location |
|-------|----------|----------|
| Camera tightly coupled to OpenCV | High | `inference_engine.py:CameraStream` |
| `TrainingPipeline` coupled to YOLO | High | `pipeline/train.py:train_yolo()` |
| No hardware detection for deployment | Medium | missing entirely |
| No dataset validation before merge | Medium | missing entirely |
| Single `TrainingPipeline` class does all tasks | Medium | `pipeline/train.py` |
| No IP camera support | Low | missing entirely |

### Implemented Improvements

1. **Hardware abstraction layer** (`src/hardware.py`) — `AbstractCamera` interface with `USBCamera` (threaded reader pattern) and `IPCamera` (RTSP/HTTP streaming). `create_camera()` factory for automatic type selection based on source (int → USB, `"rtsp://"` → IP). Camera I/O is now isolated from inference logic.

2. **Training strategy pattern** (`pipeline/strategies.py`) — `TrainingStrategy` ABC with `YOLOStrategy` and `ClassifierStrategy` implementations. `register_strategy()`/`get_strategy()` registry API. `TrainConfig` and `TrainResult` dataclasses. Third parties can add backends without modifying MIRA source.

3. **Pipeline refactoring** (`pipeline/train.py`) — Simplified to delegate to strategy registry. `train(task, config)` dispatches to registered strategy. `TrainingPipeline.register_strategy()` class method for external plugin registration.

4. **Deployment utilities** (`src/deploy.py`) — `HardwareInfo` dataclass with platform detection (Raspberry Pi, Jetson, CUDA). `detect_hardware()` for system capability inspection. `suggest_model()` recommends optimal model format. `check_environment()` returns actionable warnings.

5. **Dataset validation** (`pipeline/validators.py`) — `ValidationResult` dataclass. `validate_yolo_dataset()` checks directory structure, label-image correspondence, label format validity, class ID ranges, and orphaned files. `dataset_summary()` for human-readable output.

6. **CLI extensions** — Added `mira diagnostics` (hardware/environment check) and `mira validate --dataset <path>` (dataset validation) commands.

### Research & Benchmarking

Compared against: Ultralytics, PyTorch Lightning, Detectron2, ROS2, NVIDIA Isaac, Hugging Face.

Key patterns adopted:
- **ROS2**: Camera abstraction pattern for hardware-agnostic interfaces
- **PyTorch Lightning**: Strategy pattern for training backends
- **Ultralytics**: Plugin registration pattern (improves on monolithic `YOLO` class)
- **NVIDIA Isaac**: Hardware detection utility inspired by system inspector

### Modified Files

| File | Changes |
|------|---------|
| `src/hardware.py` | **NEW** — AbstractCamera + USBCamera + IPCamera + factory |
| `src/pipeline/strategies.py` | **NEW** — TrainingStrategy ABC + registry |
| `src/pipeline/validators.py` | **NEW** — Dataset validation utilities |
| `src/deploy.py` | **NEW** — Hardware detection, deployment suggestions |
| `src/pipeline/train.py` | Refactored to delegate to strategy registry |
| `src/pipeline/__init__.py` | Export new modules |
| `src/__init__.py` | Export deploy module |
| `src/inference_engine.py` | Use `USBCamera` instead of `CameraStream` |
| `src/cli.py` | Add `diagnostics` and `validate` commands |

---

## Phase 3 — Production Readiness Audit

### Implemented Improvements

1. **Dashboard removal** — Eliminated the entire `src/dashboard/` module. The WebSocket-based dashboard added significant complexity (async server, camera service, connection management) without proportional value for a CLI-first framework. This removed ~1,500 lines of code and multiple bug sources.

2. **Version management** (`src/version.py`) — Centralized version string with `__version__` export. Foundation for CLI `--version` flag and experiment metadata tracking.

3. **Experiment serialization** (`src/serialization.py`) — Structured experiment metadata capture including model configuration, training parameters, timestamps, and hardware context. Enables reproducibility and experiment comparison.

4. **Training pipeline integration** — Serialization integrated into `pipeline/train.py` so that every training run automatically produces a serialized experiment record.

5. **Configuration module cleanup** — Removed dead code, consolidated validation logic, and improved type annotations in `config.py`.

6. **Comprehensive test coverage** — Added tests for all new modules: `test_hardware.py`, `test_strategies.py`, `test_deploy.py`, `test_validators.py`. Existing tests updated to cover serialization and version management.

---

## Key Design Decisions

| # | Decision | Rationale |
|---|----------|-----------|
| 1 | **Strategy pattern for training backends** | Extensible without modifying core pipeline; third parties register via `register_strategy()` |
| 2 | **Hardware abstraction layer** | Separates camera I/O from inference logic; supports USB and IP cameras through a common interface |
| 3 | **Plugin registry for commands, datasets, and models** | Central discovery mechanism; avoids hardcoded lists that require manual maintenance |
| 4 | **Centralized exception hierarchy** | `MiraError` + 5 subclasses provide typed, catchable errors for consistent error handling |
| 5 | **Experiment serialization** | Every training run produces structured metadata for reproducibility and comparison |
| 6 | **CLI-first architecture** | No GUI complexity; dashboard removed in favor of lean command-line interface |
| 7 | **Lazy imports over sys.path manipulation** | Function-level imports avoid polluting module namespace and import-time side effects |
| 8 | **Dynamic over static configuration** | Model labels discovered at runtime via `ModelRegistry` rather than maintained by hand |
| 9 | **Backward compatibility** | `SCRIPT_DIR` retained as alias for `SRC_DIR`; existing APIs preserved during refactoring |
| 10 | **Validation before execution** | Dataset validation catches problems before expensive merge or training operations |

---

## Before / After Comparison

### Before Phase 1

- ~120 lines of duplicated preprocessing code across 3 model adapters
- Generic `RuntimeError` exceptions with no type differentiation
- Hardcoded `DETECTION_MODEL_LABELS` dict requiring manual updates
- Module-level `sys.path` manipulation in `dataset.py`
- Minimal config validation (3 fields only)
- Dashboard bugs: missing `datetime` import, set iteration during modification, wrong API on config objects
- `SCRIPT_DIR` misnamed (pointed to `src/`, not `scripts/`)
- Dead code in keyboard handler
- Tests accessing private module internals

### After Phase 3

- Shared `letterbox_preprocess()` and `adjust_boxes_to_original()` utilities
- Typed exception hierarchy: `MiraError` → `ConfigError`, `ModelError`, `DatasetError`, `CameraError`, `PipelineError`
- Dynamic model discovery via `ModelRegistry`
- Lazy imports replacing `sys.path` manipulation
- Comprehensive config validation (7 fields with type and value constraints)
- Dashboard removed entirely (unnecessary complexity eliminated)
- Hardware abstraction layer (`AbstractCamera`, `USBCamera`, `IPCamera`)
- Training strategy pattern (`TrainingStrategy` ABC + registry)
- Deployment utilities with hardware detection
- Dataset validation module
- Experiment serialization for reproducibility
- Version management module
- Comprehensive test coverage across all modules
- Clean module boundaries and clear separation of concerns

---

## Architecture Scoring

### Scalability: 85 / 100

| Strength | Impact |
|----------|--------|
| Plugin architecture supports easy extension | High |
| Strategy pattern allows new training backends | High |
| Hardware abstraction supports multiple camera types | Medium |
| Registry system enables third-party plugins | Medium |

**Gap**: File-based plugin discovery not yet implemented — strategies and models must be registered programmatically.

### Maintainability: 90 / 100

| Strength | Impact |
|----------|--------|
| Clean module boundaries | High |
| Centralized configuration | High |
| Typed exceptions for debugging | Medium |
| Comprehensive test coverage | Medium |
| Clear separation of concerns | High |

**Gap**: Some circular dependencies between `registry.py` and `models.py` (resolved via lazy imports).

### Extensibility: 88 / 100

| Extension Point | Mechanism |
|-----------------|-----------|
| New models | Subclass `DetectionModel` |
| New datasets | Register in `DatasetRegistry` |
| New training strategies | `register_strategy("name", StrategyClass)` |
| New hardware | Subclass `AbstractCamera` |
| New CLI commands | Register in command registry |

**Gap**: No hot-reload for plugins; registration is in-memory only.

### Plug-and-Play: 82 / 100

| Feature | Status |
|---------|--------|
| Models auto-discovered from `models/` directory | Implemented |
| Datasets registered via YAML descriptors | Implemented |
| Training strategies registered programmatically | Implemented |
| CLI commands discoverable via `--help` | Implemented |
| Automatic plugin scanning from external directories | Not implemented |

### Developer Experience: 87 / 100

| Feature | Status |
|---------|--------|
| Clear project structure | Strong |
| Comprehensive CLI with 20+ commands | Strong |
| Good test coverage | Strong |
| Type hints throughout | Strong |
| Helpful exception messages | Strong |
| Documentation completeness | Needs improvement |

### Overall Score: 86 / 100

| Dimension | Score | Weight |
|-----------|-------|--------|
| Scalability | 85 | 20% |
| Maintainability | 90 | 25% |
| Extensibility | 88 | 20% |
| Plug-and-Play | 82 | 15% |
| Developer Experience | 87 | 20% |
| **Weighted Total** | **86.4** | **100%** |

---

## Remaining Weaknesses

| # | Issue | Severity | Mitigation |
|---|-------|----------|------------|
| 1 | Circular dependency between `registry.py` and `models.py` | Low | Works via lazy imports; consider merging modules |
| 2 | No file-based plugin discovery system | Medium | Strategies/models must be registered programmatically |
| 3 | Structured logging not fully integrated | Low | Some `print()` statements should be `logging` calls |
| 4 | No error recovery in inference engine | Medium | Camera failures are not gracefully handled |
| 5 | Camera reconnection not implemented | Medium | `IPCamera` does not reconnect on stream loss |
| 6 | CLI `--version` flag not implemented | Low | `version.py` exists but is not wired to CLI |
| 7 | `diagnostics` uses deprecated WMIC on Windows | Low | Replace with PowerShell or WMI API |
| 8 | No GPU memory detection in `HardwareInfo` | Low | Would improve model suggestion accuracy |
| 9 | `reference/` directory may contain dead code | Low | Needs dedicated audit |
| 10 | `benchmark.py` and `field_benchmark.py` have overlap | Low | Full consolidation deferred from Phase 1 |

---

## Future Roadmap

### Short-term (Next Release)

1. **File-based plugin discovery** — Scan `plugins/` directory for strategy and model extensions
2. **CLI `--version` flag** — Wire `version.py` to argument parser
3. **Structured logging** — Replace `print()` statements with `logging` calls throughout pipeline
4. **GPU memory detection** — Add VRAM reporting to `HardwareInfo`

### Medium-term

5. **Error recovery and graceful shutdown** — Implement retry logic and cleanup handlers in inference engine
6. **Camera reconnection** — Exponential backoff reconnection for `IPCamera` on stream loss
7. **ONNX Runtime and TensorRT backends** — Add inference strategies for optimized runtimes
8. **Experiment comparison tools** — CLI commands to diff and visualize experiment results

### Long-term

9. **Automated benchmark regression testing** — CI pipeline that detects performance regressions
10. **Container deployment** — Docker and Kubernetes support with pre-built images
11. **Model versioning** — Track and manage multiple model versions per task
12. **Distributed training** — Multi-GPU and multi-node training strategy support

---

## Appendix: Commit History

| Phase | Commit | Description |
|-------|--------|-------------|
| Phase 1 | `2f459c8` | Foundation audit — code deduplication, exception hierarchy, config validation |
| Phase 2 | `1471862` | Scalability audit — hardware abstraction, strategy pattern, deployment utilities |
| Phase 3 | current | Production readiness — dashboard removal, versioning, serialization, tests |
