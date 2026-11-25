/**
 * Deutsche Seiten zum Dashboard (ab Version 1.1.0): Übersicht, je eine Seite pro Bereich, die Referenz der API v1
 * und die Hilfeseiten. Englisches Gegenstück: en-dashboard.ts, gleiche Struktur.
 *
 * Jede Route, jede Grenze und jeder Standardwert wurde an src/dashboard (Backend-Router und UI-Quellcode) und
 * docs/dashboard-v2/CONTRACT.md geprüft. Keine Zahl und kein Feld ohne diese Prüfung ergänzen.
 * Keine Geviert- oder Halbgeviertstriche in Texten.
 */

import { code, lines, list, note, p, table, warning } from "./helpers";
import type { DocPage } from "./types";

export const dashboard: DocPage = {
  slug: "dashboard",
  title: "Das Dashboard",
  group: "dashboard",
  summary: "Das lokale Dashboard starten, sehen, was jede Seite tut, und wo die Daten liegen.",
  lead: "Das Dashboard ist eine lokale Web-App, die `mira dashboard` ausliefert. Es zeichnet Erkennungsläufe als Sitzungen auf, spielt sie ab, exportiert sie, vergleicht Modelle und führt einen kurzen Hardwareverlauf. Kamerabilder und Erkennungen bleiben auf Ihrem Rechner.",
  sections: [
    {
      id: "start",
      title: "Starten",
      blocks: [
        code(lines("mira dashboard", "mira dashboard --port 8080", "mira dashboard --host 0.0.0.0")),
        p("Standard sind `--host 127.0.0.1` und `--port 8000`, die Seite liegt also unter `http://127.0.0.1:8000`."),
        warning(
          "Bindung an 0.0.0.0",
          "`--host 0.0.0.0` macht das Dashboard aus Ihrem Netzwerk erreichbar. Es hat keine Anmeldung, und jeder, der es erreicht, kann Ihre Kamera starten. Behalten Sie den Standard bei, außer Sie brauchen Fernzugriff in einem vertrauenswürdigen Netzwerk.",
        ),
        p(
          "Das Paket von PyPI enthält die fertig gebaute Oberfläche. In einem Quellcode-Checkout muss die Oberfläche einmal gebaut werden (`corepack pnpm install` und `corepack pnpm build` in `src/dashboard/ui`); bis dahin zeigt der Server das bisherige Einzeldatei-Dashboard. Das ist immer unter `/legacy` erreichbar, und `MIRA_DASHBOARD_UI=legacy` macht es zur Seite unter `/`.",
        ),
      ],
    },
    {
      id: "pages",
      title: "Die fünf Seiten",
      blocks: [
        table(
          "Dashboard-Seiten",
          ["Seite", "Was sie tut"],
          [
            ["[Detect](/docs/detect)", "Live-Erkennung von einer Kamera oder eine einzelne Bilddatei. Sitzung starten und stoppen."],
            ["[Sessions](/docs/sessions)", "Jeder aufgezeichnete Lauf, mit Summen, abspielbarer Zeitleiste, Export und Import."],
            ["[Models](/docs/compare-benchmark)", "Zwei bis vier Modelle an einem Bild vergleichen oder einen Benchmark starten."],
            ["[Analytics](/docs/analytics)", "Diagramme zu einer Sitzung, der Hardwareverlauf und das Protokoll des Sortierarms."],
            ["Settings", "Kamera- und Modelleinstellungen. Sie sind gesperrt, solange ein Stream läuft."],
          ],
        ),
      ],
    },
    {
      id: "data",
      title: "Wo die Daten liegen",
      blocks: [
        p(
          "Alles steht in einer SQLite-Datei: Sitzungen, Erkennungen, Metriken, Hardware-Messwerte, Jobs, Vergleiche, Benchmark-Läufe und Arm-Ereignisse. Kamerabilder werden nicht gespeichert, nur die Erkennungen (Klasse, Konfidenz, Box und Track-ID).",
        ),
        table(
          "Umgebungsvariablen",
          ["Variable", "Standard", "Wirkung"],
          [
            ["`MIRA_DASHBOARD_DB`", "`~/.mira/dashboard.db`", "Pfad der SQLite-Datei."],
            ["`MIRA_HARDWARE_INTERVAL`", "`2`", "Sekunden zwischen Hardware-Messwerten (mindestens 0,5)."],
            ["`MIRA_HARDWARE_RETENTION_HOURS`", "`24`", "Wie lange Hardware-Messwerte aufbewahrt werden."],
            ["`MIRA_DASHBOARD_UI`", "nicht gesetzt", "Auf `legacy` setzen, um das bisherige Dashboard unter `/` auszuliefern."],
          ],
        ),
        p(
          "Der Server lauscht auf der Adresse, die Sie angeben, und sendet nichts nach außen. Schriften und Diagramme gehören zur Seite, sie funktioniert also ohne Internetzugang.",
        ),
      ],
    },
  ],
};

