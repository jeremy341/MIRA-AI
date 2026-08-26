Here is the complete, structured scientific ledger of every major difficulty, bug, and architectural hurdle you faced and resolved across the entire development of MIRA. 

Documenting these obstacles is explicitly required by the *Jugend forscht* guidelines under **"Vorgehensweise, Materialien und Methoden"** and **"Ergebnisdiskussion"**, as it demonstrates true engineering persistence and problem-solving maturity.

Save this text directly into your project repository as **`docs/JuFo_Huerden_und_Fehleranalyse.md`**.

# MIRA - Wissenschaftliche Fehleranalyse und technologische Hürden
**Projekt:** Machine Intelligence for Recycling Automation (MIRA)
**Wettbewerb:** Jugend forscht 2027 (Fachgebiet Technik / Informatik)
**Zweck des Dokuments:** Systematische Dokumentation aufgetretener Schwierigkeiten, fehlerhafter Ansätze und deren ingenieurwissenschaftlicher Lösung zur Integration in die schriftliche Ausarbeitung.

---

## 1. Hürden in Stage A (Bildklassifizierung)

### 1.1 Overfitting unter extremer Datenknappheit (EXP-001)
* **Problembeschreibung:** Das initiale, von Grund auf trainierte dreischichtige Convolutional Neural Network (Scratch-CNN, EXP-001) stagnierte auf dem initialen Datensatz (126 Bilder) bei einer Validierungsgenauigkeit von lediglich 61,00 %. Insbesondere die Klasse *Papier* versagte komplett (F1-Score: 0,12; Recall: 0,07).
* **Ursachenanalyse:** Ein Scratch-CNN besitzt nicht genug statistische Stützstellen in kleinen Datensätzen, um invariante Merkmale (Kanten, Texturen) zu erlernen. Das Modell passte sich stattdessen an stochastische Rauschmuster des Hintergrunds an (Memorization / Overfitting).
* **Ingenieurwissenschaftliche Lösung:** Pivot zu Transfer Learning mittels MobileNetV2 (EXP-002/EXP-003). Durch die Nutzung vortrainierter ImageNet-Gewichte als Feature-Extractor stieg die Gesamtgenauigkeit auf 87,42 %, und der F1-Score für Papier erholte sich auf 0,77. Parallel wurde der Datensatz auf 796 Originalbilder skaliert.

### 1.2 Geometrische Verzerrung durch Aspect-Ratio-Stretching
* **Problembeschreibung:** In den ersten Trainingsläufen wurden hochformatige oder unregelmäßige Kamerabilder durch die Standard-Laderoutinen von Keras direkt auf die Zielauflösung ($180 \times 180$ bzw. $224 \times 224$ Pixel) gequetscht oder gestreckt.
* **Ursachenanalyse:** Durch das unproportionale Skalieren veränderten sich die geometrischen Seitenverhältnisse der Objekte gravierend (z. B. wirkte eine schlanke PET-Flasche im Tensor wie ein breiter Plastikbecher), was die inter-klassische Trennschärfe verschlechterte.
* **Ingenieurwissenschaftliche Lösung:** Implementierung des Parameters `crop_to_aspect_ratio=True` in der Datensatz-Pipeline (`image_dataset_from_directory`), wodurch Bilder vor der Skalierung zentriert quadratisch zugeschnitten werden.

### 1.3 Der lautlose RGB/BGR-Farbkanalfehler (Silent Bug)
* **Problembeschreibung:** Während die Offline-Evaluation des feingetunten Modells eine Validierungsgenauigkeit von 87,42 % aufwies, brach die Erkennungsleistung im Live-Kameratest (`live_classifier.py`) auf unter 40 % ein. Das Modell warf weder Syntaxfehler noch Exceptions, klassifizierte aber weiße Plastikbecher systematisch als Glas.
* **Ursachenanalyse:** Keras- und TensorFlow-Modelle erwarten Bildtensoren standardmäßig im **RGB-Farbkanalformat** (Rot, Grün, Blau). Die zum Auslesen der Live-Webcam genutzte Bibliothek OpenCV (`cv2.VideoCapture`) erfasst Bilddaten jedoch nativ im **BGR-Format** (Blau, Grün, Rot). Die Vertauschung der Farbkanäle führte zu einer spektralen Invertierung der Eingabedaten.
* **Ingenieurwissenschaftliche Lösung:** Implementierung einer expliziten Farbraumkonvertierung vor der Inferenz und Datentyp-Transformation:
  ```python
  frame_rgb = cv2.cvtColor(cropped_frame, cv2.COLOR_BGR2RGB)
  ```

---

## 2. Hürden in Stage B (Objekterkennung & Datensatz-Engineering)

