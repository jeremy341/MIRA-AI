# Dataset Origins

All dataset origins for people to download them from their original sources. The final balanced dataset is built from these sources, and the license information is included in the table below. 
The dataset is not included in this repository.


## Final Balanced Dataset Sources

The final no-SortWaste balanced dataset was built from these sources:

| Source | Canonical origin | Notes |
|---|---|---|
| dmedhi | https://huggingface.co/datasets/dmedhi/garbage-image-classification-detection | Object detection dataset |
| TACO | https://github.com/pedropro/TACO | Trash annotations in context |
| Roboflow Trash Detection | https://universe.roboflow.com/jerry-jukbu/trash-detection-1fjjc-uqlv1 | Local export: CC BY 4.0, July 5, 2026 |
| TrashNet | https://github.com/garythung/trashnet | SAM-labeled locally for detection |

TrashNet is also available as a dataset mirror at:
https://huggingface.co/datasets/garythung/trashnet

## Excluded Source

WaRP was used in earlier experiments but is excluded from the final balanced
dataset becaue it made the results worse:

https://github.com/AIRI-Institute/WaRP

also make sure to check out all the TOS as WaRP is research only and not for commercial use.