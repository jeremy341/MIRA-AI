/**
 * Deutsche Dokumentation. Gleiche Struktur wie en.ts (gleiche Slugs, Abschnitts-IDs, Blocktypen und
 * Blockanzahl), Befehle, Optionen, Konfigurationsschlüssel, Dateinamen und Code bleiben identisch zum
 * Englischen. `docs.parity.test.ts` prüft das. Keine Gedankenstriche (lange oder mittellange) im Text.
 */

import { GITHUB_URL, HF_URL, PYPI_LATEST_VERSION, PYPI_URL } from "../../lib/site";
import {
  analytics,
  apiV1,
  batchImport,
  compareBenchmark,
  dashboard,
  detect,
  exportPage,
  faq,
  sessions,
  sortingArm,
  troubleshooting,
} from "./de-dashboard";
import { code, h3, lines, list, note, output, p, table, warning } from "./helpers";
import { MIRA_YAML } from "./shared-code";
import type { DocPage } from "./types";

const quickstart: DocPage = {
  slug: "quickstart",
  title: "Schnellstart",
  group: "start",
  summary: "mira-ai von PyPI installieren, die Umgebung prüfen und die Live-Erkennung mit einer Webcam starten.",
  lead: "Installieren Sie das Paket, prüfen Sie die Umgebung und öffnen Sie ein Fenster mit Live-Erkennung. Das Paket bringt drei trainierte Detektoren mit.",
  sections: [
    {
      id: "install",
      title: "Installation",
      blocks: [
        p(
          `MIRA braucht Python 3.11 oder 3.12 und für die Live-Erkennung eine USB-Webcam. Das [Paket mira-ai](${PYPI_URL}) installiert den Befehl \`mira\` und enthält die Detektor-Gewichte von EXP-014, EXP-018 und EXP-019. Die neueste Version auf PyPI ist ${PYPI_LATEST_VERSION}.`,
        ),
        code(
          lines(
            "py -3 -m venv .venv",
            String.raw`.venv\Scripts\Activate.ps1`,
            "python -m pip install --upgrade pip",
            "python -m pip install mira-ai",
          ),
          "Windows PowerShell",
        ),
        code(
          lines(
            "python3 -m venv .venv",
            "source .venv/bin/activate",
            "python -m pip install --upgrade pip",
            "python -m pip install mira-ai",
          ),
          "macOS und Linux",
        ),
        p(
          "Diese Befehle stammen aus der README und wurden unter Windows PowerShell ausgeführt. Die Zeilen für macOS und Linux sind übliche venv-Befehle, die nicht ausgeführt wurden. Verwenden Sie eine virtuelle Umgebung: Das Paket hängt von PyTorch, OpenCV und Ultralytics ab, die groß sind und leicht mit anderen Projekten in Konflikt geraten.",
        ),
        note(
          "Python-Version und Versionsnummer",
          `Das veröffentlichte Paket verlangt \`>=3.11\`. Das Repository verlangt \`>=3.11,<3.13\`, deshalb steht hier 3.11 oder 3.12. Das Repository und die neueste Version auf PyPI stehen beide auf ${PYPI_LATEST_VERSION}, eine Installation aus dem Quellcode meldet also dieselbe Nummer.`,
        ),
      ],
    },
    {
      id: "check",
      title: "Umgebung prüfen",
      blocks: [
        code(lines("mira --version", "mira doctor", "mira models")),
        p(
          "`mira doctor` führt fünf Prüfungen aus: Konfiguration, Hardware, Umgebung, Modelle und Datensätze. Es zeigt, ob CUDA verfügbar ist, und schlägt ein Modellformat für den Rechner vor. Die letzte Zeile lautet `Status: HEALTHY`, außer die Konfiguration ist ungültig oder die Umgebungsprüfung gibt eine Warnung aus, zum Beispiel wegen einer fehlenden Bibliothek.",
        ),
        p(
          "Bei einer normalen Installation von PyPI meldet die Datensatz-Prüfung, dass keine Datensatzquellen verfügbar sind. Das ist erwartet und ändert den Status nicht. `mira models` listet die mitgelieferten Gewichte mit Typ und Größe.",
        ),
      ],
    },
    {
      id: "live",
      title: "Live-Erkennung starten",
      blocks: [
        code("mira live --model mira_exp014.pt"),
        p(
          "Es öffnet sich ein Fenster mit dem Titel `MIRA Real-Time Multi-Object Detection`. Sichere Erkennungen bekommen eine grüne Box mit Klasse und Konfidenz, eine Statuszeile zeigt Kameraindex, Auflösung, Latenz, FPS und das Überspringen von Bildern. Mit `q` im Fenster beenden Sie das Programm.",
        ),
        p(
          "Führen Sie `mira live` ohne `--model` aus, dann wählen Sie aus einer interaktiven Liste. EXP-014 ist das Standardmodell für die Demo, weil sich das Modell in der Live-Demo so verhält, nicht wegen seines gemessenen mAP50-Werts. Was die mitgelieferten Modelle sind, steht unter [Modelle](/docs/models).",
        ),
        note(
          "Keine Kamera gefunden",
          "Probieren Sie `--camera 1`. Der Befehl bricht mit einem Fehler ab, wenn sich der Kameraindex 0 nicht öffnen lässt, und stoppt nach 30 fehlgeschlagenen Lesezugriffen in Folge. Siehe [Live-Erkennung starten](/docs/live-inference).",
        ),
      ],
    },
    {
      id: "source",
      title: "Installation aus dem Quellcode",
      blocks: [
        p(
          "Training, das Zusammenführen von Datensätzen und die Experimentdateien liegen im GitHub-Repository und nicht im Wheel. Um sie zu nutzen, arbeiten Sie in einem Klon des Repositorys.",
        ),
        code(
          lines(
            `git clone ${GITHUB_URL}.git`,
            "cd MIRA-AI",
            "py -3 -m venv .venv",
            String.raw`.venv\Scripts\Activate.ps1`,
            "pip install -e .",
          ),
          "Windows PowerShell",
        ),
        h3("extras", "Optionale Extras"),
        table(
          "Optionale Abhängigkeitsgruppen aus pyproject.toml",
          ["Extra", "Installation", "Enthält"],
          [
            [
              "`train`",
              '`pip install "mira-ai[train]"`',
              "TensorFlow, gebraucht für das Training der Klassifikatoren und den TFLite-Export.",
            ],
            [
              "`analysis`",
              '`pip install "mira-ai[analysis]"`',
              "matplotlib, pandas, scikit-learn und scipy für die Auswertungsskripte mit Diagrammen.",
            ],
            ["`all`", '`pip install "mira-ai[all]"`', "Beide Gruppen zusammen."],
          ],
        ),
      ],
    },
    {
      id: "next",
      title: "Wie es weitergeht",
      blocks: [
        list([
          "Schwellenwerte und Kameras stellen Sie unter [Live-Erkennung starten](/docs/live-inference) ein.",
          "Erkennungen im Browser sehen Sie im [Dashboard](/docs/dashboard).",
          "Trainingsdaten neu aufbauen oder erweitern: [Datensätze vorbereiten](/docs/datasets).",
          "Jede Option schlagen Sie in den [CLI-Befehlen](/docs/cli) nach.",
        ]),
      ],
    },
  ],
};

