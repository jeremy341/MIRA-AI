# Dataset Origins

The local dataset artifacts are disposable. These canonical sources are kept so
the datasets can be downloaded again when needed.

## Final Balanced Dataset Sources

The final no-SortWaste balanced dataset was built from these sources:

| Source | Canonical origin | Notes |
|---|---|---|
| dmedhi | https://huggingface.co/datasets/dmedhi/garbage-image-classification-detection | Object detection dataset |
| TACO | https://github.com/pedropro/TACO | Trash annotations in context |
| Roboflow Trash Detection | https://universe.roboflow.com/jerry-jukbu/trash-detection-1fjjc-uqlv1/dataset/dataset | Local export: CC BY 4.0, July 5, 2026 |
| TrashNet | https://github.com/garythung/trashnet | SAM-labeled locally for detection |

TrashNet is also available as a dataset mirror at:
https://huggingface.co/datasets/garythung/trashnet

## Excluded Source

WaRP was used in earlier experiments but is excluded from the final balanced
dataset:

https://github.com/AIRI-Institute/WaRP

The WaRP repository describes its data as research-use-only. Check the current
upstream terms before redistributing a new derivative dataset.
