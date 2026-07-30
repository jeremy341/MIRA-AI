# User Actions Before Jugend forscht Submission

These items require personal information, new experimental evidence, or a decision by the project author. They cannot be completed from the repository alone.

## Required before PDF submission

- Confirm the exact competition name assigned in JufoWV. `latex/sections/title.tex` currently says `Regionalwettbewerb Nordrhein-Westfalen (Ruhrgebiet)`, which is not an official competition name.
- Confirm the submission year, school year, school name, and submission date on the title page.
- Replace the supervising-teacher TODO in `latex/sections/appendix.tex` with the full name and exact contribution.
- Enter the same support and AI disclosures in JufoWV. The report currently discloses Anthropic Claude and OpenAI tools for code review, debugging, drafting, and critique.
- Read the final report in full and confirm that the wording accurately reflects your own work and understanding.

## Evidence still needed

- Preserve the final YOLO11n Kaggle run: notebook URL or ID, console log, `args.yaml`, `results.csv`, plots, `best.pt`, `last.pt`, Ultralytics version, dataset ZIP identity, and run duration.
- Add the new result to the report only after validating it on the no-SortWaste validation and test splits. Do not replace EXP-014's historical numbers without a complete result artifact.
- Identify the authoritative Stage-A EXP-001 split and evaluation artifact. Current historical records disagree about image count and accuracy, so the rewritten report treats the comparison cautiously.
- If Edge performance will be claimed, run a documented benchmark on the actual target device. Record model format, input size, runtime, thread count, warm-up, number of runs, mean/median/P90 latency, peak memory, temperature, and sustained FPS.
- If the robot arm will be claimed as implemented, preserve firmware, wiring/BOM, camera calibration, coordinate transform, grasp success, sorting accuracy, cycle time, and failure cases.

## Decisions to make at the evidence cutoff

- Keep the project scope as a computer-vision software prototype unless the physical arm is demonstrably working.
- Keep Raspberry Pi and distillation work under future work unless measured artifacts exist.
- Decide whether to retain the preliminary image-level class-presence benchmark. Its historical model totals are inconsistent; it is excluded from the rewritten headline conclusions.
- Choose one physical target platform for final benchmarking rather than treating Raspberry Pi Zero 2W and Raspberry Pi 4 as interchangeable.

## Final verification

- Build the report from a clean output directory with `latexmk -pdf main.tex`.
- Verify that the counted main section remains at most 15 pages, the PDF remains below 30 MB, and no TODO text remains.
- Check every table and reported number against `docs/EVIDENCE_LEDGER.md` and its cited artifact.
- Run `python -m pytest tests -q`, `python -m ruff check src tests scripts`, `python -m ruff format --check src tests scripts`, and the CI mypy command before the final commit.
