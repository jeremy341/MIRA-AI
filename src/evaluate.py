import tensorflow as tf
import numpy as np
import pathlib
import matplotlib.pyplot as plt
from sklearn.metrics import classification_report, ConfusionMatrixDisplay

# 1. PATH RESOLUTION
ROOT_DIR = pathlib.Path(__file__).resolve().parent.parent
SCRIPT_DIR = pathlib.Path(__file__).resolve().parent
DATA_DIR = ROOT_DIR / "data"

SAVE_DIR = ROOT_DIR / 'results' / 'EXP-001_Baseline'
SAVE_DIR.mkdir(parents=True, exist_ok=True)

# Try root first, then fall back to src/
MODEL_PATH = ROOT_DIR / "mira_waste_model.keras"
if not MODEL_PATH.exists():
    MODEL_PATH = SCRIPT_DIR / "mira_waste_model.keras"

# 2. LOAD VALIDATION DATASET (We leave shuffle=True to match training split!)
val_ds = tf.keras.utils.image_dataset_from_directory(
    DATA_DIR,
    validation_split=0.2,
    subset="validation",
    seed=123,  # Same seed as training!
    image_size=(180, 180),
    batch_size=32,
    crop_to_aspect_ratio=True,
    shuffle=True  # Match the training dataset shuffling behavior!
)

class_names = val_ds.class_names

# 3. LOAD THE TRAINED AI MODEL
print(f"Loading model from {MODEL_PATH}...")
model = tf.keras.models.load_model(MODEL_PATH)

# 4. BATCH-BY-BATCH EVALUATION
# This extracts predictions and labels at the same moment, bypassing shuffle issues.
print("Evaluating model batch-by-batch...")
y_true = []
y_pred = []

for images, labels in val_ds:
    # 1. Predict probabilities for this batch
    preds = model.predict(images, verbose=0)
    # 2. Find the index of the highest probability
    batch_preds = np.argmax(preds, axis=1)

    # 3. Save the results
    y_pred.extend(batch_preds)
    y_true.extend(labels.numpy())

y_true = np.array(y_true)
y_pred = np.array(y_pred)

# 5. PRINT THE EVALUATION TABLE
print("\n--- Classification Report ---")
report = classification_report(y_true, y_pred, target_names=class_names)
print(report)

# Save text report to results folder
report_save_path = SAVE_DIR / "classification_report.txt"
with open(report_save_path, "w") as f:
    f.write(report)

# 6. DRAW AND SAVE THE CONFUSION MATRIX GRAPH
ConfusionMatrixDisplay.from_predictions(y_true, y_pred, display_labels=class_names, cmap='Blues')
plt.title("MIRA Baseline CNN Confusion Matrix")

# Save the plot automatically
plt.savefig(SAVE_DIR / 'confusion_matrix.png', dpi=300)
plt.show()