const configuration: DocPage = {
  slug: "configuration",
  title: "Konfiguration",
  group: "start",
  summary: "Wie MIRA die Datei mira.yaml findet, welche Schlüssel der Code liest und wie man sie prüft.",
  lead: "`mira.yaml` enthält die Klassenliste sowie die Standardwerte für Training und Inferenz. Nur ein Teil der Schlüssel wird vom Code gelesen. Diese Seite sagt, welche und wo.",
  sections: [
    {
      id: "location",
      title: "Wo MIRA sucht",
      blocks: [
        p("Das Projektverzeichnis ist das erste der folgenden, das zutrifft:"),
        list(
          [
            "Der Ordner aus der Umgebungsvariable `MIRA_HOME`.",
            "Der nächste Ordner, der `mira.yaml` enthält, ausgehend vom aktuellen Verzeichnis und nach oben suchend.",
            "Das aktuelle Verzeichnis.",
          ],
          true,
        ),
        p(
          "Fehlt im Projektverzeichnis die Datei `mira.yaml`, wird die Kopie im Wheel verwendet. Modelldateien werden aus `<root>/models/detection` gelesen. Enthält dieser Ordner keine Datei `.pt`, `.pth`, `.tflite` oder `.onnx`, werden stattdessen die mitgelieferten Gewichte verwendet.",
        ),
        warning(
          "Ein Modellordner verdeckt die mitgelieferten Modelle",
          "Sobald `models/detection` irgendeine Modelldatei enthält, nutzt MIRA nur diesen Ordner. Die Gewichte aus dem Paket erscheinen dann weder in `mira models` noch im Dashboard, bis Sie den Ordner leeren oder entfernen.",
        ),
      ],
    },
    {
      id: "file",
      title: "Die Datei",
      blocks: [p("Das ist die `mira.yaml` aus dem Wurzelverzeichnis des Repositorys."), code(MIRA_YAML, "mira.yaml")],
    },
    {
      id: "keys",
      title: "Was jeder Schlüssel bewirkt",
      blocks: [
        table(
          "Schlüssel in mira.yaml und der Code, der sie liest",
          ["Schlüssel", "Wert", "Verwendet von"],
          [
            [
              "`classes.names`, `classes.count`",
              "glass, metal, paper, plastic, trash; 5",
              "Klassennamen zum Zeichnen der Boxen und die Prüfung des Klassen-ID-Bereichs in `mira validate`. `count` muss der Anzahl der Namen entsprechen.",
            ],
            ["`paths.models`", "`models/`", "Dort wird der Ordner `detection/` mit den Modellen gesucht."],
            [
              "`paths.datasets`, `paths.results`",
              "`datasets/`, `results/`",
              "Werden nicht gelesen. Die Befehle verwenden `datasets/` und `results/` fest.",
            ],
            [
              "`training.default_model`",
              "`mira_exp014.pt`",
              "Standardwert für `model` bei `mira train` und im Wizard. Wird unverändert an Ultralytics übergeben, verwenden Sie also einen echten Pfad oder `yolo11n.pt` für einen frischen Lauf.",
            ],
            [
              "`training.default_epochs`, `default_batch_size`, `default_imgsz`, `default_lr`, `early_stopping_patience`",
              "120, 32, 640, 0.01, 30",
              "Standardwerte von `TrainConfig`, vom Wizard und von den erzeugten Notebooks.",
            ],
            [
              "`training.augmentation`",
              "Mapping",
              "Wird nur von den Notebooks und Docker-Dateien aus `mira generate` verwendet, wenn die Experimentdatei keine eigene `augmentation` hat. `mira train` liest die Augmentierung aus der Experimentdatei.",
            ],
            ["`inference.default_conf`", "0.5", "Standardwert von `mira benchmark --conf` und der Modell-Adapter."],
            ["`inference.default_iou`", "0.45", "NMS-IoU für `mira live` und die Modell-Adapter."],
            [
              "`inference.reject_threshold`",
              "0.55",
              "Wird von `mira config --validate` geprüft, aber kein Befehl liest ihn. `mira live` und das Dashboard nehmen die Ablehnungsschwelle aus `--reject` und aus den Modelleinstellungen.",
            ],
            [
              "`quantization.*`",
              "`int8`, `fp32`; 100",
              "Werden nicht gelesen. Die Exportformate kommen aus `mira export --formats`.",
            ],
          ],
        ),
        note(
          "Die Live-Standardwerte stehen fest im Code",
          "`mira live` verwendet 0.25 für `--conf` und `--reject` sowie 1000 ms für `--target-latency`. Das sind Konstanten in `src/config.py`, eine Änderung an `mira.yaml` wirkt sich also nicht aus. Übergeben Sie stattdessen die Option.",
        ),
      ],
    },
    {
      id: "validate",
      title: "Anzeigen und prüfen",
      blocks: [
        code(lines("mira config", "mira config --validate")),
        p(
          "`mira config` gibt die wirksame Konfiguration als JSON aus. `mira config --validate` prüft die Datei und zeigt eine kurze Zusammenfassung zu Klassen, Trainingsstandards, Datensätzen und Modellanzahl. Bei einer ungültigen Konfiguration beendet es sich mit Status 1 und listet die Fehler auf.",
        ),
        p("Die Prüfung verlangt:"),
        list([
          "dass die Abschnitte `classes`, `training` und `inference` vorhanden sind;",
          "dass `classes.names` eine nicht leere Liste von Strings ist und `classes.count` (falls gesetzt) ihrer Länge entspricht;",
          "dass `default_epochs`, `default_batch_size`, `default_imgsz` und `early_stopping_patience` ganze Zahlen von mindestens 1 sind und `default_lr` größer als 0 ist;",
          "dass `reject_threshold`, `default_conf` und `default_iou` Zahlen echt zwischen 0 und 1 sind.",
        ]),
        p("Optionen auf der Kommandozeile überschreiben diese Standardwerte für einen einzelnen Lauf."),
      ],
    },
  ],
};

const architecture: DocPage = {
  slug: "architecture",
  title: "Architektur",
  group: "start",
  summary: "Wie aus einem Kamerabild eine Erkennung wird und wo die einzelnen Teile im Repository liegen.",
  lead: "Kameraaufnahme, Inferenz, Anzeige und Forschungswerkzeuge sind getrennte Module, damit sich jedes ohne die anderen testen lässt.",
  sections: [
    {
      id: "flow",
      title: "Vom Bild zur Erkennung",
      blocks: [
        {
          type: "flow",
          label: "Datenfluss von MIRA zur Laufzeit",
          steps: [
            { title: "USB-Kamera", detail: "OpenCV-Aufnahme, MJPG, wählbare Auflösung" },
            { title: "Bildpuffer", detail: "Ein Lese-Thread behält nur das neueste Bild" },
            { title: "YOLO-Inferenz", detail: "PyTorch .pt oder TFLite, ByteTrack für .pt" },
            { title: "Ausgabe", detail: "OpenCV-Fenster oder Dashboard über REST und WebSocket" },
          ],
        },
        p(
          "`USBCamera` in `src/hardware.py` führt einen Hintergrund-Thread aus, der die Kamera etwa alle 10 ms liest und einen Puffer für ein einzelnes Bild überschreibt. Die Inferenz nimmt immer das neueste Bild, ein langsames Modell überspringt also Bilder, statt in Rückstand zu geraten. Der Puffer erkennt außerdem eine eingefrorene Kamera.",
        ),
        p(
          "`mira live` startet `InferenceEngine` und zeichnet in ein OpenCV-Fenster. `mira dashboard` startet einen FastAPI-Dienst, dessen `CameraService` dieselbe Aufnahme und Inferenz ausführt und dann JPEG-Bilder, Erkennungen und Messwerte an den Browser sendet. Eine Kameraklasse für RTSP-Streams (`IPCamera`) gibt es in `src/hardware.py`, sie ist aber weder mit der CLI noch mit dem Dashboard verbunden. Unterstützt werden also nur USB-Kameras.",
        ),
      ],
    },
    {
      id: "modules",
      title: "Wichtige Module",
      blocks: [
        table(
          "Wo was liegt",
          ["Pfad", "Aufgabe"],
          [
            [
              "`src/cli/`",
              "Ein Modul pro Befehlsgruppe. Jeder Befehl registriert sich mit `register_command`, und `src/cli/__init__.py` baut den Parser von `mira` aus dieser Registry.",
            ],
            [
              "`src/config.py`",
              "Findet und prüft `mira.yaml`, bestimmt den Modellordner und definiert die Standardwerte für Kamera und Inferenz.",
            ],
            ["`src/hardware.py`", "Kameraklassen und der threadsichere Bildpuffer."],
            [
              "`src/inference_engine.py`",
              "Modell laden, Tracking, latenzbasiertes Überspringen von Bildern und Aufräumen für `mira live`.",
            ],
            [
              "`src/visualize.py`",
              "Zeichnen der Boxen, einschließlich der Darstellung für sichere und unsichere Erkennungen.",
            ],
            [
              "`src/dashboard/backend/`",
              "FastAPI-App (`main.py`), `camera_service.py`, `command_service.py`, `websocket_handler.py` und die pydantic-Modelle.",
            ],
            [
              "`src/dashboard/frontend/`",
              "Die bisherige Dashboard-Seite (`dashboard.html`, `dashboard.css`, `dashboard.js`), unter `/legacy` ausgeliefert, und die gebaute Oberfläche in `dist/`.",
            ],
            [
              "`src/dashboard/ui/`",
              "Quellcode der Dashboard-Oberfläche (Svelte und Vite). Die Version 1 der Backend-API mit Sitzungen, Exporten, Vergleich, Benchmark, Stapel, Hardware und Arm liegt in `src/dashboard/backend/v1/`.",
            ],
            [
              "`src/pipeline/`",
              "Datensatz-Registry und Zusammenführung, Validatoren, Trainingsstrategien, Export, Modell-Registry und Adapter sowie der Benchmark.",
            ],
            [
              "`src/serialization.py`",
              "Schreibt Konfigurationen und Ergebnisse mit `.bak`-Sicherungen, dazu Metadaten zur Reproduzierbarkeit.",
            ],
            ["`src/notebooks/`", "Generatoren für Kaggle- und Colab-Notebooks und Docker-Trainingsdateien."],
            [
              "`scripts/`",
              "Eigenständige Skripte für Auswertung, Vergleich, Profiling und den Aufbau von Datensätzen.",
            ],
          ],
        ),
      ],
    },
    {
      id: "models",
      title: "Modellerkennung",
      blocks: [
        p(
          "`ModelRegistry` durchsucht den Modellordner. Eine YAML-Datei neben einer Gewichtsdatei ist eine Begleitdatei (Sidecar) und liefert Anzeigenamen, Klassennamen, Tags und die gemessenen Kennzahlen. Bei einer Begleitdatei `mira_exp019.yaml` werden auch `mira_exp019_int8.tflite` und `mira_exp019.onnx` registriert, wenn es sie gibt. Dateien ohne Begleitdatei werden unter ihrem Dateinamen registriert.",
        ),
        p(
          "Drei Adapter kapseln die Modelltypen: `yolo_pt`, `yolo_tflite` und `third_party`. Trainingsstrategien werden auf dieselbe Weise registriert, als `detection` (Ultralytics YOLO) und `classifier` (TensorFlow MobileNetV2 oder ein eigenes CNN).",
        ),
      ],
    },
    {
      id: "reproducibility",
      title: "Protokolle für die Reproduzierbarkeit",
      blocks: [
        p(
          "Ein Trainingslauf schreibt `config.yaml`, `results.json` und `metadata.json` in seinen Lauf-Ordner. Die Metadaten halten Befehl, Argumente, Git-SHA, ob der Arbeitsbaum nicht committete Änderungen hatte, die Python-Version und die Plattform fest. Existiert eine Datei schon, wird sie vor dem Ersetzen nach `<name>.bak` kopiert, damit ein erneuter Lauf frühere Ergebnisse nicht unbemerkt zerstört.",
        ),
      ],
    },
  ],
};

