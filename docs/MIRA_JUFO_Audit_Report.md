# MIRA-AI — Complete JUFO Competition Audit Report

**Auditor:** Antigravity AI (Expert Scientific Reviewer Mode)
**Date:** July 13, 2026
**Project:** MIRA — Machine Intelligence for Recycling Automation
**Competition:** Jugend forscht 2027, Fachgebiet Technik, Regionalwettbewerb NRW (Ruhrgebiet)
**Author:** Jeremy Darko, Gymnasium Broich, Stufe EF (Jahrgangsstufe 11)

---

## EXECUTIVE SUMMARY

MIRA is a **genuinely impressive student project** that demonstrates real engineering depth, systematic experimentation, and honest scientific thinking. The core concept — edge-AI recycling detection progressing from image classification to multi-object detection — is well-motivated, methodologically sound, and has produced concrete, quantitative results. The project would be competitive at a regional JUFO level.

However, the written report (LaTeX) has **significant structural gaps** that must be fixed before submission. The most critical issues are: the LaTeX report is only partially complete (missing major sections and figures for Stage B YOLO11n experiments), several key scientific claims contain contradictions, the EMA hypothesis (H4) is never experimentally verified, Stage A has only 4 classes (no trash), and there are no CPU/Raspberry Pi benchmark results.

**JUFO Competitiveness Assessment: 6/10 currently → potential 8.5/10 after improvements**

---

## PHASE 1 & 2 — PROJECT UNDERSTANDING

### What the Project Does
MIRA is a software-first prototype for an autonomous waste-sorting system. It uses computer vision (CV) to classify/detect five waste categories (glass, metal, paper, plastic, trash) on a low-cost edge device (Raspberry Pi Zero 2W target). The system progresses in two stages:
- **Stage A:** Image classification (custom CNN → MobileNetV2 transfer → fine-tune → INT8 quantization)
- **Stage B:** Object detection (YOLOv8n → YOLO11n, 4-dataset comparative study: TACO, TrashNet, Roboflow, WaRP)

### Scientific Question
*"Can a lightweight, edge-AI-optimized computer vision model achieve real-time recycling material detection on resource-constrained hardware without significant accuracy loss?"*

### Core Innovations
1. Systematic comparison of 3 CNN architectures on a small domain-specific dataset
2. Data-centric AI approach: demonstrates GIGO effect via auto-labeling failure
3. 4-dataset comparative study (TACO/TrashNet/Roboflow/WaRP — first such published comparison for 5-class recycling)
4. INT8 quantization pipeline targeting Raspberry Pi Zero 2W
5. EMA signal filter for mechatronic stability (conceptually documented)

### Technical Implementation
- **Software:** Python, TensorFlow/Keras, Ultralytics YOLO, Streamlit dashboard, threaded camera
- **Training:** Local CPU (Stage A) + Kaggle T4 GPU (Stage B)
- **Deployment target:** Raspberry Pi Zero 2W + ESP32-S3 (mechatronic arm — not yet built)
- **Pipeline:** Webcam → YOLO11n → bounding boxes → EMA filter → serial command → ESP32 → servos

---

## PHASE 3 — JUFO REQUIREMENT COMPARISON

| Category | Current Status | Evidence Found | Problems | Severity |
|---|---|---|---|---|
| **Research question** | ✅ Defined | 4 formal hypotheses in intro | H4 (EMA) has no quantitative validation | 🟡 Important |
| **Methodology** | ✅ Documented | Experiment log, training scripts, methodology.tex | Stage A dataset has only 604 images, no trash class in classifier | 🔴 Critical |
| **Experiments** | ⚠️ Partial | EXP-001 to EXP-016 logged | Report only covers up to EXP-015; EXP-016 only in README | 🟡 Important |
| **Results** | ✅ Quantitative | Full tables, per-class metrics | Report uses EXP-009 oddly in live-test discussion despite calling it "inflated" | 🟡 Important |
| **Documentation** | ⚠️ Partial | LaTeX report exists but thin | Implementation section is only 33 lines; future_work.tex mentions building dashboard that already exists | 🟡 Important |
| **Sources** | ⚠️ Weak | ~10 scientific sources | 10 of ~22 sources are self-references to own repo files; WaRP/Roboflow/ByteTrack uncited | 🔴 Critical |
| **Figures** | ⚠️ Incomplete | 9 figures in latex/figures/ | No YOLO11n figures for EXP-013/014/015 in report; no architecture diagram; no mAP comparison chart | 🔴 Critical |

