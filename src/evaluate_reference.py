#!/usr/bin/env python3
"""
================================================================================
evaluate_reference.py — MIRA Model Evaluation (Lernvorlage)
================================================================================

DIES IST EINE LERNVORLAGE. Jede Zeile ist kommentiert, damit du verstehst,
WAS passiert und WARUM es passiert. Kopiere nicht blind — lese und verstehe.

ZIEL:
    Ein trainiertes Modell auf dem Validierungsdatensatz evaluieren und
    folgende Ergebnisse produzieren:
    1. Classification Report (Accuracy, Precision, Recall, F1 pro Klasse)
    2. Confusion Matrix als PNG-Grafik
    3. Per-Class Bar Chart (Precision/Recall/F1)
    4. Ergebnisse als JSON (für JuFo-Experimente)

AUTOR:     MIRA Technical Mentor
ERSTELLT:  Juni 2026
================================================================================
"""

# ═══════════════════════════════════════════════════════════════════════════════
# TEIL 1: IMPORTS
# ═══════════════════════════════════════════════════════════════════════════════

# tensorflow — für das Laden des Modells und der Daten
import tensorflow as tf

# numpy — für numerische Operationen (Arrays, Mathematik)
import numpy as np

# pathlib — für plattformunabhängige Dateipfade (Windows/Linux/Mac)
#           pathlib.Path ist BESSER als String-Pfade mit + "/" oder os.path.join
import pathlib

# matplotlib — für professionelle Grafiken
import matplotlib.pyplot as plt

# sklearn.metrics — die gold-Standard-Bibliothek für ML-Metriken
#                    Jede JuFo-Jury erwartet, dass du sklearn verwendest
from sklearn.metrics import (
    classification_report,
    confusion_matrix,
    accuracy_score,
    precision_score,
    recall_score,
    f1_score
)

# json — für strukturierte Datenspeicherung (für JuFo-Experimentlog!)
import json

# datetime — für Zeitstempel
from datetime import datetime

# os — für Dateigrößen (z.B. Modellgröße in KB)
import os


# ═══════════════════════════════════════════════════════════════════════════════
# TEIL 2: PFADE DEFINIEREN
# ═══════════════════════════════════════════════════════════════════════════════

# pathlib.Path(__file__) gibt den Pfad zur AKTUELLEN Python-Datei
# .resolve() macht den Pfad absolut (vollständig, nicht relativ)
# .parent gibt das VERZEICHNIS, in dem diese Datei liegt
SCRIPT_DIR = pathlib.Path(__file__).resolve().parent      # z.B. .../MIRA-AI/src
ROOT_DIR = SCRIPT_DIR.parent                                 # z.B. .../MIRA-AI
DATA_DIR = ROOT_DIR / "data"                                 # .../MIRA-AI/data
RESULTS_DIR = ROOT_DIR / "results" / "EXP-001_Baseline"      # .../MIRA-AI/results/EXP-001_Baseline

# mkdir(parents=True, exist_ok=True) erstellt Verzeichnisse, falls sie nicht existieren
# parents=True: erstellt auch übergeordnete Verzeichnisse (z.B. "results/" zuerst)
# exist_ok=True: kein Fehler, wenn das Verzeichnis schon existiert
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

# MODELL-PFAD: Zuerst im Root suchen, dann im src-Ordner als Fallback
MODEL_PATH = ROOT_DIR / "mira_waste_model.keras"
if not MODEL_PATH.exists():
    MODEL_PATH = SCRIPT_DIR / "mira_waste_model.keras"

print(f"📂 Daten-Verzeichnis: {DATA_DIR}")
print(f"📂 Ergebnis-Verzeichnis: {RESULTS_DIR}")
print(f"🧠 Modell-Pfad: {MODEL_PATH}")


# ═══════════════════════════════════════════════════════════════════════════════
# TEIL 3: DATEN LADEN
# ═══════════════════════════════════════════════════════════════════════════════

# Die Validation-Daten MÜSSEN die exakt gleichen Parameter haben wie beim Training!
# Andernfalls ist der Vergleich ungültig.

# WICHTIG: shuffle=False
# Warum? Wenn shuffle=True, werden die Bilder in jedem Durchlauf anders sortiert.
# Das macht reproduzierbare Ergebnisse unmöglich. Bei der Evaluation wollen wir
# eine feste, definierte Reihenfolge.

