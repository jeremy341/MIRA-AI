"""Merge ALL datasets: TACO + TrashNet + Roboflow + WaRP.

Thin wrapper around merge_dataset.py for backward compatibility.

Usage:
    py scripts/merge_dataset_model4.py
    py scripts/merge_dataset_model4.py --output-dir datasets/MyCustom
    py scripts/merge_dataset_model4.py --dry-run
"""

import sys
from pathlib import Path

_dir = str(Path(__file__).resolve().parent)
if _dir not in sys.path:
    sys.path.insert(0, _dir)

sys.argv = [sys.argv[0]] + ["--sources", "taco_trashnet,roboflow,warp"] + sys.argv[1:]
from merge_dataset import main

main()
