# JuFo-Bericht Template: MIRA AI

> **Format:** Markdown-Vorlage für die schriftliche Dokumentation (Projektmappe)
> **Ziel:** Jugend forscht Regionalwettbewerb NRW, Einreichung Januar 2027
> **Umfang:** Max. 15 Seiten (JuFo-Vorgabe), plus Anhänge

---

## Anmerkung zur Verwendung

Dies ist eine **Strukturvorlage** basiert auf:
- Offiziellen JuFo-Richtlinien (https://www.jugend-forscht.de/teilnahme/die-projektmappe.html)
- Analyse mehrerer Landeswettbewerb-Gewinnerberichte
- Der typischen Struktur wissenschaftlicher Arbeiten

**Jeder Abschnitt enthält:**
- `[PLATZHALTER]` — Muss durch deinen Text ersetzt werden
- `💡 Tipp:` — Hinweise von deinem Mentor
- `📏 Länge:` — Empfohlene Seitenzahl

---

# MIRA: Edge-KI-basierte Erkennung und automatisierte Sortierung von Recyclingmaterialien

**[PLATZHALTER: Dein Name]**  
**[PLATZHALTER: Deine Schule, Klasse]**  
**[PLATZHALTER: Betreuende Lehrkraft]**  
**[PLATZHALTER: Datum]**

---

## Abstract / Zusammenfassung (½ Seite)

📏 **Länge:** 150–200 Wörter (max. ½ Seite)

💡 **Tipp:** Der Abstract ist das Wichtigste. Die Jury liest ihn zuerst und entscheidet oft danach, ob sie den Rest lesen will. Schreibe ihn ZULETZT, wenn der Rest fertig ist.

**Struktur (4 Sätze):**
1. Kontext/Problem (1 Satz)
2. Was wurde gemacht? (1 Satz)
3. Wichtigste Ergebnisse (1–2 Sätze)
4. Fazit/Ausblick (1 Satz)

**[PLATZHALTER]:**

```text
Die manuelle Sortierung von Recyclingmaterialien ist zeitaufwändig und fehleranfällig. 
Diese Arbeit untersucht, wie verschiedene neuronale Netzwerkarchitekturen die automatische 
Klassifikation von Glas, Metall, Papier und Plastik unter variierenden Lichtbedingungen 
beeinflussen. Durch systematischen Vergleich eines Scratch-CNN, eines MobileNetV2 mit 
Transfer Learning und eines fine-tuned MobileNetV2 wurden die Klassifikationsgenauigkeit, 
Inferenzgeschwindigkeit und Robustheit gegenüber Beleuchtungsänderungen gemessen. 
Das fine-tuned MobileNetV2 erreichte unter Standardbedingungen eine Validierungsgenauigkeit 
von [XX]% und übertraf das Scratch-CNN um [XX] Prozentpunkte. Unter erschwerten 
Lichtbedingungen war der Vorteil noch ausgeprägter. Diese Ergebnisse zeigen, dass 
Transfer Learning für Edge-KI-Anwendungen im Recyclingbereich dem Training von Grund 
auf deutlich überlegen ist.
```

---

## 1. Einleitung und Motivation (1 Seite)

📏 **Länge:** 1 Seite

💡 **Tipp:** Beginne mit einem konkreten Problem, nicht mit "Künstliche Intelligenz ist ein wichtiges Thema...". Die Jury will sehen, dass du eine echte Motivation hast.

**Abschnitte:**

### 1.1 Problemstellung
- Was ist das Problem? (Menschliche Fehler bei der Recycling-Sortierung)
- Warum ist es relevant? (Deutschland erreicht Recycling-Ziele nicht, Verunreinigung reduziert Wert)
- Konkrete Zahlen: z.B. "Verunreinigung von Papiertonne um 25% reduziert Wert um 50%"

### 1.2 Zielsetzung
- Was willst du erreichen?
- Nicht: "Ich will ein KI-Modell bauen" (zu generisch)
- Sondern: "Ich will untersuchen, welche Architektur für Edge-KI-Sortierung am besten geeignet ist"

### 1.3 Aufbau der Arbeit
- Kurzer Überblick über die Kapitel (2–3 Sätze)

**[PLATZHALTER]:**

```text
## 1. Einleitung und Motivation

### 1.1 Problemstellung

In Deutschland werden jährlich über 47 Millionen Tonnen Hausmüll erzeugt, 
von denen ein erheblicher Anteil durch unsachgemäße Trennung verloren geht. 
Laut Umweltbundesamt verunreinigt durchschnittlich jedes fünfte Plastikfläschchen 
die Papiertonne, was die Recyclingeffizienz massiv senkt. Die Ursache liegt 
häufig in menschlichen Fehlern bei der manuellen Sortierung.

### 1.2 Zielsetzung

Diese Arbeit untersucht systematisch, wie verschiedene neuronale Netzwerkarchitekturen 
(CNN von Grund auf, MobileNetV2 mit Transfer Learning, fine-tuned MobileNetV2) 
die automatische Klassifikation von vier Recyclingfraktionen (Glas, Metall, Papier, 
Plastik) unter variierenden Lichtbedingungen beeinflussen. Ziel ist es, eine 
empirisch fundierte Empfehlung für die Wahl der Architektur in Edge-KI-Anwendungen 
zu geben.

### 1.3 Aufbau der Arbeit

Kapitel 2 beschreibt den Stand der Technik. Kapitel 3 erläutert die Methodik 
und das Experimentdesign. Kapitel 4 präsentiert die Ergebnisse, gefolgt von einer 
Diskussion in Kapitel 5. Kapitel 6 fasst zusammen und gibt einen Ausblick.
```

---

## 2. Stand der Technik (2 Seiten)

📏 **Länge:** 2 Seiten

💡 **Tipp:** Das ist der Teil, der viele JuFo-Teilnehmer vernachlässigen. Die Jury will sehen, dass du recherchiert hast. Nicht zu viel, aber präzise. Zitiere 5–8 Quellen.

**Abschnitte:**

### 2.1 Künstliche Intelligenz in der Abfallsortierung
- Was gibt es schon? (Amp Robotics, Tomra, Zenrobotics)
- Was sind die Unterschiede zu deinem Ansatz? (Die kommerziellen Systeme sind riesig, teuer, Cloud-basiert. Deins ist klein, Edge-basiert, kostengünstig.)

### 2.2 Convolutional Neural Networks (CNNs)
- Kurze Erklärung: Was ist ein CNN? (3–4 Sätze, mit Verweis auf Quelle)
- Warum sind CNNs gut für Bildklassifikation?

### 2.3 Transfer Learning
- Was ist Transfer Learning? (Vortrainierte Modelle auf neue Aufgaben übertragen)
- Warum ist es für kleine Datensätze besonders geeignet?
- Nenne konkrete Modelle: MobileNetV2, EfficientNet, VGG16
- Zitiere: TensorFlow-Dokumentation, Paper zu MobileNetV2

### 2.4 Edge-KI und Embedded Deployment
- Was ist Edge-KI? (KI auf dem Gerät, nicht in der Cloud)
- Warum ist das für Recycling-Sortierung relevant? (Datenschutz, Latenz, Offline-Fähigkeit)
- Nennen: ESP32, Raspberry Pi, TensorFlow Lite

**[PLATZHALTER]:**

```text
## 2. Stand der Technik

### 2.1 Künstliche Intelligenz in der Abfallsortierung

Die automatisierte Abfallsortierung ist ein aktives Forschungsfeld. Unternehmen 
wie Amp Robotics und Tomra Systems setzen industrielle KI-gestützte Sortieranlagen 
ein, die auf Near-Infrared-Spektroskopie und computergestützte Bildanalyse basieren. 
Diese Systeme erreichen Sortiergenauigkeiten von über 95%, sind jedoch in der 
Anschaffung kostenintensiv (mehrere hunderttausend Euro) und für den 
Haushalts- oder Schulgebrauch ungeeignet. Diese Arbeit untersucht daher, ob 
ein kostengünstiger, Edge-basierter Ansatz mit Standard-Webcam und Mikrocontroller 
eine praktikable Alternative darstellen kann.

### 2.2 Convolutional Neural Networks

Convolutional Neural Networks (CNNs) sind die derzeit dominierende Architektur 
für Bildklassifikation. Sie nutzen gefaltete Faltungskerne (Convolutional Filters), 
um hierarchische Merkmale zu extrahieren: frühe Schichten erkennen Kanten und 
Texturen, spätere Schichten komplexe Objekte (LeCun et al., 1998). Für die 
Materialklassifikation sind CNNs geeignet, da sich unterschiedliche Materialien 
in Reflexion, Textur und Form unterscheiden lassen.

### 2.3 Transfer Learning

Transfer Learning nutzt vortrainierte Modelle, die auf großen Datensätzen 
(wie ImageNet mit 1,4 Millionen Bildern) trainiert wurden, und passt sie an 
spezifische Aufgaben an. Für kleine Datensätze (weniger als 1.000 Bilder pro Klasse) 
hat Transfer Learning sich als deutlich überlegen erwiesen (Yosinski et al., 2014). 
MobileNetV2 (Sandler et al., 2018) wurde speziell für mobile und eingebettete 
Geräte mit begrenzter Rechenleistung entwickelt und ist daher für Edge-KI-Anwendungen 
prädestiniert.

### 2.4 Edge-KI und Embedded Deployment

Edge-KI bezeichnet die Ausführung von KI-Modellen direkt auf dem Endgerät, 
ohne Cloud-Anbindung. Dies bietet Vorteile in Latenz, Datenschutz und 
Offline-Fähigkeit (Deng et al., 2020). Für die Recycling-Sortierung bedeutet 
dies, dass das System auch ohne Internetverbindung funktioniert und keine 
sensiblen Bilddaten überträgt. TensorFlow Lite ermöglicht die Konvertierung 
von TensorFlow-Modellen in ein für Embedded-Geräte optimiertes Format.
```

---

## 3. Methodik und Experimentdesign (2 Seiten)

📏 **Länge:** 2 Seiten (DAS WICHTIGSTE KAPITEL für die Jury!)

💡 **Tipp:** JuFo-Jurys sind oft Wissenschaftler. Sie wollen sehen, dass du Experimente kontrolliert durchgeführt hast. Nenne ALLE Parameter, damit jemand dein Experiment reproduzieren könnte.

**Abschnitte:**

### 3.1 Forschungsfrage und Hypothese
- Deine Forschungsfrage (wortgleich aus JuFo_Hypothesis_and_Timeline.md)
- Deine Hypothese (mit konkreten Zahlen!)

### 3.2 Datenerhebung
- Wie wurdest du die Bilder aufgenommen? (Webcam, Auflösung, Hintergrund)
- Wie viele Bilder pro Klasse?
- Wie wurdest du die Klassen definiert? (Was zählt als "Glas"?)

### 3.3 Modellarchitekturen
- Beschreibe jedes Modell:
  - Scratch-CNN (3 Conv-Layer, Dropout, Flatten, Dense)
  - MobileNetV2 (frozen base, eigener Klassifikationskopf)
  - MobileNetV2 (fine-tuned, top 20 Layer freigegeben)
- Warum diese Architekturen? (Vergleichbarkeit, unterschiedliche Komplexität)

### 3.4 Trainingsparameter
- Alles, was konstant gehalten wurde:
  - Optimizer (Adam, lr=0.0001)
  - Loss-Funktion (SparseCategoricalCrossentropy)
  - Batch-Size (32)
  - Train/Val Split (80/20, seed=123)
  - Bildgröße (224×224 für MobileNetV2)
  - Data Augmentation (Flip, Rotation, Zoom)

### 3.5 Variablen
- **Unabhängige Variablen:** Modellarchitektur, Lichtbedingung
- **Abhängige Variablen:** Val Accuracy, Precision, Recall, F1, Inferenzzeit (ms), Modellgröße
- **Kontrollierte Variablen:** Kamera, Hintergrund, Auflösung, Split-Seed, Batch-Size

### 3.6 Evaluation
- Wie wurden die Metriken berechnet? (sklearn, Confusion Matrix)
- Wie wurde die Inferenzzeit gemessen? (time.time() vor/nach predict, CPU)

**[PLATZHALTER]:**

```text
## 3. Methodik und Experimentdesign

### 3.1 Forschungsfrage und Hypothese

**Forschungsfrage:**
Wie beeinflussen verschiedene neuronale Netzwerkarchitekturen (Scratch-CNN, 
MobileNetV2 frozen, MobileNetV2 fine-tuned) die Klassifikationsgenauigkeit und 
Inferenzgeschwindigkeit bei der automatischen Erkennung von Recyclingmaterialien 
unter variierenden Lichtbedingungen?

**Hypothese:**
Ein auf ImageNet vortrainiertes MobileNetV2 erreicht bei der Klassifikation von 
Recyclingmaterialien eine um mindestens 15 Prozentpunkte höhere Validierungsgenauigkeit 
als ein von Grund auf trainiertes CNN, bei gleichzeitig kürzerer Inferenzzeit pro Bild. 
Unter erschwerten Lichtbedingungen (geringe Beleuchtung, Schattenwurf) ist der 
Genauigkeitsvorteil des Transfer-Learning-Modells noch ausgeprägter.

### 3.2 Datenerhebung

Die Bilder wurden mit einer Logitech C920-Webcam (Full HD, 1920×1080) aufgenommen. 
Es wurden vier Klassen definiert: Glas (Flaschen, Gläser), Metall (Dosen, Alufolie), 
Papier (Karton, Zeitung), Plastik (PET-Flaschen, Verpackungen). Pro Klasse wurden 
mindestens 150 Bilder aufgenommen, wobei verschiedene Objekte, Winkel und 
Positionen variiert wurden. Die Bilder wurden in einem Ordner pro Klasse abgelegt 
und mit TensorFlows image_dataset_from_directory geladen.

### 3.3 Modellarchitekturen

**Modell 1: Scratch-CNN (Baseline)**
Ein einfaches CNN mit drei Convolutional-Blocks (16→32→64 Filter), jeweils 
gefolgt von MaxPooling2D. Ein Dropout-Layer (0.2) reduziert Overfitting. Der 
Klassifikationskopf besteht aus einem Flatten-Layer und einem Dense-Layer mit 
128 Neuronen.

**Modell 2: MobileNetV2 (Feature Extraction)**
MobileNetV2 mit auf ImageNet vortrainierten Gewichten, wobei alle Basisschichten 
gefroren (trainable=False) sind. Der Klassifikationskopf besteht aus einem 
GlobalAveragePooling2D-Layer, einem Dropout-Layer (0.2) und einem Dense-Layer 
mit 4 Neuronen (Softmax-Output).

**Modell 3: MobileNetV2 (Fine-Tuning)**
Identisch zu Modell 2, aber die obersten 20 Schichten der Basis werden freigegeben 
und mit einer um den Faktor 10 reduzierten Learning Rate (0.00001) nachtrainiert.

### 3.4 Trainingsparameter

Alle Modelle wurden mit folgenden konstanten Parametern trainiert:
- Optimizer: Adam (lr=0.0001 für Scratch und Frozen, lr=0.00001 für Fine-Tuning)
- Loss: SparseCategoricalCrossentropy (from_logits=True)
- Batch-Size: 32
- Validation Split: 20% (seed=123)
- Bildgröße: 224×224 Pixel (MobileNetV2) bzw. 180×180 (Scratch-CNN)
- Data Augmentation: Horizontal Flip (RandomFlip), Rotation (±10%), Zoom (±10%)

### 3.5 Variablen

**Unabhängige Variablen:**
- Modellarchitektur (Scratch-CNN, MobileNetV2 frozen, MobileNetV2 fine-tuned)
- Lichtbedingung (Standard: 500 Lux, Niedrig: 50 Lux, Kontrastreich: Schlagschatten)

**Abhängige Variablen:**
- Validierungsgenauigkeit, Precision/Recall/F1 pro Klasse, Inferenzzeit (ms/Bild), Modellgröße (MB)

**Kontrollierte Variablen:**
- Kamera-Modell, Hintergrund (weiße Tischplatte), Auflösung, Split-Seed, Batch-Size, Optimizer

### 3.6 Evaluation

Die Evaluation erfolgte auf dem Validierungsdatensatz (shuffle=False, identischer 
Seed). Für die Metriken wurden die Funktionen von scikit-learn verwendet 
(classification_report, confusion_matrix, precision_score, recall_score, f1_score). 
Die Inferenzzeit wurde gemessen als Mittelwert über 100 Vorhersagen auf einem 
Intel i5-Prozessor (Einzelkern, CPU-only).
```

---

## 4. Ergebnisse (4 Seiten)

📏 **Länge:** 4 Seiten (das Herzstück!)

💡 **Tipp:** Zeige, nicht erzähle. Grafiken > Tabellen > Text. Jede Grafik braucht eine Bildunterschrift, die erklärt, was man sieht. Die Jury will QUANTITATIVE Ergebnisse sehen.

**Abschnitte:**

### 4.1 Datensatz
- Tabelle: Anzahl Bilder pro Klasse
- Grafik: Beispielbilder pro Klasse (4×4 Grid)

### 4.2 Vergleich der Modellarchitekturen
- Tabelle: 3 Modelle × Val Acc × Precision/Recall/F1 × Inferenzzeit × Modellgröße
- Grafik: Balkendiagramm (Accuracy-Vergleich)

### 4.3 Confusion Matrices
- 3 Grafiken: Confusion Matrix pro Modell
- Beschreibung: Wo macht jedes Modell Fehler?

### 4.4 Einfluss der Lichtbedingungen
- Tabelle: MobileNetV2 fine-tuned × 3 Lichtbedingungen
- Grafik: Accuracy pro Lichtbedingung
- Grafik: Per-Class F1-Score unter verschiedenen Lichtbedingungen

### 4.5 Per-Class Analyse
- Tabelle: Precision, Recall, F1 für jede Klasse (bestes Modell)
- Welche Klasse ist am schwierigsten? Warum? (z.B. "Papier und Plastik werden verwechselt, weil beide matte Oberflächen haben")

**[PLATZHALTER]:**

```text
## 4. Ergebnisse

### 4.1 Datensatz

[Tabelle: Bilder pro Klasse]

| Klasse | Trainingsbilder | Validierungsbilder | Gesamt |
|--------|----------------|-------------------|--------|
| Glas   | 120            | 43                | 163    |
| Metall | 115            | 41                | 156    |
| Papier | 118            | 42                | 160    |
| Plastik| 92             | 33                | 125    |
| **Gesamt** | **445**    | **159**           | **604**|

[Abbildung: 4×4 Grid mit Beispielbildern pro Klasse]

### 4.2 Vergleich der Modellarchitekturen

[Tabelle: Gesamtergebnisse]

| Modell | Val Acc | Glass (F1) | Metall (F1) | Papier (F1) | Plastik (F1) | Inferenz (ms) | Größe (MB) |
|--------|---------|------------|-------------|-------------|--------------|---------------|------------|
| Scratch-CNN | 55.0% | 0.83 | 0.48 | 0.12 | 0.56 | 15 | 15.2 |
| MobileNetV2 (frozen) | 85.2% | ... | ... | ... | ... | 25 | 14.0 |
| MobileNetV2 (fine-tuned) | 91.8% | ... | ... | ... | ... | 25 | 14.0 |

[Abbildung: Balkendiagramm Accuracy-Vergleich]

### 4.3 Confusion Matrices

[Abbildung: 3 Confusion Matrices nebeneinander]

Die Confusion Matrices zeigen, dass das Scratch-CNN systematisch Papier- und 
Metall-Bilder als Plastik klassifiziert. Das MobileNetV2 fine-tuned reduziert 
diese Fehler deutlich, besonders bei der Glas-Klasse (Precision 0.92).

### 4.4 Einfluss der Lichtbedingungen

[Tabelle und Grafiken für Lichtvariationen]

### 4.5 Per-Class Analyse

Das MobileNetV2 fine-tuned erzielte die besten F1-Scores für Glas (0.91) und 
Plastik (0.88). Die schwierigste Klasse war Metall (F1 0.72), da Aludosen und 
Metallfolien stark unterschiedliche Reflexionseigenschaften aufweisen und von 
dem Modell als unterschiedliche Klassen wahrgenommen wurden.
```

---

## 5. Diskussion (2 Seiten)

📏 **Länge:** 2 Seiten

💡 **Tipp:** Die Diskussion ist der Unterschied zwischen einer guten und einer gewinnenden Arbeit. Hier zeigst du, dass du DENKST, nicht nur MACHST.

**Abschnitte:**

### 5.1 Interpretation der Ergebnisse
- Was bedeuten die Ergebnisse für deine Hypothese?
- Wurde die Hypothese bestätigt oder widerlegt?
- Warum ist MobileNetV2 besser? (Vortrainierte Merkmale, weniger Parameter zu lernen)

### 5.2 Einschränkungen
- Was war nicht perfekt? (Kleiner Datensatz, nur 4 Klassen, keine echten Recyclinganlagen-Tests)
- Warum sind das Einschränkungen? (Generalisierung, Praxisrelevanz)

### 5.3 Fehlerquellen
- Was könnte die Ergebnisse verfälscht haben?
- Datensatz-Imbalance (Papier: 160 Bilder, Plastik: 125 Bilder)
- Ähnliche Objekte in verschiedenen Klassen (Kunststofffolie vs. Alufolie)
- Kamera-Qualität (Webcam vs. industrielle Kamera)

### 5.4 Vergleich mit dem Stand der Technik
- Wie stehst du im Vergleich zu kommerziellen Systemen?
- Was ist dein Vorteil? (Kostengünstig, Edge-basiert, erweiterbar)
- Was ist dein Nachteil? (Genauigkeit noch unter 95%)

**[PLATZHALTER]:**

```text
## 5. Diskussion

### 5.1 Interpretation der Ergebnisse

Die Ergebnisse bestätigen die Hypothese: Das MobileNetV2 fine-tuned übertraf 
das Scratch-CNN um 36,8 Prozentpunkte (91,8% vs. 55,0%). Dieser deutliche 
Unterschied zeigt, dass für kleine Datensätze (weniger als 1.000 Bilder pro Klasse) 
Transfer Learning nicht nur empfohlen, sondern essenziell ist. Die vortrainierten 
Gewichte von ImageNet ermöglichen dem Modell, generische visuelle Merkmale (Kanten, 
Texturen, Formen) zu nutzen, ohne sie aus den 604 vorhandenen Bildern lernen zu müssen.

Unter erschwerten Lichtbedingungen war der Vorteil des Transfer-Learning-Modells 
besonders deutlich. Während das Scratch-CNN bei 50 Lux auf 35% Accuracy fiel, 
hielt das MobileNetV2 fine-tuned 78% — ein Hinweis darauf, dass vortrainierte 
Merkmale robuster gegenüber Rauschen und Beleuchtungsänderungen sind.

### 5.2 Einschränkungen

Die Arbeit weist mehrere Einschränkungen auf: Der Datensatz umfasst nur 604 Bilder, 
was im Vergleich zu industriellen Anwendungen (oft 10.000+ Bilder pro Klasse) klein ist. 
Die Anzahl der Klassen ist auf vier begrenzt; reale Recyclinganlagen müssen oft 
20+ Fraktionen unterscheiden. Zudem wurden die Experimente unter kontrollierten 
Laborbedingungen durchgeführt, nicht unter realen Recyclinganlagen-Bedingungen 
(Förderband, Staub, Bewegung).

### 5.3 Fehlerquellen

Die Klassen-Imbalance (Glas: 163, Plastik: 125 Bilder) könnte die Ergebnisse zugunsten 
von Glas verzerrt haben. Die Verwechslung von Metall und Plastik (besonders bei 
dem Scratch-CNN) ist wahrscheinlich auf ähnliche visuelle Eigenschaften zurückzuführen: 
beide Materialien können glänzende, reflektierende Oberflächen haben. Die Webcam 
(720p) bietet eine geringere Bildqualität als industrielle Kameras, was die 
Unterscheidung subtiler Texturunterschiede erschwert.

### 5.4 Vergleich mit dem Stand der Technik

Kommerzielle Systeme wie Tomra Autosort erreichen Sortiergenauigkeiten von über 
95% und nutzen neben RGB-Kameras auch Near-Infrared-Sensoren. Das MIRA-System 
erreicht mit reinem RGB-Bild und Edge-KI 91,8% — einen akzeptablen Wert für 
einen Prototypen, aber noch nicht für industriellen Einsatz. Der entscheidende 
Vorteil von MIRA liegt in der Kostenstruktur (Gesamtkosten < 200€) und der 
Edge-Fähigkeit (keine Cloud, keine Internetverbindung nötig).
```

---

## 6. Fazit und Ausblick (1 Seite)

📏 **Länge:** 1 Seite

💡 **Tipp:** Fasse nicht einfach nur zusammen. Gib einen Ausblick, der zeigt, dass du WEITERDENKST. Das ist der Unterschied zwischen einem Schülerprojekt und einer wissenschaftlichen Arbeit.

**Abschnitte:**

### 6.1 Zusammenfassung
- 3–4 Sätze: Was hast du gemacht? Was ist das wichtigste Ergebnis?

### 6.2 Ausblick
- Was kommt als Nächstes?
- INT8-Quantisierung für ESP32-Deployment
- Erweiterung auf mehr Klassen (Batterien, Elektronik, Bioabfall)
- Einsatz eines Förderbands für kontinuierliche Sortierung
- Kombination mit Hardware-Sensoren (NIR, Gewichtssensor)
- Integration eines Servo-Arms für physische Sortierung

**[PLATZHALTER]:**

```text
## 6. Fazit und Ausblick

### 6.1 Zusammenfassung

Diese Arbeit untersuchte systematisch den Einfluss verschiedener neuronaler 
Netzwerkarchitekturen auf die Klassifikation von Recyclingmaterialien. Das 
MobileNetV2 mit Fine-Tuning erreichte eine Validierungsgenauigkeit von 91,8% 
und übertraf das von Grund auf trainierte CNN um 36,8 Prozentpunkte. Die 
Ergebnisse zeigen, dass Transfer Learning für kleine Datensätze in Edge-KI-Anwendungen 
dem Training von Grund auf deutlich überlegen ist.

### 6.2 Ausblick

Die nächsten Schritte umfassen die INT8-Quantisierung des Modells für den 
Einsatz auf einem ESP32-Mikrocontroller, die Erweiterung des Datensatzes auf 
zusätzliche Klassen (Batterien, Elektronikschrott) und die Integration eines 
3-DOF-Servo-Arms für die physische Sortierung. Langfristig könnte das System 
mit einem Gewichtssensor und einem NIR-Sensor erweitert werden, um Materialien 
zuverlässiger zu unterscheiden, die rein visuell ähnlich erscheinen (z.B. 
Plastikfolie vs. Alufolie). Die Echtzeitfähigkeit auf Embedded-Hardware wird 
durch TensorFlow Lite und Model-Quantisierung untersucht.
```

---

## Literaturverzeichnis (1 Seite)

📏 **Länge:** 1 Seite

💡 **Tipp:** Nutze Zotero (https://www.zotero.org/) — es ist kostenlos und generiert automatisch korrekte Zitate. JuFo erwartet keine spezifische Zitierweise, aber Konsistenz ist wichtig.

**[PLATZHALTER]:**

```text
## Literaturverzeichnis

Deng, L., Li, G., Han, S., Shi, L., & Xie, Y. (2020). Model compression and 
    hardware acceleration for neural networks: A comprehensive survey. 
    Proceedings of the IEEE, 108(4), 485–532.

LeCun, Y., Bengio, Y., & Hinton, G. (2015). Deep learning. Nature, 521(7553), 
    436–444.

Sandler, M., Howard, A., Zhu, M., Zhmoginov, A., & Chen, L. C. (2018). 
    MobileNetV2: Inverted residuals and linear bottlenecks. 
    Proceedings of the IEEE Conference on Computer Vision and Pattern 
    Recognition (CVPR), 4510–4520.

TensorFlow. (2024). Transfer learning and fine-tuning. 
    https://www.tensorflow.org/tutorials/images/transfer_learning

Umweltbundesamt. (2023). Verpackungsverwertung in Deutschland. 
    https://www.umweltbundesamt.de

Yosinski, J., Clune, J., Bengio, Y., & Lipson, H. (2014). How transferable 
    are features in deep neural networks? Advances in Neural Information 
    Processing Systems, 27, 3320–3328.
```

---

## Anhang (nicht in die 15 Seiten zählt)

💡 **Tipp:** Der Anhang zählt NICHT zu den 15 Seiten. Hier kannst du Code, Zusatzgrafiken, Datenblätter unterbringen.

**Empfohlene Inhalte:**
- Vollständiger Python-Code (train.py, evaluate.py, inference.py) — kommentiert
- Zusätzliche Grafiken (alle Confusion Matrices in voller Größe)
- Rohdaten-Tabellen (Excel/CSV)
- Fotos des Versuchsaufbaus
- Screenshots der Trainingsplots

---

## Checkliste vor der Einreichung

- [ ] Abstract ist schlüssig und enthält konkrete Zahlen
- [ ] Forschungsfrage ist präzise formuliert und fachbar
- [ ] Hypothese enthält eine konkrete, testbare Vorhersage
- [ ] Methodik beschreibt ALLE Parameter (jemand könnte das Experiment reproduzieren)
- [ ] Ergebnisse enthalten mindestens 3 Grafiken und 2 Tabellen
- [ ] Diskussion nennt Einschränkungen und Fehlerquellen
- [ ] Fazit gibt einen konkreten Ausblick, nicht nur "mehr Forschung nötig"
- [ ] Literaturverzeichnis ist vollständig und konsistent formatiert
- [ ] Rechtschreibung und Grammatik geprüft (z.B. mit LanguageTool)
- [ ] Betreuende Lehrkraft hat den Bericht gelesen und Feedback gegeben
- [ ] Code im Anhang ist kommentiert und läuft

---

*"Eine gute wissenschaftliche Arbeit ist nicht die, die alles beweist, sondern die, die ehrlich sagt, was sie kann und was sie nicht kann."*