val_ds = tf.keras.utils.image_dataset_from_directory(
    DATA_DIR,
    validation_split=0.2,      # 20% der Daten für Validation (gleich wie Training)
    subset="validation",         # Nur den Validation-Teil laden
    seed=123,                  # Derselbe Seed → derselbe Split wie beim Training!
    image_size=(180, 180),     # Muss zur Trainingsgröße passen
    batch_size=32,             # Batch-Größe
    crop_to_aspect_ratio=True, # Bilder zuschneiden statt verzerren
    shuffle=False              # KRITISCH: Kein Shuffle für Evaluation!
)

# class_names enthält die Namen der Ordner in data/ (alphabetisch sortiert)
# z.B. ["glass", "metal", "paper", "plastic"]
class_names = val_ds.class_names
num_classes = len(class_names)
print(f"\n🏷️  Klassen: {class_names}")
print(f"📊 Anzahl Klassen: {num_classes}")


# ═══════════════════════════════════════════════════════════════════════════════
# TEIL 4: MODELL LADEN
# ═══════════════════════════════════════════════════════════════════════════════

print(f"\n🔄 Lade Modell von {MODEL_PATH}...")
model = tf.keras.models.load_model(MODEL_PATH)

# model.summary() zeigt die Architektur — gut, um sicherzustellen, dass das
# richtige Modell geladen wurde
print("\n" + "="*60)
print("MODELL-ZUSAMMENFASSUNG:")
print("="*60)
model.summary()


# ═══════════════════════════════════════════════════════════════════════════════
# TEIL 5: VORHERSAGEN MACHEN (Batch für Batch)
# ═══════════════════════════════════════════════════════════════════════════════

# Warum Batch für Batch?
# Das Dataset ist in Batches organisiert (z.B. 32 Bilder pro Batch).
# Wir können nicht einfach "predict" auf dem ganzen Dataset aufrufen, weil
# tf.data.Dataset ein Iterator ist, keine feste Liste.
# Wir müssen durch die Batches iterieren und die Ergebnisse sammeln.

print("\n🔮 Mache Vorhersagen...")

y_true = []   # Liste für echte Labels (aus dem Dataset)
y_pred = []   # Liste für vorhergesagte Klassen (vom Modell)
y_probs = []  # Liste für Wahrscheinlichkeiten (für Confidence-Analyse)

for batch_idx, (images, labels) in enumerate(val_ds):
    # images: Tensor mit Shape (batch_size, 180, 180, 3)
    #   - batch_size: Anzahl Bilder in diesem Batch (meist 32, letzter Batch evtl. weniger)
    #   - 180, 180: Bildhöhe und -breite
    #   - 3: RGB-Kanäle (Rot, Grün, Blau)
    
    # labels: Tensor mit Shape (batch_size,)
    #   - Enthält Integer-Werte: 0, 1, 2, 3 (entsprechend den Klassen)

    # Vorhersagen für diesen Batch machen
    # model.predict gibt "Logits" zurück (Rohwerte, nicht Wahrscheinlichkeiten)
    logits = model.predict(images, verbose=0)
    
    # Logits in Wahrscheinlichkeiten umwandeln mit Softmax
    # Softmax: macht aus beliebigen Zahlen Wahrscheinlichkeiten zwischen 0 und 1,
    # die sich zu 1 addieren
    probs = tf.nn.softmax(logits).numpy()
    
    # Für jede Vorhersage den Index der höchsten Wahrscheinlichkeit finden
    # np.argmax(..., axis=1) gibt für jede Zeile den Index des Maximums
    # Beispiel: probs = [[0.1, 0.7, 0.1, 0.1], [0.8, 0.1, 0.05, 0.05]]
    #           → batch_preds = [1, 0]
    batch_preds = np.argmax(probs, axis=1)
    
    # Ergebnisse sammeln (extend = anhängen, nicht überschreiben)
    y_pred.extend(batch_preds)
    y_true.extend(labels.numpy())
    y_probs.extend(probs)
    
    # Fortschritt anzeigen (optional)
    if (batch_idx + 1) % 2 == 0:
        print(f"  Batch {batch_idx + 1} verarbeitet...")

# In NumPy-Arrays umwandeln (für sklearn Metriken benötigt)
y_true = np.array(y_true)
y_pred = np.array(y_pred)
y_probs = np.array(y_probs)

print(f"\n✅ Vorhersagen abgeschlossen: {len(y_true)} Bilder evaluiert")


# ═══════════════════════════════════════════════════════════════════════════════
# TEIL 6: METRIKEN BERECHNEN
# ═══════════════════════════════════════════════════════════════════════════════

print("\n" + "="*60)
print("KLASSIFIKATIONSMETRIKEN")
print("="*60)

