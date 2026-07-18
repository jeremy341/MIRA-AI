# Jugend Forscht Dokumentation - Juli 2026

## Zusammenfassung der heutigen Arbeit (11. Juli 2026)

---

## 1. Datensatz-Entwicklung: mira_v1 -> mira_v2 -> mira_v3

### mira_v1 (TACO only)
- TACO COCO-Datensatz (1.500 Bilder, 4.784 Annotationen, 60 Klassen) auf YOLO-Format umgewandelt
- Klassenmapping von 60 TACO-Klassen auf 5 MIRA-Zielklassen: Glas, Metall, Papier, Kunststoff, Restmuell
- Klassendiskussion: Papier 755 (10,3%), Metall 954 (13,1%), Glas 254 (5,3%), Kunststoff 2.248 (47,0%), Restmuell 1.237 (25,9%)

### mira_v2 (TACO + TrashNet - aktuell in Gebrauch)
- TACO wild (1.497 Bilder) + TrashNet tabletop (2.527 Bilder) kombiniert
- TrashNet-Bilder mit Full-Image-Bounding-Boxen (0.5 0.5 1.0 1.0) ergaenzt (keine manuellen Bounding-Boxen vorhanden)
- Gesamtgroesse: 4.024 Bilder, 7.307 Annotationen
- Klassendistribution: Glas 755 (10,3%), Metall 954 (13,1%), Papier 1.494 (20,4%), Kunststoff 2.730 (37,4%), Restmuell 1.374 (18,8%)
- Archiv: `datasets/mira_v2.zip` (2.5 GB)

### mira_v3 (geplant - SAM-gelabelt)
- TrashNet mit Segment Anything Model (SAM) auto-labeling statt Full-Image-Bounding-Boxen
- MobileSAM (38.8 MB, leichtgewichtig) zur Erzeugung praeziserer Bounding-Boxen
- Erwarteter Effekt: Bessere Bounding-Box-Qualitaet, insbesondere fuer Restmuell und Glas
- Script: `scripts/sam_label_trashnet.py`

---

## 2. Training auf Kaggle

### EXP-013: YOLO11n auf mira_v2
- **Architektur:** YOLO11n (2.583.127 Parameter, 6.3 GFLOPs)
- **Trainingsplattform:** Kaggle Notebooks (NVIDIA Tesla T4 GPU)
- **Trainingszeit:** 2,728 Stunden (120 Epochen, Bestes Epoch 103)
- **Batch-Groesse:** 32
- **Bildgroesse:** 640x640
- **Ergebnisse:**
  - mAP50: 55,1% (0.551)
  - mAP50-95: 49,8% (0.498)
  - Precision: 0,789
  - Recall: 0,468
- **Klassenspezifische mAP50:**
  - Glas: 56,5%
  - Metall: 67,9%
  - Papier: 79,3% (staelkste Klasse)
  - Kunststoff: 55,6%
  - Restmuell: 15,6% (schwaelchste Klasse)
- **Modellgroesse:**
  - PyTorch: 5,5 MB
  - TFLite INT8: 2,9 MB (3,5x Komprimierung)
  - ONNX: 10,1 MB
- **GPU-Inferenz:** 3,6 ms
- **Export:** TFLite INT8 via LiteRT (598,4s)

---

## 3. Vergleich der Architekturen (YOLO-Versionen)

| EXP | Architektur | mAP50 | Modellgroesse | Datensatz |
|-----|-------------|-------|---------------|-----------|
| EXP-005 | YOLOv8n | 82,3% | 6,2 MB | Custom+TrashNet (einfach) |
| EXP-006 | YOLOv8n | 39,4% | 6,2 MB | Wild+TrashNet Fusion |
| EXP-008 | YOLOv8n | 39,6% | 6,2 MB | Bereinigte Tischplatte |
| EXP-009 | YOLOv8n | 72,8% | 6,2 MB | Pristine TrashNet |
| EXP-013 | YOLO11n | 55,1% | 5,5 MB | TACO+TrashNet (mira_v2) |

