# MIRA-AI Session Memory

## User Context
- Location: Europe (Germany — Mülheim an der Ruhr)
- Competition: Jugend forscht 2027 (regional round in ~Mar 2027)
- FreeLLMAPI: paused (was used for initial exploration, no longer active for experiments)
- HF username: Jeremy341
- GitHub username: jeremy341 (repo: MIRA-AI)
- PyTorch: CPU-only locally (no CUDA); Kaggle T4 used for training
- Google API key: stored in env (AIzaSyB...), used for Gemini experiments
- Wandb API key: stored in env
- Jupyter password: stored in env
- No display server on this Windows machine (cannot preview matplotlib/cv2 windows)
- Local system: Windows, Python 3.11/3.14, no webcam available
- Target deployment: Raspberry Pi Zero 2W (ARM, limited RAM, no GPU)

## Repo Facts

### Project Structure
- `mira.yaml` — single source of truth configuration
- `src/` — main package with __main__.py entry point
- `src/cli.py` — 17 subcommands (train, export, eval-yolo, live, download, merge, datasets, validate, doctor, diagnostics, config, models, experiments, benchmark, generate, dashboard, wizard)
- `src/__main__.py` — entry point for `python -m src`
- `src/pipeline/` — research framework (registry, dataset, models adapters, training, benchmark)
- `src/dashboard/` — FastAPI+WebSocket web control center (light theme, JUFO/StarDance modes)
- `scripts/` — standalone utility scripts (cloud notebook generators, data viz, etc.)
- `models/` — Git LFS: 5 classifier + 18 detection models
- `tests/` — 99 tests, all passing (test_config, test_pipeline, test_visualize, test_deploy, test_framebuffer, test_hardware, test_strategies, test_validators)
- `experiments/` — YAML configs for EXP-009, EXP-013, EXP-014
- `datasets/registry/` — YAML descriptors: taco_trashnet, roboflow, warp, mira_v3
- `results/` — experiments_log.md (full metrics for all 17 experiments), per-experiment subdirs
- `latex/` — Jugend forscht report (22 pages)
- `mira.bat` — Windows CMD launcher (uses %~dp0, PYTHONUTF8=1)
- `mira.sh` — Linux/macOS launcher

### Experiments (17 total)
- EXP-001–004: Classification (Custom CNN → MobileNetV2 → fine-tune → INT8)
- EXP-005–012: YOLOv8n detection experiments (EXP-007 excluded as exploratory)
- EXP-013: YOLO11n + TACO + TrashNet (55.1% mAP50)
- EXP-014: YOLO11n + TACO + TrashNet + Roboflow (60.7% mAP50) ← CURRENT BEST
- EXP-015: YOLO11n + TACO + TrashNet + WaRP (56.0% mAP50)
- EXP-016: YOLO11n + WaRP only (58.8% mAP50)
- EXP-017: YOLO11n + all 4 sources (59.3% mAP50)

### Key Decisions
- Plugin-based CLI registry (@register_command, @register_dataset_source)
- Dataset sources managed via YAML descriptors in datasets/registry/
- Third-party model support: drop .pt/.tflite/.pth + optional YAML in models/detection/
- CORS restricted to localhost for security
- Dashboard defaults to 127.0.0.1:8000; --host/--port flags available
- Optional imports for torch/tensorflow (graceful fallback if not installed)

### Fixed Issues (Full Diagnostic Audit — ~100 fixes)
- Ruff lint N806 (lowercase _cmds), ruff format (2 files reformatted)
- mira.bat fixed (%~dp0 + -m src + PYTHONUTF8=1)
- mira.sh created for Linux
- Doctor Unicode crash fixed (✓/✗/⚠ → [OK]/[!] ASCII)
- torch/tensorflow made optional (lazy imports, _module_available catches more exceptions)
- camera_service.py: CAP_DSHOW check, model cleanup, division-by-zero guard, _event_loop None checks, hardcoded class names → CLASS_NAMES, temperature via psutil, print→logging
- CORS restricted to localhost
- InferenceEngine cleanup releases model
- Model adapters: select_device("auto") instead of hardcoded "cpu"
- _safe_cpu_count simplified to os.cpu_count()
- _safe_memory_mb uses psutil
- suggest_model checks tflite runtime availability
- check_environment checks ultralytics
- _load_sidecar_meta/_load_descriptor use encoding="utf-8", support model_type alias
- discover() guards missing directory
- validators.py: empty dataset marked invalid
- websocket_handler.py: fixed mutable default argument (list → None)
- dashboard/main.py: all .dict() → .model_dump()
- cli/inference.py: download shows SHA-256 hash
- Tests: 99 passed, 0 failed (was 97 passed, 2 failed)
- Ruff lint: 0 errors (was 1)
- Ruff format: 0 files need formatting (was 2)
- Doctor command: WORKS (was crashing with UnicodeEncodeError)
- README.md: Full CLI table, dashboard flags, models/results tables, project structure updated

## Blocked / Known Issues
- `.\mira datasets` shows Exists: NO for some registry entries (expected — datasets directory not fully populated locally)
- No webcam available locally; live detection tested only in simulation
- No CUDA locally; training done on Kaggle T4
- Raspberry Pi Zero 2W benchmarks pending
- Crumpled paper → misclassified as plastic (80-90% confidence)
- Trash class weakest performer (as low as 7.1% mAP50)

## API Keys & Services
- GOOGLE_API_KEY=AIzaSyB... (stored in env)
- WANDB_API_KEY=... (stored in env)
- No active Hugging Face token in env (git clone uses HTTPS for HF Hub downloads)
