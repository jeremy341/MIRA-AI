import type { Dictionary } from "./en";

/**
 * Deutsche Fassung. Muss dieselben Schlüssel wie en.ts haben (der Typ `Dictionary` erzwingt das).
 * Gleiche Inline-Auszeichnung wie in en.ts: ==Marker==, `Code`, [Text](Link).
 * Zahlen im deutschen Format (Komma als Dezimalzeichen, Leerzeichen vor dem Prozentzeichen).
 * Keine Gedankenstriche.
 */
export const de: Dictionary = {
  meta: {
    siteName: "MIRA",
    title: "MIRA: Machine Intelligence for Recycling Automation",
    description:
      "MIRA ist ein Open-Source-Modell, das Glas, Metall, Papier, Kunststoff und Restmüll in Kamerabildern erkennt. Ein Projekt von einem Schüler für Jugend forscht 2027, mit Experimenten, ehrlichen Grenzen und dem Python-Paket mira-ai.",
    ogTagline: "Ein Müll-Detektor, mit seinen Zahlen und seinen Grenzen",
    pages: {
      research: {
        title: "Forschung",
        description:
          "Alle MIRA-Experimente mit Zahlen, Datensätzen, Diagrammen und Grenzen. Nur Validierungsergebnisse, keine Genauigkeit im Praxiseinsatz behauptet.",
      },
      package: {
        title: "Paket",
        description:
          "Das Python-Paket mira-ai: Installation, mitgelieferte Modelle, Live-Erkennung per Webcam, Dashboard und Befehlsübersicht.",
      },
      docs: {
        title: "Dokumentation",
        description:
          "Anleitungen und Referenz zum Paket mira-ai: Installation, Live-Erkennung, Dashboard, Datensätze, Training, Export, CLI-Befehle und Dashboard-API.",
      },
    },
  },
  common: {
    skipToContent: "Zum Hauptinhalt springen",
    opensInNewTab: "(öffnet in einem neuen Tab)",
    figure: "Abbildung",
    table: "Tabelle",
    languageLabel: "Sprache",
    languageNames: { en: "English", de: "Deutsch" },
    switchTo: "Wechseln zu {language}",
    copy: {
      copy: "Kopieren",
      copied: "Kopiert",
      failed: "Fehler",
      labelFor: "Kopieren: {command}",
      copiedMessage: "In die Zwischenablage kopiert",
      failedMessage: "Kopieren fehlgeschlagen, bitte den Befehl markieren und von Hand kopieren",
    },
    classes: {
      glass: "Glas",
      metal: "Metall",
      paper: "Papier",
      plastic: "Kunststoff",
      trash: "Restmüll",
    },
  },
  nav: {
    label: "Hauptnavigation",
    home: "Start",
    research: "Forschung",
    package: "Paket",
    docs: "Doku",
    github: "GitHub",
  },
  header: {
    homeLabel: "MIRA, Startseite",
  },
  footer: {
    blurb: "Machine Intelligence for Recycling Automation. Ein Projekt von einem Schüler für Jugend forscht 2027.",
    pagesTitle: "Seiten",
    projectTitle: "Anderswo",
    licence: "MIT-Lizenz.",
    github: "GitHub",
    pypi: "PyPI",
    huggingface: "Hugging Face",
  },
  redirect: {
    title: "MIRA",
    message: "Sprache wählen",
    note: "Sie werden zur bevorzugten Sprache Ihres Browsers weitergeleitet.",
  },
  figures: {
    boxesToggle: "Erkennungsrahmen",
    boxesOn: "an",
    boxesOff: "aus",
    altPrefix: "Foto mit den Erkennungen des Modells.",
    altNone: "Keine Erkennungen.",
    altListIntro: "Erkennungen:",
    altItem: "{cls}, Konfidenz {conf}",
    placeholderTitle: "Erkennungsfoto noch nicht verfügbar",
    placeholderHint: "Erwartete Datei: {file}",
    unitConfidence: "Konfidenz",
  },
  home: {
    hero: {
      title: "Abfallerkennung mit MIRA",
      lede: "MIRA markiert Glas, Metall, Papier, Kunststoff und Restmüll in einem Kamerabild.",
      copyLabel: "Installationsbefehl kopieren",
      tryCta: "Jetzt starten",
      resultsCta: "Ergebnisse ansehen",
      benchmark:
        "EXP-019 auf {count} TrashNet-Validierungsbildern unter Tischbedingungen. Keine Aussage über die Genauigkeit im Praxiseinsatz.",
      benchmarkLink: "Benchmark und seine Grenzen",
    },
    problem: {
      title: "Das Problem und was ich versucht habe",
      p1: "Müll von Hand zu trennen ist langsam, und eine Maschine kann nur sortieren, was sie vorher erkennt. Deshalb habe ich mit dem Teil angefangen, der zuerst funktionieren muss: einem Modell, das ein Kamerabild ansieht und sagt, was darauf zu sehen ist.",
      note: "Langfristig soll ein Roboterarm sortieren, was die Kamera sieht. Diese Seite betrifft nur den Erkennungsschritt.",
      p2: "Ich habe nicht mit YOLO angefangen. Zuerst habe ich ein eigenes CNN gebaut, um das Klassifikationsproblem zu verstehen, dann MobileNetV2 getestet, dann YOLOv8n und schließlich YOLO11n, das einen Rahmen um jedes gefundene Objekt zeichnet.",
      triedLabel: "Modelle, die ich getestet habe, der Reihe nach",
      tried: [
        { name: "Eigenes CNN", text: "Klassifikation, ein Label pro Bild. Zum Verstehen des Problems." },
        { name: "MobileNetV2", text: "Klassifikation mit Transfer Learning." },
        { name: "YOLOv8n", text: "Erkennung: Rahmen um mehrere Objekte." },
        { name: "YOLO11n", text: "Erkennung. Das Modell hinter allen Ergebnissen unten." },
      ],
      p3: "Außerdem habe ich mehrere Datensätze ausprobiert, darunter dmedhi, TACO, TrashNet und Roboflow-Daten zur Müllerkennung. Ich dachte, mehr Daten machen das Modell besser. Das stimmte nicht. Manche größeren Mischungen enthielten uneinheitliche Bildstile, Labels und Anordnungen der Objekte. WaRP habe ich wieder entfernt, weil es die Ergebnisse verschlechtert hat und nur für Forschung lizenziert ist.",
    },
    evidence: {
      title: "Die Ergebnisse",
      subtitle: "Sauberere Daten waren besser als mehr Daten.",
      p1: "Die Basis mit zusammengeführten Daten, EXP-014, erreichte 60,7 % mAP50. Nachdem ich die Daten bereinigt und ausbalanciert hatte, kam YOLO11n in EXP-018 auf 90,6 %, und bei der Wiederholung als EXP-019 auf 90,58 %.",
      mapNote:
        "mAP50 bewertet, wie gut die vorhergesagten Rahmen zu den markierten passen (mindestens 50 % Überlappung), gemittelt über alle Klassen. 100 % wäre perfekt.",
      statValue: "==90,58 %==",
      statLabel: "mAP50, EXP-019, auf dem Validierungsdatensatz mit 415 Bildern",
      chartCaption:
        "mAP50 von EXP-014, EXP-018 und EXP-019, jeweils auf dem eigenen Validierungsdatensatz (Fotos, die nicht zum Training gehören und nur zur Bewertung dienen).",
      chartAria: "Balkendiagramm der mAP50: EXP-014 60,7 %, EXP-018 90,6 %, EXP-019 90,58 %.",
      chartRows: [
        { id: "EXP-014", note: "zusammengeführte Quellen" },
        { id: "EXP-018", note: "bereinigt und ausbalanciert" },
        { id: "EXP-019", note: "Wiederholung von EXP-018" },
      ],
      tableCaption: "EXP-018 und EXP-019 pro Klasse, Validierungsdatensatz mit 415 Bildern.",
      tableAll: "EXP-019, alle Klassen",
      tableColumns: { cls: "Klasse", precision: "Präzision", recall: "Trefferquote", map50: "mAP50" },
      plasticNote:
        "Kunststoff ist die schwache Klasse. Die Trefferquote sagt, wie viele der tatsächlich vorhandenen Kunststoff-Objekte das Modell findet.",
      plastic:
        "Die Schwachstelle ist Kunststoff. Das Modell findet nur 64,4 % der Kunststoff-Objekte (Trefferquote), etwa jedes dritte wird übersehen. Die Präzision liegt bei 87,4 %: Wenn es Kunststoff sagt, stimmt das meistens.",
      caveatTitle: "Was die Zahlen nicht zeigen",
      caveat:
        "Alle diese Zahlen stammen von Validierungsbildern, nicht von einer echten Kamera über einem echten Mülleimer. Sie sagen nichts über die Genauigkeit im Praxiseinsatz. EXP-014 und EXP-018 wurden auf verschiedenen Validierungsdatensätzen bewertet (1.588 gemischte Bilder gegenüber 415 TrashNet-Tischbildern). Der Sprung von 60,7 % auf 90,6 % vergleicht also zwei Ansätze und nicht zwei Modelle auf denselben Daten. Den unabhängigen Testdatensatz mit 1.375 Bildern habe ich für EXP-019 nicht ausgewertet, und MIRA wurde noch nicht mit einer echten Kamera evaluiert.",
    },
    landscape: {
      title: "Alle Experimente im Überblick",
      lede: "Alle 19 dokumentierten Experimente in einem 3D-Säulendiagramm. Die Höhe jeder Säule entspricht dem protokollierten Wert.",
      ledeFlat: "Alle 19 dokumentierten Experimente als Balken. Die Länge jedes Balkens entspricht dem protokollierten Wert.",
      note: "Keine Rangliste: Die Läufe wurden auf verschiedenen Validierungsdatensätzen bewertet, die Höhen sind deshalb protokollierte Werte und nicht eins zu eins vergleichbar.",
      caption: "EXP-014, EXP-018 und EXP-019 sind hervorgehoben: Das sind die drei Modelle, die im Paket enthalten sind.",
      hint: "Zum Drehen ziehen. Mit den Pfeiltasten springt der Fokus von Säule zu Säule.",
      hintFlat: "Auf diesem Bildschirm als flache Balken dargestellt.",
      resetView: "Ansicht zurücksetzen",
      legendLabel: "Legende",
      stageA: "Stufe A: Klassifikatoren",
      stageB: "Stufe B: Detektoren",
      metricA: "Validierungsgenauigkeit",
      metricB: "mAP50",
      noScore: "kein Wert protokolliert",
      noScoreShort: "kein Wert",
      axisTick: "{n} %",
      highlighted: "im Paket enthalten",
      chartLabel: "Werte der Experimente",
      tableSummary: "Als Tabelle anzeigen",
      tableCaption: "Alle 19 Experimente mit dem Wert, den das Protokoll verzeichnet",
      columns: {
        experiment: "Experiment",
        stage: "Stufe",
        metric: "Kennzahl",
        value: "Wert",
        split: "Validierungsdatensatz",
      },
      stageNames: { A: "A, Klassifikator", B: "B, Detektor" },
      images: "{n} Bilder",
      splits: {
        "Validation split, size not recorded in the log": "Validierungsdatensatz, Größe nicht protokolliert",
        "Mixed, wild-heavy validation data": "Gemischte Validierungsdaten, überwiegend im Freien",
        "Diverse outdoor validation set": "Vielfältiger Validierungsdatensatz im Freien",
        "Own mixed validation split": "Eigener gemischter Validierungsdatensatz",
        "TrashNet tabletop validation split": "TrashNet-Validierungsdatensatz unter Tischbedingungen",
        "Not evaluated, size only": "Nicht ausgewertet, nur Dateigröße",
      },
      models: {
        "EXP-001": "Eigenes CNN",
        "EXP-002": "MobileNetV2, eingefrorene Basis",
        "EXP-003": "MobileNetV2, feinabgestimmt",
        "EXP-004": "MobileNetV2, INT8-Export von EXP-003",
        "EXP-005": "YOLOv8n, erster Detektor",
        "EXP-006": "YOLOv8n, mit Roboflow-Daten",
        "EXP-007": "YOLOv8n, INT8-Export von EXP-006",
        "EXP-008": "YOLOv8n, bereinigte Labels",
        "EXP-009": "YOLOv8n, nur TrashNet",
        "EXP-010": "YOLOv8n, INT8-Export von EXP-006",
        "EXP-011": "YOLOv8n, nur TACO",
        "EXP-012": "YOLOv8n, INT8-Export von EXP-011",
        "EXP-013": "YOLO11n, TACO und TrashNet",
        "EXP-014": "YOLO11n, TACO, TrashNet und Roboflow",
        "EXP-015": "YOLO11n, TACO, TrashNet und WaRP",
        "EXP-016": "YOLO11n, nur WaRP",
        "EXP-017": "YOLO11n, vier Quellen zusammengeführt",
        "EXP-018": "YOLO11n, bereinigte, ausbalancierte Daten",
        "EXP-019": "YOLO11n, Wiederholung von EXP-018",
      },
    },
    stats: {
      experiments: "dokumentierte Experimente",
      classes: "Abfallklassen",
    },
    tryit: {
      title: "Ausprobieren",
      p1: "Das Paket enthält schon die Gewichte von EXP-014, EXP-018 und EXP-019. Es muss nichts weiter heruntergeladen werden.",
      steps: [
        { label: "Installieren", command: "pip install mira-ai" },
        { label: "Mitgelieferte Modelle auflisten", command: "mira models" },
        { label: "Live-Erkennung mit der Webcam starten", command: "mira live --model mira_exp014.pt" },
        { label: "Lokales Dashboard öffnen", command: "mira dashboard" },
      ],
      defaultNote:
        "EXP-014 ist das Standardmodell für die Live-Demo. Ich habe es nach seinem Verhalten in der Live-Demo gewählt, nicht nach seinem mAP50-Wert.",
      video: {
        title: "MIRA-Demo: Live-Erkennung per Webcam mit mira live",
        videoCaption: "Live-Erkennung per Webcam mit `mira live`.",
        unsupported: "Dieser Browser kann das Video nicht abspielen.",
        playLabel: "Video abspielen",
        privacyNote: "Das Video wird erst beim Abspielen von YouTube (youtube-nocookie.com) geladen.",
      },
      downloadsTitle: "Downloads auf Hugging Face",
      downloadsAllTime: "insgesamt",
      downloadsLast30: "{n} in den letzten 30 Tagen",
      downloadsHonest:
        "Gezählt werden Dateiabrufe aus dem Modell-Repository auf Hugging Face, nicht einzelne Personen. PyPI-Installationen sind nicht enthalten.",
      status: {
        checking: "wird geprüft",
        live: "live",
        cached: "zwischengespeichert",
        fallback: "eingebauter Wert",
        checkingLong: "Hugging Face wird nach dem aktuellen Stand gefragt. Angezeigt wird der zuletzt bekannte Wert.",
        liveLong: "Live-Zahl, gerade eben von Hugging Face abgerufen.",
        cachedLong:
          "Zwischengespeicherte Zahl. Hugging Face war nicht erreichbar, deshalb ist das der zuletzt bekannte Wert.",
        fallbackLong:
          "Eingebaute Zahl. Hugging Face war nicht erreichbar und es war kein früherer Wert gespeichert, deshalb ist das die Zahl, die in der Seite steht.",
      },
    },
    status: {
      title: "Was funktioniert, was offen ist, wer es gemacht hat",
      worksTitle: "Was funktioniert",
      works: [
        "Erkennt Glas, Metall, Papier, Kunststoff und Restmüll in Bildern und live per Webcam.",
        "Erreicht 90,58 % mAP50 auf dem Validierungsdatensatz mit 415 Bildern, in einem zweiten Lauf bestätigt (EXP-018, EXP-019).",
        "Läuft über die Kommandozeile, mit lokalem Dashboard sowie Werkzeugen für Datensätze und Auswertung.",
        "Exportiert nach ONNX und TFLite.",
      ],
      openTitle: "Was offen ist",
      open: [
        "Evaluation mit einer echten Kamera. Noch nicht gemacht.",
        "Der Testdatensatz mit 1.375 Bildern für EXP-019. Nicht ausgewertet.",
        "Trefferquote bei Kunststoff: 64,4 %. Schwach.",
        "Geschwindigkeit auf kleiner Hardware wie dem Raspberry Pi. Nicht gemessen.",
        "Der Sortierroboter. Nicht gebaut.",
        "Bekannte Schwächen: zerknülltes Papier, Dosen mit Blick auf die Öffnung, sich überlappende Objekte und ungewöhnliche Bildbedingungen.",
      ],
      planned:
        "EXP-020 ist geplant und noch nicht gelaufen. Es nutzt dieselben Einstellungen wie EXP-019, gewichtet aber Roboflow-Bilder am stärksten (70 % Roboflow, 20 % TACO, 5 % dmedhi, 5 % TrashNet). Ergebnisse gibt es noch nicht.",
      whoTitle: "Wer es gemacht hat",
      who: "MIRA ist ein Ein-Personen-Projekt. Ich habe es allein für Jugend forscht 2027 umgesetzt.",
      transparency:
        "Für Teile der Programmierung und der Fehlersuche habe ich KI-Werkzeuge benutzt. Die Wahl des Problems, die Datensatz-Experimente, die Modellvergleiche und die Entscheidungen darüber, was funktioniert hat und was nicht, sind meine eigene Projektarbeit.",
      licence: "MIT-Lizenz.",
      linksTitle: "Wo alles liegt",
      links: {
        github: { name: "GitHub", text: "Quellcode, Tests und CI." },
        pypi: { name: "PyPI", text: "Neueste Version: {version}." },
        huggingface: {
          name: "Hugging Face",
          text: "Die meisten Experiment-Modelle von EXP-006 bis EXP-019 und die Klassifikatoren.",
        },
        datasets: { name: "Herkunft der Datensätze", text: "Woher jeder Trainingsdatensatz stammt, mit Lizenzen." },
        log: { name: "Experiment-Protokoll", text: "Alle Experimente mit Einstellungen und Einschränkungen." },
      },
    },
  },
};