# 1. ACCURACY = (richtige Vorhersagen) / (alle Vorhersagen)
#    Beispiel: 120 von 159 richtig → 120/159 = 0.7547 = 75.47%
accuracy = accuracy_score(y_true, y_pred)
print(f"\n📈 Gesamt-Accuracy: {accuracy:.4f} ({accuracy*100:.2f}%)")

# 2. PRECISION, RECALL, F1 pro Klasse
#    average=None gibt ein Array zurück: [precision_klasse_0, precision_klasse_1, ...]
precision = precision_score(y_true, y_pred, average=None)
recall = recall_score(y_true, y_pred, average=None)
f1 = f1_score(y_true, y_pred, average=None)

print(f"\n📊 Per-Class Metriken:")
print(f"{'Klasse':<12} {'Precision':>10} {'Recall':>10} {'F1-Score':>10}")
print("-" * 50)
for i, name in enumerate(class_names):
    print(f"{name:<12} {precision[i]:>10.4f} {recall[i]:>10.4f} {f1[i]:>10.4f}")

# 3. Classification Report (alles zusammen, schön formatiert)
print("\n" + "="*60)
print("CLASSIFICATION REPORT (sklearn)")
print("="*60)
report = classification_report(y_true, y_pred, target_names=class_names)
print(report)