const liveInference: DocPage = {
  slug: "live-inference",
  title: "Live-Erkennung starten",
  group: "guides",
  summary:
    "Ein Webcam-Fenster mit Erkennung öffnen und Kamera, Schwellenwerte und das Überspringen von Bildern einstellen.",
  sections: [
    {
      id: "run",
      title: "Starten",
      blocks: [
        code(
          lines(
            "mira live",
            "mira live --model mira_exp014.pt",
            "mira live --model mira_exp014.pt --camera 1 --resolution 1280x720",
            "mira live --model mira_exp014.pt --conf 0.4 --reject 0.6",
          ),
        ),
        p(
          "`--model` erwartet einen Dateinamen aus dem Modellordner, keinen Pfad. Ohne die Option listet eine interaktive Auswahl die gefundenen Modelle auf. Namen mit `classifier` werden abgelehnt, weil die Live-Erkennung einen Detektor braucht. Mit `q` im Fenster beenden Sie das Programm.",
        ),
        p("Das Fenster zeichnet eine Statuszeile in diesem Format. Die Zahlen sind Beispiele, keine Messwerte."),
        output("Cam: 0 | 640x360 | Latency: 12.3ms (avg: 11.8ms) | FPS: 24.5 | Skip: OFF", "Statuszeile"),
      ],
    },
    {
      id: "options",
      title: "Optionen",
      blocks: [
        table(
          "Optionen von mira live",
          ["Option", "Standard", "Hinweise"],
          [
            ["`--model`", "Auswahl", "Dateiname des Modells."],
            ["`--camera`", "`0`", "Index des Kamerageräts."],
            ["`--resolution`", "`640x360`", "Eine von `640x360`, `1280x720`, `1920x1080`."],
            ["`--conf`", "`0.25`", "Erkennungen darunter werden nicht gezeichnet."],
            ["`--reject`", "`0.25`", "Erkennungen darunter werden als unsicher (`uncertain`) beschriftet."],
            [
              "`--imgsz`",
              "`640`",
              "Inferenzgröße für PyTorch-Modelle. TFLite-Modelle haben ihre eigene feste Größe und ignorieren die Option mit einer Warnung.",
            ],
            ["`--target-latency`", "`1000`", "Millisekunden. Siehe das Überspringen von Bildern weiter unten."],
          ],
        ),
      ],
    },
    {
      id: "tiers",
      title: "Konfidenzstufen",
      blocks: [
        table(
          "Wie eine Erkennung gezeichnet wird",
          ["Konfidenz", "Darstellung"],
          [
            ["Unter `--conf`", "Wird nicht gezeichnet."],
            [
              "Ab `--conf`, unter `--reject`",
              "Bernsteinfarbene Box mit der Beschriftung `uncertain` und der Konfidenz.",
            ],
            ["Ab `--reject`", "Grüne Box mit Klasse und Konfidenz."],
          ],
        ),
        p(
          "Beide Schwellenwerte stehen standardmäßig auf 0.25, daher wird standardmäßig nichts als unsicher beschriftet. Setzen Sie `--reject` über `--conf`, um die mittlere Stufe zu nutzen. Das Dashboard verhält sich anders: Es verwirft Erkennungen unter dem größeren der beiden Schwellenwerte und kennt keine Stufe für unsichere Erkennungen.",
        ),
      ],
    },
    {
      id: "tracking",
      title: "Tracking und Überspringen von Bildern",
      blocks: [
        p(
          "Für `.pt`-Modelle führt MIRA das Ultralytics-Tracking mit den ByteTrack-Einstellungen aus `bytetrack.yaml` aus, damit Objekte zwischen Bildern ihre ID behalten. Das Live-Fenster zeichnet die IDs nicht, das Dashboard sendet sie als `track_id`. Bei jedem TFLite-Modell ist das Tracking abgeschaltet.",
        ),
        p(
          "Nach jedem Bild bildet MIRA den Mittelwert der Inferenzzeit über die letzten 30 Bilder. Überschreitet er `--target-latency`, wird das nächste Kamerabild übersprungen. Beim Standardwert von 1000 ms passiert das fast nie, auf langsamer Hardware können Sie ihn senken. Die Statuszeile zeigt `Skip: ON` oder `Skip: OFF`.",
        ),
      ],
    },
    {
      id: "problems",
      title: "Wenn es nicht startet",
      blocks: [
        list([
          "`Failed to open USB camera index N`: Ein anderes Programm belegt die Kamera, oder der Index stimmt nicht. Probieren Sie `--camera 1`.",
          "`Camera N disconnected or frozen`: 30 Lesezugriffe in Folge sind fehlgeschlagen. Prüfen Sie das Kabel und verbinden Sie die Kamera neu.",
          "`Model '...' not found`: Die Fehlermeldung listet die verfügbaren Namen auf. Führen Sie `mira models` aus.",
          "`is a classifier model, not a detector`: Wählen Sie einen Detektor.",
        ]),
      ],
    },
  ],
};

