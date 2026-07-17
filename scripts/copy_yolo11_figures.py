import os
import shutil

# Root directory setup
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
RESULTS_DIR = os.path.join(ROOT_DIR, "results")
FIGURES_DIR = os.path.join(ROOT_DIR, "latex", "figures")

os.makedirs(FIGURES_DIR, exist_ok=True)

# List of mappings: (source_folder, source_file, target_file)
mappings = [
    ("exp013_yolo11n_v2", "results.png", "exp13-results.png"),
    ("exp013_yolo11n_v2", "confusion_matrix.png", "exp13-confusion.png"),
    ("exp014_yolo11n_tnr", "results.png", "exp14-results.png"),
    ("exp014_yolo11n_tnr", "confusion_matrix.png", "exp14-confusion.png"),
    ("exp015_yolo11n_tnw", "results.png", "exp15-results.png"),
    ("exp015_yolo11n_tnw", "confusion_matrix.png", "exp15-confusion.png"),
    ("exp016_yolo11n_warp", "results.png", "exp16-results.png"),
    ("exp016_yolo11n_warp", "confusion_matrix.png", "exp16-confusion.png")
]

for src_folder, src_file, dest_file in mappings:
    src_path = os.path.join(RESULTS_DIR, src_folder, src_file)
    dest_path = os.path.join(FIGURES_DIR, dest_file)
    if os.path.exists(src_path):
        shutil.copy2(src_path, dest_path)
        print(f"Copied {src_folder}/{src_file} to figures/{dest_file}")
    else:
        print(f"WARNING: Source file not found: {src_path}")

print("All YOLO11 figures copied successfully!")
