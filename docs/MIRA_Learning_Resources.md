# MIRA Lernressourcen — Alles was du brauchst

> Erstellt: Juni 2026 | Für: MIRA AI Edge-Vision Sortierarm
> Enthält: Matplotlib, evaluate.py, Transfer Learning, JuFo-Schreiben

---

## 📊 TEIL 1: Matplotlib — Von 0 auf "Publication Quality"

### Warum du struggled (und das ist normal)

Du hast `plt.plot()` und `plt.show()` gesehen, aber nicht verstanden, **wie Matplotlib wirklich funktioniert**. Matplotlib hat zwei APIs:

1. **Pyplot-API** (`plt.plot`, `plt.title`) — schnell, aber unübersichtlich
2. **Object-Oriented API** (`fig, ax = plt.subplots()`) — sauber, skalierbar, professionell

Du wirst ab jetzt NUR die Object-Oriented API nutzen.

### Die 3 Schichten von Matplotlib (musst du verstehen!)

```
Figure (die Leinwand)
  └── Axes (die einzelne Zeichnung)
        └── Axis (x- und y-Achse)
```

```python
import matplotlib.pyplot as plt
import numpy as np

# 1. Figure + Axes erstellen
fig, ax = plt.subplots(figsize=(8, 5))  # Breite=8, Höhe=5 (Zoll)

# 2. Daten plotten
x = np.linspace(0, 10, 100)
y = np.sin(x)
ax.plot(x, y, color='blue', linewidth=2, label='Sinus')

# 3. Achsen beschriften
ax.set_xlabel('Zeit (s)', fontsize=12)
ax.set_ylabel('Amplitude', fontsize=12)
ax.set_title('Sinuswelle', fontsize=14, fontweight='bold')
ax.legend()
ax.grid(True, alpha=0.3)

# 4. Speichern UND anzeigen
plt.tight_layout()  # Passt Layout an, damit nichts abgeschnitten wird
fig.savefig('sinus.png', dpi=300, bbox_inches='tight')
plt.show()
```

### Multiple Subplots (dein Accuracy/Loss Plot)

```python
fig, axes = plt.subplots(1, 2, figsize=(12, 5))  # 1 Zeile, 2 Spalten

# Linker Plot
ax1 = axes[0]
ax1.plot(epochs, acc, label='Train', color='blue')
ax1.plot(epochs, val_acc, label='Val', color='orange')
ax1.set_title('Accuracy')
ax1.legend()
ax1.set_xlabel('Epoch')
ax1.set_ylabel('Accuracy')
ax1.set_ylim([0, 1])  # Y-Achse von 0 bis 1 fixieren

# Rechter Plot
ax2 = axes[1]
ax2.plot(epochs, loss, label='Train', color='blue')
ax2.plot(epochs, val_loss, label='Val', color='orange')
ax2.set_title('Loss')
ax2.legend()
ax2.set_xlabel('Epoch')
ax2.set_ylabel('Loss')

plt.tight_layout()
fig.savefig('training.png', dpi=300)
plt.show()
```

### Confusion Matrix mit Matplotlib (was du in evaluate.py brauchst)

```python
from sklearn.metrics import confusion_matrix
import matplotlib.pyplot as plt
import numpy as np

# Beispiel-Daten
y_true = [0, 1, 2, 2, 0, 1, 0, 2]
y_pred = [0, 1, 2, 0, 0, 1, 0, 2]
class_names = ['Glas', 'Metall', 'Papier']

cm = confusion_matrix(y_true, y_pred)

fig, ax = plt.subplots(figsize=(8, 6))
im = ax.imshow(cm, cmap='Blues')  # Blaue Farbskala

# Farbleiste
fig.colorbar(im, ax=ax)

# Achsen beschriften
ax.set_xticks(np.arange(len(class_names)))
ax.set_yticks(np.arange(len(class_names)))
ax.set_xticklabels(class_names)
ax.set_yticklabels(class_names)
ax.set_xlabel('Predicted')
ax.set_ylabel('True')
ax.set_title('Confusion Matrix')

# Zahlen in die Zellen schreiben
for i in range(len(class_names)):
    for j in range(len(class_names)):
        text = ax.text(j, i, cm[i, j],
                      ha="center", va="center", color="black", fontsize=14)

plt.tight_layout()
fig.savefig('confusion_matrix.png', dpi=300)
plt.show()
```

