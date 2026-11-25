# Changelog

All notable changes to MIRA are recorded here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and versions follow
[Semantic Versioning](https://semver.org/).

## [Unreleased]

### Changed
- Package metadata: added PyPI classifiers, Documentation, Issues, Changelog and
  Hugging Face project links, and removed a placeholder author email.

### Fixed
- CI is green again: Ruff, formatting and mypy errors are resolved, and tests no
  longer depend on the local-only `scripts/run_exp020.py`.
- `camera_service` raised `NameError` in `get_statistics` because `defaultdict`
  was not imported.

## [1.0.3] - 2026-10-27

### Changed
- The package homepage now points to the project portfolio.

## [1.0.2] - 2026-08-24

### Added
- The EXP-014, EXP-018 and EXP-019 detector weights ship inside the PyPI package,
  so no model download is needed after installation.

## [1.0.1] - 2026-08-21

### Changed
- Prepared the PyPI release: packaging, CLI entry point and dashboard assets.

## [1.0.0] - 2026-08-19

### Added
- First public release: YOLO11n waste detection for glass, metal, paper, plastic
  and trash, the `mira` CLI, a local dashboard, and dataset, training and
  evaluation tooling.

[Unreleased]: https://github.com/jeremy341/MIRA-AI/compare/v1.0.2...HEAD
[1.0.3]: https://github.com/jeremy341/MIRA-AI/compare/v1.0.2...HEAD
[1.0.2]: https://github.com/jeremy341/MIRA-AI/releases/tag/v1.0.2
[1.0.1]: https://github.com/jeremy341/MIRA-AI/releases/tag/v1.0.1
[1.0.0]: https://github.com/jeremy341/MIRA-AI/releases/tag/v1.0.0