---

## PHASE 4 — SCIENTIFIC REPORT EVALUATION (as a JUFO judge)

### 4.1 Scientific Quality Assessment

#### Strengths
- **H1 (Transfer Learning):** Perfectly proven. +26.42 pp improvement is dramatic and well-documented with confusion matrices.
- **H2 (Quantization):** Well-proven. 9x compression, 75% latency reduction, <0.1pp accuracy loss — textbook result.
- **H3 (Multi-object detection):** Demonstrated but not fully proven at >15 FPS on CPU (only GPU metrics reported).
- **GIGO Effect section:** Outstanding example of scientific honesty and engineering problem-solving. This will impress judges.
- **Data-centric AI finding:** The EXP-008 vs EXP-006 comparison is a genuine scientific contribution.
- **4-dataset comparison (EXP-013 to EXP-016):** Systematic and novel. This is the project's strongest scientific contribution.

#### Critical Problems

**P1 — The "Trash" class is absent from Stage A entirely.**
The classifier (EXP-001 to EXP-004) was trained on only 4 classes (glass, metal, paper, plastic). The 5th class "trash" does not appear. This is a major inconsistency: the abstract and introduction claim 5 classes, but Stage A only has 4. The methodology table (Table 1 in methodology.tex) confirms only 4 classes with 604 total images. This must be explicitly acknowledged and explained.

**P2 — EXP-005 results (82.3% mAP50) are never discussed in the report.**
EXP-005 achieves 82.3% mAP50 — the highest detection result in the entire project — but is essentially dismissed without explanation. The README notes it used Canny-edge auto-labeled bounding boxes. If auto-labeling caused the GIGO effect, how did EXP-005 achieve 82.3%? This contradiction is never resolved. The experiments.tex section skips EXP-005 entirely.

**P3 — H4 (EMA filter) is stated but never empirically measured.**
The report states the EMA filter "eliminates mechatronic misfires" but provides zero quantitative evidence: no before/after jitter measurements, no servo response curves, no frequency analysis. A hypothesis without a measurable test is not science.

**P4 — EXP-009 is described contradictorily.**
Results.tex says "Im Live-Test mit dem quantisierten 320×320 Modell (EXP-009)..." but EXP-009 is the YOLOv8n tabletop-only model flagged as having "inflated mAP." Using it as the live test benchmark is confusing and potentially misleading.

**P5 — No actual Raspberry Pi deployment results.**
The entire premise is edge deployment on Raspberry Pi, but there are no measurements on actual target hardware. Every paper in the Related Benchmarks table refers to target hardware tests.

### 4.2 Writing Quality Assessment

**Strengths:**
- Scientific German is mostly correct and technical
- Mathematical equations properly typeset (convolution formula, softmax, quantization, EMA)
- Consistent use of `\SI{}{}` and `siunitx`
- Logical structure following scientific convention

**Problems:**
- **Section numbering inconsistency:** Introduction says "Kapitel 4 dokumentiert das Experimentdesign" AND "Kapitel 5 dokumentiert die funktionale Software-Implementierung" — but Chapter 4 covers both.
- **Discussion section (23 lines) is far too short.** JUFO judges expect the discussion to demonstrate scientific maturity.
- **Conclusion (9 lines) is too short.** Should be at least half a page.
- **Future work contradicts current state:** Mentions building a "cloud-based IoT Dashboard" but the Streamlit dashboard already exists locally.
- **Spelling error in experiments.tex L55:** "anschliessend" should be "anschließend" (missing ß).