const datasets: DocPage = {
  slug: "datasets",
  title: "Datensätze vorbereiten",
  group: "guides",
  summary: "Registrierte Datensatzquellen auflisten, zu einem YOLO-Datensatz zusammenführen und das Ergebnis prüfen.",
  lead: "Datensatzdateien liegen nicht in Git, und die Registry-Dateien und Zusammenführungs-Befehle sind im GitHub-Repository und nicht im PyPI-Paket. Arbeiten Sie in einem Klon.",
  sections: [
    {
      id: "registry",
      title: "Registrierte Quellen",
      blocks: [
        code("mira datasets"),
        p(
          "Der Befehl liest `datasets/registry/*.yaml` und gibt für jede Quelle Schlüssel, Name, Format und die Information aus, ob ihr Ordner existiert. Jede Registry-Datei hält fest, wo die Daten liegen, wie ihre Splits aufgebaut sind und, bei Quellen mit eigenen Labels, eine Zuordnung zu den fünf MIRA-Klassen.",
        ),
        table(
          "Quellenschlüssel in datasets/registry",
          ["Schlüssel", "Format", "Erwarteter Ordner"],
          [
            ["`garbage_detection`", "YOLO", "`datasets/raw/garbage_detection`"],
            ["`recycle_trash`", "COCO", "`datasets/raw/recycle_trash`"],
            ["`roboflow`", "YOLO, auf fünf Klassen abgebildet", "`datasets/roboflow_raw`"],
            ["`trashnet`", "YOLO, mit SAM beschriftet", "`datasets/trashnet_labeled`"],
            ["`warp`", "YOLO", "`datasets/mira_warp`"],
          ],
        ),
      ],
    },
    {
      id: "merge",
      title: "Zusammenführen",
      blocks: [
        code(
          lines(
            "mira merge --sources roboflow trashnet --output datasets/mira_merged --dry-run",
            "mira merge --sources roboflow trashnet --output datasets/mira_merged",
          ),
        ),
        p(
          "`--dry-run` zeigt, was zusammengeführt würde, ohne zu kopieren. Der Ausgabeordner muss im Projektverzeichnis liegen. Quellen, deren Labels andere Klassen-IDs nutzen, werden auf die fünf MIRA-Klassen umgemappt, und ein Bild wird übersprungen, wenn keines seiner Labels zu einer Klasse passt. Die Splits `valid` und `test` werden nach `val` geschrieben, und aus einer Quelle mit nur einem Train-Split werden 20 % als Validierungsdaten abgetrennt.",
        ),
        p(
          "Das Ergebnis sind `images/train`, `images/val`, `labels/train`, `labels/val` und eine `dataset.yaml`. Der Befehl gibt aus, wie viele Bilder hinzugefügt und übersprungen wurden. Eigene Daten im YOLO-Format fügen Sie mit `--custom PATH` hinzu.",
        ),
      ],
    },
    {
      id: "validate",
      title: "Prüfen",
      blocks: [
        code("mira validate --dataset datasets/mira_merged"),
        p(
          "Der Validator prüft für jeden Split die Ordner `images/` und `labels/` und meldet verwaiste Labels und Bilder, Klassen-IDs außerhalb des Klassenbereichs, Koordinaten außerhalb von 0 bis 1 und Boxen ohne Größe. Er gibt die Klassenverteilung aus und beendet sich mit Status 1, wenn der Datensatz ungültig ist.",
        ),
      ],
    },
    {
      id: "origins",
      title: "Woher die Daten stammen",
      blocks: [
        p(
          "Der endgültige, ausbalancierte Datensatz wurde mit `scripts/build_balanced_dataset.py` gebaut und nach `datasets/merged_mira_balanced` geschrieben. Er verwendet vier Quellen.",
        ),
        table(
          "Quellen des endgültigen ausbalancierten Datensatzes, aus docs/DATASET_ORIGINS.md",
          ["Quelle", "Herkunft", "Hinweise"],
          [
            [
              "dmedhi",
              "[Hugging Face](https://huggingface.co/datasets/dmedhi/garbage-image-classification-detection)",
              "Datensatz für Objekterkennung.",
            ],
            ["TACO", "[GitHub](https://github.com/pedropro/TACO)", "Trash Annotations in Context."],
            [
              "Roboflow Trash Detection",
              "[Roboflow Universe](https://universe.roboflow.com/jerry-jukbu/trash-detection-1fjjc-uqlv1)",
              "Lokaler Export unter CC BY 4.0, 5. Juli 2026.",
            ],
            [
              "TrashNet",
              "[GitHub](https://github.com/garythung/trashnet)",
              "Lokal mit SAM für die Objekterkennung beschriftet.",
            ],
          ],
        ),
        warning(
          "Lizenzen einzeln prüfen",
          "WaRP wurde in früheren Experimenten verwendet und ist im endgültigen Datensatz ausgeschlossen, weil es die Ergebnisse verschlechtert hat. Außerdem ist es nur für Forschungszwecke lizenziert. Lesen Sie vor jeder Weitergabe von Daten die Bedingungen der jeweiligen Quelle. Das Repository dokumentiert die Herkunft und enthält die Datensätze nicht.",
        ),
      ],
    },
  ],
};

const trainEvaluate: DocPage = {
  slug: "train-evaluate",
  title: "Training und Auswertung",
  group: "guides",
  summary: "Einen YOLO-Detektor aus einer Experimentdatei trainieren, dann auswerten und vergleichen.",
  lead: 'Für das Training brauchen Sie einen Klon des Repositorys, einen vorbereiteten Datensatz und für einen GPU-Lauf einen CUDA-Build von PyTorch. Installieren Sie mit `pip install -e ".[train]"`.',
  sections: [
    {
      id: "train",
      title: "Trainieren",
      blocks: [
        code(
          lines(
            "mira train --config experiments/exp014_yolo11n_multidataset.yaml --dry-run",
            "mira train --config experiments/exp014_yolo11n_multidataset.yaml",
            "mira train --model yolo11n.pt --dataset datasets/mira_merged/dataset.yaml --epochs 120 --name exp_local",
          ),
        ),
        p(
          "`--dry-run` prüft die Konfiguration und gibt Modell, Datensatz, Epochen, Batchgröße und Bildgröße aus, ohne zu trainieren. Die Experimentdateien in `experiments/` halten Modell, Datensatz, Bildgröße, Epochen, Batchgröße, Optimierer-Einstellungen und Augmentierung fest.",
        ),
        table(
          "Standardwerte, wenn nichts anderes gesetzt ist",
          ["Einstellung", "Standard"],
          [
            ["Epochen, Batchgröße, Bildgröße", "120, 32, 640"],
            ["Gerät", "`0` (erste GPU). Verwenden Sie `cpu` oder IDs wie `0,1`."],
            ["Name des Laufs", "Ein UTC-Zeitstempel, geschrieben unter `runs/`."],
            ["Datensatz", "Die erste gefundene `datasets/*/dataset.yaml`, wenn `--dataset` fehlt."],
          ],
        ),
        p(
          "Ein Lauf schreibt `runs/<name>/weights/best.pt` und `last.pt` sowie `config.yaml`, `results.json` und `metadata.json`. In einer Experimentdatei bleiben Schlüssel, die `mira train` nicht kennt, etwa `augmentation` und `optimizer`, erhalten und werden an Ultralytics übergeben, soweit es sie akzeptiert. Ein `export`-Block wird von `mira train` ignoriert und nur von `mira generate` verwendet.",
        ),
        warning(
          "Das Basismodell selbst festlegen",
          "Der Standard `training.default_model` ist `mira_exp014.pt`, das Ultralytics nicht über den Namen findet. Mit `--auto` und ohne `--model` wählt MIRA die zuletzt gefundene `.pt`-Datei, und das ist eines seiner eigenen trainierten Gewichte. Übergeben Sie `--model yolo11n.pt`, um vom vortrainierten Basismodell zu starten.",
        ),
        h3("wizard", "Geführte Einrichtung"),
        p(
          "`mira wizard` fragt nach Aufgabe (Detektion oder Klassifikator), Datensatzschlüssel, Basismodell, Epochen, Batchgröße und Exportformaten, zeigt eine Zusammenfassung und ruft dann `mira train` auf. `--auto-start` überspringt die Bestätigung. `mira train --task classifier` trainiert den Klassifikator (MobileNetV2 oder eigenes CNN) auf einem Ordner pro Klasse.",
        ),
      ],
    },
    {
      id: "evaluate",
      title: "Auswerten",
      blocks: [
        code(
          lines(
            "mira eval-yolo --model mira_exp019.pt --data datasets/mira_merged/dataset.yaml",
            "mira benchmark --models mira_exp019.pt mira_exp019_int8_640.tflite --dataset datasets/mira_merged/dataset.yaml --output results/benchmark.json",
          ),
        ),
        p(
          "`mira eval-yolo` führt den Ultralytics-Validator für ein Modell aus dem Modellordner aus, mit 640 px oder der festen Eingabegröße einer TFLite-Datei. `mira benchmark` führt eine eigene Auswertungsschleife aus und gibt für jedes Modell eine Tabelle mit Bildanzahl, Precision, Recall, F1, mAP50 und mittlerer Latenz aus, nach F1 sortiert. `--output` schreibt zusätzlich das vollständige Ergebnis samt Kennzahlen pro Klasse als JSON.",
        ),
        warning(
          "Benchmark-Zahlen sind nicht mit dem mAP50-Hauptwert vergleichbar",
          "`mira benchmark` wertet standardmäßig nur die ersten 100 Bilder des Datensatzes aus (`--max-images`) und nutzt `--conf 0.5`. Die gemessenen 90,58 % mAP50 stammen aus der Ultralytics-Validierung auf dem Validierungsdatensatz mit 415 Bildern. Stellen Sie die beiden Werte nicht nebeneinander.",
        ),
      ],
    },
    {
      id: "scripts",
      title: "Skripte",
      blocks: [
        code(
          lines(
            "python scripts/evaluate.py --model mira_exp019.pt",
            "python scripts/compare.py --models mira_exp018.pt mira_exp019.pt --data datasets/mira_merged/dataset.yaml",
            "python scripts/profile.py --model mira_exp019.pt",
          ),
        ),
        list([
          "`evaluate.py` schreibt Diagramme und Kennzahlen nach `results/eval_<timestamp>/` (`--conf` steht standardmäßig auf 0.25).",
          "`compare.py` braucht mindestens zwei Modelle und kann mit `--output` einen Markdown-Bericht speichern.",
          "`profile.py` misst FPS, Latenz und Speicher über 500 Durchläufe nach 50 Aufwärmläufen. Mit `--iterations`, `--warmup` und `--batch-size` ändern Sie das.",
          "`evaluate.py` und `compare.py` brauchen das Extra `analysis` für matplotlib.",
        ]),
      ],
    },
    {
      id: "cloud",
      title: "In der Cloud trainieren",
      blocks: [
        code(
          lines(
            "mira generate kaggle --config experiments/exp014_yolo11n_multidataset.yaml",
            "mira generate colab --config experiments/exp014_yolo11n_multidataset.yaml",
            "mira generate docker --config experiments/exp014_yolo11n_multidataset.yaml",
          ),
        ),
        p(
          "Die Befehle für Kaggle und Colab schreiben `<name>_kaggle.ipynb` oder `<name>_colab.ipynb` ins aktuelle Verzeichnis. Der Docker-Befehl schreibt einen Ordner `docker_<name>` mit `Dockerfile`, `docker-compose.yml`, `train.py` und `entrypoint.sh`. Mit `--output` wählen Sie einen anderen Pfad. Das Kaggle-Notebook sucht unter `/kaggle/input` nach einem angehängten Datensatz und erwartet darin `images/train` und `images/val`. Die Exportformate kommen aus `export.formats` der Experimentdatei.",
        ),
        p(
          "`docs/EXP020_RUNBOOK.md` beschreibt EXP-020, das die Architektur von EXP-019 behält, aber Roboflow-Daten mit 70 % gewichtet. Führen Sie `py -3 scripts/run_exp020.py --prepare-only` aus, um den Datensatz zu bauen, oder `--train`, um zu bauen, zu trainieren und zu exportieren. Für EXP-020 ist noch kein Ergebnis festgehalten.",
        ),
      ],
    },
  ],
};