### Bar Chart (Precision/Recall pro Klasse)

```python
import numpy as np
import matplotlib.pyplot as plt

classes = ['Glas', 'Metall', 'Papier', 'Plastik']
precision = [0.82, 0.62, 0.43, 0.39]
recall = [0.84, 0.39, 0.07, 0.97]

x = np.arange(len(classes))
width = 0.35

fig, ax = plt.subplots(figsize=(8, 5))
rects1 = ax.bar(x - width/2, precision, width, label='Precision', color='steelblue')
rects2 = ax.bar(x + width/2, recall, width, label='Recall', color='coral')

ax.set_ylabel('Score')
ax.set_title('Precision & Recall per Class')
ax.set_xticks(x)
ax.set_xticklabels(classes)
ax.legend()
ax.set_ylim([0, 1])
ax.grid(axis='y', alpha=0.3)

# Werte über den Balken anzeigen
for rect in rects1:
    height = rect.get_height()
    ax.annotate(f'{height:.2f}',
                xy=(rect.get_x() + rect.get_width() / 2, height),
                xytext=(0, 3), textcoords="offset points",
                ha='center', va='bottom', fontsize=9)

plt.tight_layout()
fig.savefig('precision_recall.png', dpi=300)
plt.show()
```

### Ressourcen zum Lernen (Matplotlib)

| Ressource | Typ | Zeit | Link |
|-----------|-----|------|------|
| **Matplotlib Official Tutorials** | Dokumentation | 2h | https://matplotlib.org/stable/tutorials/introductory/usage.html |
| **Matplotlib Cheat Sheet** | PDF (ausdrucken!) | 15 min | https://matplotlib.org/cheatsheets/ |
| **Real Python: Matplotlib Guide** | Artikel | 1h | https://realpython.com/python-matplotlib-guide/ |
| **Seaborn Official Tutorial** | Dokumentation | 1h | https://seaborn.pydata.org/tutorial.html |
| **3Blue1Brown: But what is a neural network?** | Video | 20 min | YouTube (nicht Matplotlib, aber hilft beim Verständnis) |

**Dein Plan:** 1 Tag = 3 Stunden Matplotlib. Übung: Plotte deine eigenen Trainingsdaten aus der evaluate.py mit OO-API neu.

---

## 🧠 TEIL 2: evaluate.py — Wie man ein Modell WIRKLICH evaluiert

### Was du falsch gemacht hast (und warum)

Dein evaluate.py hat funktioniert, aber du hast es **nicht verstanden**. Du hast Code kopiert und gehofft, dass er läuft. Das ist okay für den ersten Durchgang, aber jetzt lernen wir es richtig.

### Die 4 Säulen der Modellevaluation

```
1. Metriken berechnen    (Accuracy, Precision, Recall, F1)
2. Confusion Matrix      (Wo liegt das Modell genau falsch?)
3. Per-Class Analysis    (Welche Klasse ist das Problem?)
4. Visualisierung        (Für JuFo: Grafiken > Tabellen)
```

### Schritt-für-Schritt: evaluate.py von Grund auf neu schreiben

**Schritt 1: Daten laden (verstehen, nicht kopieren)**

```python
import tensorflow as tf
import numpy as np
import pathlib
from sklearn.metrics import classification_report, confusion_matrix
import matplotlib.pyplot as plt
import json

# Pfade auflösen (verstehe das!)
SCRIPT_DIR = pathlib.Path(__file__).resolve().parent
ROOT_DIR = SCRIPT_DIR.parent  # Ein Verzeichnis höher = Projektroot
DATA_DIR = ROOT_DIR / "data"
MODEL_PATH = ROOT_DIR / "mira_classifier_baseline.keras"
RESULTS_DIR = ROOT_DIR / "results" / "EXP-001"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

# VALIDIERUNGSDATEN laden (shuffle=False ist KRITISCH!)
val_ds = tf.keras.utils.image_dataset_from_directory(
    DATA_DIR,
    validation_split=0.2,
    subset="validation",
    seed=123,
    image_size=(180, 180),
    batch_size=32,
    crop_to_aspect_ratio=True,
    shuffle=False  # Wichtig: Bei shuffle=True verlieren Label ihre Reihenfolge!
)
class_names = val_ds.class_names
print(f"Klassen: {class_names}")
```

