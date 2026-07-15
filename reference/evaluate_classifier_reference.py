#!/usr/bin/env python3
"""
================================================================================
evaluate_reference.py — MIRA Model Evaluation (Learning Template)
================================================================================

THIS IS A LEARNING TEMPLATE. Every line is commented so you understand
WHAT happens and WHY it happens. Don't copy blindly — read and understand.

GOAL:
    Evaluate a trained model on the validation dataset and produce:
    1. Classification Report (Accuracy, Precision, Recall, F1 per class)
    2. Confusion Matrix as PNG image
    3. Per-Class Bar Chart (Precision/Recall/F1)
    4. Results as JSON (for JuFo experiments)

AUTHOR:     MIRA Technical Mentor
CREATED:    June 2026
================================================================================
"""

# ═══════════════════════════════════════════════════════════════════════════════
# PART 1: IMPORTS
# ═══════════════════════════════════════════════════════════════════════════════

# tensorflow — for loading the model and data
import tensorflow as tf

# numpy — for numerical operations (arrays, mathematics)
import numpy as np

# pathlib — for platform-independent file paths (Windows/Linux/Mac)
#           pathlib.Path is BETTER than string paths with + "/" or os.path.join
import pathlib

# matplotlib — for professional graphics
import matplotlib.pyplot as plt

# sklearn.metrics — the gold standard library for ML metrics
#                  Every JuFo jury expects you to use sklearn
from sklearn.metrics import (
    classification_report,
    confusion_matrix,
    accuracy_score,
    precision_score,
    recall_score,
    f1_score
)

# json — for structured data storage (for JuFo experiment log!)
import json

# datetime — for timestamps
from datetime import datetime

# os — for file sizes (e.g. model size in KB)
import os


# ═══════════════════════════════════════════════════════════════════════════════
# PART 2: DEFINE PATHS
# ═══════════════════════════════════════════════════════════════════════════════

# pathlib.Path(__file__) returns the path to the CURRENT Python file
# .resolve() makes the path absolute (complete, not relative)
# .parent returns the DIRECTORY containing this file
SCRIPT_DIR = pathlib.Path(__file__).resolve().parent      # e.g. .../MIRA-AI/src
ROOT_DIR = SCRIPT_DIR.parent                                 # e.g. .../MIRA-AI
DATA_DIR = ROOT_DIR / "data" / "classes"                      # .../MIRA-AI/data/classes
RESULTS_DIR = ROOT_DIR / "results" / "EXP-001_Baseline"      # .../MIRA-AI/results/EXP-001_Baseline

# mkdir(parents=True, exist_ok=True) creates directories if they don't exist
# parents=True: creates parent directories too (e.g. "results/" first)
# exist_ok=True: no error if directory already exists
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

# MODEL PATH: First look in root, then in src folder as fallback
MODEL_PATH = ROOT_DIR / "mira_classifier_baseline.keras"
if not MODEL_PATH.exists():
    MODEL_PATH = SCRIPT_DIR / "mira_classifier_baseline.keras"

print(f"Data directory: {DATA_DIR}")
print(f"Results directory: {RESULTS_DIR}")
print(f"Model path: {MODEL_PATH}")


# ═══════════════════════════════════════════════════════════════════════════════
# PART 3: LOAD DATA
# ═══════════════════════════════════════════════════════════════════════════════

# The validation data MUST use exactly the same parameters as training!
# Otherwise the comparison is invalid.

# IMPORTANT: shuffle=False
# Why? If shuffle=True, images get sorted differently on each pass.
# This makes reproducible results impossible. During evaluation we want
# a fixed, defined order.

val_ds = tf.keras.utils.image_dataset_from_directory(
    DATA_DIR,
    validation_split=0.2,      # 20% of data for validation (same as training)
    subset="validation",         # Only load the validation portion
    seed=123,                  # Same seed → same split as training!
    image_size=(180, 180),     # Must match training size
    batch_size=32,             # Batch size
    crop_to_aspect_ratio=True, # Crop images instead of distorting
    shuffle=False              # CRITICAL: No shuffle for evaluation!
)