# Report als Textdatei speichern (für JuFo-Mappe!)
report_path = RESULTS_DIR / "classification_report.txt"
with open(report_path, "w", encoding="utf-8") as f:
    f.write("MIRA Model Evaluation Report\n")
    f.write("="*60 + "\n\n")
    f.write(f"Modell: {MODEL_PATH.name}\n")
    f.write(f"Datum: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    f.write(f"Gesamt-Accuracy: {accuracy:.4f}\n\n")
    f.write(report)
print(f"\n💾 Report gespeichert unter: {report_path}")


# ═══════════════════════════════════════════════════════════════════════════════
# TEIL 7: CONFUSION MATRIX ALS GRAFIK
# ═══════════════════════════════════════════════════════════════════════════════

print("\n📊 Erstelle Confusion Matrix...")

cm = confusion_matrix(y_true, y_pred)

# FIGURE + AXES erstellen (Object-Oriented API — immer so machen!)
fig, ax = plt.subplots(figsize=(8, 6))

# imshow zeigt die Matrix als Bild an
# cmap='Blues': Blaue Farbskala (dunkel = mehr Einträge)
# interpolation='nearest': Keine Glättung, scharfe Pixel
im = ax.imshow(cm, cmap='Blues', interpolation='nearest')

# Colorbar (Legende für die Farben)
cbar = fig.colorbar(im, ax=ax)
cbar.set_label('Anzahl', rotation=270, labelpad=20, fontsize=12)

# Achsenticks setzen
ax.set_xticks(np.arange(num_classes))
ax.set_yticks(np.arange(num_classes))

# Achsenbeschriftungen (Klassennamen)
ax.set_xticklabels(class_names, fontsize=11)
ax.set_yticklabels(class_names, fontsize=11)

# Achsentitel
ax.set_xlabel('Predicted Label (Vorhersage)', fontsize=12, fontweight='bold')
ax.set_ylabel('True Label (Tatsächlich)', fontsize=12, fontweight='bold')
ax.set_title('MIRA Confusion Matrix', fontsize=14, fontweight='bold', pad=15)

# In jede Zelle den Wert schreiben
for i in range(num_classes):
    for j in range(num_classes):
        # Farbe des Textes: Weiß bei dunklen Zellen, Schwarz bei hellen
        cell_value = cm[i, j]
        max_val = cm.max()
        text_color = "white" if cell_value > max_val / 2 else "black"
        
        ax.text(j, i, cell_value,
                ha="center", va="center",
                color=text_color, fontsize=14, fontweight='bold')

# Layout anpassen, damit nichts abgeschnitten wird
plt.tight_layout()

# Speichern (dpi=300 = Druckqualität, gut für JuFo-Mappe!)
cm_path = RESULTS_DIR / "confusion_matrix.png"
fig.savefig(cm_path, dpi=300, bbox_inches='tight')
print(f"💾 Confusion Matrix gespeichert unter: {cm_path}")

# Anzeigen (optional — kann auskommentiert werden, wenn du nur speichern willst)
plt.show()


# ═══════════════════════════════════════════════════════════════════════════════
# TEIL 8: PER-CLASS PRECISION/RECALL/F1 BAR CHART
# ═══════════════════════════════════════════════════════════════════════════════

print("\n📊 Erstelle Precision/Recall/F1 Bar Chart...")

x = np.arange(num_classes)  # x-Positionen: [0, 1, 2, 3]
width = 0.25                 # Breite der Balken

fig, ax = plt.subplots(figsize=(10, 6))

# 3 Balkengruppen nebeneinander
rects1 = ax.bar(x - width, precision, width, label='Precision', color='steelblue', edgecolor='black', linewidth=0.5)
rects2 = ax.bar(x, recall, width, label='Recall', color='coral', edgecolor='black', linewidth=0.5)
rects3 = ax.bar(x + width, f1, width, label='F1-Score', color='mediumseagreen', edgecolor='black', linewidth=0.5)

# Achsen und Titel
ax.set_ylabel('Score', fontsize=12, fontweight='bold')
ax.set_xlabel('Klasse', fontsize=12, fontweight='bold')
ax.set_title('MIRA: Precision, Recall & F1-Score per Class', fontsize=14, fontweight='bold')
ax.set_xticks(x)
ax.set_xticklabels(class_names, fontsize=11)
ax.set_ylim([0, 1.1])  # Y-Achse von 0 bis 1.1 (1.0 = perfekt)
ax.legend(loc='upper right', fontsize=10)
ax.grid(axis='y', alpha=0.3, linestyle='--')

# Werte über den Balken anzeigen
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
print(f"💾 Bar Chart gespeichert unter: {bar_path}")
plt.show()


# ═══════════════════════════════════════════════════════════════════════════════
# TEIL 9: ERGEBNISSE ALS JSON SPEICHERN (JuFo-Experimentlog!)
# ═══════════════════════════════════════════════════════════════════════════════

print("\n📝 Speichere Ergebnisse als JSON...")

# Modellgröße in KB berechnen
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

# Per-Class Metriken in JSON einfügen
for i, name in enumerate(class_names):
    results["metrics"]["per_class"][name] = {
        "precision": float(precision[i]),
        "recall": float(recall[i]),
        "f1_score": float(f1[i]),
        "support": int(cm[i].sum())  # Anzahl echter Samples dieser Klasse
    }

json_path = RESULTS_DIR / "metrics.json"
with open(json_path, "w", encoding="utf-8") as f:
    json.dump(results, f, indent=2, ensure_ascii=False)

print(f"💾 JSON-Metriken gespeichert unter: {json_path}")


# ═══════════════════════════════════════════════════════════════════════════════
# TEIL 10: ZUSAMMENFASSUNG AUSGEBEN
# ═══════════════════════════════════════════════════════════════════════════════

print("\n" + "="*60)
print("ZUSAMMENFASSUNG")
print("="*60)
print(f"Modell:              {MODEL_PATH.name}")
print(f"Validierungsbilder:  {len(y_true)}")
print(f"Gesamt-Accuracy:     {accuracy:.4f} ({accuracy*100:.2f}%)")
print(f"Modellgröße:         {model_size_kb:.1f} KB")
print(f"\nGespeicherte Dateien:")
print(f"  - {report_path}")
print(f"  - {cm_path}")
print(f"  - {bar_path}")
print(f"  - {json_path}")
print(f"\n📁 Alle Ergebnisse in: {RESULTS_DIR}")
print("="*60)


# ═══════════════════════════════════════════════════════════════════════════════
# LERNFRAGEN (beantworte diese, um zu prüfen, ob du alles verstanden hast):
# ═══════════════════════════════════════════════════════════════════════════════
#
# 1. Warum verwenden wir shuffle=False beim Validierungsdatensatz?
#    → Damit die Reihenfolge der Bilder und Labels identisch bleibt.
#
# 2. Was ist der Unterschied zwischen Logits und Wahrscheinlichkeiten?
#    → Logits = Rohwerte (können negativ sein, Summe ≠ 1)
#    → Wahrscheinlichkeiten = nach Softmax, zwischen 0 und 1, summieren zu 1
#
# 3. Was macht np.argmax(..., axis=1)?
#    → Gibt den INDEX des höchsten Werts in jeder ZEILE zurück.
#
# 4. Was ist der Unterschied zwischen Precision und Recall?
#    → Precision: "Wenn ich 'Plastik' sage, wie oft habe ich recht?"
#    → Recall: "Wie viel der echten Plastik-Bilder habe ich gefunden?"
#
# 5. Warum speichern wir Ergebnisse als JSON?
#    → Maschinenlesbar, strukturiert, perfekt für Experiment-Logs und JuFo.
#
# ═══════════════════════════════════════════════════════════════════════════════