export const detect: DocPage = {
  slug: "detect",
  title: "Detect",
  group: "dashboard",
  summary: "Live-Erkennung von einer Kamera ausführen oder ein einzelnes Bild prüfen und den Lauf als Sitzung aufzeichnen.",
  lead: "Detect ist die erste Seite. Sie zeigt die Live-Vorschau mit Boxen, nennt den nächsten Schritt, wenn etwas fehlt, und startet und stoppt Sitzungen.",
  sections: [
    {
      id: "source",
      title: "Kamera oder Bild",
      blocks: [
        p(
          "Der Schalter oben rechts wählt die Quelle. **Connected camera** führt die Live-Erkennung aus. **Image file** prüft ein JPEG oder PNG mit dem geladenen Modell, bis 8 MB und 16 Megapixel. Eine Bildprüfung braucht einen gestoppten Stream, und ihr Ergebnis wird keiner Sitzung hinzugefügt.",
        ),
      ],
    },
    {
      id: "start",
      title: "Einen Stream starten",
      blocks: [
        p(
          "Ein Knopf über der Vorschau zeigt immer den nächsten Schritt: **Connect camera**, **Load model**, **Start stream** und, solange er läuft, **Stop stream**. Kamera und Modell stammen aus den Einstellungen, die Sie auf der Seite Settings angewendet haben. Ist noch kein Modell gewählt, öffnet der Knopf die Einstellungen.",
        ),
        list(
          [
            "Öffnen Sie **Settings**, wählen Sie Kamera und Modell und drücken Sie **Apply settings**.",
            "Gehen Sie zurück zu **Detect** und drücken Sie den Knopf, bis er **Stop stream** zeigt.",
          ],
          true,
        ),
        p(
          "Die API verweigert den Start eines Streams, bis Kamera und Modell bereit sind. Einstellungen sind gesperrt, solange der Stream läuft, drücken Sie also zuerst **Stop stream**.",
        ),
      ],
    },
    {
      id: "preview",
      title: "Die Vorschau",
      blocks: [
        p(
          "Die Vorschau zeichnet für jedes Objekt eine Box und ein Label. **Min. confidence** (0,05 bis 1) blendet Boxen und Listeneinträge unterhalb des gewählten Werts aus. Das ändert nur, was Sie sehen; die Schwellen des Modells stehen in den Einstellungen. Unter der Vorschau zeigt eine Zeile die Bilder pro Sekunde, die Zeit pro Bild und die Zahl der Objekte im Bild.",
        ),
        p("Die Liste **Detections** rechts zeigt die Objekte im aktuellen Bild, mit der höchsten Konfidenz zuerst."),
      ],
    },
    {
      id: "session",
      title: "Eine Sitzung aufzeichnen",
      blocks: [
        p(
          "Die Karte **Session** rechts zeichnet den Lauf auf. Geben Sie einen Namen ein oder lassen Sie das Feld leer, dann heißt die Sitzung `Session YYYY-MM-DD HH:MM`, und drücken Sie **Start session**. Solange der Stream läuft, werden jede Erkennung und ein Metrik-Messwert (Bilder pro Sekunde, Latenz, Prozessor und Speicher) in der Sitzung gespeichert. **Stop session** beendet sie. Es kann immer nur eine Kamera-Sitzung aktiv sein.",
        ),
        p("Der aufgezeichnete Lauf erscheint auf der Seite [Sessions](/docs/sessions)."),
      ],
    },
    {
      id: "behaviour",
      title: "Gut zu wissen",
      blocks: [
        list([
          "Erkennungen unterhalb des größeren Werts von Konfidenz- und Reject-Schwelle werden verworfen, bevor sie gezählt oder aufgezeichnet werden.",
          "Die Standardwerte sind 0,25 Konfidenz, 0,25 Reject, 0,45 IoU, Tracking an und 1000 ms Ziellatenz.",
          "Bei INT8-TFLite-Modellen ist die Konfidenzschwelle auf 0,25 begrenzt, und Tracking ist für jedes TFLite-Modell aus.",
          "Das Tracking nutzt das Paket `lap`, das ab Version 1.1.0 mit `mira-ai` installiert wird.",
        ]),
      ],
    },
  ],
};