# class_names contains the names of folders in data/ (alphabetically sorted)
# e.g. ["glass", "metal", "paper", "plastic"]
class_names = val_ds.class_names
num_classes = len(class_names)
print(f"\nClasses: {class_names}")
print(f"Number of classes: {num_classes}")


# ═══════════════════════════════════════════════════════════════════════════════
# PART 4: LOAD MODEL
# ═══════════════════════════════════════════════════════════════════════════════

print(f"\nLoading model from {MODEL_PATH}...")
model = tf.keras.models.load_model(MODEL_PATH)

# model.summary() shows the architecture — good to ensure the correct model was loaded
print("\n" + "="*60)
print("MODEL SUMMARY:")
print("="*60)
model.summary()


# ═══════════════════════════════════════════════════════════════════════════════
# PART 5: MAKE PREDICTIONS (Batch by Batch)
# ═══════════════════════════════════════════════════════════════════════════════

# Why batch by batch?
# The dataset is organized in batches (e.g. 32 images per batch).
# We can't simply call "predict" on the whole dataset because
# tf.data.Dataset is an iterator, not a fixed list.
# We must iterate through batches and collect results.

print("\nMaking predictions...")

y_true = []   # List for true labels (from dataset)
y_pred = []   # List for predicted classes (from model)
y_probs = []  # List for probabilities (for confidence analysis)

for batch_idx, (images, labels) in enumerate(val_ds):
    # images: Tensor with Shape (batch_size, 180, 180, 3)
    #   - batch_size: Number of images in this batch (usually 32, last batch may be smaller)
    #   - 180, 180: Image height and width
    #   - 3: RGB channels (Red, Green, Blue)
    
    # labels: Tensor with Shape (batch_size,)
    #   - Contains integer values: 0, 1, 2, 3 (corresponding to classes)
    
    # Make predictions for this batch
    # model.predict returns "Logits" (raw values, not probabilities)
    logits = model.predict(images, verbose=0)
    
    # Convert logits to probabilities using Softmax
    # Softmax: turns arbitrary numbers into probabilities between 0 and 1,
    # that sum to 1
    probs = tf.nn.softmax(logits).numpy()
    
    # For each prediction, find the index of the highest probability
    # np.argmax(..., axis=1) returns for each row the index of the maximum
    # Example: probs = [[0.1, 0.7, 0.1, 0.1], [0.8, 0.1, 0.05, 0.05]]
    #           → batch_preds = [1, 0]
    batch_preds = np.argmax(probs, axis=1)
    
    # Collect results (extend = append, not overwrite)
    y_pred.extend(batch_preds)
    y_true.extend(labels.numpy())
    y_probs.extend(probs)
    
    # Show progress (optional)
    if (batch_idx + 1) % 2 == 0:
        print(f"  Processed batch {batch_idx + 1}...")

# Convert to NumPy arrays (required for sklearn metrics)
y_true = np.array(y_true)
y_pred = np.array(y_pred)
y_probs = np.array(y_probs)

print(f"\nPredictions complete: {len(y_true)} images evaluated")


# ═══════════════════════════════════════════════════════════════════════════════
# PART 6: CALCULATE METRICS
# ═══════════════════════════════════════════════════════════════════════════════

print("\n" + "="*60)
print("CLASSIFICATION METRICS")
print("="*60)

# 1. ACCURACY = (correct predictions) / (all predictions)
#    Example: 120 of 159 correct → 120/159 = 0.7547 = 75.47%
accuracy = accuracy_score(y_true, y_pred)
print(f"\nOverall Accuracy: {accuracy:.4f} ({accuracy*100:.2f}%)")

# 2. PRECISION, RECALL, F1 per class
#    average=None returns an array: [precision_class_0, precision_class_1, ...]
precision = precision_score(y_true, y_pred, average=None)
recall = recall_score(y_true, y_pred, average=None)
f1 = f1_score(y_true, y_pred, average=None)

print(f"\nPer-Class Metrics:")
print(f"{'Class':<12} {'Precision':>10} {'Recall':>10} {'F1-Score':>10}")
print("-" * 50)
for i, name in enumerate(class_names):
    print(f"{name:<12} {precision[i]:>10.4f} {recall[i]:>10.4f} {f1[i]:>10.4f}")

