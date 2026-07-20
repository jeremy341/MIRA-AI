"""[DEPRECATED] Thin wrapper for backward compatibility.

Use instead:
    mira merge --sources taco_trashnet roboflow warp --output datasets/MyCustom
"""

import sys
from pathlib import Path

_dir = str(Path(__file__).resolve().parent)
if _dir not in sys.path:
    sys.path.insert(0, _dir)

print("WARNING: merge_dataset_model4.py is deprecated. Use 'mira merge' instead.")

sys.argv = [sys.argv[0]] + ["--sources", "taco_trashnet,roboflow,warp"] + sys.argv[1:]
from merge_dataset import main

main()