### 2.1 Das Versagen des Auto-Labelers durch Glanzlichter (GIGO-Effekt)
* **Problembeschreibung:** Beim Übergang zur Objekterkennung (YOLOv8-Nano) wurden Bounding Boxes benötigt. Das initial entwickelte Auto-Labeling-Skript (`build_detector_dataset.py`), welches auf Canny-Edge-Detection und Otsu-Thresholding basierte, erzeugte fehlerhafte Annotationsdateien: Die Bounding Boxes umschlossen fast auf jedem Bild den gesamten Schreibtisch statt des Müllobjekts.
* **Ursachenanalyse:** Die direkte Deckenbeleuchtung erzeugte starke weiße Glanzlichter (Specular Highlights) auf der Tischoberfläche sowie dunkle Schatten und harte Tischkanten. Der Canny-Algorithmus identifizierte die kontrastreiche Tischkante und die Reflexionen als größte zusammenhängende Kontur im Bild. Dies demonstrierte das klassische Prinzip „Garbage In, Garbage Out“ (GIGO) - das nachfolgende YOLO-Modell lernte fehlerfrei, dass der gesamte Tisch als Müll zu klassifizieren ist.
* **Ingenieurwissenschaftliche Lösung:** Verwerfen des fehlerhaften synthetischen Label-Ansatzes für unkontrollierte Umgebungen. Pivot zu professionell von Menschen annotierten Open-Source-Datensätzen (Stanford TrashNet auf reinweißem Grund kombiniert mit verifizierten Roboflow/TACO-Daten).

### 2.2 Domain Shift vs. Domain Specialization (EXP-006 vs. EXP-008)
* **Problembeschreibung:** Das Training von YOLOv8-Nano auf einem hochgradig heterogenen "Wild Data"-Datensatz (64 remappte Klassen von Müll in Wäldern, Stränden und Sträuchern, EXP-006) ergab nach 3,3 Stunden GPU-Training eine moderate mAP50 von 39,4 %.
* **Ursachenanalyse:** Die Kapazität eines extrem leichten Nano-Modells (~3 Millionen Parameter) ist begrenzt. Das Training auf "Wild Data" zwang das Modell dazu, seine Parameterkapazität für das Lernen komplexer Naturhintergründe (Gras, Sand) zu verbrauchen, anstatt sich auf die geometrischen Merkmale von Wertstoffen auf einem glatten Sortiertisch zu fokussieren.
* **Ingenieurwissenschaftliche Lösung:** Data-Centric AI Optimierung. Bereinigung des Datensatzes um alle Out-of-Distribution-Naturaufnahmen und Reduktion auf reine Tabletop- und TrashNet-Bilder (EXP-008). Das Modell erreichte in der Hälfte der Trainingszeit (1,6 Stunden / 50 Epochen) exakt dieselbe globale mAP50 (39,6 %) bei drastisch gesteigerter Erkennungssicherheit auf dem realen Schreibtisch.

---

## 3. Hürden in Modellkompression und Deployment (LiteRT / TFLite)

### 3.1 Plattformbeschränkungen beim LiteRT-Export unter Windows
* **Problembeschreibung:** Der Versuch, das trainierte PyTorch-Modell lokal unter Windows mittels `model.export(format="tflite", quantize=True)` auf INT8 zu quantisieren, schlug fehl mit dem Fehler: `AssertionError: LiteRT export only supported on Linux x86 and macOS`.
* **Ursachenanalyse:** Ultralytics stellte die Export-Schnittstelle auf Googles neuen LiteRT-Standard um. Die darunterliegenden Compiler-Werkzeuge für die Post-Training-Quantisierung weisen aktuell fehlende Binärkompatibilität auf Windows-Hostsystemen auf.
* **Ingenieurwissenschaftliche Lösung:** Verlagerung des gesamten Kalibrierungs- und Export-Workflows in eine cloudbasierte Linux-Umgebung (Google Colab). Das quantisierte Modell (`mira_exp006_int8.tflite`) wurde anschließend für die lokale CPU-Inferenz heruntergeladen.

### 3.2 Statische Tensor-Dimensionskonflikte (`imgsz=320` vs. `640`)
* **Problembeschreibung:** Das Einbinden des quantisierten TFLite-Modells in das Flask+SocketIO-Dashboard erzeugte den fatalen Laufzeitfehler: `ValueError: Cannot set tensor: Dimension mismatch. Got 320 but expected 640`.
* **Ursachenanalyse:** Im Gegensatz zu dynamischen PyTorch-Modellen (`.pt`), die Eingabeauflösungen zur Laufzeit flexibel skalieren, werden quantisierte TFLite-Modelle mit einer **statisch fixierten Eingabematrix** kompiliert. Ein bei $640 \times 640$ Pixeln exportiertes TFLite-Modell akzeptiert physisch keine $320 \times 320$ Eingabetensoren.
* **Ingenieurwissenschaftliche Lösung:** Re-Kompilierung und gezielter INT8-Export des Modells in der Cloud unter expliziter Angabe des Ziel-Parameters `imgsz=320`. Dies reduzierte die rechnerische Faltungslast auf der CPU quadratisch um exakt 75 % und senkte die Inferenzzeit auf 46,0 ms (~21,8 FPS).