# 3. Classification Report (everything together, nicely formatted)
print("\n" + "="*60)
print("CLASSIFICATION REPORT (sklearn)")
print("="*60)
report = classification_report(y_true, y_pred, target_names=class_names)
print(report)

# Save report as text file (for JuFo portfolio!)
report_path = RESULTS_DIR / "classification_report.txt"
with open(report_path, "w", encoding="utf-8") as f:
    f.write("MIRA Model Evaluation Report\n")
    f.write("="*60 + "\n\n")
    f.write(f"Model: {MODEL_PATH.name}\n")
    f.write(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    f.write(f"Overall Accuracy: {accuracy:.4f}\n\n")
    f.write(report)
print(f"\nReport saved to: {report_path}")


# ═══════════════════════════════════════════════════════════════════════════════
# PART 7: CONFUSION MATRIX AS GRAPHIC
# ═══════════════════════════════════════════════════════════════════════════════

print("\nCreating Confusion Matrix...")

cm = confusion_matrix(y_true, y_pred)

# CREATE FIGURE + AXES (Object-Oriented API — always do this!)
fig, ax = plt.subplots(figsize=(8, 6))

# imshow displays the matrix as an image
# cmap='Blues': Blue color scale (dark = more entries)
# interpolation='nearest': No smoothing, sharp pixels
im = ax.imshow(cm, cmap='Blues', interpolation='nearest')

# Colorbar (legend for colors)
cbar = fig.colorbar(im, ax=ax)
cbar.set_label('Count', rotation=270, labelpad=20, fontsize=12)

# Set axis ticks
ax.set_xticks(np.arange(num_classes))
ax.set_yticks(np.arange(num_classes))

# Axis labels (class names)
ax.set_xticklabels(class_names, fontsize=11)
ax.set_yticklabels(class_names, fontsize=11)

# Axis titles
ax.set_xlabel('Predicted Label', fontsize=12, fontweight='bold')
ax.set_ylabel('True Label', fontsize=12, fontweight='bold')
ax.set_title('MIRA Confusion Matrix', fontsize=14, fontweight='bold', pad=15)

# Write value in each cell
for i in range(num_classes):
    for j in range(num_classes):
        # Text color: White on dark cells, black on light cells
        cell_value = cm[i, j]
        max_val = cm.max()
        text_color = "white" if cell_value > max_val / 2 else "black"
        
        ax.text(j, i, cell_value,
                ha="center", va="center",
                color=text_color, fontsize=14, fontweight='bold')

# Adjust layout to prevent clipping
plt.tight_layout()

# Save (dpi=300 = print quality, good for JuFo portfolio!)
cm_path = RESULTS_DIR / "confusion_matrix.png"
fig.savefig(cm_path, dpi=300, bbox_inches='tight')
print(f"Confusion Matrix saved to: {cm_path}")

# Display (optional — can comment out if you only want to save)
plt.show()


# ═══════════════════════════════════════════════════════════════════════════════
# PART 8: PER-CLASS PRECISION/RECALL/F1 BAR CHART
# ═══════════════════════════════════════════════════════════════════════════════

print("\nCreating Precision/Recall/F1 Bar Chart...")

x = np.arange(num_classes)  # x-positions: [0, 1, 2, 3]
width = 0.25                 # width of bars

fig, ax = plt.subplots(figsize=(10, 6))

# 3 groups of bars side by side
rects1 = ax.bar(x - width, precision, width, label='Precision', color='steelblue', edgecolor='black', linewidth=0.5)
rects2 = ax.bar(x, recall, width, label='Recall', color='coral', edgecolor='black', linewidth=0.5)
rects3 = ax.bar(x + width, f1, width, label='F1-Score', color='mediumseagreen', edgecolor='black', linewidth=0.5)

# Axes and title
ax.set_ylabel('Score', fontsize=12, fontweight='bold')
ax.set_xlabel('Class', fontsize=12, fontweight='bold')
ax.set_title('MIRA: Precision, Recall & F1-Score per Class', fontsize=14, fontweight='bold')
ax.set_xticks(x)
ax.set_xticklabels(class_names, fontsize=11)
ax.set_ylim([0, 1.1])  # Y-axis from 0 to 1.1 (1.0 = perfect)
ax.legend(loc='upper right', fontsize=10)
ax.grid(axis='y', alpha=0.3, linestyle='--')

# Show values above bars
for rects in [rects1, rects2, rects3]:
    for rect in rects:
        height = rect.get_height()
        ax.annotate(f'{height:.2f}',
                    xy=(rect.get_x() + rect.get_width() / 2, height),
                    xytext=(0, 3),
                    textcoords="offset points",
                    ha='center', va='bottom', fontsize=8)

plt.tight_layout()
bar_path = RESULTS_DIR / "per_class_metrics.png"
fig.savefig(bar_path, dpi=300, bbox_inches='tight')
print(f"Bar Chart saved to: {bar_path}")
plt.show()


# ═══════════════════════════════════════════════════════════════════════════════
# PART 9: SAVE RESULTS AS JSON (JuFo experiment log!)
# ═══════════════════════════════════════════════════════════════════════════════

print("\nSaving results as JSON...")

# Calculate model size in KB
model_size_kb = os.path.getsize(MODEL_PATH) / 1024 if MODEL_PATH.exists() else 0

results = {
    "experiment_id": "EXP-001",
    "experiment_name": "Baseline CNN Evaluation",
    "timestamp": datetime.now().isoformat(),
    "model": {
        "path": str(MODEL_PATH),
        "name": MODEL_PATH.name,
        "size_kb": round(model_size_kb, 2),
        "total_params": int(model.count_params())
    },
    "dataset": {
        "path": str(DATA_DIR),
        "num_classes": num_classes,
        "class_names": class_names,
        "num_validation_samples": int(len(y_true))
    },
    "metrics": {
        "accuracy": {
            "value": float(accuracy),
            "percentage": round(float(accuracy) * 100, 2)
        },
        "per_class": {}
    },
    "confusion_matrix": cm.tolist()
}

# Add per-class metrics to JSON
for i, name in enumerate(class_names):
    results["metrics"]["per_class"][name] = {
        "precision": float(precision[i]),
        "recall": float(recall[i]),
        "f1_score": float(f1[i]),
        "support": int(cm[i].sum())  # Number of true samples of this class
    }

json_path = RESULTS_DIR / "metrics.json"
with open(json_path, "w", encoding="utf-8") as f:
    json.dump(results, f, indent=2, ensure_ascii=False)

print(f"JSON metrics saved to: {json_path}")


# ═══════════════════════════════════════════════════════════════════════════════
# PART 10: PRINT SUMMARY
# ═══════════════════════════════════════════════════════════════════════════════

print("\n" + "="*60)
print("SUMMARY")
print("="*60)
print(f"Model:              {MODEL_PATH.name}")
print(f"Validation images:  {len(y_true)}")
print(f"Overall Accuracy:   {accuracy:.4f} ({accuracy*100:.2f}%)")
print(f"Model size:         {model_size_kb:.1f} KB")
print(f"\nSaved files:")
print(f"  - {report_path}")
print(f"  - {cm_path}")
print(f"  - {bar_path}")
print(f"  - {json_path}")
print(f"\nAll results in: {RESULTS_DIR}")
print("="*60)


# ═══════════════════════════════════════════════════════════════════════════════
# LEARNING QUESTIONS (answer these to check if you understood everything):
# ═══════════════════════════════════════════════════════════════════════════════
#
# 1. Why do we use shuffle=False for the validation dataset?
#    → So the order of images and labels remains identical.
#
# 2. What is the difference between Logits and Probabilities?
#    → Logits = raw values (can be negative, sum ≠ 1)
#    → Probabilities = after Softmax, between 0 and 1, sum to 1
#
# 3. What does np.argmax(..., axis=1) do?
#    → Returns the INDEX of the highest value in each ROW.
#
# 4. What is the difference between Precision and Recall?
#    → Precision: "When I say 'Plastic', how often am I right?"
#    → Recall: "How much of the true Plastic images did I find?"
#
# 5. Why do we save results as JSON?
#    → Machine-readable, structured, perfect for experiment logs and JuFo.
#
# ═══════════════════════════════════════════════════════════════════════════════
