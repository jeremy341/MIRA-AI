# Contributing to MIRA

Thanks for your interest in contributing! Here's how to help.

---

## Getting Started

1. **Fork** the repository
2. **Clone** your fork:
   ```bash
   git clone https://github.com/YOUR_USERNAME/MIRA-AI.git
   cd MIRA-AI
   ```
3. **Create a branch:**
   ```bash
   git checkout -b feature/your-feature-name
   ```

---

## Development Setup

```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\Activate.ps1 on Windows

# Install dependencies + dev tools
pip install -r requirements.txt
pip install pytest black flake8 mypy
```

---

## Code Style

- **Format:** Use `black` for consistent formatting
  ```bash
  black src/
  ```
- **Lint:** Check with `flake8`
  ```bash
  flake8 src/ --max-line-length=100
  ```
- **Comments:** Only comment code that needs clarification. Self-documenting code is preferred.
- **Type hints:** Use them where practical (especially in public APIs)

---

## Testing

### Running Tests

```bash
# Run all tests
pytest tests/

# Run specific test
pytest tests/test_live_detection.py -v

# With coverage
pytest --cov=src tests/
```

### Writing Tests

Place tests in `tests/` directory with `test_*.py` naming:

```python
# tests/test_cli.py
def test_model_loading():
    from src.cli import run_script
    # Your test here
    assert True
```

---

## Model Contributions

### Adding a New Model

1. **Train & test** your model locally
2. **Export to format** we support (.pt, .tflite, .keras)
3. **Save to `models/`** with clear naming:
   ```
   models/mira_detector_[description]_[format].pt
   models/mira_classifier_[description]_[format].tflite
   ```
4. **Document in README.md** — Model Guide section
5. **Test with live_detection.py:**
   ```bash
   python src/live_detection.py --model your_new_model.pt
   ```

### Submitting Model Performance Data

Include in PR:
- Architecture details
- Training dataset size
- Validation metrics (mAP50, accuracy, etc.)
- Inference speed (FPS, latency)
- Model size
- Hardware tested on

---

## Bug Reports

When reporting issues:

1. **Title:** Short, descriptive (`[BUG] Camera detection crashes on Pi`)
2. **Environment:**
   ```
   OS: Windows / Linux / macOS
   Python: 3.10 / 3.11
   Hardware: Laptop / Pi 4 / etc.
   ```
3. **Steps to reproduce:**
   ```
   1. Install MIRA
   2. Run: .\mira live
   3. See error...
   ```
4. **Error output:** Full traceback or logs
5. **Expected vs actual:** What should happen vs what does

---

## Feature Requests

- **Description:** What does it do?
- **Use case:** Why is it needed?
- **Example:**
  ```bash
  .\mira live --model model.pt --record output.mp4
  ```

---

## Documentation

Help improve the docs!

### Updating README.md

- Keep sections clear and concise
- Add examples where helpful
- Update table of contents if adding sections
- Verify all commands actually work

### Adding Guides

Create new `.md` files for:
- New features
- Deployment scenarios (DEPLOYMENT.md already exists)
- Troubleshooting topics

---

## Pull Request Process

1. **Before submitting:**
   ```bash
   black src/
   flake8 src/
   pytest tests/
   ```

2. **Create PR** with:
   - Clear title: `[FEATURE] Add webcam recording`
   - Description of changes
   - Link to related issues
   - Tested on: (Windows/Linux/Pi/etc.)

3. **Wait for review** — maintainers will comment

4. **Address feedback** — push updates to same branch

5. **Merge** — maintainers will merge when approved

---

## Branch Naming

```
feature/description        # New feature
bugfix/description         # Bug fix
docs/description          # Documentation
refactor/description      # Code refactoring
experiment/description    # Research/experiment (temporary)
```

---

## Commit Messages

```
# Bad
git commit -m "fixed stuff"

# Good
git commit -m "Fix camera warmup timing on Raspberry Pi

- Reduce WARMUP_FRAMES from 15 to 10 for faster startup
- Add debug logging for frame capture
- Tested on Pi 4 and Pi Zero 2W"
```

---

## Release Process (Maintainers Only)

1. Update version in `__init__.py`
2. Update `CHANGELOG.md`
3. Tag release: `git tag v1.0.0`
4. Push: `git push origin main --tags`

---

## License

By contributing, you agree that your contributions will be licensed under the same license as the project (see LICENSE).

---

## Questions?

- Check [TROUBLESHOOTING.md](TROUBLESHOOTING.md)
- Check existing [GitHub Issues](https://github.com/jeremy341/MIRA-AI/issues)
- Reach out on the Jugend Forscht forum

**Thank you for contributing! 🚀**