---

## PHASE 5 — GRAPH AND FIGURE ANALYSIS

### Existing Figures in `latex/figures/`

| Figure | Purpose | Problems | Priority |
|---|---|---|---|
| `exp1-curves.png` | EXP-001 training/val curves | Good — noisy curves prove CNN limitations | Low |
| `exp2-curves.png` | EXP-002 training/val curves | Good — clear convergence | Low |
| `exp3-curves.png` | EXP-003 training/val curves | Good — fine-tuning visible | Low |
| `exp1-confusion.png` | EXP-001 confusion matrix | Good — shows paper class failure | Low |
| `exp2-confusion.png` | EXP-002 confusion matrix | Good | Low |
| `exp3-confusion.png` | EXP-003 confusion matrix | Good | Low |
| `exp4-confusion.png` | EXP-004 INT8 confusion matrix | Good — quantization effect visible | Low |
| `yolov8-results.png` | EXP-009 training metrics | Labeled in caption as EXP-009 — fine but inconsistent with inflated mAP context | Medium |
| `yolov8-confusion.png` | EXP-009 confusion matrix | Same issue | Medium |

### Critically Missing Figures

| Missing Figure | Importance | Available Data | Difficulty |
|---|---|---|---|
| YOLO11n training curves (EXP-013, 014, 015 comparison) | 🔴 Critical | `results/exp013*/results.png` — **files exist** | Low |
| YOLO11n confusion matrix (EXP-014 best model) | 🔴 Critical | `results/exp014*/confusion_matrix.png` — **file exists** | Low |
| mAP50 comparison bar chart (all detection experiments) | 🔴 Critical | All data in experiments_log.md | Low |
| Stage A accuracy comparison bar chart (EXP-001–004) | 🔴 Critical | All data in experiments_log.md | Low |
| Per-class mAP50 heatmap (EXP-013 vs 014 vs 015 vs 016) | 🟡 Important | All in experiments_log.md | Low |
| Dataset class distribution bar chart (Stage A and B) | 🟡 Important | Available in methodology | Low |
| System architecture diagram | 🟡 Important | Described in multiple docs | Medium |
| Field benchmark F1 comparison (all models) | 🟡 Important | `results/field_benchmark_results.md` | Low |
| EMA filter effect visualization | 🔴 Critical (for H4) | None currently exists | High |

---

## PHASE 6 — SOURCE AND CITATION AUDIT

### Current Reference Quality

| Source | Type | Quality | Issues |
|---|---|---|---|
| LeCun et al. (2015) — Deep Learning | Nature article | ✅ Excellent | Correct |
| Sandler et al. (2018) — MobileNetV2 | CVPR | ✅ Excellent | Correct |
| Yosinski et al. (2014) — Transfer Learning | NeurIPS | ✅ Excellent | Correct |
| Deng et al. (2020) — Model Compression | IEEE Proc. | ✅ Good | Overused (cited for almost everything) |
| Umweltbundesamt (2023) | Government data | ✅ Good | Need to verify exact statistics |
| TensorFlow (2024) tutorial | Web page | ⚠️ Weak | Tutorial, not peer-reviewed |
| Ultralytics YOLO — GitHub | GitHub repo | ⚠️ Weak | No DOI |
| Yang & Thung (2016) — TrashNet | CS229 student report | ⚠️ Weak | Not peer-reviewed |
| Proença & Simões (2020) — TACO | arXiv | ✅ Good | Correct |
| Redmon et al. (2016) — YOLO original | CVPR | ✅ Good | Correct for YOLO history |
| `mira_experiments`, `mira_live`, etc. (×10) | Own repo files | 🔴 Bad | Self-citations are not scientific sources |

### Critical Citation Problems

