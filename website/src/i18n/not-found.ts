import type { Locale } from "./config";

export type NotFoundCopy = {
  title: string;
  text: string;
  /** Link back to the Home page of that language. */
  home: string;
};

/**
 * Copy of the 404 pages. Kept apart from the dictionaries on purpose: the global 404 shows BOTH languages
 * at once and the per-language 404 is a client component, so neither should pull a whole dictionary in.
 * No em dashes or en dashes.
 */
export const NOT_FOUND_COPY: Record<Locale, NotFoundCopy> = {
  en: {
    title: "Page not found",
    text: "This page does not exist or has moved. The home page links to everything that is here.",
    home: "Go to the home page",
  },
  de: {
    title: "Seite nicht gefunden",
    text: "Diese Seite gibt es nicht oder sie wurde verschoben. Von der Startseite aus erreichen Sie alles, was es hier gibt.",
    home: "Zur Startseite",
  },
};