---

## 4. System- und Echtzeit-Hürden (Inferenz & UI)

### 4.1 USB-Bandbreiten-Bottleneck und Kamera-Latenz
* **Problembeschreibung:** Trotz schnellem Modell lag die gemessene Gesamt-Latenz im Live-Stream anfänglich bei über 150 ms (ca. 6 FPS).
* **Ursachenanalyse:** Die Windows-Kameraeinstellungen waren standardmäßig auf 2560x1440 (1440p / 2,5K) eingestellt. Das Dekodieren von 3,68 Millionen Pixeln pro Frame im USB-Controller und die anschließende CPU-skalierung auf 320 Pixel erzeugten einen massiven I/O-Stau.
* **Ingenieurwissenschaftliche Lösung:** Erzwungene Reduktion der Hardware-Aufnahmeauflösung auf der Kamera-Ebene (`cap.set`) auf $640 \times 360$ Pixel (16:9). Die Reduktion der Rohdatenmenge um den Faktor 16 entlastete den USB-Bus vollständig.

### 4.2 Halluzinationen und Hintergrund-Überdetektion
* **Problembeschreibung:** Bei niedrigen Konfidenz-Schwellenwerten (`conf=0.25`) zeichnete das YOLO-Modell im Live-Betrieb gelegentlich eine Bounding Box um die gesamte weiße Tischplatte und klassifizierte diese als Plastik oder Papier.
* **Ursachenanalyse:** Große, strukturlose weiße Flächen weisen spektrale Ähnlichkeiten mit nah aufgenommenem Papier auf.
* **Ingenieurwissenschaftliche Lösung:** Implementierung eines mathematischen **Area Ratio Filters** im Rendering-Loop des Dashboards. Bounding Boxes, deren Grundfläche mehr als 60 % der gesamten Bildauflösung einnimmt (`(box_area / total_area) > 0.60`), werden vor dem Zeichnen programmatisch verworfen.

### 4.3 Signalflackern (Jitter) und mechatronische Instabilität
* **Problembeschreibung:** Kamerarauschen und Autofokus-Schwankungen führten dazu, dass die berechneten Klassen-Wahrscheinlichkeiten im Live-Stream von Frame zu Frame flimmerten (z. B. 85 % Metall $\rightarrow$ 40 % Metall $\rightarrow$ 80 % Metall). Für einen Roboterarm würde dies zu einem destruktiven Zittern der Servomotoren führen.
* **Ingenieurwissenschaftliche Lösung:** 
  1. Hardwareseitiges Deaktivieren der Kamera-Automatik (`AUTOFOCUS=0`, `AUTO_EXPOSURE=0`).
  2. Softwareseitige Implementierung eines **Exponential Moving Average (EMA) Filters** auf dem Wahrscheinlichkeitsvektor ($\alpha = 0,15$):
     \begin{equation}
     p_{\text{smooth}}(t) = 0,15 \cdot p_{\text{raw}}(t) + 0,85 \cdot p_{\text{smooth}}(t-1)
     \end{equation}
  3. Integration des **ByteTrack-Algorithmus** (`persist=True`), der Objekten über Frames hinweg persistente IDs zuweist.

### 4.4 Canonical View Bias (Liegende Metalldosen)
* **Problembeschreibung:** In abschließenden Stresstests wurde festgestellt, dass Getränkedosen zuverlässig erkannt werden, wenn sie seitlich liegen oder aufrecht stehen. Zeigt die Dosenöffnung jedoch frontal direkt in die Kamera (vertikale Achse), bricht die Detektion ein.
* **Ursachenanalyse:** Dies ist ein klassischer „Canonical View Bias“. In den Trainingsdatensätzen ist die zylindrische Seitenansicht von Dosen stark überrepräsentiert. Die frontale Draufsicht auf die Öffnung stellt sich als dunkler Kreis dar, der eher der Klasse *Trash* oder einer Anomalie ähnelt.
* **Ausblick/Lösung:** Identifiziert als Edge-Case für Targeted Fine-Tuning (Data Mix-In) vor dem physischen Aufbau des Sortierarms.

---

### Wie du diesen Text in deinem LaTeX-Bericht einsetzt:
Du musst diesen Text nicht zwingend 1:1 am Stück einfügen. Du kannst ihn aufteilen:
*   Die Punkte **1.1, 1.2, 2.1 und 2.2** passen perfekt in dein Kapitel **4. Methodik & Experimentdesign**.
*   Die Punkte **1.3, 3.1, 3.2, 4.1 und 4.2** passen perfekt in dein Kapitel **5. Ergebnisse & Diskussion (Fehleranalyse)**.
*   Die Punkte **4.3 und 4.4** leiten perfekt in dein Kapitel **6. Systemarchitektur & Ausblick (Roboterarm)** über.

Damit hast du jede einzelne Hürde wissenschaftlich und professionell dokumentiert.