**Schritt 2: Modell laden und Vorhersagen machen**

```python
model = tf.keras.models.load_model(MODEL_PATH)

# Batch für Batch vorhersagen
y_true = []
y_pred = []

for images, labels in val_ds:
    # images: Tensor mit Shape (batch_size, 180, 180, 3)
    # labels: Tensor mit Shape (batch_size,) — Integer-Labels

    logits = model.predict(images, verbose=0)  # Rohwerte (vor Softmax)
    probs = tf.nn.softmax(logits).numpy()       # Wahrscheinlichkeiten [0,1]
    batch_preds = np.argmax(probs, axis=1)      # Index des höchsten Werts

    y_pred.extend(batch_preds)
    y_true.extend(labels.numpy())

y_true = np.array(y_true)
y_pred = np.array(y_pred)

print(f"Gesamtbilder: {len(y_true)}")
```

**Schritt 3: Metriken berechnen (verstehe die Mathematik!)**

```python
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score

# Accuracy = (richtige Vorhersagen) / (alle Vorhersagen)
acc = accuracy_score(y_true, y_pred)
print(f"Accuracy: {acc:.4f}")

# Precision = TP / (TP + FP) — "Wie zuverlässig ist eine positive Vorhersage?"
precision = precision_score(y_true, y_pred, average=None)  # Pro Klasse!
print(f"Precision pro Klasse: {dict(zip(class_names, precision))}")

# Recall = TP / (TP + FN) — "Wie viele der echten Klasse wurden gefunden?"
recall = recall_score(y_true, y_pred, average=None)
print(f"Recall pro Klasse: {dict(zip(class_names, recall))}")

# F1 = 2 * (Precision * Recall) / (Precision + Recall)
f1 = f1_score(y_true, y_pred, average=None)
print(f"F1 pro Klasse: {dict(zip(class_names, f1))}")

# Classification Report (alles auf einmal)
report = classification_report(y_true, y_pred, target_names=class_names)
print("\n--- Classification Report ---")
print(report)
```

**Schritt 4: Confusion Matrix als Bild**

```python
cm = confusion_matrix(y_true, y_pred)

fig, ax = plt.subplots(figsize=(8, 6))
im = ax.imshow(cm, cmap='Blues')
fig.colorbar(im, ax=ax)

ax.set_xticks(np.arange(len(class_names)))
ax.set_yticks(np.arange(len(class_names)))
ax.set_xticklabels(class_names)
ax.set_yticklabels(class_names)
ax.set_xlabel('Predicted', fontsize=12)
ax.set_ylabel('True', fontsize=12)
ax.set_title('MIRA Confusion Matrix', fontsize=14, fontweight='bold')

# Zahlen in die Zellen
for i in range(len(class_names)):
    for j in range(len(class_names)):
        color = "white" if cm[i, j] > cm.max() / 2 else "black"
        ax.text(j, i, cm[i, j], ha="center", va="center",
                color=color, fontsize=14, fontweight='bold')

plt.tight_layout()
fig.savefig(RESULTS_DIR / 'confusion_matrix.png', dpi=300)
plt.show()
```

**Schritt 5: Ergebnisse als JSON speichern (für JuFo-Experimente!)**

```python
results = {
    "experiment": "EXP-001",
    "model": "baseline_cnn",
    "accuracy": float(acc),
    "per_class": {
        name: {
            "precision": float(p),
            "recall": float(r),
            "f1": float(f)
        }
        for name, p, r, f in zip(class_names, precision, recall, f1)
    },
    "confusion_matrix": cm.tolist(),
    "timestamp": "2026-06-27T15:00:00"
}

with open(RESULTS_DIR / "metrics.json", "w") as f:
    json.dump(results, f, indent=2)
```

### Die evaluate.py Philosophie

> **Jede evaluate.py muss drei Fragen beantworten:**
> 1. Wie gut ist das Modell insgesamt? (Accuracy)
> 2. Wo macht es Fehler? (Confusion Matrix)
> 3. Welche Klasse ist das Problem? (Per-Class Precision/Recall)

---

