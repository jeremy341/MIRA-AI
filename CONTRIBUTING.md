# Contributing to MIRA

Thanks for your interest. MIRA is a student research project, so small, focused
changes are easiest to review.

## Set up

```bash
git clone https://github.com/jeremy341/MIRA-AI.git
cd MIRA-AI
python -m venv .venv
# Windows: .venv\Scripts\Activate.ps1    Linux/macOS: source .venv/bin/activate
pip install -e ".[dev]"
```

Python 3.11 or 3.12 is required.

## Before opening a pull request

CI runs the same checks, using the pinned versions from `pyproject.toml`:

```bash
ruff check src/ tests/
ruff format --check src/ tests/
mypy src/ --ignore-missing-imports --follow-imports=skip --exclude 'src/dashboard/'
pytest tests/ -v
```

Add or update a test for behavior you change.

## Reporting results

If you share metrics, say which dataset split they come from. The repository
separates validation numbers from real-world accuracy, and the same care applies
to contributions. See [`results/experiments_log.md`](results/experiments_log.md).

## Datasets and models

Datasets and trained weights are not committed to Git (see
[`docs/DATASET_ORIGINS.md`](docs/DATASET_ORIGINS.md) for sources and licenses).
Please do not add large binary files in a pull request.
