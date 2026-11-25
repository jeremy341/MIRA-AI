/**
 * Interface strings of the documentation section (sidebar, search, code blocks, index page).
 * Page content lives in en.ts and de.ts next to this file. Same shape in both languages; tsc and
 * docs.parity.test.ts catch a missing key. No em dashes or en dashes.
 */

import type { Locale } from "../config";
import type { DocGroupId } from "./types";

export type DocsUi = {
  groups: Record<DocGroupId, string>;
  /** Sidebar entry for the docs index. */
  overview: string;
  /** Visible name of the section, used as the sidebar and drawer heading. */
  sectionName: string;
  navLabel: string;
  menu: string;
  menuTitle: string;
  closeMenu: string;
  /** Visible text of the drawer's close button (its accessible name is `closeMenu`). */
  close: string;
  onThisPage: string;
  /** Placeholder of the section filter on the Research and Package sidebars. */
  filterSections: string;
  /** Placeholder of the filter at the top of the docs sidebar, and the message when it matches nothing. */
  filterSidebar: string;
  noMatches: string;
  /** Accessible name of the breadcrumb trail, and its first entry. */
  breadcrumbLabel: string;
  breadcrumbHome: string;
  /** Page actions under the title. */
  copyMarkdown: string;
  copiedMarkdown: string;
  copyMarkdownFailed: string;
  editOnGithub: string;
  /** Contains {title}. Accessible name of a group's expand and collapse button. */
  toggleGroup: string;
  /** Label of the primary button in the docs top bar. */
  installCta: string;
  /** Accessible name of the scrollable area around a wide table; the table's own name is its caption. */
  tableScrollLabel: string;
  prevNextLabel: string;
  previous: string;
  next: string;
  /** Contains {title}. */
  anchorLabel: string;
  /** Appended to a page title in the browser tab, e.g. "Quickstart | Docs". */
  metaSuffix: string;
  note: string;
  warning: string;
  terminal: string;
  /** Default label of sample output. */
  outputLabel: string;
  /** Contains {title}. */
  copyCodeLabel: string;
  /** Hint for assistive tech on scrollable tables and code blocks. */
  scrollable: string;
  classesLabel: string;
  endpointsLabel: string;
  search: {
    label: string;
    placeholder: string;
    results: string;
    /** Contains {query}. */
    noResults: string;
    /** Contains {query}. Spoken status line. */
    noResultsStatus: string;
    /** Contains {count}. */
    resultOne: string;
    /** Contains {count}. */
    resultMany: string;
    /** Contains {count}. Used when the list is cut off at the maximum number of results. */
    resultCapped: string;
    /** Examples in the empty-result hint: a flag and two words. */
    hintFlag: string;
    hintWords: string;
    tryHint: string;
  };
  index: {
    browse: string;
    quick: { slug: string; title: string; text: string }[];
    title: string;
    lede: string;
    installLabel: string;
    start: string;
    cli: string;
    pressKey: string;
    toSearch: string;
    issuesLead: string;
    issuesLink: string;
    issuesTail: string;
  };
};

const en: DocsUi = {
  groups: { start: "Get started", dashboard: "Dashboard", guides: "Guides", reference: "Reference", help: "Help" },
  overview: "Overview",
  sectionName: "Documentation",
  navLabel: "Documentation",
  menu: "Contents",
  menuTitle: "Documentation",
  closeMenu: "Close contents",
  close: "Close",
  onThisPage: "On this page",
  filterSections: "Filter sections",
  filterSidebar: "Filter sidebar",
  noMatches: "No page matches.",
  breadcrumbLabel: "Breadcrumb",
  breadcrumbHome: "Docs",
  copyMarkdown: "Copy as Markdown",
  copiedMarkdown: "Copied",
  copyMarkdownFailed: "Could not copy",
  editOnGithub: "Edit on GitHub",
  toggleGroup: "Toggle {title}",
  installCta: "Install",
  tableScrollLabel: "Scrolls sideways on small screens",
  prevNextLabel: "Previous and next pages",
  previous: "Previous",
  next: "Next",
  anchorLabel: "Link to {title}",
  metaSuffix: "Docs",
  note: "Note",
  warning: "Caution",
  terminal: "Terminal",
  outputLabel: "Output",
  copyCodeLabel: "Copy code: {title}",
  scrollable: "scrollable",
  classesLabel: "MIRA classes in index order",
  endpointsLabel: "Endpoints",
  search: {
    label: "Search the documentation",
    placeholder: "Search the docs",
    results: "Search results",
    noResults: "No results for {query}.",
    noResultsStatus: "No results for {query}",
    resultOne: "{count} result",
    resultMany: "{count} results",
    resultCapped: "First {count} results",
    hintFlag: "--conf",
    hintWords: "camera or export",
    tryHint: "Try a flag such as {flag} or a word such as {words}.",
  },
  index: {
    browse: "Browse the docs",
    quick: [
      { slug: "quickstart", title: "Install MIRA", text: "Install from PyPI, check the environment and run the first detection." },
      { slug: "dashboard", title: "Open the dashboard", text: "Detect, record sessions, replay them and export the results." },
      { slug: "train-evaluate", title: "Train a detector", text: "Train from an experiment file, then evaluate and benchmark it." },
      { slug: "dashboard-api", title: "Use the API", text: "Sessions, exports, jobs and live events over HTTP." },
    ],
    title: "Documentation",
    lede: "Guides and reference for the `mira-ai` package. Each command, option and default was checked against the repository code.",
    installLabel: "Install command",
    start: "Start with the quickstart",
    cli: "CLI commands",
    pressKey: "Press",
    toSearch: "to search every page.",
    issuesLead: "Found something wrong or out of date? Open an issue on",
    issuesLink: "GitHub",
    issuesTail: ".",
  },
};