**C1 — 10 of ~22 sources are self-references to own code files**
JUFO judges will immediately notice that `mira_live`, `mira_dashboard`, `mira_experiments`, etc. appear in the bibliography. Citing your own code scripts as scientific sources is not academically acceptable. Replace these with actual published sources.

**C2 — No citation for WaRP dataset** — used in EXP-015 and EXP-016

**C3 — No citation for Roboflow Trash Detection** — the dataset behind EXP-014 (best model)

**C4 — No citation for ByteTrack** — used as tracker throughout

**C5 — No citation for SAM/MobileSAM** — used in label_trashnet_with_sam.py

### Missing Sources That Must Be Added

| Missing Source | Why Needed | Section |
|---|---|---|
| WaRP dataset paper/source | Core dataset for EXP-015/016 | Methodology, Experiments |
| Roboflow Trash Detection citation | Core dataset for EXP-014 (best model) | Methodology, Experiments |
| ByteTrack (Zhang et al., 2022, arXiv:2110.06864) | Used as tracker | Implementation |
| Kirillov et al. (2023) — SAM | Used for auto-labeling pipeline | Methodology |
| Krishnamoorthi (2018) — Quantization whitepaper | Better quantization source | Background |
| A recycling robotics comparison paper | Stand der Technik | Background |

---

## PHASE 7 — CODEBASE AUDIT

### Overall Assessment
The codebase is well-structured with clear separation of concerns (`src/` runtime, `reference/` training, `scripts/` dataset prep, `models/` exports). **Quality: Good for a student project. Above average.**

### Identified Issues

| File | Problem | Severity |
|---|---|---|
| `reference/evaluate_classifier_reference.py` L100 | Uses `image_size=(180,180)` for validation — wrong size if evaluating MobileNetV2 (expects 224×224) | 🟡 Medium |
| `src/live_detector.py` L170–185 | TFLite uses `model.predict()` but `.pt` uses `model.track()` — INT8 models have no ByteTrack tracking | 🟡 Medium (document as limitation) |
| `src/field_benchmark.py` L102–119 | Uses per-image binary class presence (not bounding-box IoU matching) — results are image-level F1, not mAP50 | 🟡 Medium (label correctly in report) |
| `scripts/label_trashnet_with_sam.py` L90–91 | `random.shuffle(samples)` before split — no fixed seed, not reproducible | 🟡 Medium |
| `scripts/merge_dataset_model1.py` L70 | Roboflow test set merged into val — can slightly inflate val metrics | 🟡 Medium |
| `src/config.py` L22–33 | EXP-016 missing from DETECTION_MODEL_LABELS | 🟢 Minor |
| All Stage A training scripts | No early stopping callback — may miss best checkpoint | 🟡 Medium |

### Data Leakage Assessment
**No data leakage detected.** Stage A uses consistent `seed=123`. Stage B uses YOLO-standard dataset splits.

### Dataset Quality Notes
- **Stage A:** 604 images, 4 classes. **Missing trash class entirely.**
- **Stage B (mira_tnr):** 6,802 images. Class imbalance: Plastic has 1316 val instances vs 336 for Glass.
- **TrashNet in Stage B:** Full-image bounding boxes (0.5, 0.5, 1.0, 1.0) are an approximation that forces the detector to treat entire images as single objects.

---

## PHASE 8 — README ANALYSIS

### Strengths
- Exceptionally detailed and well-organized for a student project
- Honest labeling of EXP-009 as "WEAK — Inflated from clean backgrounds"
- Excellent camera optimization documentation
- Related benchmarks section with honest caveats is outstanding
- Good CLI reference documentation

### Weaknesses
- The "4-Model Comparison (In Progress)" shows Model 4 as "Planned" — needs updating
- README badge says "Jugend forscht 2026" but title page says "JUGEND FORSCHT 2027" — **year inconsistency**
- Missing dataset download/setup instructions
- No screenshots of live dashboard or detection output

---

