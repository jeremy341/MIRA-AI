# MIRA-AI Refactoring & Feature Plan

## Overview

A comprehensive plan to restructure the MIRA-AI codebase, improve the CLI, add an interactive wizard, build a Gradio web UI, and generate training code for cloud platforms (Kaggle, Colab, Docker) with Hugging Face Hub integration.

---

## Phase A — Codebase Restructure

**Goal:** Clean up the code so it's maintainable and publishable

1. **Split `cli.py` into modules** — Move commands into `src/cli/{train,inference,data,system,generate}.py`
2. **Add `src/__main__.py`** — Enable `python -m src`
3. **Prune deprecated commands** — Remove `data-build`, 6 legacy wrappers that shell out to `reference/` scripts
4. **Integrate dashboard** — Move `dashboard_output/ -> src/dashboard/`, fix imports, add `mira dashboard` command
5. **Fix packaging** — Update `pyproject.toml` to include `src/dashboard`, add `scripts` as package
6. **Clean `.gitignore`** — Add patterns for generated notebooks, Gradio cache, Hugging Face cache

---

## Phase B — CLI Improvements

**Goal:** Make training accessible without coding

7. **Build `mira wizard`** — Interactive step-by-step training wizard using `questionary` / `prompt_toolkit`
8. **Add `mira download`** — Download pretrained models from Hugging Face Hub
9. **Add `mira train --wizard`** — Alias to launch wizard from train command
10. **Improve `mira train` defaults** — Auto-detect GPU, suggest batch size based on VRAM
11. **Add tab completion** — Shell completion for `mira <TAB>` via `argcomplete` / `shtab`

---

## Phase C — Cloud Training Generation

**Goal:** One command -> ready-to-upload training notebook

12. **`mira generate kaggle`** — Renders training logic into a `.ipynb` with setup cells, dataset download, config injection, export
13. **`mira generate colab`** — Same but for Google Colab (different mount paths)
14. **`mira generate docker`** — Generates a `Dockerfile` + `docker-compose.yml` for local GPU training
15. **`mira push`** — Upload trained model to Hugging Face Hub with auto-generated model card

---

## Phase D — Gradio Web UI

**Goal:** Visual training config + inference demo

16. **`src/gui/app.py`** — Gradio `Blocks` with tabs:
    - **Train**: Model picker, dataset picker, epochs slider, start/stop, live loss plot
    - **Inference**: Image upload + webcam, confidence slider, detection overlay
    - **Datasets**: List/merge sources, validate, view stats
    - **Export**: Pick model, pick format, download
    - **Generate**: Platform selector -> download generated notebook
17. **`mira gui`** — Launches `gradio app.py` with browser auto-open
18. **Dashboard stays as-is** — `mira dashboard` for real-time camera monitoring

---

## Phase E — Release Polish

19. **Hugging Face org** — Create `huggingface.co/jeremy341/mira-ai-models`, upload pretrained weights
20. **Update README** — New badges: "Open in Colab", "Run on Hugging Face Spaces", "Download models"
21. **Replace cloud datasets** — Upload sample datasets to Hugging Face Datasets, update `docs/datasets.md`

---

## Proposed File Layout

```
src/
├── __init__.py
├── __main__.py               # NEW: "python -m src" works
├── cli.py                    # REDUCED to just main() + imports from cli/
├── cli/
│   ├── __init__.py
│   ├── wizard.py             # NEW: interactive training wizard
│   ├── train.py              # MOVED: train, export commands
│   ├── inference.py          # MOVED: live, eval-yolo, eval-class
│   ├── data.py               # MOVED: merge, datasets, validate
│   ├── system.py             # MOVED: doctor, diagnostics, config
│   └── generate.py           # NEW: Kaggle/Colab/Docker generation
├── dashboard/                # MOVED: from dashboard_output/
├── gui/
│   ├── app.py                # NEW: Gradio web UI
│   └── launch.py             # NEW: entry point
├── config.py
├── pipeline/
│   ├── registry.py
│   ├── dataset.py
│   ├── models.py
│   ├── train.py
│   ├── strategies.py
│   ├── benchmark.py
│   └── validators.py
├── deploy.py
├── inference_engine.py
├── hardware.py
├── model_picker.py
├── logger.py
├── serialize.py
├── exceptions.py
├── version.py
└── visualize.py
```

---

## CLI Command Map

| Command | Phase | Status |
|---------|-------|--------|
| `mira train` | B | Improve defaults |
| `mira wizard` | B | **NEW** |
| `mira live` | B | Keep |
| `mira dashboard` | A | **NEW** (wire existing) |
| `mira gui` | D | **NEW** |
| `mira download` | B | **NEW** |
| `mira push` | C | **NEW** |
| `mira generate` | C | **NEW** (kaggle/colab/docker) |
| `mira merge` | — | Keep |
| `mira datasets` | — | Keep |
| `mira models` | — | Keep |
| `mira experiments` | — | Keep |
| `mira export` | B | Keep |
| `mira benchmark` | — | Keep |
| `mira validate` | — | Keep |
| `mira doctor` | — | Keep |
| `mira diagnostics` | — | Keep |
| `mira config` | — | Keep |
| `data-build` | A | **REMOVE** |
| `data-viz` | A | **REMOVE** |
| `train-baseline` | A | **REMOVE** |
| `train-transfer` | A | **REMOVE** |
| `train-tune` | A | **REMOVE** |
| `train-detection` | A | **REMOVE** |
| `quant-class` | A | **REMOVE** |
| `quant-yolo` | A | **REMOVE** |
| `eval-class` | A | **REMOVE** |
| `field-bench` | A | **REMOVE** |

---

## Decisions Made

| Question | Decision |
|----------|----------|
| GUI framework | **Both Gradio + existing dashboard** |
| Cloud platforms | **Kaggle + Colab + Docker + Hugging Face** |
| Interactive wizard | **Yes** (`mira wizard`) |
| Priority | **Structure + CLI first** |
