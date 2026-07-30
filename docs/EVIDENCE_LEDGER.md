# MIRA Evidence Ledger

Verified against the working repository on 2026-07-30. **Measured** means a
repository artifact records the observation. **Projected** and **pending** are
not results. Local dataset/model artifacts named below are gitignored and are
therefore not supplied by a fresh clone.

| Claim | Status | Evidence | Report-safe wording |
|---|---|---|---|
| Current no-SortWaste dataset contains 6,898 images and 12,832 boxes. | Measured, local artifact | `datasets/merged_mira_balanced/manifest.jsonl` (6,898 records; 12,832 entries across `labels`) | "The locally generated no-SortWaste dataset contains 6,898 annotated images and 12,832 boxes." |
| Dataset split is 5,108 train / 415 validation / 1,375 test images, with 8,948 / 415 / 3,469 boxes. | Measured, local artifact | `datasets/merged_mira_balanced/manifest.jsonl`; generation logic in `scripts/build_balanced_dataset.py` | "The generated split contains 5,108/415/1,375 train/validation/test images (8,948/415/3,469 boxes)." |
| Dataset sources are dmedhi 2,472 images/3,258 boxes; Roboflow 1,578/4,126; TACO 1,004/3,604; TrashNet 1,844/1,844. | Measured, local artifact | `datasets/merged_mira_balanced/manifest.jsonl` fields `source` and `labels` | "The generated dataset combines dmedhi (2,472 images), Roboflow (1,578), TACO (1,004), and TrashNet (1,844)." |
| Source/split image counts are dmedhi 2,156 train + 316 test; Roboflow 969 train + 609 test; TACO 554 train + 450 test; TrashNet 1,429 train + 415 validation. | Measured, local artifact | `datasets/merged_mira_balanced/manifest.jsonl` fields `source` and `split` | "Source-specific splits are recorded in the generated manifest; the dedicated 415-image validation split is TrashNet." |
| SortWaste is absent from the current balanced dataset. | Verified | No `source: sortwaste` records in `datasets/merged_mira_balanced/manifest.jsonl`; exclusion rationale in `scripts/build_balanced_dataset.py` | "The current balanced dataset excludes SortWaste because its class/domain distribution was judged unsuitable for this build." |
| EXP-014 achieved 60.7% mAP50 and 50.6% mAP50-95. | Measured, historical | `results/experiments_log.md` (EXP-014 validation table); local training curve `results/exp014_yolo11n_tnr/results.csv` | "On its historical 6,802-image TACO + TrashNet + Roboflow dataset, the FP32 EXP-014 checkpoint achieved 60.7% mAP50 and 50.6% mAP50-95." |
| EXP-014 INT8 is approximately 2.90 MiB. | Measured size only | `results/experiments_log.md` (EXP-014 quantization section); local `models/detection/mira_exp014_int8.tflite` is 3,042,004 bytes | "The EXP-014 INT8 export is 2.90 MiB; the FP32 validation mAP values must not be presented as an INT8 evaluation." |
| INT8 preserves EXP-014's 60.7% mAP50. | Not established | No repository detection-mAP evaluation of the INT8 export; `results/field_benchmark_results.md` instead records lower image-level F1 under a threshold-sensitive protocol | "INT8 detection mAP has not yet been measured under the FP32 validation protocol." |
| EXP-017 used 9,774 images. | Measured, historical | `results/experiments_log.md` (EXP-017 dataset line) | "EXP-017 was trained on a 9,774-image four-source dataset." |
| Field benchmark reports detector localization quality. | Unsupported | `results/field_benchmark_results.md` explicitly defines image-level class-presence F1, not bounding-box mAP | "A preliminary benchmark measured image-level class-presence F1; it does not measure localization quality." |
| Field benchmark is directly comparable across FP32 and INT8. | Preliminary/inconsistent | `results/field_benchmark_results.md` states confidence 0.5, while its findings say future INT8 runs are capped at 0.25; one INT8 model produced no detections | "Existing field results are preliminary and threshold-inconsistent, so FP32/INT8 comparisons are not conclusive." |
| Raspberry Pi deployment and robot sorting work end to end. | Pending | `README.md` architecture labels robotic sorting planned; no Pi benchmark artifact exists | "Raspberry Pi benchmarking and end-to-end robot integration are planned but not yet demonstrated." |
| Distillation results exist. | Pending/projected | EXP-018 through EXP-023 are configs/plans; no corresponding entries in `results/experiments_log.md` | "Teacher/student and distillation experiments are planned; numerical targets are projections." |
| Dashboard is a verified working product. | Implemented, integration unverified | Components exist under `src/dashboard/`; tests cover models/WebSocket helpers, but no tracked end-to-end dashboard integration result is present | "A dashboard implementation exists, but end-to-end camera/model/browser integration remains to be verified." |
| A fresh clone includes trained models through Git LFS. | False for current HEAD | `.gitignore` ignores model binaries; `git ls-files models/` lists descriptors only; `git lfs ls-files` returns no files. `.gitattributes` patterns alone do not add objects. | "A fresh clone contains code and model descriptors, not trained model binaries or datasets." |
| `mira download` currently provides verified public model downloads and checksum validation. | Not verified | URLs are listed in `src/cli/inference.py`, but the repository records no expected hashes and the configured Hugging Face endpoint returned HTTP 401 on 2026-07-30 | "The download command is implemented, but public availability and integrity verification must be confirmed before relying on it." |

## Detailed Dataset Counts

| Source | Train images/boxes | Val images/boxes | Test images/boxes | Total images/boxes |
|---|---:|---:|---:|---:|
| dmedhi | 2,156 / 2,762 | 0 / 0 | 316 / 496 | 2,472 / 3,258 |
| Roboflow | 969 / 2,722 | 0 / 0 | 609 / 1,404 | 1,578 / 4,126 |
| TACO | 554 / 2,035 | 0 / 0 | 450 / 1,569 | 1,004 / 3,604 |
| TrashNet | 1,429 / 1,429 | 415 / 415 | 0 / 0 | 1,844 / 1,844 |
| **Total** | **5,108 / 8,948** | **415 / 415** | **1,375 / 3,469** | **6,898 / 12,832** |

The manifest and `merged_mira_balanced_no_sortwaste.zip` are local,
gitignored artifacts. Their counts are evidence for this working copy, not a
claim that the dataset is distributed by the repository.