## PHASE 9 — FINAL AUDIT REPORT

### 🔴 CRITICAL — Must Fix Before Submission

| ID | Problem | Location | Fix Required |
|---|---|---|---|
| C1 | Trash class absent from Stage A (classifier only 4 classes) | methodology.tex, abstract.tex | Explicitly acknowledge and justify this limitation |
| C2 | 10 self-citations to own repo files used as scientific sources | references.bib | Replace with actual published citations |
| C3 | Missing YOLO11n figures for EXP-013/014/015 in LaTeX report | experiments.tex, results.tex | Add existing files from `results/exp013*/` and `exp014*/` |
| C4 | H4 (EMA filter) has no quantitative experimental proof | discussion.tex | Measure jitter or explicitly downgrade to "planned experiment" |
| C5 | EXP-005 (82.3% mAP50) contradiction never explained | experiments.tex | Address how auto-labeling "failure" still yielded 82.3% |
| C6 | No Raspberry Pi benchmark results despite stated target | results.tex | Add CPU inference timing or explicitly note as future work |
| C7 | Missing mAP50 comparison visualization across experiments | results.tex | Create comparative bar chart from existing data |
| C8 | WaRP and Roboflow datasets completely uncited | references.bib | Find and add proper citations |

### 🟡 IMPORTANT — Strongly Recommended

| ID | Problem | Location | Fix Required |
|---|---|---|---|
| I1 | Discussion section (23 lines) far too short | discussion.tex | Expand to ≥1.5 pages: hypothesis table, data quality analysis, limitations |
| I2 | Conclusion section (9 lines) too short | conclusion.tex | Expand to ~0.5 page |
| I3 | Section numbering inconsistency in introduction | introduction.tex | Fix "Kapitel 4/5 dokumentiert" conflicts |
| I4 | Future work still mentions building the dashboard | future_work.tex | Update to reflect dashboard already exists |
| I5 | Field benchmark results not referenced in report | results.tex | Add field_benchmark_results.md data |
| I6 | Class imbalance in Stage B dataset not discussed | discussion.tex | Add Plastic dominance analysis |
| I7 | All latency numbers are GPU — not clearly labeled | results.tex | Clarify all latency measurements are GPU, not target hardware |
| I8 | Spelling error: "anschliessend" → "anschließend" | experiments.tex L55 | Fix |
| I9 | README year says 2026, title page says 2027 | README.md | Fix year |
| I10 | EXP-009 used as live test example contradicts "inflated" warning | results.tex | Switch to EXP-014 as live demo reference |

### 🟢 OPTIONAL — Additional Improvements

| ID | Problem | Fix |
|---|---|---|
| O1 | No system architecture diagram in report | Add TikZ pipeline diagram |
| O2 | No dataset sample grid (example images) | Add 4×4 image grid per class |
| O3 | ByteTrack not cited | Add Zhang et al. (2022) citation |
| O4 | Roboflow 64→5 class mapping not shown in report | Add mapping table to methodology |
| O5 | EXP-016 (WaRP-only) not in LaTeX report | Add as fourth comparison point |
| O6 | Field benchmark metric ≠ mAP50 not clarified | Note it measures image-level F1 |
| O7 | No photo of physical setup | Add experimental setup figure |
| O8 | EMA alpha=0.15 not justified | Brief justification in background.tex |
| O9 | Training time comparison underemphasized | Highlight 0.3h vs 4.7h comparison |

---

## Missing Information Summary

### Missing Experiments
1. **EMA filter quantification:** Before/after jitter measurement (required for H4)
2. **CPU inference timing:** Laptop CPU or Raspberry Pi for all models
3. **EXP-016 in report:** Completed but not in LaTeX
4. **EXP-017 (all datasets):** Listed as "Planned" — decide to complete or remove