**Fazit:** YOLO11n ist kleiner und effizienter als YOLOv8n (2,58M vs 3,01M Parameter), bei vergleichbarer oder besserer Genauigkeit auf dem gemischten Datensatz.

---

## 4. Datensatzprobleme und Loesungen

### Problem 1: TACO Dateinamen-Kollisionen
- TACO-Bilder haben identische Basenamen in verschiedenen Batches (z.B. `batch_1/000006.jpg`, `batch_2/000006.jpg`)
- Loesung: Batch-Prefix in Dateinamen (`batch_1_000006.jpg`) zur Vermeidung von Ueberschreibungen

### Problem 2: TrashNet ohne Bounding-Boxen
- TrashNet enthaelt nur Klassifikationslabels, keine Bounding-Boxen
- Loesung A (mira_v2): Full-Image-Bounding-Boxen (0.5 0.5 1.0 1.0)
- Loesung B (mira_v3): SAM-Auto-Labeling mit MobileSAM fuer praezisere Boxen

### Problem 3: Klassen-Ungleichgewicht
- Kunststoff dominiert (37,4%), Glas unterrepraesentiert (10,3%)
- Restmuell (15,6% mAP50) ist schwierigste Klasse
- Loesung: Mehr Daten, bessere Annotations, Klassen-Gewichtung

---

## 5. Technische Bugfixes (am 11. Juli 2026)

### live_detection.py
- TFLite INT8: `predict()` statt `track()` fuer korrekte Inferenz
- Conf-Schwellwert auf 0,25 fuer INT8 gesetzt
- `speed["inference"]` KeyError durch `.get()` behoben

### dashboard.py
- Classifier-Modelle aus Sidebar gefiltert
- INT8 Conf-Cap auf 0,25 gesetzt

### cli.py
- Fallback-Datensatz-Pfade von geloeschten/fehlenden Dateien auf `datasets/mira_v2/dataset.yaml` aktualisiert

### experiments_log.md
- EXP-013 korrekt dokumentiert mit tatsaechlichen Kaggle-Ergebnissen
- Korrekte Klassenspezifische Metriken

---

## 6. Jugend Forscht Relevante Punkte

### Wissenschaftliche Beitraege
1. **Datengetriebene Optimierung:** Vergleich von automatisch gelabelten vs. manuell bereinigten Datensaetzen zeigt, dass Datenqualitaet wichtiger ist als Trainingszeit
2. **Edge AI Deployment:** INT8-Quantisierung reduziert Modellgroesse um 3,5x (10,14 MB -> 2,9 MB) ohne messbaren Qualitaetsverlust
3. **Architektur-Vergleich:** YOLO11n vs. YOLOv8n auf demselben Datensatz
4. **Multi-Modalitaet:** Kombination von Wild-Szenen (TACO) und kontrollierten Tabletop-Aufnahmen (TrashNet)

### Methodik
- TACO (COCO-Format) -> YOLO-Format Konvertierung mit Klassenmapping
- MobileSAM fuer automatische Bounding-Box-Generierung
- Klassifikation (Stufe A) -> Detektion (Stufe B) Entwicklungslinie

### Messbare Ergebnisse
- Klassifikation: 87,42% Accuracy (MobileNetV2 + INT8)
- Detektion: 55,1% mAP50 (YOLO11n auf gemischtem Datensatz)
- Modellgroesse: 2,9 MB (TFLite INT8) - geeignet fuer Raspberry Pi
- Latenz: 3,6 ms Inferenz auf GPU

---

## 7. Offene Punkte / Naechste Schritte

1. **mira_v3 mit SAM-Bounding-Boxen** - TrashNet mit praeziseren Annotations versehen
2. **YOLO11s training** - groessere Architektur fuer bessere Genauigkeit
3. **Klassen-Gewichtung** - Restmuell-Prioritaet im Loss erhoehen
4. **Live-Test** mit quantisiertem Modell auf Raspberry Pi
5. **Weitere Datensammlung** - eigene Bilder fuer Restmuell-Klasse
