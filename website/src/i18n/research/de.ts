import type { ResearchDictionary } from "./en";

/**
 * Deutsche Fassung der Forschungsseite. Muss dieselben Schlüssel, Platzhalter und Markierungen wie en.ts haben.
 * Zahlen im deutschen Format (Dezimalkomma, Leerzeichen vor dem Prozentzeichen, Punkt als Tausendertrenner).
 * Keine Gedankenstriche.
 */
export const de: ResearchDictionary = {
  meta: {
    title: "Forschung",
    description:
      "Ein Schülerbericht zum MIRA-Müllerkennungsmodell: 19 Experimente, die Datensätze, Ergebnisse pro Klasse, echte Fotos und Fehler, Export für kleine Geräte und ehrliche Grenzen. Nur Validierungsergebnisse.",
  },
  head: {
    eyebrow: "Forschungsbericht",
    title: "Neunzehn Experimente, um Müll zu unterscheiden",
    subtitle: "Was ich versucht habe, was funktioniert hat und was ich noch nicht sagen kann.",
    byline: "MIRA, ein Ein-Personen-Projekt für Jugend forscht 2027. Experimente von Juni bis Juli 2026.",
    abstractLabel: "Zusammenfassung",
    abstract:
      "Ich habe Modelle trainiert, die Glas, Metall, Papier, Kunststoff und Restmüll in Kamerabildern finden. In 19 Experimenten, von einem CNN mit drei Schichten bis zu YOLO11n, ging es vor allem um die Daten. Drei Quellen zusammenzuführen ergab {exp014} mAP50 (EXP-014), alle vier {exp017} (EXP-017). Ein kleinerer, bereinigter und nach Klassen ausbalancierter Datensatz kam auf {exp018} (EXP-018) und bei der Wiederholung auf {exp019} (EXP-019). Kunststoff ist die schwache Klasse, mit einer Trefferquote (Recall) von {plasticRecall}. Das sind alles Validierungswerte auf Fotos, kein Test mit einer echten Kamera, und beide Läufe nutzten verschiedene Validierungsdatensätze. Das Modell ist noch nicht auf einem Raspberry Pi gelaufen, und den Sortierroboter gibt es noch nicht.",
    contentsLabel: "Abschnitte",
    contents: {
      question: "Frage und Aufbau",
      tried: "Was ich ausprobiert habe",
      results: "Ergebnisse",
      runs: "Alle Experimente",
      photos: "Echte Fotos und Fehler",
      edge: "Export für kleine Geräte",
      limits: "Grenzen und nächste Schritte",
      data: "Daten und Nachvollziehbarkeit",
    },
  },
  question: {
    title: "Frage und Aufbau",
    p1: "Kann ein kleines Modell auf einem Kamerabild Glas, Metall, Papier, Kunststoff und Restmüll unterscheiden, und das gut genug, um als Auge eines Sortierroboters zu dienen?",
    classesLabel: "Die fünf Klassen",
    note: "mAP50 bewertet, wie gut die vorhergesagten Rahmen zu den markierten passen (mindestens 50 % Überlappung), gemittelt über alle Klassen. 100 % wäre perfekt.",
    p2: "Die Idee für die Hardware ist ein Raspberry Pi Zero 2W mit Kamera, der einem Roboterarm sagt, was er greifen soll. Es gibt nur den Erkennungsschritt.",
    p3: "Ich habe zwei Arten von Aufgaben bearbeitet. In Stufe A gibt ein Klassifikator ein Label pro Foto aus und wird an der Genauigkeit gemessen. In Stufe B zeichnet ein Detektor einen Rahmen um jedes gefundene Objekt und wird mit mAP50 bewertet. Jede Zahl auf dieser Seite ist ein Validierungswert: Sie wurde auf einem festgehaltenen Satz von Bildern gemessen, mit denen das Modell nicht trainiert wurde.",
  },
  tried: {
    title: "Was ich ausprobiert habe",
    p1: "Ich habe bewusst klein angefangen. Ein CNN mit drei Schichten hat mir das Problem gezeigt, MobileNetV2 hat gezeigt, was Transfer Learning bringt, und erst danach bin ich zu Detektoren gewechselt, die Rahmen zeichnen.",
    modelsCaption: "Die vier Modelle, in der Reihenfolge, in der ich sie getestet habe.",
    modelsLabel: "Auf kleinen Bildschirmen seitlich scrollbar",
    modelsColumns: { model: "Modell", task: "Aufgabe", runs: "Läufe", lesson: "Was ich daraus gelernt habe" },
    models: [
      {
        name: "Eigenes CNN",
        task: "Klassifikator, Stufe A",
        runs: "EXP-001",
        lesson: "Ich habe es gebaut, um das Problem zu verstehen. Papier wurde fast nie erkannt.",
      },
      {
        name: "MobileNetV2",
        task: "Klassifikator, Stufe A",
        runs: "EXP-002 bis EXP-004",
        lesson:
          "Transfer Learning erreichte 87,42 % Genauigkeit auf einem größeren, selbst gesammelten Datensatz. Aber weiter nur ein Label pro Foto.",
      },
      {
        name: "YOLOv8n",
        task: "Detektor, Stufe B",
        runs: "EXP-005 bis EXP-012",
        lesson: "Rahmen erlauben mehrere Objekte pro Bild. Mit Fotos aus dem Freien sank mAP50 auf 39,4 %.",
      },
      {
        name: "YOLO11n",
        task: "Detektor, Stufe B",
        runs: "EXP-013 bis EXP-019",
        lesson: "Das Modell hinter allen Kernzahlen auf dieser Seite.",
      },
    ],
    p2: "Die Trainingsdaten waren am Ende die größere Geschichte. Der endgültige Datensatz nutzt vier Quellen. Eine fünfte, WaRP, habe ich ausprobiert und wieder fallen gelassen. SortWaste und Keremberke wurden ebenfalls ausgeschlossen, das Protokoll hält den Ausschluss fest, aber nicht den Grund.",
    datasetsCaption: "Woher die Trainingsbilder kommen.",
    datasetsLabel: "Auf kleinen Bildschirmen seitlich scrollbar",
    datasetsColumns: { source: "Quelle", what: "Was es ist", status: "Stand" },
    datasets: [
      {
        name: "dmedhi",
        what: "Ein Datensatz für die Objekterkennung, von Hugging Face.",
        status: "Im endgültigen Datensatz",
      },
      {
        name: "TACO",
        what: "Trash Annotations in Context: Müll, im Freien fotografiert.",
        status: "Im endgültigen Datensatz",
      },
      {
        name: "Roboflow",
        what: "Ein Export zur Müllerkennung mit 64 Klassen, von mir auf meine fünf abgebildet. CC BY 4.0.",
        status: "Im endgültigen Datensatz",
      },
      {
        name: "TrashNet",
        what: "Tischfotos einzelner Gegenstände. Ich habe sie mit SAM für die Erkennung beschriftet.",
        status: "Im endgültigen Datensatz",
      },
      {
        name: "WaRP",
        what: "Ein Müll-Datensatz mit Lizenz nur für die Forschung und ohne Klasse Restmüll.",
        status: "Verworfen, Läufe damit waren schlechter",
      },
    ],
    p3: "Mehr Daten haben nicht geholfen. EXP-014 führte drei Quellen zusammen (6.802 Bilder) und erreichte {exp014} mAP50. Alle vier zusammenzuführen ergab in EXP-017 den größten Datensatz mit 9.774 Bildern und {exp017}. Der saubere Datensatz von EXP-018 hat nur {train} Trainingsbilder, mit 1.621 bis 1.982 Rahmen pro Klasse, und erreichte {exp018} in 2,7 Stunden statt 4,7. Das Protokoll folgert, dass die Qualität der Daten viel wichtiger war als Architektur oder Trainingsdauer. Meine eigene Einschätzung ist vorsichtiger, und die steht in Abschnitt 7.",
    splitNote:
      "Der saubere Datensatz hat 6.898 Bilder und 12.832 Rahmen: {train} zum Trainieren, {val} zur Validierung und {test} zum Testen.",
  },
  results: {
    title: "Ergebnisse",
    p1: "Auf dem bereinigten Datensatz erreichte YOLO11n in EXP-018 {exp018} mAP50 und bei der Wiederholung als EXP-019 {exp019}. Die frühere Basis mit zusammengeführten Daten, EXP-014, kam auf {exp014}.",
    chartAria: "Balkendiagramm der mAP50: EXP-014 {exp014}, EXP-018 {exp018}, EXP-019 {exp019}.",
    chartRows: [
      { id: "EXP-014", note: "zusammengeführte Quellen" },
      { id: "EXP-018", note: "bereinigt und ausbalanciert" },
      { id: "EXP-019", note: "Wiederholung von EXP-018" },
    ],
    chartCaption:
      "mAP50 von EXP-014, EXP-018 und EXP-019. Der umrandete Balken wurde auf einem anderen Validierungsdatensatz gemessen (1.588 gemischte Bilder statt {val} TrashNet-Tischbilder). Er vergleicht also zwei Ansätze und nicht zwei Modelle auf denselben Daten.",
    statValue: "==90,58 %==",
    statLabel: "mAP50 von EXP-019 auf {val} Validierungsbildern. Die Wiederholung entspricht EXP-018 fast genau.",
    p2: "Tabelle 3 schlüsselt EXP-019 nach Klassen auf. Kunststoff ist die schwache Klasse. Der Detektor findet {plasticRecall} der Kunststoff-Objekte, etwa jedes dritte wird also übersehen. Wenn er Kunststoff sagt, stimmt das meistens (Präzision {plasticPrecision}).",
    marginRecall:
      "Die Trefferquote (Recall) ist der Anteil der tatsächlich vorhandenen Objekte einer Klasse, die das Modell findet. Die Präzision ist der Anteil seiner Erkennungen, die richtig sind.",
    classTableCaption:
      "EXP-019 pro Klasse auf dem Validierungsdatensatz mit {val} Bildern. Das Protokoll nennt für EXP-018 dieselben Werte pro Klasse.",
    classTableLabel: "Auf kleinen Bildschirmen seitlich scrollbar",
    classColumns: { cls: "Klasse", precision: "Präzision", recall: "Trefferquote", map50: "mAP50" },
    classAll: "Alle Klassen",
    classWeakMark: "schwächste",
    p3: "Abbildung 2 stellt die mAP50 pro Klasse für die beiden Ansätze nebeneinander. Jede Klasse ist besser geworden. Restmüll hat sich am stärksten verändert, von der schwächsten Klasse ({trashBefore}) zur stärksten ({trashAfter}). Diesem Sprung traue ich noch nicht, und Abschnitt 7 sagt, warum.",
    classChartAria: "Balkendiagramm der mAP50 pro Klasse für EXP-014 und EXP-018, fünf Klassen.",
    classChartCaption:
      "mAP50 pro Klasse, EXP-014 (schraffiert) gegenüber EXP-018 (voll). Verschiedene Validierungsdatensätze, die Balken vergleichen also Ansätze und nicht Gleiches mit Gleichem.",
    classChartBefore: "EXP-014",
    classChartAfter: "EXP-018",
  },
  runs: {
    title: "Alle Experimente",
    p1: "Abbildung 3 zeigt die Kernzahl jedes bewerteten Laufs, und Tabelle 4 listet alle 19 mit dem auf, was sie gezeigt haben. Jeder Lauf wurde auf seinem eigenen Validierungsdatensatz bewertet. Die Balken sind deshalb eine Dokumentation und keine Rangliste. Drei Export-Läufe haben eine Dateigröße, aber keine Bewertung.",
    panelA: "A. Klassifikatoren, Genauigkeit",
    panelB: "B. Detektoren, mAP50",
    chartAriaA: "Balkendiagramm der Genauigkeit für die vier Klassifikator-Läufe.",
    chartAriaB: "Balkendiagramm der mAP50 für die zwölf bewerteten Detektor-Läufe.",
    chartCaption:
      "Kernzahl jedes bewerteten Laufs. Die dunklen Balken sind die Läufe mit sauberen Daten, EXP-018 und EXP-019. Die Läufe der Stufe A nutzten vier Klassen ohne Restmüll.",
    tableCaption: "Alle 19 dokumentierten Experimente, dazu EXP-020, das geplant und noch nicht gelaufen ist.",
    filterLabel: "Anzeigen",
    filters: { all: "Alle", A: "Stufe A", B: "Stufe B" },
    filterStatus: "{shown} von {total} Zeilen angezeigt.",
    tableLabel: "Auf kleinen Bildschirmen seitlich scrollbar",
    scrollHint: "Die Tabelle seitlich wischen, um alle Spalten zu sehen.",
    columns: { run: "Lauf", what: "Was es war", score: "Ergebnis", note: "Was es gezeigt hat" },
    scoreMap: "mAP50",
    scoreAcc: "Genauigkeit",
    sizeOnly: "nur Größe",
    scoredOn: "Bewertet auf",
    images: "{n} Bildern",
    caveatLabel: "Einschränkung",
    planned: "geplant, nicht gelaufen",
    plannedSetup: "YOLO11n. Roboflow 70 %, TACO 20 %, dmedhi 5 %, TrashNet 5 %.",
    plannedNote: "Es gibt kein Ergebnis. Nur die Konfiguration ist geschrieben (Abschnitt 7).",
    plannedSplit: "Noch nicht bewertet",
    exportKind: "Export",
    logLink: "Das ganze Experiment-Protokoll auf GitHub lesen",
  },
  photos: {
    title: "Echte Fotos und Fehler",
    unavailable: "Dieses Foto ist in dieser Version nicht verfügbar.",
    p1: "Zahlen verbergen, wie ein Fehler aussieht. Deshalb hier zwei Beispiele. Beides sind öffentliche TrashNet-Fotos, mit dem Modell EXP-019 bei einem Konfidenz-Schwellenwert von 0,25 ausgewertet.",
    note: "Diese Fotos sind Illustrationen, keine Belege. TrashNet gehört zu den Trainingsdaten, deshalb kann ich nicht sagen, dass sie zurückgehalten wurden. Sie werden in ihrer Originalbreite von 512 Pixeln gezeigt.",
    missed:
      "Ein Fehler. Das Foto zeigt eine zerdrückte Kunststoffflasche. Das Modell findet bei einer Konfidenz ab {conf} nichts.",
    outOfScope:
      "Außerhalb des Modells. Das Foto zeigt Karton, und MIRA hat keine Klasse dafür. Das Modell nennt es {predicted} ({conf}).",
    wrong: "Ein Fehler. Das Foto zeigt {trueClass}. Das Modell erkennt {predicted} ({conf}).",
    p2: "Beides passt zu Tabelle 3. Kunststoff übersieht der Detektor am häufigsten, und alles außerhalb der fünf Klassen wird in eine davon gepresst. Die meisten TrashNet-Fotos zeigen ein Objekt, das das Bild füllt, deshalb sind die Rahmen fast bildfüllend. Eine unordentliche Szene sieht anders aus.",
  },
  edge: {
    title: "Export für kleine Geräte",
    p1: "Der Raspberry Pi Zero 2W ist klein, deshalb habe ich EXP-019 in kleinere Formate exportiert. Tabelle 5 listet die Dateien auf.",
    tableCaption: "Die Dateien von EXP-019 und ihre Größe.",
    tableLabel: "Auf kleinen Bildschirmen seitlich scrollbar",
    columns: { format: "Format", file: "Datei", size: "Größe" },
    formats: {
      "mira_exp019.pt": "PyTorch, FP32",
      "mira_exp019_int8_320.tflite": "TFLite, 320 px, quantisierte Gewichte",
      "mira_exp019_int8_640.tflite": "TFLite, 640 px, quantisierte Gewichte",
      "mira_exp019.onnx": "ONNX",
    },
    sizeUnit: "MB",
    marginSize:
      "Die Größen sind die genauen Byte-Zahlen aus dem Protokoll, in dezimalen MB. Das Protokoll selbst nutzt MB und MiB durcheinander.",
    p2: "Quantisieren kostet Genauigkeit. Der TFLite-Export mit 320 px erreicht {tflite320} mAP50 gegenüber {exp019} beim Original, etwa {drop} Punkte weniger. Beide TFLite-Dateien behalten FP32 als Ein- und Ausgabe. Es sind also verkleinerte Exporte mit quantisierten Gewichten und keine reinen Ganzzahl-Modelle. Das Protokoll nennt nicht, auf welchem Datensatz diese lokale Prüfung lief.",
    p3: "Nicht gemessen habe ich Geschwindigkeit oder Genauigkeit auf einem Raspberry Pi. Die einzige CPU-Zeitmessung eines Detektors im Protokoll sind etwa 40,4 ms pro Bild für EXP-006, ein YOLOv8n-Modell, auf einer lokalen CPU. Das Protokoll nennt für denselben Lauf auch etwa 15,6 FPS, was nicht dazu passt (40,4 ms wären etwa 25 FPS). Das ist weder ein Pi noch das aktuelle Modell. Der MobileNetV2-Klassifikator EXP-004 hat eine CPU-Latenz von 10,32 ms.",
    p4: "Der Benchmark vom Juli (bildweise, ohne Kamera) bewertete 11 Modelle danach, ob eine Klasse überhaupt in einem Validierungsbild vorkommt (F1 bei Konfidenz {fieldConf}, nicht mAP50). EXP-014 lag mit {fieldBest} vorn, und sein INT8-Export fiel auf {fieldInt8}. EXP-018 und EXP-019 waren nicht dabei.",
  },
  limits: {
    title: "Grenzen und nächste Schritte",
    limitsTitle: "Grenzen",
    limits: [
      "Keine Evaluation mit einer echten Kamera. Jede Zahl stammt von einem festgehaltenen Satz Fotos. MIRA wurde nicht mit einer Kamera über einem echten Mülleimer getestet.",
      "Der unabhängige Testdatensatz mit {test} Bildern wurde für EXP-019 nicht ausgewertet. Ein volles Laufwerk hat das Notebook beim Speichern gestoppt, nachdem Training, Validierung und Exporte schon fertig waren.",
      "EXP-014 und EXP-018 wurden auf verschiedenen Validierungsdatensätzen bewertet (1.588 gemischte Bilder gegenüber {val} TrashNet-Tischbildern). Der Sprung von {exp014} auf {exp018} vergleicht zwei Ansätze. Ein Teil davon kann daher kommen, dass auf einem saubereren Tisch-Datensatz bewertet wurde, und das Protokoll kann beides nicht trennen. Es waren keine kontrollierten Vergleiche: Daten, Datensatz und manchmal das Modell haben sich zusammen geändert.",
      "Die Trefferquote bei Kunststoff liegt bei {plasticRecall}, und Restmüll hat die niedrigste Präzision ({trashPrecision}).",
      "Restmüll war in jedem früheren Detektor-Lauf mit Ergebnissen pro Klasse und einer Klasse Restmüll die schwächste Klasse und ist jetzt mit {trashAfter} die stärkste. Diese Umkehr muss mit echtem Kameramaterial geprüft werden, bevor sich jemand darauf verlässt.",
      "Bekannte Fehlerfälle sind zerknülltes Papier, Dosen mit Blick auf die Öffnung und sich überlappende Objekte.",
      "Geschwindigkeit und Genauigkeit auf einem Raspberry Pi sind nicht gemessen, und der Sortierroboter ist nicht gebaut.",
    ],
    logTitle: "Widersprüche in meinem eigenen Protokoll",
    logIntro: "Diese habe ich beim Schreiben der Seite gefunden. Ich habe jeweils die Zahlen des Laufs selbst benutzt.",
    log: [
      "EXP-018: Präzision und Trefferquote über alle Klassen (90,4 und 82,5) sind im Protokoll identisch mit der Zeile für Glas, was nach einem Übertragungsfehler aussieht. Tabelle 3 nutzt die Gesamtzeile von EXP-019.",
      "EXP-017: Die Vergleichsangaben nennen die Werte von EXP-014 für Restmüll und Kunststoff anders als die eigene Tabelle von EXP-014.",
      "EXP-001: Das Protokoll nennt 126 Bilder, aber die Stützwerte (Support) pro Klasse ergeben zusammen 159.",
      "EXP-004: Die Genauigkeit steht sowohl als 87,42 % als auch als 0,8735 im Protokoll.",
    ],
    nextTitle: "Nächste Schritte",
    next: [
      "Mit echtem Kameramaterial auswerten und dabei Trefferquote und Fehlalarme vergleichen, nicht nur die Konfidenz.",
      "Den unabhängigen Testdatensatz mit {test} Bildern auswerten.",
      "Geschwindigkeit und Genauigkeit der TFLite-Exporte auf einem Raspberry Pi messen.",
    ],
    plannedTitle: "EXP-020: geplant, nicht gelaufen",
    plannedIntro:
      "EXP-020 ändert nur, wie die Quellen gewichtet werden. Es nutzt dieselbe Architektur und dieselben dokumentierten Einstellungen wie EXP-019. Es gibt eine Konfigurationsdatei, aber kein Ergebnis.",
    plannedCaption: "Die geplante Konfiguration von EXP-020. Es gibt keine Bewertung, weil es nicht trainiert wurde.",
    plannedLabel: "Auf kleinen Bildschirmen seitlich scrollbar",
    plannedRows: {
      model: "Modell",
      mix: "Mischung der Quellen",
      images: "Trainingsbilder",
      settings: "Einstellungen",
      validation: "Validierung",
      camera: "Echte Kamera",
      result: "Ergebnis",
      config: "Konfigurationsdatei",
    },
    plannedMix: "Roboflow 70 %, TACO 20 %, dmedhi 5 %, TrashNet 5 %",
    plannedSettings:
      "{epochs} Epochen, Batch {batch}, {imgsz} px, {optimizer}, lr0 {lr0}, lrf {lrf}, Weight Decay {wd}, Patience {patience}, Seed {seed}",
    plannedValidation: "Gemischte, zurückgehaltene Teile der Quellen-Datensätze",
    plannedCamera: "Muss vor dem Einsatz getrennt ausgewertet werden",
    plannedResult: "Keins. Es gibt nichts zu berichten.",
  },
  data: {
    title: "Daten und Nachvollziehbarkeit",
    p1: "Die Datensätze liegen nicht im Repository. Die [Herkunft der Datensätze]({originsUrl}) nennt, wo man jeden herunterladen kann, mit Lizenzen. Alle 19 Experimente stehen im [Experiment-Protokoll]({logUrl}) mit Einstellungen und Einschränkungen. Die trainierten Modelle liegen auf [Hugging Face]({hfUrl}), der Code auf [GitHub]({githubUrl}). Das [Paket](/package) enthält die Gewichte von EXP-014, EXP-018 und EXP-019.",
  },
  experiments: {
    "EXP-001": {
      title: "Basis: eigenes CNN",
      setup: "Eigenes CNN, 3 Faltungsschichten. Selbst gesammelte Bilder, 4 Klassen (ohne Restmüll). 126 Bilder.",
      split: "Validierungsdatensatz, Größe nicht festgehalten",
      note: "Eine Basis, um das Problem zu verstehen. Papier wurde fast nie erkannt (Trefferquote 0,07).",
      caveat: [
        "Das Protokoll nennt 126 Bilder, aber die Stützwerte (Support) pro Klasse ergeben zusammen 159. Die Größe der Validierung ist also nicht verlässlich angegeben.",
      ],
    },
    "EXP-002": {
      title: "MobileNetV2, eingefrorene Basis",
      setup:
        "MobileNetV2 (ImageNet, eingefroren) + kleiner Kopf. Selbst gesammelte Bilder, 4 Klassen (ohne Restmüll). 796 Bilder.",
      split: "Validierungsdatensatz, Größe nicht festgehalten",
      note: "Transfer Learning hob die Genauigkeit um über 23 Punkte, auf einem größeren selbst gesammelten Datensatz.",
      caveat: [],
    },
    "EXP-003": {
      title: "MobileNetV2, feinabgestimmt",
      setup:
        "MobileNetV2 (ab Schicht 100 aufgetaut) + kleiner Kopf. Dieselben 796 selbst gesammelten Bilder, 4 Klassen.",
      split: "Validierungsdatensatz, Größe nicht festgehalten",
      note: "Zweistufiges Feinabstimmen ergab den besten Klassifikator. Er vergibt trotzdem nur ein Label pro Bild.",
      caveat: [],
    },
    "EXP-004": {
      title: "MobileNetV2, volles INT8-TFLite",
      setup:
        "MobileNetV2, quantisiert (Gewichte mit kleineren Zahlen gespeichert) auf 8-Bit-Ganzzahlen, aus EXP-003. 796 Bilder, 4 Klassen.",
      split: "Validierungsdatensatz, Größe nicht festgehalten",
      note: "Durch Quantisierung schrumpfte das Modell auf 2,61 MB (9,0-mal kleiner als die Keras-Datei), ohne dass ein Genauigkeitsverlust festgehalten wurde.",
      caveat: ["Das Protokoll gibt die Genauigkeit sowohl als 87,42 % als auch als 0,8735 an."],
    },
    "EXP-005": {
      title: "Erster Detektor",
      setup: "YOLOv8n. Selbst gesammelte Tischbilder + TrashNet. Etwa 3.300 Bilder.",
      split: "Validierungsdatensatz, Größe nicht festgehalten",
      note: "Mit Rahmen wurden mehrere Objekte pro Bild möglich.",
      caveat: ["Die Rahmen wurden automatisch mit Canny-Kantenerkennung erzeugt und nicht von Hand gezeichnet."],
    },
    "EXP-006": {
      title: "TrashNet + Roboflow-Bilder aus dem Freien",
      setup: "YOLOv8n. Selbst gesammelt + TrashNet + Roboflow (64 Klassen auf 5 abgebildet). Etwa 3.300 Bilder.",
      split: "Gemischte Validierungsdaten, überwiegend im Freien",
      note: "Mit Bildern aus dem Freien sank mAP50 auf 39,4 %. Das Protokoll nennt etwa 40,4 ms pro Bild auf einer lokalen CPU und eine FPS-Angabe, die dazu nicht passt.",
      caveat: [
        "Bewertet auf überwiegend Bildern aus dem Freien, daher nicht mit reinen Tischbild-Läufen vergleichbar.",
      ],
    },
    "EXP-007": {
      title: "YOLOv8n INT8-Export",
      setup: "YOLOv8n, TFLite INT8. Abgeleitet aus EXP-006.",
      split: "Nicht bewertet, nur Größe",
      note: "Statische INT8-Quantisierung: von 11,69 MB auf 3,18 MB (3,7-mal kleiner).",
      caveat: ["Das Protokoll hält die Dateigröße fest, aber keine Genauigkeit des quantisierten Modells."],
    },
    "EXP-008": {
      title: "Tischbilder, bereinigte Labels",
      setup: "YOLOv8n. Selbst gesammelte Tischbilder + von Hand beschriftetes TrashNet. Etwa 3.000 Bilder.",
      split: "Validierungsdatensatz, Größe nicht festgehalten",
      note: "Das Entfernen fehlerhaft automatisch beschrifteter Bilder erreichte in der halben Zeit das Niveau des verrauschten Laufs mit 100 Epochen.",
      caveat: [],
    },
    "EXP-009": {
      title: "Saubere TrashNet-Basis",
      setup: "YOLOv8n. Nur TrashNet, automatisch per Canny-Kanten beschriftet. Etwa 2.527 Bilder.",
      split: "Validierungsdatensatz, Größe nicht festgehalten",
      note: "Ohne die verrauschten eigenen Bilder stieg mAP50 von 39,6 % auf 72,8 %.",
      caveat: [
        "Trainiert und validiert auf sauberen TrashNet-Bildern mit weißem Hintergrund. Das Protokoll merkt an, dass diese Validierung den Wert überschätzen kann.",
      ],
    },
    "EXP-010": {
      title: "INT8-Export der Daten aus dem Freien",
      setup: "YOLOv8n, TFLite INT8. Abgeleitet aus EXP-006.",
      split: "Nicht bewertet, nur Größe",
      note: "Ein zweiter INT8-Export des Modells aus EXP-006, mit 100 Bildern aus dem Freien kalibriert: 3,16 MB.",
      caveat: ["Das Protokoll hält die Dateigröße fest, aber keine Genauigkeit des quantisierten Modells."],
    },
    "EXP-011": {
      title: "Nur Daten aus dem Freien",
      setup: "YOLOv8n. TACO, Müll im Freien, 60 Kategorien auf 5 abgebildet. 3.365 Bilder.",
      split: "Vielfältiger Validierungsdatensatz aus dem Freien",
      note: "Ein Test, wie gut das Modell verallgemeinert: ohne Tischbilder, Restmüll bei 7,5 % mAP50.",
      caveat: [],
    },
    "EXP-012": {
      title: "INT8-Export, nur Daten aus dem Freien",
      setup: "YOLOv8n, TFLite INT8. Abgeleitet aus EXP-011.",
      split: "Nicht bewertet, nur Größe",
      note: "INT8-Export von EXP-011: von 11,62 MB auf 3,16 MB (3,7-mal kleiner).",
      caveat: [
        "Im Benchmark vom Juli (bildweise, ohne Kamera) lieferte dieser Export bei der Standard-Konfidenz 0,5 keine Erkennungen (INT8 senkt die Werte). Bei 0,25 funktioniert er.",
      ],
    },
    "EXP-013": {
      title: "YOLO11n auf TACO + TrashNet",
      setup: "YOLO11n. TACO (1.497) + TrashNet (2.527), bildfüllende Rahmen. 4.024 Bilder.",
      split: "Validierungsdatensatz, Größe nicht festgehalten",
      note: "Erster YOLO11n-Lauf, 20 Punkte über EXP-011 mit nur Daten aus dem Freien. Restmüll war die schwächste Klasse (15,6 % mAP50).",
      caveat: [
        "Architektur und Datensatz haben sich zugleich geändert, der Gewinn lässt sich also nicht allein dem Modell zuschreiben.",
      ],
    },
    "EXP-014": {
      title: "TACO + TrashNet + Roboflow",
      setup: "YOLO11n. TACO + TrashNet + Roboflow (64 Klassen auf 5 abgebildet). 6.802 Bilder.",
      split: "Eigener gemischter Validierungsdatensatz",
      note: "Die Basis mit gemischten Daten. Mit Roboflow stieg mAP50 um 5,6 Punkte gegenüber EXP-013.",
      caveat: [
        "Validiert auf dem eigenen gemischten Datensatz, nicht auf dem TrashNet-Datensatz mit 415 Bildern, den EXP-018 und EXP-019 nutzen.",
      ],
    },
    "EXP-015": {
      title: "TACO + TrashNet + WaRP",
      setup: "YOLO11n. TACO + TrashNet + WaRP (28 Klassen auf 5 abgebildet). Etwa 6.800 Bilder.",
      split: "Eigener gemischter Validierungsdatensatz",
      note: "WaRP statt Roboflow half bei Glas, kostete aber Metall, Papier und Restmüll. Die Trefferquote für Restmüll fiel auf 0,087.",
      caveat: [],
    },
    "EXP-016": {
      title: "Nur WaRP",
      setup: "YOLO11n. Nur WaRP (28 Klassen auf 5 abgebildet). Bildanzahl nicht festgehalten.",
      split: "Validierungsdatensatz, Größe nicht festgehalten",
      note: "Eine saubere Quelle schlug das gemischte EXP-015 (56,0 %), obwohl sie weniger Klassen hat.",
      caveat: ["WaRP hat keine Klasse Restmüll, dieses Modell kann Restmüll also gar nicht erkennen."],
    },
    "EXP-017": {
      title: "Alle vier Quellen zusammen",
      setup: "YOLO11n. TACO + TrashNet + Roboflow + WaRP. 9.774 Bilder.",
      split: "Eigener gemischter Validierungsdatensatz",
      note: "Der größte Datensatz war schlechter als EXP-014. Mehr Daten waren nicht bessere Daten.",
      caveat: [
        "Die Vergleichspunkte im Protokoll nennen die Werte von EXP-014 für Restmüll und Kunststoff anders als die eigene Tabelle von EXP-014. Diese Seite nutzt jeweils die eigene Tabelle des Laufs.",
      ],
    },
    "EXP-018": {
      title: "Sauberer, ausbalancierter Datensatz",
      setup:
        "YOLO11n. dmedhi + TACO + Roboflow + TrashNet (mit SAM beschriftet). SortWaste und Keremberke ausgeschlossen. 5.108 Bilder zum Trainieren, 415 zur Validierung, 1.375 zum Testen.",
      split: "TrashNet-Tischbilder als Validierungsdatensatz",
      note: "Ein kleinerer, nach Klassen ausbalancierter Datensatz (1.621 bis 1.982 Rahmen pro Klasse) hob mAP50 um 29,9 Punkte.",
      caveat: [
        "Der Datensatz mit 415 Bildern unterscheidet sich von dem von EXP-014, das vergleicht also Ansätze und nicht Gleiches mit Gleichem.",
        "Präzision und Trefferquote über alle Klassen im Protokoll entsprechen der Zeile für Glas, was ein Übertragungsfehler sein kann. Ein Ergebnis auf dem Testdatensatz ist nicht festgehalten.",
      ],
    },
    "EXP-019": {
      title: "Wiederholung von EXP-018",
      setup: "YOLO11n. Derselbe saubere, ausbalancierte Datensatz und dieselben Einstellungen wie EXP-018.",
      split: "TrashNet-Tischbilder als Validierungsdatensatz",
      note: "Reproduziert EXP-018 fast genau, das Ergebnis ist also wiederholbar und kein Glückstreffer.",
      caveat: [
        "Der Testdatensatz mit 1.375 Bildern wurde nicht ausgewertet. Ein volles Laufwerk hat das Notebook beim Speichern gestoppt.",
      ],
    },
  },
};