export const sessions: DocPage = {
  slug: "sessions",
  title: "Sitzungen und Wiedergabe",
  group: "dashboard",
  summary: "Jeder aufgezeichnete Lauf, seine Summen, eine abspielbare Zeitleiste, Notizen und das Löschen.",
  lead: "Eine Sitzung ist ein Lauf: eine Strecke Live-Erkennung, ein geprüftes Video oder ein Stapel Bilder. Sie behält ihre Erkennungen und Metriken, sodass Sie sie später noch einmal ansehen können.",
  sections: [
    {
      id: "what",
      title: "Was eine Sitzung enthält",
      blocks: [
        table(
          "Felder einer Sitzung",
          ["Feld", "Bedeutung"],
          [
            ["`source`", "`camera`, `image`, `video` oder `batch`."],
            ["`status`", "`active`, solange sie aufzeichnet, danach `completed` oder `failed`."],
            ["`model_name`", "Das Modell, das die Erkennungen erzeugt hat."],
            ["Erkennungen", "Zeit, Bildindex, Klasse, Konfidenz, Box und Track-ID."],
            ["Metriken", "Bilder pro Sekunde, Latenz, Prozessor und Speicher, gemessen während des Laufs."],
          ],
        ),
        p(
          "Kamera-Sitzungen starten Sie auf [Detect](/docs/detect). Video- und Bild-Sitzungen entstehen durch einen [Import](/docs/batch-import).",
        ),
      ],
    },
    {
      id: "list",
      title: "Die Liste",
      blocks: [
        p(
          "Die Seite Sessions listet die Läufe mit den neuesten zuerst. Eine Kamera-Sitzung, die noch aufzeichnet, trägt das Kennzeichen **Live**. **Load more** lädt ältere Läufe nach. Eine noch aktive Sitzung lässt sich nicht löschen, und die Seite nennt den Grund.",
        ),
      ],
    },
    {
      id: "detail",
      title: "Eine Sitzung",
      blocks: [
        p(
          "Eine Sitzungsseite zeigt die Summen, die Aufteilung nach Klassen, die Links zum [Export](/docs/export) und Felder für den Namen und Ihre Notizen. **Delete** fragt nach und entfernt die Sitzung samt Erkennungen und Metriken.",
        ),
      ],
    },
    {
      id: "replay",
      title: "Wiedergabe",
      blocks: [
        p(
          "Die Wiedergabe spielt eine beendete Sitzung auf einer Zeitleiste ab. Die Zeitleiste ist in Zeitabschnitte geteilt, höchstens 240 Spalten breit. Ein Schieberegler springt an jeden beliebigen Punkt. **Play** und **Pause** starten und stoppen sie, die Geschwindigkeit ist 1x (das aufgezeichnete Tempo), 2x oder 4x. Gestapelte Balken zeigen die Klassenverteilung über die Zeit, und die Liste darunter zeigt die Erkennungen im aktuellen Abschnitt. Die Wiedergabe pausiert, wenn der Browser-Tab verborgen ist.",
        ),
        note(
          "Lange Sitzungen",
          "Die Wiedergabe liest Erkennungen in Seiten zu 500, bis zu 5000 Zeilen. Ein Hinweis sagt, wenn eine Sitzung länger ist und die Wiedergabe abgeschnitten wird. Summen und Exporte nutzen immer alle Erkennungen.",
        ),
      ],
    },
  ],
};

export const exportPage: DocPage = {
  slug: "export",
  title: "Export und Berichte",
  group: "dashboard",
  summary: "Eine Sitzung als CSV oder JSON herunterladen oder einen einseitigen Bericht öffnen, der sich als PDF drucken lässt.",
  lead: "Jede Sitzung kann das Dashboard in drei Formen verlassen: als CSV-Datei für Tabellen, als JSON-Datei mit allem und als einseitiger Bericht für eine Ausarbeitung oder ein Poster.",
  sections: [
    {
      id: "csv",
      title: "CSV",
      blocks: [
        p("Eine Zeile pro Erkennung, mit dieser Kopfzeile. Die Datei wird gestreamt, große Sitzungen laden also ohne Wartezeit."),
        code("ts,offset_seconds,frame_index,class_name,confidence,x1,y1,x2,y2,track_id", "CSV-Kopfzeile"),
        p("`offset_seconds` zählt ab dem Start der Sitzung. Die Box ist `x1,y1,x2,y2` in Pixeln des Bildes."),
      ],
    },
    {
      id: "json",
      title: "JSON",
      blocks: [
        p(
          "Die JSON-Datei hat vier Teile: `session`, `class_counts`, `detections` (dieselben Felder wie die CSV) und `metrics` (die Messwerte, die während der Sitzung genommen wurden).",
        ),
      ],
    },
    {
      id: "report",
      title: "Einseitiger Bericht",
      blocks: [
        p(
          "Der Bericht ist eine HTML-Seite mit eigenen Stilen und Diagrammen. Er stellt keine Netzwerkanfragen und öffnet sich daher auch offline, und er ist so gesetzt, dass er beim Drucken auf eine A4-Seite passt. Wählen Sie im Browser **Drucken** und **Als PDF speichern**, um ein PDF zu erhalten.",
        ),
        list([
          "Titel, Sitzungsname, Datum, Modell und Dauer.",
          "Gesamtzahl der Erkennungen und mittlere Konfidenz.",
          "Eine Klassentabelle und ein Balkendiagramm pro Klasse.",
          "Erkennungen über die Zeit.",
          "Ihre Notizen.",
        ]),
        p(
          "Die Fußzeile sagt immer, dass die Zahlen einer Sitzung nur diesen Lauf beschreiben und keine Genauigkeit beim Sortieren in der Praxis sind. Von Ihnen getippter Text wird maskiert, ein Sitzungsname kann die Seite also nicht verändern.",
        ),
      ],
    },
    {
      id: "api",
      title: "Aus einem Skript",
      blocks: [
        code(
          lines(
            "curl -O -J http://127.0.0.1:8000/api/v1/sessions/<id>/export.csv",
            "curl -O -J http://127.0.0.1:8000/api/v1/sessions/<id>/export.json",
            "curl http://127.0.0.1:8000/api/v1/sessions/<id>/report.html",
          ),
        ),
        p(
          "Hängen Sie `?download=1` an die Adresse des Berichts, um ihn als Datei zu erhalten. Die Sitzungs-IDs liefert `GET /api/v1/sessions`; siehe die [API-Referenz](/docs/api-v1).",
        ),
      ],
    },
  ],
};

