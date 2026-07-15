# Cursor Brief — MIRA JUFO Report
# Your job: ADJUST, FIX, ADD to the existing LaTeX report. Do NOT rewrite from scratch.
# Project: Jugend forscht 2027, Jeremy Darko, Gymnasium Broich
# Language: German academic (KOMA-Script scrartcl, 15 pages max)
# Files: latex/sections/*.tex, latex/references.bib

---

## SECTION STATUS

| Section | File | Lines | Status |
|---------|------|-------|--------|
| Title | sections/title.tex | 26 | OK |
| Abstract | sections/abstract.tex | 13 | FIX needed |
| Introduction | sections/introduction.tex | 26 | OK |
| Background | sections/background.tex | 64 | OK |
| Methodology | sections/methodology.tex | 81 | OK |
| Implementation | sections/implementation.tex | 67 | OK |
| Experiments | sections/experiments.tex | 141 | FIX needed |
| Results | sections/results.tex | 171 | FIX needed |
| Discussion | sections/discussion.tex | 64 | EXPAND (too short) |
| Future Work | sections/future_work.tex | 9 | FIX + EXPAND |
| Conclusion | sections/conclusion.tex | 11 | EXPAND (too short) |
| Appendix | sections/appendix.tex | 8 | OK |

---

## ALL FIXES NEEDED

### FIX 1: abstract.tex — Update EXP range
Line 3: says "EXP-001 bis EXP-015" but EXP-016 exists.
Change to: "EXP-001 bis EXP-016"

### FIX 2: experiments.tex — Add EXP-016 figures
Files exist in latex/figures/: exp16-results.png, exp16-confusion.png
Currently NOT referenced. Add a subfigure block after the EXP-015 figures (after line 140).
Use same pattern as EXP-013/015 subfigures.

### FIX 3: results.tex — Add stagea-acc-comparison.png
File exists in latex/figures/ but is NOT referenced anywhere.
Add it to the Stage A results subsection (after line 22, the table).
Caption: "Vergleich der Validierungsgenauigkeit der vier Klassifikationsmodelle (Stage A)."

### FIX 4: future_work.tex — Dashboard claim is WRONG
Line 8 says: "Cloud-basiertes IoT-Dashboard: Das bereits funktionierende lokale Streamlit-Dashboard wird um Cloud-IoT-Telemetriefunktionen erweitert."
The dashboard ALREADY EXISTS (src/dashboard.py, 148 lines). Rewrite to say the dashboard is done, and future work is cloud/MQTT extension only.

### FIX 5: discussion.tex — EXPAND from 64 to 150+ lines
Current discussion has:
- Hypothesis table (H1-H4) ✓
- EMA filter analysis ✓
- Data-Centric AI finding ✓
- Class imbalance ✓
- Platform compatibility ✓

MISSING from discussion (add these subsections):
- **Limitation: Stage A has only 4 classes (no trash)** — Acknowledge this honestly. The classifier cannot detect trash, only glass/metal/paper/plastic. This limits Stage A's real-world applicability but was intentional (proof of concept before scaling to 5 classes in Stage B).
- **Limitation: No Raspberry Pi benchmark** — Only CPU i7 and GPU T4 numbers exist. Acknowledge that edge deployment on Raspberry Pi is future work. The INT8 quantization results (2.90 MB, ~90-120ms estimated latency) suggest feasibility.
- **Quantization trade-off analysis** — INT8 costs ~13pp F1 on average (85.8% → 72.8% for EXP-014). Discuss when INT8 is worth it (size-critical) vs when FP32 is better (accuracy-critical).
- **Dataset size impact** — Compare 604 images (Stage A) vs 6802 images (EXP-014). More data = better generalization. Discuss scaling laws.
- **Real-world performance gap** — Validation mAP50 (60.7%) vs Field F1 (85.8%). Explain why F1 is higher: field benchmark uses image-level detection (not IoU-based), so it's more lenient. This is appropriate for the sorting use case.

### FIX 6: conclusion.tex — EXPAND from 11 to 50+ lines
Current conclusion is 4 sentences. Expand to include:
- Concrete numbers recap (87.42% classifier, 60.7% mAP50, 85.8% F1, 2.90 MB INT8)
- Key finding: Data quality > architecture (GIGO lesson)
- Key finding: Transfer learning critical for small datasets
- Practical impact: Cost comparison (MIRA ~€50 hardware vs industrial NIR sorters ~€100,000+)
- Broader impact: Environmental benefit of better recycling
- One sentence on what comes next (physical arm integration)

### FIX 7: references.bib — Clean up weak citations
These entries are weak/self-referencing and should be noted:
- `tensorflow2024transfer` (tutorial URL)
- `ultralyticsyolov8` (GitHub URL)
- `roboflow2023trash` (URL only)
- `warp2024dataset` (URL only)
- `jufo2025guide` (self-reference to repo files)

Do NOT remove them — they are valid sources for a Jugend forscht project. But if Cursor finds proper published alternatives, suggest them.

---

## KEY NUMBERS (use these, don't guess)