const exportEdge: DocPage = {
  slug: "export-edge",
  title: "Export für Edge-Geräte",
  group: "guides",
  summary:
    "Ein PyTorch-Modell nach INT8-TFLite oder ONNX konvertieren und vor dem Einsatz auf einem Edge-Gerät, einem kleinen Rechner wie dem Raspberry Pi, prüfen.",
  sections: [
    {
      id: "export",
      title: "Exportieren",
      blocks: [
        code(
          lines(
            "mira export --model models/detection/mira_exp019.pt --dry-run",
            "mira export --model models/detection/mira_exp019.pt --formats tflite_int8 onnx",
            "mira export --model models/detection/mira_exp019.pt --formats tflite_int8 --dataset datasets/mira_merged/dataset.yaml",
          ),
        ),
        table(
          "Werte für mira export --formats",
          ["Wert", "Ergebnis"],
          [
            ["`tflite_int8`", "TFLite mit INT8-Gewichten (Standard)."],
            ["`tflite_fp32`", "TFLite ohne Quantisierung."],
            ["`onnx`", "ONNX."],
          ],
        ),
        p(
          "`--dataset` verweist auf eine Datensatz-YAML, mit der die INT8-Quantisierung kalibriert wird. `--dry-run` prüft nur, ob das Modell existiert. Der Befehl gibt den Pfad jeder exportierten Datei aus. Unbekannte Formatnamen werden mit einer Warnung übersprungen.",
        ),
      ],
    },
    {
      id: "use",
      title: "Das exportierte Modell verwenden",
      blocks: [
        p(
          "Kopieren Sie die exportierte Datei nach `models/detection/`. Behalten Sie `int8` im Dateinamen: MIRA behandelt eine `.tflite`-Datei als INT8, wenn ihr Name `int8` enthält. Das begrenzt den Konfidenz-Schwellenwert im Dashboard auf 0.25 und markiert die Datei in der Modellliste des Dashboards als empfohlen. TFLite-Modelle haben eine feste Eingabegröße, die `mira live` aus der Datei liest, und das Tracking ist aus.",
        ),
        code("mira live --model mira_exp019_int8_640.tflite"),
        p(
          "Installieren Sie auf einem Raspberry Pi zuerst eine TFLite-Laufzeit. `mira doctor` warnt, wenn ein Pi weder `tflite-runtime` noch TensorFlow hat, und gibt ein vorgeschlagenes Format für den Rechner aus, zum Beispiel `tflite_int8` auf einem Pi mit TFLite-Laufzeit oder `pt`, wenn CUDA verfügbar ist.",
        ),
      ],
    },
    {
      id: "check",
      title: "Das Exportergebnis prüfen",
      blocks: [
        p(
          "Quantisierung (Speichern der Gewichte mit kleineren Zahlen) kostet Genauigkeit. Bei EXP-019 erreichte das PyTorch-Modell mit 640 px 0,906 mAP50 auf dem Validierungsdatensatz, der INT8-TFLite-Export mit 320 px erreichte 0,862. Beide TFLite-Exporte behalten FP32-Tensoren für Ein- und Ausgabe, es sind also kleinere Dateien mit quantisierten Gewichten und keine Modelle mit reiner Ganzzahl-Rechnung.",
        ),
        code(
          "mira benchmark --models mira_exp019.pt mira_exp019_int8_640.tflite mira_exp019_int8_320.tflite --dataset datasets/mira_merged/dataset.yaml",
        ),
        warning(
          "Auf einem Raspberry Pi noch nicht gemessen",
          "Die TFLite-Dateien sind enthalten, aber Latenz und Speicherbedarf auf Raspberry-Pi-Hardware wurden nicht gemessen. Die Modell-Metadaten markieren den Einsatz als ausstehend bis zur Validierung auf der Zielhardware.",
        ),
      ],
    },
  ],
};