export const compareBenchmark: DocPage = {
  slug: "compare-benchmark",
  title: "Vergleich und Benchmark",
  group: "dashboard",
  summary: "Zwei bis vier Modelle am selben Bild laufen lassen oder Modelle auf einem Datensatz bewerten.",
  lead: "Die Seite Models hat zwei Tabs. Compare stellt Modelle an einem Bild nebeneinander. Benchmark bewertet Modelle auf einem ganzen Datensatz und nutzt dieselbe Engine wie `mira benchmark`.",
  sections: [
    {
      id: "compare",
      title: "Vergleich",
      blocks: [
        p(
          "Wählen Sie zwei bis vier Modelle und ein JPEG oder PNG (bis 8 MB) und stellen Sie die Konfidenz ein (0,05 bis 1, Standard 0,25). Der Server lässt die Modelle nacheinander auf dem Bild laufen. Für jedes Modell sehen Sie das annotierte Bild, die Zeit in Millisekunden, die Zahl der Objekte, die Klassenzahlen und die mittlere Konfidenz.",
        ),
        p(
          "Ein kurzer Satz nennt das schnellere Modell und das mit mehr Erkennungen. Das ist ein Hinweis und kein Urteil: Ein einzelnes Bild sagt wenig darüber, welches Modell besser ist.",
        ),
        note(
          "Gespeicherte Vergleiche",
          "Frühere Vergleiche werden nur mit ihren Zahlen aufbewahrt. Die Bilder werden nicht gespeichert, und die Seite sagt das, wenn Sie einen wieder öffnen.",
        ),
      ],
    },
    {
      id: "benchmark",
      title: "Benchmark",
      blocks: [
        p(
          "Wählen Sie ein bis sechs Modelle, optional einen Datensatz (eine YOLO-`dataset.yaml` oder einen Ordner, bei leerem Feld der Projektstandard), eine Konfidenz und eine Höchstzahl an Bildern. Der Lauf ist ein Hintergrundjob: Er zeigt seinen Fortschritt, und Sie können ihn abbrechen.",
        ),
        p(
          "Die Ergebnistabelle listet für jedes Modell mAP50, mAP50-95, Precision, Recall, F1 und die mittlere Zeit pro Bild, mit einer Ansicht pro Klasse. Werte, die der Benchmark nicht misst, etwa Bilder pro Sekunde, erscheinen als Strich und nie als Zahl. Fehler, die für ein Modell gemeldet werden, stehen über der Tabelle.",
        ),
        warning(
          "Was die Zahlen bedeuten",
          "Ein Benchmark-Wert wird auf dem gewählten Datensatz gemessen, nicht mit einer echten Kamera über einem echten Mülleimer. Vergleichen Sie nur Werte desselben Datensatzes.",
        ),
      ],
    },
  ],
};

