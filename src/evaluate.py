import tensorflow as tf
import numpy as np
import pathlib
import matplotlib.pyplot as plt
import argparse
import time  # For calculating CPU latency
from sklearn.metrics import classification_report, ConfusionMatrixDisplay

# 0. ARGUMENT PARSING
parser = argparse.ArgumentParser(description="Evaluate a MIRA Waste Classification Model.")
parser.add_argument(
    "--model",
    type=str,
    default="mira_waste_model.keras",
    help="Name of the model file to evaluate (e.g., mira_transfer_model.keras)"
)
parser.add_argument(
    "--exp",
    type=str,
    default="EXP-001_Baseline",
    help="Name of the experiment folder for saving results (e.g., EXP-002_MobileNetV2)"
)
args = parser.parse_args()

# 1. PATH RESOLUTION
SCRIPT_DIR = pathlib.Path(__file__).resolve().parent
ROOT_DIR = SCRIPT_DIR.parent
DATA_DIR = ROOT_DIR / "data"

SAVE_DIR = ROOT_DIR / 'results' / args.exp
SAVE_DIR.mkdir(parents=True, exist_ok=True)

# Central models directory path with safe fallback logic
MODEL_PATH = ROOT_DIR / "models" / args.model
if not MODEL_PATH.exists():
    MODEL_PATH = SCRIPT_DIR / args.model

if not MODEL_PATH.exists():
    raise FileNotFoundError(f"Could not locate model file: {args.model} under /models or /src")

# Match image size dynamically based on which model is selected
img_size = (180, 180) if "waste" in args.model else (224, 224)

# 2. LOAD VALIDATION DATASET
val_ds = tf.keras.utils.image_dataset_from_directory(
    DATA_DIR,
    validation_split=0.2,
    subset="validation",
    seed=123,
    image_size=img_size,
    batch_size=32,
    crop_to_aspect_ratio=True,
    shuffle=True
)

class_names = val_ds.class_names

# 3. LOAD THE TRAINED AI MODEL
print(f"Loading model from {MODEL_PATH}...")
model = tf.keras.models.load_model(MODEL_PATH)

# 4. BATCH-BY-BATCH EVALUATION & LATENCY TRACKING
print(f"Evaluating model batch-by-batch using {args.model}...")
y_true = []
y_pred = []
inference_times = []

for images, labels in val_ds:
    # Measure exact CPU execution start
    start_time = time.perf_counter()
    preds = model.predict(images, verbose=0)
    end_time = time.perf_counter()

    # Calculate inference latency per single image in milliseconds
    batch_time_ms = (end_time - start_time) * 1000
    time_per_image = batch_time_ms / len(images)
    inference_times.append(time_per_image)

    batch_preds = np.argmax(preds, axis=1)

    y_pred.extend(batch_preds)
    y_true.extend(labels.numpy())

y_true = np.array(y_true)
y_pred = np.array(y_pred)
avg_latency_ms = np.mean(inference_times)

# 5. PRINT THE EVALUATION TABLE
print(f"\n--- Classification Report: {args.exp} ---")
report = classification_report(y_true, y_pred, target_names=class_names)
print(report)
print(f"Average CPU Inference Latency: {avg_latency_ms:.2f} ms per image")

# Save text report to results folder
report_save_path = SAVE_DIR / "classification_report.txt"
with open(report_save_path, "w") as f:
    f.write(report)
    f.write(f"\nAverage CPU Inference Latency: {avg_latency_ms:.2f} ms per image\n")

# 6. DRAW AND SAVE THE CONFUSION MATRIX GRAPH
ConfusionMatrixDisplay.from_predictions(y_true, y_pred, display_labels=class_names, cmap='Blues')
plt.title(f"MIRA {args.exp} Confusion Matrix")

# Save the plot automatically
plt.savefig(SAVE_DIR / 'confusion_matrix.png', dpi=300)
plt.show()