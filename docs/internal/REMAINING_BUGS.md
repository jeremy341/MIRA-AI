# Remaining Bugs — Post-Review Audit (2026-07-17)

## Fixed (2026-07-17)

- **B12** — Inventory reset on model switch: Added `model_switch_event` (threading.Event), set in `handle_load_model`, checked + locals reinitialized in `_camera_loop`
- **B17** — Frame height 480→360 in `reference/live_classifier.py:43`
- **B23** — bytetrack.yaml `frame_rate: 30`→`20`
- **R#6** — README project tree `~14,000`→`~6,800`
- **R#12** — Removed false SHA256 hashes claim from README Reproducibility section

## Skipped (Deferred)
- B16: EarlyStopping — user said "wait"
- R#8: Dashboard screenshot + GIF — waiting for user assets

## Intentional / Won't Fix
- B6/B7: sys.path hack & import inconsistency — project-wide convention, guarded and documented