### Stage A — Classification
| EXP | Model | Val Accuracy | Model Size | CPU Latency |
|-----|-------|-------------|------------|-------------|
| 001 | Scratch CNN | 61.00% | 15.22 MB | 5.81 ms |
| 002 | MobileNetV2 Frozen | 84.28% | 8.49 MB | 38.00 ms |
| 003 | MobileNetV2 Fine-Tuned | 87.42% | 23.48 MB | 40.00 ms |
| 004 | INT8 TFLite | 87.35% | 2.61 MB | 10.32 ms |

### Stage B — Detection
| EXP | Model | Dataset | mAP50 | Notes |
|-----|-------|---------|-------|-------|
| 005 | YOLOv8n | Custom+TrashNet | 82.3% | GIGO (inflated) |
| 006 | YOLOv8n | Wild-Fusion | 39.4% | Noisy auto-labels |
| 008 | YOLOv8n | Bereinigter Tisch | 39.6% | Data-centric |
| 009 | YOLOv8n | Pristine TrashNet | 72.8% | Inflated (white bg) |
| 011 | YOLOv8n | TACO only | 35.0% | Wild-only baseline |
| 013 | YOLO11n | TACO+TrashNet | 55.1% | mira_v2 baseline |
| 014 | YOLO11n | TACO+TrashNet+Roboflow | **60.7%** | **Best model** |
| 015 | YOLO11n | TACO+TrashNet+WaRP | 56.0% | Glass strong |
| 016 | YOLO11n | WaRP only | 58.8% | No trash class |

### Field Benchmark (Live Webcam)
| Model | F1 | Precision | Recall |
|-------|-----|-----------|--------|
| mira_exp014.pt | **85.8%** | 92.9% | 79.7% |
| mira_exp014_int8.tflite | 72.8% | 96.1% | 58.6% |
| mira_exp011_int8.tflite | 0.0% | 0.0% | 0.0% (needs conf=0.25) |

### EXP-014 Per-Class (Validation)
| Class | mAP50 | Instances |
|-------|-------|-----------|
| Paper | 82.9% | 474 |
| Plastic | 72.1% | 1316 |
| Metal | 71.3% | 439 |
| Glass | 50.2% | 336 |
| Trash | 26.9% | 561 |

### EXP-014 Per-Class (Field)
| Class | F1 |
|-------|-----|
| Paper | 90.7% |
| Glass | 89.9% |
| Plastic | 88.9% |
| Metal | 84.9% |
| Trash | 54.0% |

---

## HYPOTHESES

| ID | Claim | Verdict | Evidence |
|----|-------|---------|----------|
| H1 | Transfer Learning > Scratch CNN by ≥20pp | **Bestätigt** | +26.42pp (87.42% vs 61.00%) |
| H2 | INT8 quant: ≥4x smaller, ≥40% latency cut, <2pp loss | **Bestätigt** | 9.0x smaller (2.61 MB), 74.2% latency cut (10.32ms vs 40ms), -0.07pp loss |
| H3 | YOLO11n enables multi-object localization ≥15 FPS on CPU | **Bestätigt** | 21.8 FPS (~46ms latency) |
| H4 | EMA filter (α=0.15) prevents mechatronic jitter without critical lag | **Bestätigt** | ~250ms lag, mechanical cycle is 1.5s (10x slower) |

---

## GERMAN ACADEMIC WRITING RULES
- Use passive voice: "Es wurde gezeigt..." not "Wir haben gezeigt..."
- Use \SI{}{} for numbers with units: \SI{60.7}{\percent}, \SI{2.90}{\mega\byte}
- Use \num{} for pure numbers: \num{604}
- Use \cite{} for every claim: \cite{deng2020model}
- Use \emph{} for emphasis, not bold/italic in body text
- Tables: use booktabs (\toprule, \midrule, \bottomrule)
- Keep sentences long, formal, and precise
- No contractions, no colloquialisms

## JUFO FORMATTING
- Max 15 pages (main content, excluding title/abstract/TOC/bibliography)
- A4, 2.5cm L/R/T, 2.0cm bottom
- 1.5 line spacing, no paragraph indent
- Font: 11pt, serif (default lmodern)
- Citations: numeric style (biblatex, biber backend)

## AVAILABLE FIGURES (in latex/figures/)
All exist and are valid PNGs:
class-distribution.png, exp1-curves.png, exp2-curves.png, exp3-curves.png,
exp1-confusion.png, exp2-confusion.png, exp3-confusion.png, exp4-confusion.png,
yolov8-results.png, yolov8-confusion.png,
exp13-results.png, exp13-confusion.png, exp14-results.png, exp14-confusion.png,
exp15-results.png, exp15-confusion.png, exp16-results.png, exp16-confusion.png,
det-map-comparison.png, heatmap-4datasets.png,
field-benchmark-f1.png, ema-filter-effect.png,
stagea-acc-comparison.png (UNREFERENCED — add to results.tex)

## WHAT NOT TO DO
- Do NOT rewrite sections from scratch
- Do NOT change the document structure (chapter order)
- Do NOT add new chapters
- Do NOT change the hypothesis table format
- Do NOT remove any existing content
- Do NOT modify title.tex, appendix.tex, main.tex unless absolutely necessary
