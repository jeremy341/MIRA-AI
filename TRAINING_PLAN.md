# MIRA-AI Training Plan

> **Deployment target:** Raspberry Pi Zero 2W and tabletop robot arm (pending)
>
> **Measured historical baseline:** EXP-014 FP32, 60.7% mAP50 and 50.6% mAP50-95
>
> **Current dataset:** 6,898 images and 12,832 boxes, no SortWaste
>
> **Status date:** 2026-07-30

See [`docs/EVIDENCE_LEDGER.md`](docs/EVIDENCE_LEDGER.md) for evidence and
report-safe wording.

## Current State

| Item | Status | Evidence |
|---|---|---|
| No-SortWaste dataset | Measured locally: 6,898 images, 12,832 boxes | `datasets/merged_mira_balanced/manifest.jsonl` |
| EXP-014 FP32 | Measured historically: 60.7% mAP50, 50.6% mAP50-95 | `results/experiments_log.md` |
| EXP-014 INT8 | Measured size: 2.90 MiB; detection mAP pending | `results/experiments_log.md` |
| EXP-017 dataset | Measured historically: 9,774 images | `results/experiments_log.md` |
| Field benchmark | Preliminary image-level class-presence F1 | `results/field_benchmark_results.md` |
| Dashboard | Implemented; end-to-end integration unverified | `src/dashboard/` |
| Raspberry Pi/robot | Pending | No repository benchmark/integration artifact |
| Distillation | Planned; compatibility-gated | EXP-018 through EXP-023 configs; no result log entries |

EXP-014 was trained on an older 6,802-image TACO + TrashNet + Roboflow build.
Its results are a historical baseline and are not results on the current
dataset. EXP-017 used 9,774 images, not approximately 17,000.

## Dataset Protocol

The current build combines dmedhi, Roboflow, TACO, and SAM-labeled TrashNet.
SortWaste is excluded by `scripts/build_balanced_dataset.py` because of its
plastic skew and deployment-domain mismatch.

| Split | Images | Boxes | Role |
|---|---:|---:|---|
| Train | 5,108 | 8,948 | Balanced model fitting |
| Validation | 415 | 415 | TrashNet tabletop validation |
| Test | 1,375 | 3,469 | Held-out dmedhi, Roboflow, and TACO data |
| **Total** | **6,898** | **12,832** | |

The dataset and ZIP are local, gitignored artifacts. Before cloud training,
package the manifest with the data and verify these counts after extraction.

## Experiment Sequence

1. **Data audit:** validate labels, class IDs, hashes, split isolation, and the
   exact manifest counts above.
2. **Baseline controls:** train YOLO11n and YOLO26n without distillation on the
   same dataset and split.
3. **Teacher models:** train larger teacher candidates only after baselines are
   reproducible.
4. **Distillation:** train student models using the selected teacher and compare
   against the matching non-distilled controls.
5. **Export:** produce FP32 and INT8 artifacts, recording bytes and hashes.
6. **Evaluation:** evaluate FP32 and INT8 independently on the same test set;
   never copy FP32 mAP values onto an INT8 row.
7. **Deployment:** measure latency, memory, thermals, and stability on the actual
   Raspberry Pi Zero 2W before calling a model deployable.
8. **Integration:** verify camera, dashboard, serial protocol, and robot arm
   end-to-end before describing the sorting system as operational.

## Quota-Constrained Kaggle Run

The selected Kaggle workflow retains YOLO11n as the teacher because of the
limited Kaggle quota. In this workflow it is an exploratory/reference teacher,
not a high-capacity teacher. The run can test whether the chosen distillation
path is usable, but it cannot establish the benefit expected from a larger
teacher without a measured comparison.

Notebook 3 installs Ultralytics using the same setup as Notebooks 1 and 2, then
checks for `distill_model`, `dis`, and functional `MuSGD` support before dataset
preparation or a long training run. Distillation remains planned unless that
environment check passes, and it remains unmeasured until run artifacts and
evaluation records exist.

## Planned Experiments

| Experiment | Purpose | Status |
|---|---|---|
| EXP-018 | YOLO11x teacher | Planned; no measured result |
| EXP-019 | YOLO26x teacher | Planned; no measured result |
| EXP-020 | Distilled YOLO26n | Planned; no measured result |
| EXP-021 | Distilled YOLO11n | Planned; no measured result |
| EXP-022 | YOLO26n non-distilled control | Planned; no measured result |
| EXP-023 | YOLO11n non-distilled control | Planned; no measured result |

The quota-constrained YOLO11n teacher run is separate from the planned
high-capacity EXP-018 and EXP-019 teacher candidates; it does not replace or
constitute a result for either experiment.

Accuracy ranges such as 65-68% mAP50 and size estimates such as 2.5 MB are
**projections**. They must remain in planning notes and must not appear in a
results table until artifacts record the measurements.

## Evaluation Rules

- Report `mAP50` and `mAP50-95` with model precision, dataset version, split,
  image count, and box count.
- Label file size separately from accuracy. Quantization changes the artifact;
  evaluate that artifact rather than assuming FP32 accuracy is preserved.
- Keep image-level class-presence F1 separate from detection mAP. The existing
  field benchmark also used an inconsistent threshold policy and is preliminary.
- Record measured values as measured, literature values as external, and all
  expected values as projected.
- Preserve checkpoints, result CSVs, environment versions, and SHA-256 hashes
  outside Git if they cannot be tracked in the repository.

## Release Gates

- Dataset manifest and aggregate counts archived with the training run.
- FP32 and INT8 evaluated under the same detection protocol.
- Public model download tested from an unauthenticated fresh environment, or
  access requirements documented.
- Raspberry Pi benchmark completed on target hardware.
- Dashboard and robot integration covered by an end-to-end verification record.

Until these gates pass, describe the Raspberry Pi, robot, dashboard, and
distillation work as targets or pending integration, not completed results.
