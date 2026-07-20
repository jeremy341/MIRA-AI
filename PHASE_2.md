# Phase 2 — Scalability & Extensibility Audit

## Agent Responsibilities

### Architecture Improvement Agents (20)

1. **Hardware Abstraction Agent** — Created `src/hardware.py` with `AbstractCamera` interface and concrete `USBCamera` and `IPCamera` implementations. `InferenceEngine` now delegates to the abstract interface instead of directly managing OpenCV capture.

2. **Training Strategy Agent** — Extracted `TrainConfig` and `TrainingStrategy` into `pipeline/strategies.py` with a pluggable strategy registry. Added `register_strategy()`/`get_strategy()` API for third-party training backends.

3. **Pipeline Refactoring Agent** — Simplified `pipeline/train.py` to delegate to the strategy registry. Added `TrainingPipeline.register_strategy()` class method for external plugin registration.

4. **Deployment Utility Agent** — Created `src/deploy.py` with `detect_hardware()`, `suggest_model()`, and `check_environment()` functions. Supports Raspberry Pi, Jetson, CUDA detection.

5. **Dataset Validator Agent** — Created `pipeline/validators.py` with `validate_yolo_dataset()` that checks directory structure, label-image correspondence, label format validity, and class ID ranges.

6. **CLI Extensibility Agent** — Added `mira diagnostics` and `mira validate` CLI commands.

7. **Camera Factory Agent** — Implemented `create_camera()` factory function in `hardware.py` for automatic camera type selection.

8–20. Additional agents analyzed API boundaries, dependency direction, and plugin architecture.

### Research & Innovation Agents (20)

Compared against: Ultralytics, PyTorch Lightning, Detectron2, ROS2, NVIDIA Isaac, Hugging Face.

Key findings:
- **ROS2**: Camera abstraction pattern adapted for hardware-agnostic interfaces
- **PyTorch Lightning**: Strategy pattern for training backends (similar to Lightning's `Trainer` + `LightningModule`)
- **Ultralytics**: Plugin registration pattern improves on Ultralytics' monolithic `YOLO` class
- **NVIDIA Isaac**: Hardware detection utility inspired by Isaac's system inspector

### User Experience Simulation Agent (1)

- `mira diagnostics` provides a single command to understand hardware capabilities and get a model suggestion
- `mira validate` helps dataset debugging without needing to run training
- Adding a new training backend now requires only `register_strategy("name", MyStrategy)` — no pipeline modification
- Adding camera support: subclass `AbstractCamera` and register in `create_camera()`

## Architectural Problems Discovered

| Issue | Severity | Location |
|-------|----------|----------|
| Camera tightly coupled to OpenCV | High | `inference_engine.py:CameraStream` |
| TrainingPipeline coupled to YOLO | High | `pipeline/train.py:train_yolo()` |
| No hardware detection for deployment | Medium | missing entirely |
| No dataset validation before merge | Medium | missing entirely |
| Single TrainingPipeline class does all tasks | Medium | `pipeline/train.py` |
| No IP camera support | Low | missing entirely |

## Implemented Improvements

1. **`src/hardware.py`** — Abstract camera interface (`AbstractCamera`) with `USBCamera` (threaded), `IPCamera` (RTSP/HTTP), and `create_camera()` factory. Threaded reader pattern isolates camera I/O from inference.

2. **`pipeline/strategies.py`** — `TrainingStrategy` ABC with `YOLOStrategy` and `ClassifierStrategy` implementations. `register_strategy()`/`get_strategy()` registry API. `TrainConfig` and `TrainResult` dataclasses. `from_yaml()` class method for config loading.

3. **`pipeline/train.py` refactored** — Now delegates to strategy registry. `train(task, config)` dispatches to registered strategy. `train_yolo()`, `train_classifier()` convenience methods preserved. `register_strategy()` class method added.

4. **`src/deploy.py`** — `HardwareInfo` dataclass with platform detection. `detect_hardware()` detects RPi, Jetson, CUDA, library availability. `suggest_model()` recommends optimal model format. `check_environment()` returns actionable warnings.

5. **`pipeline/validators.py`** — `ValidationResult` dataclass. `validate_yolo_dataset()` checks structure, label-image match, label format, class IDs, orphaned files. `dataset_summary()` for human-readable output.

6. **CLI additions** — `mira diagnostics` (hardware/environment check), `mira validate --dataset <path>` (dataset validation).

7. **Pipeline `__init__.py` exports** — New modules exported for external use.

## Modified Files

| File | Changes |
|------|---------|
| `src/hardware.py` | **NEW** — AbstractCamera + USBCamera + IPCamera + factory |
| `src/pipeline/strategies.py` | **NEW** — TrainingStrategy ABC + YOLOStrategy + ClassifierStrategy + registry |
| `src/pipeline/validators.py` | **NEW** — Dataset validation utilities |
| `src/deploy.py` | **NEW** — Hardware detection, deployment suggestions |
| `src/pipeline/train.py` | Refactored to delegate to strategy registry |
| `src/pipeline/__init__.py` | Export new modules |
| `src/__init__.py` | Export deploy module |
| `src/inference_engine.py` | Use USBCamera instead of CameraStream |
| `src/cli.py` | Add `diagnostics` and `validate` commands |

## Important Decisions

- **Strategy pattern over inheritance**: Training backends use composition (strategy registry) rather than subclassing `TrainingPipeline`, making it easier for third parties to add backends without modifying MIRA source.
- **Camera abstraction separates concerns**: Camera I/O (threading, warmup) is no longer mixed with inference logic.
- **`create_camera()` factory**: Automatic type selection based on source (int → USB, "rtsp://" → IP).
- **Validation before execution**: Dataset validation can catch problems before expensive merge or training operations.

## Remaining Issues

- `diagnostics` `_safe_cpu_count()` on Windows uses WMIC which is deprecated
- No GPU memory detection in `HardwareInfo`
- `IPCamera` doesn't support reconnection on stream loss
- Training strategy registry is in-memory only — no file-based plugin discovery yet
- No tests for new hardware, deploy, or validator modules (test coverage deferred)
- `reference/` directory scripts still have legacy code paths
