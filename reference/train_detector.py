import pathlib
from ultralytics import YOLO

# 1. PATH RESOLUTION
SCRIPT_DIR = pathlib.Path(__file__).resolve().parent
ROOT_DIR = SCRIPT_DIR.parent
YOLO_DATA_DIR = ROOT_DIR / "datasets" / "mira_v2"
DATA_YAML = YOLO_DATA_DIR / "dataset.yaml"

# 2. VERIFY DATASET CONFIGURATION
if not DATA_YAML.exists():
    raise FileNotFoundError(f"dataset.yaml not found at {DATA_YAML}. Run merge scripts first.")

# 3. INITIALIZE MODEL
# We start with the 'nano' version (yolov8n) which is optimized for edge devices like Raspberry Pi
print("Initializing YOLOv8-Nano model...")
model = YOLO("yolov8n.pt")

# 4. START TRAINING (EXP-005)
print("Starting training for Stage B: Object Detection...")

# Note for JuFo Report: We use imgsz=640 as it is the standard for YOLOv8.
# For CPU training, this will take some time.
results = model.train(
    data=str(DATA_YAML),
    epochs=30,               # Number of passes over the dataset
    imgsz=640,               # Training image resolution
    batch=16,                # Number of images per batch
    name="mira_exp005",    # Subfolder name in results
    project=str(ROOT_DIR / "results" / "EXP-005_YOLOv8"),
    exist_ok=True,           # Overwrite if folder exists
    device="cpu",            # Force CPU (change to 0 if you have an NVIDIA GPU)
    lr0=0.01,                # Initial learning rate
    lrf=0.01                 # Final learning rate factor
)

print("\nTraining complete.")
print(f"Results saved to: {ROOT_DIR / 'results' / 'EXP-005_YOLOv8' / 'mira_exp005'}")