export const batchImport: DocPage = {
  slug: "batch-import",
  title: "Video- und Stapelimport",
  group: "dashboard",
  summary: "Ein Modell über ein Video, mehrere Bilder oder einen Ordner laufen lassen, mit Fortschritt und Abbruch.",
  lead: "Der Import macht aus vorhandenem Material Sitzungen. Ein Video oder ein Haufen Bilder läuft im Hintergrund, während Sie weiterarbeiten, und das Ergebnis ist eine normale Sitzung.",
  sections: [
    {
      id: "video",
      title: "Ein Video",
      blocks: [
        p(
          "Wählen Sie auf der Seite Sessions **Video**. Angenommen werden MP4-, AVI-, MOV- und MKV-Dateien bis 500 MB. Das Modell läuft auf jedem N-ten Bild; **Frame stride** legt N fest (Standard 5, von 1 bis 120). Ein größerer Wert ist schneller und kann Objekte verpassen, die nur kurz im Bild sind. Die Erkennungen werden mit der Zeit ihres Bildes gespeichert, die Wiedergabe passt also zum Video.",
        ),
      ],
    },
    {
      id: "images",
      title: "Bilder oder ein Ordner",
      blocks: [
        p(
          "Wählen Sie Bilddateien (JPEG oder PNG, bis zu 200 auf einmal) oder geben Sie den Pfad eines Ordners auf dem Rechner an, auf dem das Dashboard läuft. Ein Ordnerimport nimmt höchstens 2000 JPEG- oder PNG-Dateien, geht standardmäßig nicht in Unterordner und folgt keinen symbolischen Links. Er legt eine Sitzung mit der Quelle `batch` an.",
        ),
      ],
    },
    {
      id: "jobs",
      title: "Fortschritt und Abbruch",
      blocks: [
        p(
          "Jeder Import ist ein Job. Das Feld zeigt seinen Fortschritt einmal pro Sekunde, und **Cancel** stoppt ihn. Wenn er fertig ist, lädt die Liste neu, und das Feld verlinkt die neue Sitzung. Laden Sie die Seite neu, während ein Job läuft, nimmt die Seite ihn wieder auf.",
        ),
        table(
          "Job-Zustände",
          ["Zustand", "Bedeutung"],
          [
            ["`queued`", "Wartet auf einen freien Worker."],
            ["`running`", "Arbeitet. Der Fortschritt läuft von 0 bis 1."],
            ["`completed`", "Fertig. Die Sitzung ist bereit."],
            ["`failed`", "Durch einen Fehler gestoppt. Die Meldung nennt den Grund."],
            ["`cancelled`", "Sie haben ihn gestoppt."],
          ],
        ),
      ],
    },
  ],
};

export const analytics: DocPage = {
  slug: "analytics",
  title: "Analytics und Hardware",
  group: "dashboard",
  summary: "Diagramme zu einer Sitzung und der Verlauf von Prozessor, Speicher und Temperatur des Rechners.",
  lead: "Analytics hat drei Teile: die Diagramme einer Sitzung, den Zustand des Rechners, auf dem der Detektor läuft, und das Protokoll des Sortierarms.",
  sections: [
    {
      id: "session",
      title: "Sitzungsdiagramme",
      blocks: [
        p(
          "Wählen Sie eine Sitzung. **Objects over time** ist ein Liniendiagramm, wie viele Objekte im Bild waren, und die **Klassenverteilung** listet, wie viele von jeder Klasse gefunden wurden. Jedes Diagramm hat einen Knopf **Show data table**, der seine Zahlen als Text auflistet.",
        ),
      ],
    },
    {
      id: "hardware",
      title: "Hardware",
      blocks: [
        p(
          "Vier Kacheln zeigen die aktuelle Prozessorlast, Speichernutzung, Temperatur und die Last der letzten Minute. Sie werden alle 5 Sekunden aktualisiert. Darunter zeigt ein Diagramm den Verlauf über 15 Minuten, 1 Stunde, 6 Stunden oder 24 Stunden. Der Verlauf wird im Hintergrund gemessen, solange das Dashboard läuft, und 24 Stunden aufbewahrt.",
        ),
        p(
          "Die Temperatur kommt aus der ersten Quelle, die der Rechner bietet: den Sensoren des Betriebssystems, `/sys/class/thermal/thermal_zone0/temp` oder `vcgencmd measure_temp` auf einem Raspberry Pi. Gibt es keine, wie auf vielen Windows-Rechnern, steht auf der Kachel **No temperature sensor**, und das Diagramm wird durch diese Meldung ersetzt.",
        ),
      ],
    },
    {
      id: "arm",
      title: "Sortierarm",
      blocks: [
        p("Das letzte Feld gehört dem [Sortierarm](/docs/sorting-arm): sein Zustand, eine Genauigkeitszahl und das Ereignisprotokoll."),
      ],
    },
  ],
};

