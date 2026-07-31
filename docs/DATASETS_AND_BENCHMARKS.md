# MIRA-AI: Datasets and Benchmarks

This document separates current repository evidence from future work. See
[`docs/EVIDENCE_LEDGER.md`](docs/EVIDENCE_LEDGER.md) for claim-level evidence.

## Current Training Dataset

The current locally generated dataset is `merged_mira_balanced`, also archived
locally as `merged_mira_balanced_no_sortwaste.zip`. It **excludes SortWaste**.
Both artifacts are gitignored and are not available in a fresh clone.

| Source | Train images/boxes | Val images/boxes | Test images/boxes | Total images/boxes |
|---|---:|---:|---:|---:|
| dmedhi | 2,156 / 2,762 | 0 / 0 | 316 / 496 | 2,472 / 3,258 |
| Roboflow | 969 / 2,722 | 0 / 0 | 609 / 1,404 | 1,578 / 4,126 |
| TACO | 554 / 2,035 | 0 / 0 | 450 / 1,569 | 1,004 / 3,604 |
| TrashNet | 1,429 / 1,429 | 415 / 415 | 0 / 0 | 1,844 / 1,844 |
| **Total** | **5,108 / 8,948** | **415 / 415** | **1,375 / 3,469** | **6,898 / 12,832** |

Evidence: `datasets/merged_mira_balanced/manifest.jsonl`. The builder and split
policy are documented in `scripts/build_balanced_dataset.py`. TrashNet supplies
the validation set; non-TrashNet held-out records supply the test set.

### Why SortWaste Is Excluded

SortWaste was investigated but is not part of this build. The builder records
the reason as a severe plastic-class skew and a domain mismatch with the
tabletop robot-arm use case. Historical SortWaste download-size and annotation
claims are therefore not current MIRA dataset statistics.

### Classes

| ID | Class |
|---:|---|
| 0 | glass |
| 1 | metal |
| 2 | paper |
| 3 | plastic |
| 4 | trash |

## Measured Model Results

| Model/artifact | Dataset/protocol | Result | Status |
|---|---|---|---|
| EXP-014 FP32 | Historical 6,802-image TACO + TrashNet + Roboflow validation set | 60.7% mAP50; 50.6% mAP50-95 | Measured |
| EXP-014 INT8 | Export of EXP-014 | 2.90 MiB | Measured size; INT8 detection mAP not measured |
| EXP-017 FP32 | Historical 9,774-image four-source dataset | 59.3% mAP50; 46.5% mAP50-95 | Measured |
| Field benchmark | 805-image `mira_v2` validation set | Image-level class-presence F1 | Preliminary; threshold-inconsistent and not detection mAP |

Evidence: `results/experiments_log.md` and
`results/field_benchmark_results.md`. EXP-014/017 results predate the current
6,898-image no-SortWaste dataset and must not be represented as evaluations on
it.

## Pending Benchmarks

- Evaluate an FP32 baseline on the current 6,898-image dataset.
- Evaluate each INT8 export using the same held-out detection protocol as FP32.
- Repeat the image-level field benchmark with one fixed threshold policy.
- Measure latency and memory on the Raspberry Pi Zero 2W.
- Verify dashboard camera/model/browser integration and robot-arm operation.

Teacher/student training, knowledge distillation, and expected accuracy or
model-size ranges are **projections**, not measured outcomes.