const models: DocPage = {
  slug: "models",
  title: "Modelle",
  group: "reference",
  summary: "Die mitgelieferten Detektor-Gewichte, ihre gemessenen Kennzahlen und wie MIRA Modelldateien findet.",
  lead: "Alle Zahlen sind Validierungskennzahlen auf dem Tischaufnahmen-Validierungsdatensatz von TrashNet, keine Genauigkeit beim Sortieren im Praxiseinsatz.",
  sections: [
    {
      id: "bundled",
      title: "Mitgelieferte Detektoren",
      blocks: [
        p(
          `Das PyPI-Paket enthält diese drei Gewichtsdateien, jeweils mit einer Begleitdatei für die Metadaten. Weitere Experiment-Modelle und Exporte gibt es auf [Hugging Face](${HF_URL}). Sie sind optional, nichts in MIRA hängt von dieser Seite ab.`,
        ),
        table(
          "Im Wheel von mira-ai enthaltene Gewichte",
          ["Datei", "Experiment", "mAP50", "mAP50-95"],
          [
            ["`mira_exp014.pt`", "EXP-014, früherer Lauf mit mehreren Datensätzen", "60,7 %", "50,6 %"],
            ["`mira_exp018.pt`", "EXP-018, sauberer ausbalancierter Datensatz", "90,6 %", "82,2 %"],
            ["`mira_exp019.pt`", "EXP-019, Wiederholung von EXP-018", "90,58 %", "82,15 %"],
          ],
        ),
        p(
          "EXP-019 wurde 120 Epochen lang mit 640 px, Batchgröße 32 und AdamW mit einer Lernrate von 0,001 auf einer Tesla T4 in 2,67 Stunden trainiert. Die Präzision liegt bei 87,2 %, die Trefferquote bei 84,6 %. Die Architektur ist YOLO11n mit 2.583.127 Parametern. Der Trainingsdatensatz hat 5.108 Bilder, der Validierungsdatensatz 415.",
        ),
      ],
    },
    {
      id: "classes",
      title: "Klassen",
      blocks: [
        p("Der Detektor sagt fünf Klassen voraus, in dieser Indexreihenfolge."),
        { type: "classes" },
        table(
          "mAP50 von EXP-019 pro Klasse auf den Validierungsdaten",
          ["Klasse", "mAP50"],
          [
            ["glass", "90,8 %"],
            ["metal", "94,8 %"],
            ["paper", "88,7 %"],
            ["plastic", "81,1 %"],
            ["trash", "97,5 %"],
          ],
        ),
        p(
          "Kunststoff (`plastic`) hat mit 64,4 % die niedrigste Trefferquote der fünf Klassen. Der hohe Wert für Restmüll (`trash`) spiegelt die Tischaufnahmen des Validierungsdatensatzes wider und darf nicht als allgemeine Fähigkeit gelesen werden, beliebigen Müll zu erkennen.",
        ),
      ],
    },
    {
      id: "files",
      title: "Dateigrößen und Exporte",
      blocks: [
        table(
          "Dateien von EXP-019 laut Experimentprotokoll",
          ["Datei", "Größe", "Hinweise"],
          [
            ["`mira_exp019.pt`", "5,47 MB", "PyTorch-Gewichte, Eingabe mit 640 px."],
            ["`mira_exp019_int8_640.tflite`", "3,04 MB", "INT8-Gewichte, FP32 für Ein- und Ausgabe."],
            ["`mira_exp019_int8_320.tflite`", "3,02 MB", "Export mit 320 px, 0,862 mAP50 auf den Validierungsdaten."],
            ["`mira_exp019.onnx`", "10,6 MB", "ONNX-Export."],
          ],
        ),
        p(
          "Die TFLite- und ONNX-Dateien sind nicht im Wheel. Erzeugen Sie sie mit [Export für Edge-Geräte](/docs/export-edge) oder laden Sie sie von Hugging Face.",
        ),
      ],
    },
    {
      id: "discovery",
      title: "Wie Modelle gefunden werden",
      blocks: [
        p(
          "`mira models` listet alles auf, was `ModelRegistry` im Modellordner findet, mit Bezeichnung, Typ (`yolo_pt`, `yolo_tflite` oder `yolo_onnx`) und Größe. `mira download` lädt nichts herunter. Es listet die mitgelieferten Modelle auf oder meldet, ob eine genannte Datei verfügbar ist. Wie der Modellordner gewählt wird, steht unter [Konfiguration](/docs/configuration).",
        ),
      ],
    },
  ],
};

const cli: DocPage = {
  slug: "cli",
  title: "CLI-Befehle",
  group: "reference",
  summary: "Jeder Unterbefehl von mira mit seinen Optionen und Standardwerten.",
  lead: "`mira --version` gibt die installierte Version aus, und `mira` allein zeigt die Hilfe. Ein fehlgeschlagener Befehl beendet sich mit Status 1, ein unterbrochener mit 130.",
  sections: [
    {
      id: "live",
      title: "mira live",
      blocks: [
        p("Startet die Echtzeit-Erkennung mit der Webcam. Siehe [Live-Erkennung starten](/docs/live-inference)."),
        code(
          "mira live [--model NAME] [--camera N] [--resolution WxH] [--conf X] [--reject X] [--imgsz N] [--target-latency MS]",
        ),
        table(
          "Optionen",
          ["Option", "Standard", "Beschreibung"],
          [
            ["`--model`", "Auswahl", "Dateiname des Modells."],
            ["`--camera`", "`0`", "Kameraindex."],
            ["`--resolution`", "`640x360`", "`640x360`, `1280x720` oder `1920x1080`."],
            ["`--conf`", "`0.25`", "Schwellenwert für die Konfidenz."],
            ["`--reject`", "`0.25`", "Erkennungen darunter werden als unsicher (`uncertain`) beschriftet."],
            ["`--imgsz`", "`640`", "Inferenzgröße für PyTorch-Modelle."],
            ["`--target-latency`", "`1000`", "Ziel-Latenz in ms."],
          ],
        ),
      ],
    },
    {
      id: "dashboard",
      title: "mira dashboard",
      blocks: [
        p("Startet den Dashboard-Server. Siehe [Dashboard verwenden](/docs/dashboard)."),
        code("mira dashboard [--host ADDRESS] [--port N]"),
        table(
          "Optionen",
          ["Option", "Standard", "Beschreibung"],
          [
            ["`--host`", "`127.0.0.1`", "Adresse, an die der Server bindet."],
            ["`--port`", "`8000`", "Port."],
          ],
        ),
      ],
    },
    {
      id: "models",
      title: "mira models und mira download",
      blocks: [
        p("`mira models` listet die gefundenen Modelldateien auf. Der Befehl hat keine Optionen."),
        p("`mira download` listet die mit der Installation mitgelieferten Modelle auf. Es lädt nichts herunter."),
        code("mira download [NAME] [--list] [--all]"),
        table(
          "Argumente",
          ["Argument", "Beschreibung"],
          [
            [
              "`NAME`",
              "Der Dateiname eines mitgelieferten Modells. Meldet, wo es liegt, oder schlägt fehl, wenn es nicht verfügbar ist.",
            ],
            ["`--list`, `--all`", "Listet die mitgelieferten Modelle auf."],
          ],
        ),
      ],
    },
    {
      id: "datasets",
      title: "mira datasets",
      blocks: [
        p(
          "Listet die Datensatzquellen aus `datasets/registry/*.yaml` auf und zeigt, ob der jeweilige Ordner existiert. Der Befehl hat keine Optionen.",
        ),
      ],
    },
    {
      id: "merge",
      title: "mira merge",
      blocks: [
        p(
          "Führt registrierte Quellen zu einem YOLO-Datensatz zusammen. Siehe [Datensätze vorbereiten](/docs/datasets).",
        ),
        code("mira merge --sources KEY [KEY ...] --output DIR [--custom PATH] [--dry-run]"),
        table(
          "Optionen",
          ["Option", "Standard", "Beschreibung"],
          [
            ["`--sources`", "erforderlich", "Ein oder mehrere Registry-Schlüssel."],
            ["`--output`", "erforderlich", "Ausgabeordner innerhalb des Projektverzeichnisses."],
            ["`--custom`", "keiner", "Zusätzlicher Datensatz im YOLO-Format."],
            ["`--dry-run`", "aus", "Zeigt den Plan, ohne zu kopieren."],
          ],
        ),
      ],
    },
    {
      id: "validate",
      title: "mira validate",
      blocks: [
        p("Prüft einen YOLO-Datensatzordner. Beendet sich mit Status 1, wenn er ungültig ist."),
        code("mira validate --dataset DIR"),
      ],
    },
    {
      id: "train",
      title: "mira train",
      blocks: [
        p("Trainiert einen Detektor oder Klassifikator. Siehe [Training und Auswertung](/docs/train-evaluate)."),
        code(
          "mira train [--config FILE] [--model NAME] [--dataset YAML] [--epochs N] [--batch-size N] [--name NAME] [--device D] [--auto] [--dry-run]",
        ),
        table(
          "Optionen",
          ["Option", "Standard", "Beschreibung"],
          [
            ["`--config`", "keiner", "Experiment-YAML. Andere Optionen überschreiben ihre Werte."],
            [
              "`--model`",
              "Standard aus `mira.yaml`",
              "Name oder Pfad des Basismodells. Verwenden Sie `yolo11n.pt` für einen frischen Lauf.",
            ],
            ["`--dataset`", "automatisch", "Datensatz-YAML. Fällt auf die erste `datasets/*/dataset.yaml` zurück."],
            ["`--epochs`", "`120`", "Trainingsepochen."],
            ["`--batch-size`", "`32`", "Batchgröße."],
            ["`--name`", "Zeitstempel", "Name des Laufs. Nur Buchstaben, Ziffern, Bindestriche und Unterstriche."],
            ["`--device`", "`0`", "`cpu` oder GPU-IDs wie `0` oder `0,1`."],
            ["`--auto`", "aus", "Erkennt die Hardware: GPU mit Batchgröße 32, sonst CPU mit Batchgröße 8."],
            ["`--task`", "`detection`", "`detection` oder `classifier`."],
            ["`--data-dir`", "`data/classes`", "Bildordner für das Klassifikator-Training."],
            ["`--base-model`", "`mobilenetv2`", "`mobilenetv2` oder `custom_cnn`, nur für den Klassifikator."],
            ["`--fine-tune`", "aus", "Feintuning des Klassifikators."],
            ["`--dry-run`", "aus", "Prüft und gibt die Einstellungen aus, dann Ende."],
          ],
        ),
      ],
    },
    {
      id: "wizard",
      title: "mira wizard",
      blocks: [
        p("Interaktive Einrichtung des Trainings, die mit dem Aufruf von `mira train` endet."),
        code("mira wizard [--auto-start]"),
      ],
    },
    {
      id: "eval-yolo",
      title: "mira eval-yolo",
      blocks: [
        p("Führt den Ultralytics-Validator für ein Modell aus."),
        code("mira eval-yolo [--model NAME] [--data YAML]"),
        p("Ohne `--model` öffnet sich die Auswahl. `--data` fällt auf die erste `datasets/*/dataset.yaml` zurück."),
      ],
    },
    {
      id: "benchmark",
      title: "mira benchmark",
      blocks: [
        p("Vergleicht Modelle nach Genauigkeit und Latenz."),
        code("mira benchmark --models NAME [NAME ...] [--dataset YAML] [--conf X] [--max-images N] [--output FILE]"),
        table(
          "Optionen",
          ["Option", "Standard", "Beschreibung"],
          [
            ["`--models`", "erforderlich", "Dateinamen von Modellen aus dem Modellordner."],
            ["`--dataset`", "automatisch", "Datensatz-YAML."],
            ["`--conf`", "`0.5`", "Schwellenwert für die Konfidenz, aus `inference.default_conf`."],
            ["`--max-images`", "`100`", "Anzahl der ausgewerteten Bilder. Mindestens 1."],
            ["`--output`", "keiner", "Schreibt das vollständige Ergebnis als JSON."],
          ],
        ),
      ],
    },
    {
      id: "export",
      title: "mira export",
      blocks: [
        p("Exportiert ein `.pt`-Modell. Siehe [Export für Edge-Geräte](/docs/export-edge)."),
        code("mira export --model PATH [--formats F [F ...]] [--dataset YAML] [--dry-run]"),
        table(
          "Optionen",
          ["Option", "Standard", "Beschreibung"],
          [
            ["`--model`", "erforderlich", "Pfad zur `.pt`-Datei, relativ zum Projektverzeichnis."],
            ["`--formats`", "`tflite_int8`", "`tflite_int8`, `tflite_fp32` oder `onnx`."],
            ["`--dataset`", "keiner", "Datensatz-YAML zur Kalibrierung der INT8-Quantisierung."],
            ["`--dry-run`", "aus", "Prüft nur den Modellpfad."],
          ],
        ),
      ],
    },
    {
      id: "generate",
      title: "mira generate",
      blocks: [
        p("Erzeugt Dateien für das Training in der Cloud aus einer Experiment-YAML."),
        code("mira generate {kaggle|colab|docker} --config FILE [--output PATH] [--project-root DIR]"),
        p(
          "`kaggle` und `colab` schreiben ein Notebook. `docker` schreibt einen Ordner mit Dateien. Ohne Ziel gibt der Befehl seine Hilfe aus.",
        ),
      ],
    },
    {
      id: "experiments",
      title: "mira experiments",
      blocks: [
        p(
          "Listet die YAML-Dateien in `experiments/` mit ihrem `name` oder `model` auf. Der Befehl hat keine Optionen.",
        ),
      ],
    },
    {
      id: "doctor",
      title: "mira doctor und mira config",
      blocks: [
        p(
          "`mira doctor` prüft Konfiguration, Hardware, Umgebung, Modelle und Datensätze. Siehe [Schnellstart](/docs/quickstart).",
        ),
        code("mira config [--validate]"),
        p(
          "`mira config` gibt die wirksame Konfiguration als JSON aus. `--validate` prüft sie und beendet sich bei Fehlern mit Status 1. Siehe [Konfiguration](/docs/configuration).",
        ),
      ],
    },
  ],
};