export const sortingArm: DocPage = {
  slug: "sorting-arm",
  title: "Sortierarm",
  group: "dashboard",
  summary: "Die Platzhalter-Schnittstelle für den künftigen Sortierroboter, sein Ereignisprotokoll und die Rückmeldung.",
  lead: "Den Sortierroboter gibt es noch nicht. Dieser Teil des Dashboards ist der Ort, an dem er später angeschlossen wird, damit die Software drumherum schon gebaut und getestet werden kann.",
  sections: [
    {
      id: "simulated",
      title: "Nur simuliert",
      blocks: [
        warning(
          "Kein Roboter verbunden",
          "Nichts in diesem Teil des Dashboards spricht mit Hardware. Der Status meldet immer `connected: false` und `mode: simulated`, und die Seite zeigt den Hinweis **No robot connected. Commands are simulated.**",
        ),
        p(
          "Ein Befehl ist `sort` (mit einer Klasse), `home` oder `stop`. Der Simulator schreibt ein Ereignis `sort_requested` und einen Moment später ein Ereignis `sort_completed`. Unbekannte Klassen werden abgelehnt.",
        ),
      ],
    },
    {
      id: "log",
      title: "Ereignisprotokoll und Rückmeldung",
      blocks: [
        p(
          "Wählen Sie auf Analytics eine Klasse und drücken Sie **Send simulated sort**, um es auszuprobieren. Das Protokoll listet jedes Ereignis. Bei einem Ereignis `sort_completed` können Sie das Ergebnis als **correct** oder **incorrect** markieren. Die Genauigkeit ist der Anteil richtiger Antworten an den gegebenen Antworten, und sie zeigt **No feedback yet**, bis es eine gibt.",
        ),
        p(
          "Dieselbe Zahl füllt `sorting_accuracy` in `GET /api/statistics`. Weil der Arm simuliert ist, misst sie Ihre Klicks und keinen Roboter, und sie ist keine Genauigkeit beim Sortieren in der Praxis.",
        ),
      ],
    },
    {
      id: "driver",
      title: "Für einen echten Arm später",
      blocks: [
        p(
          "Der Simulator liegt hinter einer Schnittstelle `ArmDriver` mit einer Methode, `send(command)`. Ein Treiber für echte Hardware kann `SimulatedArm` ersetzen, ohne die API oder die Seiten zu ändern.",
        ),
      ],
    },
  ],
};