const de: DocsUi = {
  groups: { start: "Einstieg", dashboard: "Dashboard", guides: "Anleitungen", reference: "Referenz", help: "Hilfe" },
  overview: "Übersicht",
  sectionName: "Dokumentation",
  navLabel: "Dokumentation",
  menu: "Inhalt",
  menuTitle: "Dokumentation",
  closeMenu: "Inhaltsverzeichnis schließen",
  close: "Schließen",
  onThisPage: "Auf dieser Seite",
  filterSections: "Abschnitte filtern",
  filterSidebar: "Seitenleiste filtern",
  noMatches: "Keine passende Seite.",
  breadcrumbLabel: "Brotkrumen",
  breadcrumbHome: "Doku",
  copyMarkdown: "Als Markdown kopieren",
  copiedMarkdown: "Kopiert",
  copyMarkdownFailed: "Kopieren nicht möglich",
  editOnGithub: "Auf GitHub bearbeiten",
  toggleGroup: "{title} ein- oder ausklappen",
  installCta: "Installieren",
  tableScrollLabel: "Auf kleinen Bildschirmen seitlich scrollbar",
  prevNextLabel: "Vorherige und nächste Seite",
  previous: "Zurück",
  next: "Weiter",
  anchorLabel: "Link zu {title}",
  metaSuffix: "Doku",
  note: "Hinweis",
  warning: "Warnung",
  terminal: "Terminal",
  outputLabel: "Ausgabe",
  copyCodeLabel: "Code kopieren: {title}",
  scrollable: "scrollbar",
  classesLabel: "Die MIRA-Klassen in Indexreihenfolge",
  endpointsLabel: "Endpunkte",
  search: {
    label: "Dokumentation durchsuchen",
    placeholder: "Doku suchen",
    results: "Suchergebnisse",
    noResults: "Keine Treffer für {query}.",
    noResultsStatus: "Keine Treffer für {query}",
    resultOne: "{count} Treffer",
    resultMany: "{count} Treffer",
    resultCapped: "Die ersten {count} Treffer",
    hintFlag: "--conf",
    hintWords: "Kamera oder Export",
    tryHint: "Versuchen Sie eine Option wie {flag} oder ein Wort wie {words}.",
  },
  index: {
    browse: "Die Doku durchsuchen",
    quick: [
      { slug: "quickstart", title: "MIRA installieren", text: "Von PyPI installieren, die Umgebung prüfen und die erste Erkennung starten." },
      { slug: "dashboard", title: "Das Dashboard öffnen", text: "Erkennen, Sitzungen aufzeichnen, abspielen und die Ergebnisse exportieren." },
      { slug: "train-evaluate", title: "Einen Detektor trainieren", text: "Aus einer Experimentdatei trainieren, dann auswerten und vergleichen." },
      { slug: "dashboard-api", title: "Die API nutzen", text: "Sitzungen, Exporte, Jobs und Live-Ereignisse über HTTP." },
    ],
    title: "Dokumentation",
    lede: "Anleitungen und Referenz zum Paket `mira-ai`. Jeder Befehl, jede Option und jeder Standardwert wurde am Code des Repositorys geprüft.",
    installLabel: "Installationsbefehl",
    start: "Mit dem Schnellstart beginnen",
    cli: "CLI-Befehle",
    pressKey: "Mit",
    toSearch: "durchsuchen Sie alle Seiten.",
    issuesLead: "Etwas falsch oder veraltet? Eröffnen Sie ein Issue auf",
    issuesLink: "GitHub",
    issuesTail: ".",
  },
};

export const DOCS_UI: Record<Locale, DocsUi> = { en, de };