### Missing Graphs (ranked by JUFO priority)
1. mAP50 comparison bar chart: all detection experiments (EXP-005 to EXP-016)
2. YOLO11n confusion matrix for EXP-014 — **file exists** in `results/exp014_yolo11n_tnr/`
3. YOLO11n training curves for EXP-013/014/015 side-by-side — **files exist**
4. Per-class mAP50 heatmap across all 4 dataset experiments
5. Stage A accuracy comparison bar chart (EXP-001 to EXP-004)
6. Dataset class distribution charts (Stage A and Stage B)
7. System architecture diagram
8. Field benchmark F1 bar chart

### Missing Citations
1. WaRP dataset
2. Roboflow Trash Detection dataset
3. ByteTrack (Zhang et al., 2022, arXiv:2110.06864)
4. SAM / MobileSAM (Kirillov et al., 2023)
5. A Raspberry Pi edge AI deployment benchmark paper
6. A commercial recycling AI comparison paper (e.g., Tomra, AMP Robotics)

---

## Improvement Roadmap

| Priority | Improvement | JUFO Impact | Difficulty | Time Estimate | Files |
|---|---|---|---|---|---|
| 1 | Add YOLO11n figures (existing files) to LaTeX | 🔴 Very High | Easy | 1 h | experiments.tex + copy figures |
| 2 | Create mAP50 comparison bar chart | 🔴 Very High | Easy | 1 h | results.tex + new figure |
| 3 | Expand discussion to ≥1.5 pages | 🔴 Very High | Medium | 3 h | discussion.tex |
| 4 | Fix bibliography: remove self-refs, add 6 missing sources | 🔴 Very High | Medium | 2 h | references.bib |
| 5 | Acknowledge trash class absence in Stage A | 🔴 Very High | Easy | 30 min | methodology.tex |
| 6 | Add field benchmark results to report | 🟡 High | Easy | 1 h | results.tex |
| 7 | Expand conclusion to ~0.5 page | 🟡 High | Easy | 1 h | conclusion.tex |
| 8 | Add EXP-016 to experiments section | 🟡 High | Easy | 30 min | experiments.tex |
| 9 | Create per-class mAP50 heatmap (4 datasets) | 🟡 High | Medium | 2 h | results.tex + new figure |
| 10 | Address H4 EMA: measure or mark as future work | 🟡 High | Hard | 4 h | discussion.tex |
| 11 | Fix section numbering in introduction | 🟢 Medium | Easy | 15 min | introduction.tex |
| 12 | Add system architecture diagram | 🟢 Medium | Medium | 2 h | implementation.tex + figure |
| 13 | Add dataset sample grid | 🟢 Medium | Easy | 1 h | methodology.tex + figure |
| 14 | Clarify all latency = GPU latency | 🟢 Medium | Easy | 30 min | results.tex |
| 15 | Fix spelling: "anschliessend" → "anschließend" | 🟢 Low | Trivial | 5 min | experiments.tex L55 |

---

## Strengths to Emphasize in Submission

These are **genuine scientific contributions** that JUFO judges will value:

1. **GIGO effect documentation** — A real engineering failure that led to a better scientific approach. This shows persistence and maturity.
2. **Data-centric AI finding** (EXP-008 vs EXP-006) — Same accuracy in half the training time by cleaning data. A publishable-quality insight.
3. **4-dataset comparative study** — First systematic comparison of TACO/TrashNet/Roboflow/WaRP for 5-class recycling detection.
4. **Honest handling of EXP-009 inflation** — Scientific integrity is explicitly valued by JUFO judges over inflated results.
5. **INT8 quantization pipeline** — 9x model compression with no accuracy loss, fully documented.
6. **Threaded camera + EMA filter** — Practical engineering solutions with documented design decisions.
7. **Serial handshake protocol** — Concrete plan for mechatronic integration with real code.

---

> [!CAUTION]
> **STOP — Audit Complete. No files were modified.**
>
> This report identifies all problems, missing elements, and improvement opportunities.
> The next phase (implementation/rewriting) should be performed as a separate task based on this audit.
