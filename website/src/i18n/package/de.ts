import type { PackageCopy } from "./en";

/**
 * Deutsche Fassung der Paket-Seite. Muss dieselben Schlüssel wie en.ts haben (der Typ `PackageCopy` erzwingt das).
 * Gleiche Inline-Auszeichnung wie in en.ts: ==Marker==, `Code`, [Text](Link). Platzhalter wie {version} bleiben gleich.
 * Befehle, Optionen und Dateinamen bleiben englisch. Keine Gedankenstriche.
 */
export const packageDe: PackageCopy = {
  header: {
    title: "Das Paket mira-ai",
    lede: "`mira-ai` ist das quelloffene Python-Paket hinter MIRA: drei trainierte YOLO11n-Detektoren und ein Befehl `mira`, der sie auf Ihrer Webcam ausführt. Es erkennt Glas, Metall, Papier, Kunststoff und Restmüll und zeichnet um jedes Objekt einen Rahmen.",
    installLabel: "Installationsbefehl kopieren",
    installNote: "Das ist schon die ganze Installation. Die Schritte darunter ergänzen eine virtuelle Umgebung.",
    factsLabel: "Eckdaten des Pakets",
    facts: {
      pypi: "Aktuell auf PyPI",
      python: "Python",
      pythonValue: "3.11 oder 3.12",
      pythonNote:
        "PyPI deklariert {requires}. Das Repository begrenzt es auf <3.13, was die Abhängigkeiten unterstützen.",
      licence: "Lizenz",
      bundled: "Im Paket",
      bundledValue: "3 Detektor-Gewichte, kein Modell-Download",
    },
    versionNote:
      "Das Repository steht schon bei {repoVersion}, das ist nicht veröffentlicht. `pip install mira-ai` installiert {version}.",
    contentsLabel: "Auf dieser Seite",
  },
  contents: {
    install: "Installation",
    quickstart: "Schnellstart",
    judged: "Wie eine Erkennung bewertet wird",
    commands: "Befehle",
    models: "Modelle",
    requirements: "Voraussetzungen",
    status: "Stand",
    links: "Links",
  },
  install: {
    title: "Installation",
    p1: "Sie brauchen Python 3.11 oder 3.12 und eine virtuelle Umgebung. Das Paket zieht PyTorch und Ultralytics nach sich, deshalb ist die erste Installation ein großer Download.",
    windows: {
      label: "Windows PowerShell",
      copyLabel: "Installationsbefehle für Windows PowerShell kopieren",
      note: "Diese Befehle stammen aus der README des Projekts und wurden unter Windows PowerShell ausgeführt.",
    },
    unix: {
      label: "macOS und Linux",
      copyLabel: "Installationsbefehle für macOS und Linux kopieren",
      note: "Dieselben Schritte mit dem Unix-Aktivierungsskript. Es sind übliche venv-Befehle, die nicht ausgeführt wurden.",
    },
  },
  quickstart: {
    title: "Schnellstart",
    intro:
      "Führen Sie die Schritte der Reihe nach in der aktivierten Umgebung aus. Bei jedem steht, was Sie sehen sollten.",
    youSee: "Das sollten Sie sehen",
    checkInstall: "Installation prüfen",
    steps: [
      {
        title: "Prüfen, ob die Installation geklappt hat",
        text: "Gibt die Version Ihrer Installation aus.",
        copyLabel: "Versionsbefehl kopieren",
        expected: "Eine Zeile: `MIRA` und die Versionsnummer.",
      },
      {
        title: "Mitgelieferte Modelle auflisten",
        text: "Die Gewichte liegen im Paket, deshalb wird hier nur aufgelistet. Es wird nichts heruntergeladen.",
        copyLabel: "Befehl zum Auflisten der Modelle kopieren",
        expected:
          "Eine Liste mit der Überschrift „Models bundled with mira-ai“ und `mira_exp014.pt`, `mira_exp018.pt` und `mira_exp019.pt`, danach „No model download is required.“",
      },
      {
        title: "Umgebung prüfen",
        text: "Führt fünf Prüfungen aus und endet mit einer Statuszeile.",
        copyLabel: "Doctor-Befehl kopieren",
        expected:
          "Abschnitte zu Konfiguration, Hardware, Umgebung, Modellen und Datensätzen, am Ende `Status: HEALTHY`. Eine fehlende GPU oder fehlende Datensatz-Ordner erscheinen als Hinweise und lassen die Prüfung nicht scheitern.",
      },
      {
        title: "Live-Erkennung starten",
        text: "Öffnet Ihre Standardkamera (Index 0) und zeichnet um jedes erkannte Objekt einen Rahmen.",
        copyLabel: "Befehl für die Live-Erkennung kopieren",
        expected:
          "Ein Fenster mit dem Titel „MIRA Real-Time Multi-Object Detection“, mit Rahmen, Klassenname und Konfidenz an jedem erkannten Objekt. Mit `q` schließen Sie es. Für eine zweite Kamera verwenden Sie `--camera 1`.",
      },
    ],
    modelNote:
      "`mira_exp014.pt` ist das Standardmodell der Demo in der README. Verwenden Sie `mira_exp019.pt` für das Modell mit dem höheren Validierungswert, oder lassen Sie `--model` weg und wählen Sie aus einer Liste.",
    dashboard:
      "Für die Browseroberfläche starten Sie `mira dashboard` und öffnen `http://127.0.0.1:8000`. Die noch nicht veröffentlichte Repository-Version erkennt auch Objekte in lokalen JPEG- und PNG-Dateien.",
  },
  judged: {
    title: "Wie eine Erkennung bewertet wird",
    p1: "Jeder Rahmen, den das Modell findet, hat eine Konfidenz zwischen 0 und 1. `mira live` ordnet ihn mit zwei Schwellenwerten, `--conf` und `--reject`, einem von drei Ergebnissen zu.",
    p2: "Ohne Änderung ==sind beide Schwellenwerte 0,25==, das Band „unsicher“ ist also leer. Erhöhen Sie `--reject`, um es zu nutzen:",
    exampleCopyLabel: "Beispiel mit beiden Schwellenwerten kopieren",
    figureCaption:
      "Die drei Ergebnisse für `--conf 0.25 --reject 0.55`. Der Wert 0,55 ist der `reject_threshold` in `mira.yaml` und dient hier als Beispiel. Standard auf der Kommandozeile ist für beide 0,25.",
    scaleLabels: { hidden: "ausgeblendet", uncertain: "unsicher", labelled: "benannt" },
    tiers: [
      { name: "Unter `--conf`", text: "Der Rahmen wird gar nicht gezeichnet." },
      {
        name: "Von `--conf` bis unter `--reject`",
        text: "Der Rahmen wird gezeichnet und mit „uncertain“ und seiner Konfidenz beschriftet, in einer anderen Rahmenfarbe.",
      },
      {
        name: "Bei oder über `--reject`",
        text: "Der Rahmen wird mit Klassenname und Konfidenz gezeichnet, in der Farbe für sichere Erkennungen.",
      },
    ],
  },
  commands: {
    title: "Befehlsübersicht",
    intro:
      "Der Befehl `mira` hat sechzehn Unterbefehle, gelesen aus dem Code. Mit `--help` bekommen Sie bei jedem die vollständige Liste der Optionen. `mira --version` zeigt die installierte Version, `mira` allein die Befehlsliste.",
    columns: { command: "Befehl", does: "Was er macht, und wichtige Optionen (Standardwerte in Klammern)" },
    required: "erforderlich",
    none: "keine Optionen",
    caption: "Die sechzehn Unterbefehle von `mira`, gelesen aus `src/cli`.",
    groups: {
      run: { title: "Ausführen und prüfen", intro: "Diese funktionieren nach einer normalen pip-Installation." },
      develop: {
        title: "Auswertung, Daten und Training",
        intro:
          "Gedacht für einen Projektordner mit `datasets/` und `experiments/`, etwa einen Git-Klon. Aus einer normalen pip-Installation wurden sie nicht ausprobiert.",
      },
    },
    does: {
      live: "Erkennung per Webcam in Echtzeit in einem Fenster. Mit q beenden. Ohne --model öffnet sich eine Auswahlliste.",
      dashboard: "Startet den lokalen Dashboard-Server.",
      models: "Listet die gefundenen Modelldateien mit Bezeichnung, Typ und Größe auf.",
      download: "Listet die mitgelieferten Modelle auf. Es wird nichts heruntergeladen.",
      doctor: "Prüft Konfiguration, Hardware, Bibliotheken, Modelle und Datensatzquellen und gibt einen Status aus.",
      config: "Gibt die gültigen Einstellungen aus mira.yaml aus.",
      evalYolo: "Validiert einen Detektor auf einem YOLO-Datensatz.",
      benchmark: "Vergleicht mehrere Modelle bei Genauigkeit und Latenz.",
      experiments: "Listet die YAML-Dateien der Experimente in experiments/ auf.",
      datasets: "Listet die registrierten Datensatzquellen auf.",
      merge: "Führt registrierte Quellen zu einem YOLO-Datensatz zusammen.",
      validate: "Prüft Aufbau und Labels eines YOLO-Datensatzes.",
      train: "Trainiert einen YOLO-Detektor oder einen Klassifikator.",
      export: "Exportiert ein trainiertes .pt-Modell nach TFLite oder ONNX.",
      wizard: "Interaktive Einrichtung eines Trainings.",
      generate: "Schreibt ein Kaggle- oder Colab-Notebook oder Docker-Dateien für einen Trainingslauf.",
    },
  },
  models: {
    title: "Modelle",
    p1: "Drei Gewichte liegen im Paket: EXP-014, EXP-018 und EXP-019. Die übrigen Dateien in der Tabelle sind optional und kommen von [Hugging Face](https://huggingface.co/Jeremy341/MIRA-AI). Sie sind aufgeführt, weil die Werkzeuge sie lesen können, aber pip installiert sie nicht. Mit `mira models` sehen Sie, was Ihre Installation laden kann.",
    columns: { file: "Datei", format: "Format", size: "Größe", map50: "mAP50", map5095: "mAP50-95" },
    notRecorded: "nicht erfasst",
    groups: { bundled: "Im pip-Paket", separate: "Optionale Dateien auf Hugging Face" },
    notes: {
      exp014: "Standardmodell der Demo in der README. Validiert auf einer anderen Aufteilung mit 1.588 Bildern.",
      exp018: "Saubere, klassenausgewogene Daten.",
      exp019: "Wiederholung von EXP-018 mit demselben Aufbau.",
      exp019Int8320: "Float32-Ein- und -Ausgabe, ganzzahlige Gewichte.",
    },
    tableLabel: "Auf kleinen Bildschirmen seitlich scrollbar",
    caption:
      "Die Detektordateien. mAP50 bewertet, wie gut die vorhergesagten Rahmen zu den markierten passen (mindestens 50 % Überlappung), mAP50-95 nutzt strengere Überlappungen. Beide sind Validierungswerte aus dem Experiment-Protokoll, keine Genauigkeit im Praxiseinsatz. Die Größen sind Dateigrößen in Dezimal-Megabyte.",
    splitNote:
      "EXP-018 und EXP-019 wurden auf denselben 415 Bildern der TrashNet-Tischaufnahmen bewertet. EXP-014 nutzte eine andere Aufteilung mit 1.588 Bildern, sein Wert von 60,7 % ist deshalb mit den anderen nicht vergleichbar.",
  },
  requirements: {
    title: "Voraussetzungen und Extras",
    requirementsTitle: "Voraussetzungen",
    items: {
      python: {
        label: "Python",
        text: "3.11 oder 3.12. PyPI deklariert `>=3.11`, das Repository begrenzt es auf `<3.13`, was die Abhängigkeiten unterstützen, und die CI läuft mit 3.11 und 3.12.",
      },
      camera: { label: "Kamera", text: "Eine Webcam für `mira live`. Die übrigen Befehle brauchen keine." },
      gpu: { label: "GPU", text: "Optional. `mira doctor` meldet, ob CUDA gefunden wird." },
      network: { label: "Netzwerk", text: "Nur für die Installation." },
    },
    extrasTitle: "Extras",
    extras: {
      train: "TensorFlow 2.10 oder neuer, wird von den Trainingsstrategien genutzt.",
      analysis: "matplotlib, pandas, scikit-learn und scipy zur Auswertung von Ergebnissen.",
      all: "Beide Extras von oben.",
      dev: "Alles von oben plus pytest, ruff und mypy, für die Arbeit am Paket selbst.",
    },
    extrasNote: "Ein eigenes Dashboard-Extra gibt es nicht: FastAPI und uvicorn gehören zur Basisinstallation.",
  },
  status: {
    title: "Was funktioniert und was nicht getestet ist",
    intro: "Nichts davon ist eine Aussage über Genauigkeit im Praxiseinsatz.",
    worksTitle: "Heute im Paket",
    works: [
      "Drei Detektor-Gewichte (EXP-014, EXP-018, EXP-019) liegen im Paket. Kein Konto und kein Download der Modelle nötig.",
      "Live-Erkennung per Webcam mit Konfidenz- und Ablehnungsschwelle, die Sie bei jedem Lauf einstellen können.",
      "Ein lokales Dashboard, das auf Ihrem eigenen Rechner läuft. Es ist ein Entwicklungswerkzeug.",
      "Export eines trainierten Modells nach TFLite oder ONNX sowie Werkzeuge, um Datensätze zu bauen, zu prüfen und zu vergleichen.",
    ],
    openTitle: "Nicht getestet oder nicht gebaut",
    open: [
      "Geschwindigkeit und Genauigkeit auf einem Raspberry Pi sind nicht gemessen. Die INT8-TFLite-Datei gibt es, aber keine Zahlen dazu auf dieser Hardware.",
      "Der Roboter oder Sortierarm ist nicht gebaut. Das Paket erkennt Objekte und sortiert nichts.",
      "Es gibt keine Auswertung mit einer echten Kamera. Der Testdatensatz mit 1.375 Bildern wurde für EXP-019 nicht ausgeführt.",
      "Kunststoff ist die schwache Klasse (64,4 % Trefferquote bei EXP-019). Zerknülltes Papier, Dosen mit Blick auf die Öffnung und sich überlappende Objekte sind bekannte Schwächen.",
      "Die Installationsbefehle für macOS und Linux sind übliche venv-Schritte, die nicht ausgeführt wurden.",
      "Das Dashboard hat Unit-Tests, aber eine durchgehende Prüfung mit Kamera und Browser wurde nicht festgehalten, und es wurde nicht aus einem installierten Wheel ausprobiert.",
    ],
  },
  links: {
    title: "Links und Downloads",
    downloads: {
      title: "Downloads auf Hugging Face",
      allTime: "insgesamt",
      last30: "{n} in den letzten 30 Tagen",
      honest:
        "Gezählt werden Dateiabrufe aus dem Modell-Repository auf Hugging Face, nicht einzelne Personen. PyPI-Installationen sind nicht enthalten.",
      status: { checking: "wird geprüft", live: "live", cached: "zwischengespeichert", fallback: "eingebauter Wert" },
      statusLong: {
        checking: "Hugging Face wird nach dem aktuellen Stand gefragt. Angezeigt wird der zuletzt bekannte Wert.",
        live: "Live-Zahl, gerade eben von Hugging Face abgerufen.",
        cached:
          "Zwischengespeicherte Zahl. Hugging Face war nicht erreichbar, deshalb ist das der zuletzt bekannte Wert.",
        fallback:
          "Eingebaute Zahl. Hugging Face war nicht erreichbar und es war kein früherer Wert gespeichert, deshalb ist das die Zahl, die in der Seite steht.",
      },
    },
    listTitle: "Wo alles liegt",
    items: {
      pypi: { name: "PyPI", text: "Neueste Version: {version}." },
      github: { name: "GitHub", text: "Quellcode, Tests, CI und Issues." },
      huggingface: { name: "Hugging Face", text: "Optionale Modelldateien und Exporte." },
      docs: { name: "Dokumentation", text: "Befehle und Konfiguration im Detail." },
      research: { name: "Forschung", text: "Die Experimente hinter den Modellen." },
      licence: { name: "MIT-Lizenz", text: "Frei nutzbar, veränderbar und weitergebbar." },
    },
  },
};