## 🤖 TEIL 3: Transfer Learning — MobileNetV2 & EfficientNet

### Warum Transfer Learning dein einziger Weg ist

Dein Datensatz: ~630 Bilder, 4 Klassen = ~157 Bilder pro Klasse.
MobileNetV2 wurde auf 1,4 Millionen Bildern trainiert. Es hat bereits gelernt:
- Layer 1-3: Kanten und Farbübergänge
- Layer 4-10: Texturen und einfache Muster
- Layer 11-20: Komplexe Formen (Augen, Räder, Flaschenformen)
- Layer 21+: Abstrakte Konzepte

Du nutzt die ersten 20 Layer direkt (gefroren) und trainierst nur die obersten 5-10 Layer für deine spezifischen Klassen.

### Lernressourcen Transfer Learning

| Ressource | Typ | Zeit | Warum wichtig |
|-----------|-----|------|---------------|
| **TensorFlow: Transfer Learning Tutorial** | Offizielle Doku | 2h | https://www.tensorflow.org/tutorials/images/transfer_learning |
| **Sentdex: Transfer Learning Video** | YouTube | 30 min | Praktische Intuition |
| **Fast.ai Lesson 1 (Practical Deep Learning)** | Kurs | 2h | https://course.fast.ai/ — die beste Erklärung, warum Transfer Learning funktioniert |
| **CS231n Lecture 7 (CNNs)** | Stanford-Vorlesung | 1h | YouTube: "CS231n Winter 2016: Lecture 7: Training Neural Networks, part 2" |
| **Andrew Ng: Transfer Learning (Coursera)** | Video | 15 min | Sehr kompakt, sehr gut |

### Was du verstehen musst (Teste dich selbst)

Kannst du diese Fragen beantworten?

1. Was ist der Unterschied zwischen **Feature Extraction** und **Fine-Tuning**?
2. Warum muss man bei Fine-Tuning die **Learning Rate verkleinern**?
3. Was passiert, wenn du **alle Layer** von MobileNetV2 sofort trainierst?
4. Warum muss man die **gleiche Normalisierung** (Rescaling) bei Inference wie beim Training verwenden?
5. Was ist ein **GlobalAveragePooling2D** Layer und warum ist er besser als Flatten?

**Wenn du eine dieser Fragen nicht beantworten kannst:** Schaue das TensorFlow Tutorial.

---

## 📝 TEIL 4: JuFo-Bericht schreiben — Lernressourcen

### Struktur eines JuFo-Berichts (15 Seiten max.)

```
1. Abstract / Zusammenfassung      (½ Seite)
2. Einleitung & Motivation         (1 Seite)
3. Forschungsfrage & Hypothese     (1 Seite)
4. Stand der Technik               (2 Seiten)
5. Methodik & Experimentdesign     (2 Seiten)
6. Ergebnisse                      (4 Seiten)
   - Tabellen, Grafiken, Confusion Matrices
   - Vergleich verschiedener Modelle
7. Diskussion                      (2 Seiten)
   - Einschränkungen, Fehlerquellen
8. Fazit & Ausblick                (1 Seite)
9. Literaturverzeichnis            (1 Seite)
```

### Lernressourcen JuFo-Bericht

| Ressource | Typ | Link |
|-----------|-----|------|
| **Jugend forscht: Tipps zur Projektmappe** | Offizielle Doku | https://www.jugend-forscht.de/teilnahme/die-projektmappe.html |
| **Jugend forscht: Beispielprojekte** | Beispielberichte | https://www.jugend-forscht.de/meldungen/archiv.html |
| **Writing in the Sciences (Stanford)** | Kurs | Coursera: "Writing in the Sciences" (kostenlos) |
| **Zotero** | Tool | https://www.zotero.org/ — Literaturverwaltung (kostenlos) |

### Spezifische JuFo-Beispiele (zum Nachlesen)

- **"SOGLA – Selbstständiger Objekterkennungsgestützter Lager- und Sortierautomat"** (JuFo Technik, Regionalwettbewerb) — sehr ähnlich zu MIRA!
- **"KI-gesteuerter Feldroboter"** (JuFo Technik) — KI + Robotik Kombination
- **"Predictive Maintenance mit Shallow Learning"** (JuFo Mathematik/Informatik, Landessieger Brandenburg) — ML-Evaluation gut dokumentiert
- Suche auf: https://www.jugend-forscht.de/meldungen/archiv.html nach "Technik"-Gewinnern

