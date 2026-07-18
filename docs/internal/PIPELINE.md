# MIRA Research Pipeline

## Quick Start

```bash
mira datasets          # list available datasets
mira merge             # merge selected datasets into training set
mira train             # train a YOLO model
mira export            # export trained model (tflite, onnx, etc.)
mira benchmark         # benchmark exported models against dataset
mira models            # list known models (built-in + third-party)
```

## File Structure

```
mira.yaml                       # CLI config & defaults
datasets/registry/              # dataset YAML descriptors
datasets/<merged>/              # merged training data
experiments/                    # training runs & logs
src/pipeline/                   # pipeline modules (merge, train, export, bench)
models/detection/               # trained & third-party model files
```

## Adding a Dataset

1. Drop a YAML descriptor in `datasets/registry/`
2. Follow the existing schema (name, sources, classes, split ratios)
3. Run `mira datasets` to verify it appears

## Adding a Third-Party Model

1. Place the model file in `models/detection/`
2. Create a YAML descriptor (see `example_third_party.yaml`)
3. Run `mira benchmark --models <model_name> --dataset datasets/mira_all`

## Extension Points

| What                    | Where                      | How                                       |
| ----------------------- | -------------------------- | ----------------------------------------- |
| New CLI command         | `src/pipeline/`            | Add module, register in CLI entry point   |
| New dataset             | `datasets/registry/`       | Drop YAML descriptor                      |
| New model format        | `src/pipeline/models.py`  | Add inference adapter + type constant     |
| New training strategy   | `src/pipeline/train.py`    | Add strategy fn, expose as CLI flag       |
| New export target       | `src/pipeline/train.py`    | Add exporter in TrainingPipeline.export   |
| New benchmark metric    | `src/pipeline/benchmark.py`| Add metric fn, include in report output   |