const dashboardApi: DocPage = {
  slug: "dashboard-api",
  title: "Dashboard-API",
  group: "reference",
  summary: "REST- und WebSocket-Endpunkte des lokalen FastAPI-Dashboards mit den Formen von Anfragen und Nachrichten.",
  lead: "Das Dashboard ist eine FastAPI-App mit dem Titel MIRA Control Center API. FastAPI liefert auf demselben Server außerdem die erzeugte Referenz unter `/docs` und das Schema unter `/openapi.json`. Es gibt keine Authentifizierung.",
  sections: [
    {
      id: "endpoints",
      title: "Endpunkte",
      blocks: [
        {
          type: "endpoints",
          items: [
            { method: "GET", path: "/api/status", text: "Zustand des Streams und Bereitschaft." },
            { method: "GET", path: "/api/models", text: "Modelldateien, die das Dashboard laden kann." },
            {
              method: "POST",
              path: "/api/camera/initialize",
              text: "Öffnet eine Kamera mit den angegebenen Einstellungen.",
            },
            { method: "POST", path: "/api/model/load", text: "Lädt ein Modell mit den angegebenen Schwellenwerten." },
            { method: "POST", path: "/api/stream/start", text: "Startet Aufnahme und Inferenz." },
            { method: "POST", path: "/api/stream/stop", text: "Stoppt den Stream." },
            {
              method: "POST",
              path: "/api/detect/image",
              text: "Erkennt Objekte in einem hochgeladenen Bild, ohne den Sitzungsverlauf zu ändern.",
            },
            {
              method: "GET",
              path: "/api/statistics",
              text: "Klassenzahlen und mittlere Konfidenz für einen letzten Zeitraum.",
            },
            {
              method: "GET",
              path: "/api/metrics/history",
              text: "Letzte Messwerte für FPS, Latenz, CPU und Speicher.",
            },
            { method: "GET", path: "/api/detections/recent", text: "Letzte Erkennungen." },
            { method: "WS", path: "/ws/video", text: "Bilder, Erkennungen, Messwerte und Statusereignisse." },
            {
              method: "WS",
              path: "/ws/control",
              text: "Dieselben Steuerbefehle wie die REST-Endpunkte, dazu Abfragen von Status und Statistik.",
            },
          ],
        },
        p("Der Server liefert die gebaute Oberfläche unter `/` aus, die bisherige Seite unter `/legacy` und Version 1 der API unter `/api/v1`. Siehe [Dashboard-API v1](/docs/api-v1)."),
      ],
    },
    {
      id: "rest",
      title: "REST-Anfragen",
      blocks: [
        h3("status", "Status"),
        p(
          "`GET /api/status` liefert `status` (`idle`, `initializing`, `running`, `paused` oder `error`), `message`, `camera_initialized`, `model_loaded`, `streaming` und einen `timestamp`.",
        ),
        h3("camera-body", "Body der Kamera-Anfrage"),
        table(
          "POST /api/camera/initialize",
          ["Feld", "Standard", "Grenzen"],
          [
            ["`index`", "`0`", "0 oder mehr."],
            ["`width`, `height`", "`640`, `360`", "1 bis 8192."],
            ["`fps`", "`30`", "1 bis 240."],
            ["`autofocus`", "`false`", "Boolean."],
            ["`auto_exposure`", "`true`", "Boolean."],
          ],
        ),
        h3("model-body", "Body der Modell-Anfrage"),
        table(
          "POST /api/model/load",
          ["Feld", "Standard", "Grenzen"],
          [
            ["`name`", "erforderlich", "Ein reiner Dateiname aus dem Modellordner. Pfade werden abgelehnt."],
            ["`conf_threshold`", "`0.25`", "0 bis 1."],
            ["`reject_threshold`", "`0.25`", "0 bis 1."],
            ["`iou_threshold`", "`0.45`", "0 bis 1."],
            ["`enable_tracking`", "`true`", "Wird bei TFLite-Modellen ignoriert."],
            ["`target_latency_ms`", "`1000`", "Größer als 0."],
          ],
        ),
        h3("errors", "Fehler"),
        list([
          "`409` bei Kamera-Initialisierung oder Modell-Laden, während ein Stream läuft. Stoppen Sie ihn zuerst.",
          "`409` bei `stream/start` mit `{ message, missing }`, wobei `missing` `camera` oder `model` nennt.",
          "`500`, wenn sich Kamera oder Modell nicht öffnen lassen oder der Stream nicht starten kann.",
          "`400` für `period` außerhalb von 1 bis 86400 und für `limit` außerhalb von 1 bis 1000.",
        ]),
        h3("queries", "Abfragen"),
        list([
          "`GET /api/statistics?period=60` liefert `statistics` (Beginn und Ende des Zeitraums, `total_detections`, `class_counts`, `avg_confidence`, `average_confidence`) und `period_seconds`.",
          "`GET /api/metrics/history?limit=100` liefert `metrics`, `count` und `timestamp`. Der Server hält höchstens 100 Messwerte.",
          "`GET /api/detections/recent?limit=50` liefert `detections`, `count` und `timestamp`. Der Server hält höchstens 1000 Erkennungen.",
        ]),
      ],
    },
    {
      id: "websockets",
      title: "WebSockets",
      blocks: [
        h3("video", "/ws/video"),
        p(
          "Der Server sendet JSON-Nachrichten und ignoriert alles außer dem Text `ping`, den er mit `pong` beantwortet. Beim Verbinden sendet er eine `status`-Nachricht und dann das neueste Bild, falls eines existiert.",
        ),
        table(
          "Nachrichten von /ws/video",
          ["type", "Felder"],
          [
            ["`status`", "`status`, `message`, `timestamp`"],
            ["`frame`", "`frame_id`, `frame` (JPEG als Base64, Qualität 85), `detections`, `timestamp`"],
            [
              "`metrics`",
              "`fps`, `inference_latency_ms`, `avg_latency_ms`, `cpu_percent`, `memory_percent`, `temperature_celsius`, `detections_per_second`, `skip_frames`, `timestamp`",
            ],
          ],
        ),
        p(
          "Jede Erkennung hat die Form `{ class, confidence, bbox: [x1, y1, x2, y2], track_id, timestamp }`. Die Broadcast-Warteschlange fasst 32 Nachrichten. Ist sie voll, wird das älteste Bild verworfen, damit die Ansicht aktuell bleibt.",
        ),
        h3("control", "/ws/control"),
        p('Senden Sie `{ "command": NAME, "params": { ... } }`.'),
        table(
          "Steuerbefehle",
          ["command", "params", "Antwort"],
          [
            ["`set_camera_config`", "Kamera-Body", "`response`"],
            ["`load_model`", "Modell-Body", "`response`"],
            ["`start_stream`, `stop_stream`", "keine", "`response`"],
            ["`get_status`", "keine", "`status`, mit den Feldern von `/api/status`"],
            ["`get_statistics`", "`{ period }`, Standard 60", "`statistics`"],
          ],
        ),
        p(
          'Eine `response` hat `command`, `success`, `message` und `missing`. Ein unbekannter Befehl liefert `{ type: "error", message }`.',
        ),
      ],
    },
    {
      id: "example",
      title: "Beispiel",
      blocks: [
        p("Starten Sie den Server mit `mira dashboard` und steuern Sie ihn dann ohne zusätzliche Pakete aus Python."),
        code(
          lines(
            "import json",
            "import urllib.request",
            "",
            'BASE = "http://127.0.0.1:8000"',
            "",
            "def post(path, body=None):",
            "    request = urllib.request.Request(",
            "        BASE + path,",
            "        data=json.dumps(body or {}).encode(),",
            '        headers={"Content-Type": "application/json"},',
            '        method="POST",',
            "    )",
            "    with urllib.request.urlopen(request) as response:",
            "        return json.load(response)",
            "",
            'print(post("/api/camera/initialize", {"index": 0}))',
            'print(post("/api/model/load", {"name": "mira_exp014.pt", "conf_threshold": 0.4}))',
            'print(post("/api/stream/start"))',
          ),
          "Python",
        ),
      ],
    },
  ],
};