export const apiV1: DocPage = {
  slug: "api-v1",
  title: "Dashboard-API v1",
  group: "reference",
  summary: "Die Endpunkte unter /api/v1 für Sitzungen, Exporte, Vergleich, Benchmark, Stapel, Jobs, Hardware und den Arm.",
  lead: "Version 1 der API liegt unter `/api/v1` neben den älteren Routen, die die Seite [Dashboard-API](/docs/dashboard-api) beschreibt. Sie spricht JSON mit snake_case-Namen. Zeiten in Nutzdaten sind ISO 8601 in UTC. Es gibt keine Authentifizierung.",
  sections: [
    {
      id: "conventions",
      title: "Konventionen",
      blocks: [
        table(
          "Fehlercodes",
          ["Code", "Bedeutung"],
          [
            ["`404`", "Unbekannte ID."],
            ["`409`", "Falscher Zustand, zum Beispiel beim Löschen einer aktiven Sitzung."],
            ["`413`", "Datei zu groß."],
            ["`415`", "Falscher Dateityp."],
            ["`422`", "Ungültige Eingabe."],
          ],
        ),
        p(
          "Fehler sind `{\"detail\": \"...\"}` mit einem Satz, den Sie einer Person zeigen können. Die Klassennamen sind immer `glass`, `metal`, `paper`, `plastic` und `trash`.",
        ),
      ],
    },
    {
      id: "sessions",
      title: "Sitzungen und Exporte",
      blocks: [
        {
          type: "endpoints",
          items: [
            { method: "POST", path: "/api/v1/sessions", text: "Eine Sitzung starten: name, source, model_name. Nur eine Kamera-Sitzung kann aktiv sein." },
            { method: "POST", path: "/api/v1/sessions/{id}/stop", text: "Eine Sitzung beenden." },
            { method: "GET", path: "/api/v1/sessions", text: "Sitzungen auflisten: limit, offset, status." },
            { method: "GET", path: "/api/v1/sessions/{id}", text: "Eine Sitzung mit Konfiguration und Notizen." },
            { method: "PATCH", path: "/api/v1/sessions/{id}", text: "Name oder Notizen ändern." },
            { method: "DELETE", path: "/api/v1/sessions/{id}", text: "Eine Sitzung mit Erkennungen und Metriken löschen (409, wenn aktiv)." },
            { method: "GET", path: "/api/v1/sessions/{id}/detections", text: "Erkennungen: limit, offset, class_name, min_confidence." },
            { method: "GET", path: "/api/v1/sessions/{id}/timeline", text: "Abschnitte für die Wiedergabe: bucket_seconds." },
            { method: "GET", path: "/api/v1/sessions/{id}/export.csv", text: "CSV-Download." },
            { method: "GET", path: "/api/v1/sessions/{id}/export.json", text: "JSON-Download." },
            { method: "GET", path: "/api/v1/sessions/{id}/report.html", text: "Einseitiger Bericht; mit ?download=1 als Datei." },
          ],
        },
      ],
    },
    {
      id: "models",
      title: "Vergleich und Benchmark",
      blocks: [
        {
          type: "endpoints",
          items: [
            { method: "POST", path: "/api/v1/compare", text: "Multipart: image, models (2 bis 4 Namen, kommagetrennt), confidence." },
            { method: "GET", path: "/api/v1/compare", text: "Frühere Vergleiche ohne Bilder." },
            { method: "GET", path: "/api/v1/compare/{id}", text: "Ein Vergleich." },
            { method: "DELETE", path: "/api/v1/compare/{id}", text: "Einen Vergleich löschen." },
            { method: "POST", path: "/api/v1/benchmark/runs", text: "Einen Benchmark starten: models, dataset, confidence, max_images. Liefert run_id und job_id." },
            { method: "GET", path: "/api/v1/benchmark/runs", text: "Frühere Läufe." },
            { method: "GET", path: "/api/v1/benchmark/runs/{id}", text: "Ein Lauf mit seinen Ergebnissen." },
            { method: "DELETE", path: "/api/v1/benchmark/runs/{id}", text: "Einen Lauf löschen." },
          ],
        },
      ],
    },
    {
      id: "jobs",
      title: "Stapel und Jobs",
      blocks: [
        {
          type: "endpoints",
          items: [
            { method: "POST", path: "/api/v1/batch/video", text: "Multipart: video, model_name, confidence, frame_stride, name. Liefert job_id und session_id." },
            { method: "POST", path: "/api/v1/batch/images", text: "Multipart-Bilder oder JSON mit einem Verzeichnis. Liefert job_id und session_id." },
            { method: "GET", path: "/api/v1/jobs", text: "Letzte Jobs." },
            { method: "GET", path: "/api/v1/jobs/{id}", text: "Ein Job: status, progress, message, result, error." },
            { method: "POST", path: "/api/v1/jobs/{id}/cancel", text: "Einen Job abbrechen (409, sobald er fertig ist)." },
          ],
        },
        p("Das Starten eines Jobs antwortet mit `202`. Fragen Sie den Job ab oder hören Sie den Ereignis-Socket unten."),
      ],
    },
    {
      id: "hardware",
      title: "Hardware und Arm",
      blocks: [
        {
          type: "endpoints",
          items: [
            { method: "GET", path: "/api/v1/hardware/current", text: "Prozessor, Speicher, Temperatur, Last, Plattform und Kernzahl." },
            { method: "GET", path: "/api/v1/hardware/history", text: "Gemittelte Punkte: minutes, points." },
            { method: "GET", path: "/api/v1/arm/status", text: "Immer simuliert: connected, mode, state, accuracy." },
            { method: "POST", path: "/api/v1/arm/commands", text: "Einen simulierten Befehl senden: sort, home oder stop." },
            { method: "GET", path: "/api/v1/arm/events", text: "Das Ereignisprotokoll: limit, kind." },
            { method: "POST", path: "/api/v1/arm/events/{id}/feedback", text: "Ein abgeschlossenes Sortieren als richtig oder falsch markieren." },
            { method: "GET", path: "/api/v1/arm/accuracy", text: "Richtige, Gesamtzahl und die Genauigkeit." },
          ],
        },
      ],
    },
    {
      id: "events",
      title: "Ereignis-Socket",
      blocks: [
        {
          type: "endpoints",
          items: [{ method: "WS", path: "/ws/v1/events", text: "Live-Ereignisse zu Jobs, Sitzungen, Arm und Hardware." }],
        },
        p(
          "Beim Verbinden sendet der Server `{\"type\": \"hello\", \"ts\": ..., \"data\": {\"version\": 1}}`, danach jedes Ereignis als `{\"type\", \"ts\", \"data\"}`. Die Typen sind `session_started`, `session_stopped`, `job_progress`, `job_finished`, `arm_event`, `hardware_sample` und `detection_batch`. Alle 20 Sekunden kommt ein `ping`. Ein langsamer Client verliert Ereignisse und bremst den Server nie.",
        ),
      ],
    },
  ],
};