---

## ⏱️ Lernplan: Wie lange brauchst du für jeden Block?

| Block | Inhalt | Geschätzte Zeit | Priorität |
|-------|--------|-----------------|-----------|
| **Block A** | Matplotlib OO-API verstehen | 1 Tag (3h) | 🔴 Hoch |
| **Block B** | evaluate.py von Grund auf neu schreiben | 1 Tag (3h) | 🔴 Hoch |
| **Block C** | Transfer Learning Tutorial durcharbeiten | 2 Tage (4h) | 🔴 Hoch |
| **Block D** | train_transfer.py implementieren & trainieren | 2 Tage (4h) | 🔴 Hoch |
| **Block E** | inference.py schreiben | ½ Tag (1,5h) | 🟡 Mittel |
| **Block F** | JuFo-Bericht Struktur verstehen, erste Notizen | 1 Tag (2h) | 🟡 Mittel |
| **Block G** | Daten erweitern (50 Bilder/Klasse/Woche) | Laufend | 🟢 Basis |

**Gesamtschätzung:** 7-8 Tage fokussiertes Arbeiten (a 3h) bis der Software-Part von Phase 1 fertig ist. Wenn du jetzt anfängst und 3h/Tag machst, bist du in **2,5-3 Wochen** durch.

---

## 🔗 Quick-Links (Bookmark diese!)

1. **TensorFlow Transfer Learning Tutorial:** https://www.tensorflow.org/tutorials/images/transfer_learning
2. **Matplotlib Cheat Sheet:** https://matplotlib.org/cheatsheets/
3. **Matplotlib Tutorials:** https://matplotlib.org/stable/tutorials/
4. **Jugend forscht Projektmappe:** https://www.jugend-forscht.de/teilnahme/die-projektmappe.html
5. **Fast.ai Kurs (Practical Deep Learning):** https://course.fast.ai/
6. **Zotero (Literaturverwaltung):** https://www.zotero.org/

---

*"Verstehen > Kopieren. Wenn du es nicht erklären kannst, hast du es nicht verstanden."* — Richard Feynman


---

## EXP-008: Specialized Tabletop YOLOv8-Nano (Data-Centric Optimization)
* **Date:** July 5, 2026
* **Commit Hash:** `[your_commit_hash]`
* **Architecture:** YOLOv8-Nano (PyTorch)
* **Dataset Size:** ~3,000 images (Custom Tabletop + Labeled TrashNet)
* **Training Platform:** Google Colab (NVIDIA Tesla T4 GPU)
* **Training Time:** 1.661 hours (50 epochs)

### Hyperparameters
* **Learning Rate (lr0):** 0.01 (Adam)
* **Image Size (imgsz):** 640 (Training) / 320 (Inference Target)
* **Batch Size:** 16
* **Loss Functions:** Complete IoU (box_loss), BCE (cls_loss), DFL (dfl_loss)

### Final Epoch Metrics (Epoch 50/50)
* **Box Loss:** 0.6241
* **Class Loss (cls_loss):** 0.7603
* **Distribution Focal Loss (dfl_loss):** 0.9023
* **Validation Accuracy (mAP50):** 39.6% (0.3960)
* **mAP50-95:** 32.9% (0.3290)

### Class-Specific Validation Performance (mAP50)
* **Glass:** 38.8% (0.3880)
* **Metal:** 51.0% (0.5100)
* **Paper:** 36.6% (0.3660)
* **Plastic:** 64.4% (0.6440)
* **Trash:** 7.1% (0.0711)

### Speed & Performance (GPU)
* **Preprocess:** 0.2 ms
* **Inference Latenz:** 2.1 ms
* **Postprocess:** 3.1 ms

### Observation & Scientific Value
EXP-008 represents a Data-Centric AI optimization. By purging the corrupted auto-labeled custom images and training strictly on human-annotated, high-quality bounding boxes, the model converged to the exact same accuracy profile as the 100-epoch noisy model (EXP-006) in half the training time. The sharp contrast in classification confidence confirms that removing spatial label noise is more effective than brute-force longer training cycles.