const limitations: DocPage = {
  slug: "limitations",
  title: "Grenzen",
  group: "reference",
  summary: "Was MIRA noch nicht kann, wo die Modelle versagen und wie weit man den Zahlen trauen kann.",
  lead: "Die Ergebnisse sind Validierungskennzahlen aus einem kontrollierten Aufbau. Sie sind kein Beleg dafür, dass MIRA Müll im Alltag zuverlässig sortiert.",
  sections: [
    {
      id: "models",
      title: "Grenzen der Modelle",
      blocks: [
        list([
          "Die Modelle haben Schwierigkeiten mit zerknülltem Papier, Dosen, die man von der Öffnung her sieht, sich überlappenden Objekten und ungewöhnlichen Aufnahmebedingungen.",
          "Der gemessene mAP50 stammt aus dem Tischaufnahmen-Validierungsdatensatz von TrashNet mit 415 Bildern. EXP-019 hat seinen unabhängigen Test-Split mit 1.375 Bildern nicht ausgewertet.",
          "Die Trefferquote für Kunststoff liegt bei EXP-019 bei 64,4 %, und Restmüll war im Benchmark vom Juli (bildweise, ohne Kamera) die schwächste Klasse früherer Modelle.",
          "Ein kleinerer, saubererer, ausbalancierter Datensatz schlug das bloße Zusammenfügen aller Quellen. Mehr Daten sind nicht automatisch besser.",
        ]),
      ],
    },
    {
      id: "system",
      title: "Grenzen des Systems",
      blocks: [
        list([
          "Der Sortierroboter ist nicht gebaut. MIRA erkennt und beschriftet Objekte, es bewegt nichts.",
          "Latenz und Speicherbedarf auf dem Raspberry Pi und anderen kleinen Geräten wurden nicht gemessen.",
          "Nur USB-Kameras sind mit CLI und Dashboard verbunden.",
          "Das Dashboard hat Unit-Tests, aber keinen festgehaltenen End-to-End-Lauf mit echter Kamera und Browser.",
          "Das Dashboard hat keine Authentifizierung. Lassen Sie es auf `127.0.0.1`, außer Sie vertrauen dem Netzwerk.",
          "Die Dashboard-Oberfläche bringt ihre Schriften und Diagramme mit und stellt keine Anfragen an andere Websites. Der Betrieb ganz ohne Netzwerk wurde nicht getestet.",
          "Python 3.11 und 3.12 sind die vorgesehenen Versionen. Das veröffentlichte Paket verlangt `>=3.11`, das Repository verlangt `>=3.11,<3.13`.",
        ]),
      ],
    },
    {
      id: "tooling",
      title: "Hinweise zu den Werkzeugen",
      blocks: [
        list([
          "`mira live` nimmt seine Standardwerte für Konfidenz und Ablehnung aus Konstanten im Code, nicht aus `mira.yaml`.",
          "`inference.reject_threshold`, `paths.datasets`, `paths.results` und der Block `quantization` in `mira.yaml` werden von keinem Befehl gelesen.",
          "Ein Ordner `models/detection` mit irgendeiner Modelldatei verdeckt die im Paket mitgelieferten Gewichte.",
          "`mira download` listet mitgelieferte Modelle auf und lädt nie etwas herunter.",
        ]),
        p(`Wenn hier etwas falsch oder veraltet ist, eröffnen Sie bitte ein Issue auf [GitHub](${GITHUB_URL}/issues).`),
      ],
    },
  ],
};

export const DE_PAGES: readonly DocPage[] = [
  quickstart,
  configuration,
  architecture,
  dashboard,
  detect,
  sessions,
  exportPage,
  compareBenchmark,
  batchImport,
  analytics,
  sortingArm,
  liveInference,
  datasets,
  trainEvaluate,
  exportEdge,
  models,
  cli,
  dashboardApi,
  apiV1,
  limitations,
  troubleshooting,
  faq,
];