export const troubleshooting: DocPage = {
  slug: "troubleshooting",
  title: "Fehlersuche",
  group: "help",
  summary: "Häufige Probleme mit dem Dashboard und was man dagegen tut.",
  lead: "Wenn etwas nicht funktioniert, suchen Sie unten das Symptom. Steht es nicht da, eröffnen Sie ein Issue auf GitHub und beschreiben Sie, was Sie gesehen haben.",
  sections: [
    {
      id: "dashboard",
      title: "Das Dashboard",
      blocks: [
        table(
          "Probleme und Lösungen",
          ["Was Sie sehen", "Warum, und was zu tun ist"],
          [
            [
              "Das alte Dashboard öffnet sich statt des neuen",
              "Die neue Oberfläche ist nicht gebaut. Eine PyPI-Installation enthält sie. In einem Quellcode-Checkout führen Sie `corepack pnpm install` und `corepack pnpm build` in `src/dashboard/ui` aus und starten dann neu.",
            ],
            ["Die Seite öffnet sich nicht", "Prüfen Sie Adresse und Port. Starten Sie auf einem anderen Port mit `mira dashboard --port 8080`, wenn 8000 belegt ist."],
            [
              "Start stream tut nichts, oder der Knopf verlangt einen Schritt",
              "Zuerst werden Kamera und Modell gebraucht. Folgen Sie dem Knopf auf [Detect](/docs/detect): erst die Kamera verbinden, dann das Modell laden.",
            ],
            ["Einstellungen lassen sich nicht ändern", "Sie sind gesperrt, solange der Stream läuft. Drücken Sie zuerst **Stop stream**."],
            ["Ein Bild wird abgelehnt", "Angenommen werden nur JPEG und PNG bis 8 MB und 16 Megapixel, und der Stream muss gestoppt sein."],
            ["Eine Sitzung lässt sich nicht löschen", "Sie ist noch aktiv. Beenden Sie sie zuerst."],
            ["Die Wiedergabe endet früh", "Ein Hinweis sagt es: Die Wiedergabe liest bis zu 5000 Erkennungen. Die Exporte enthalten alle."],
            ["Keine Temperatur in Analytics", "Der Rechner meldet keinen Sensor. Das ist auf vielen Windows-Rechnern normal."],
          ],
        ),
      ],
    },
    {
      id: "imports",
      title: "Importe",
      blocks: [
        list([
          "Ein Video wird abgelehnt: Nutzen Sie MP4, AVI, MOV oder MKV und bleiben Sie unter 500 MB.",
          "Ein Ordnerimport findet nichts: Der Ordner muss auf dem Rechner existieren, auf dem das Dashboard läuft, und es werden nur JPEG- und PNG-Dateien direkt darin genutzt.",
          "Ein Import hängt scheinbar: Ein langes Video mit Stride 1 braucht lange. Erhöhen Sie den Stride oder drücken Sie **Cancel**.",
        ]),
      ],
    },
  ],
};

export const faq: DocPage = {
  slug: "faq",
  title: "FAQ",
  group: "help",
  summary: "Kurze Antworten zu Datenschutz, Genauigkeit, Hardware und dazu, wo etwas liegt.",
  lead: "Kurze Antworten auf Fragen, die oft gestellt werden.",
  sections: [
    {
      id: "privacy",
      title: "Sendet es meine Daten irgendwohin?",
      blocks: [
        p(
          "Nein. Das Dashboard läuft auf Ihrem Rechner und lauscht auf `127.0.0.1`, solange Sie das nicht ändern. Erkennungen liegen in einer lokalen SQLite-Datei, Bilder werden nicht gespeichert. Die Seiten laden keine Schriften oder Skripte von anderen Websites.",
        ),
      ],
    },
    {
      id: "accuracy",
      title: "Wie genau ist es?",
      blocks: [
        p(
          "Der Hauptwert, 90,58 % mAP50, wurde auf 415 Validierungsfotos gemessen, nicht mit einer echten Kamera. Siehe den [Forschungsbericht](/research) und die [Einschränkungen](/docs/limitations). Die eigenen Zahlen des Dashboards beschreiben einen Lauf und sind keine Genauigkeit beim Sortieren in der Praxis.",
        ),
      ],
    },
    {
      id: "robot",
      title: "Kann es einen Roboter steuern?",
      blocks: [
        p(
          "Noch nicht. Der Roboter ist nicht gebaut. Die Schnittstelle des [Sortierarms](/docs/sorting-arm) ist eine Simulation, die es gibt, damit die Software vorbereitet werden kann.",
        ),
      ],
    },
    {
      id: "location",
      title: "Wo liegen meine Daten, und wie setze ich sie zurück?",
      blocks: [
        p(
          "In `~/.mira/dashboard.db` oder in der Datei, die `MIRA_DASHBOARD_DB` nennt. Beenden Sie das Dashboard und löschen Sie die Datei, um mit leerem Verlauf zu beginnen.",
        ),
      ],
    },
    {
      id: "update",
      title: "Wie aktualisiere ich?",
      blocks: [
        code("python -m pip install --upgrade mira-ai"),
        p("Der Verlauf bleibt erhalten. Neue Versionen ergänzen Tabellen in derselben Datei und lassen Ihre Sitzungen in Ruhe."),
      ],
    },
  ],
};
