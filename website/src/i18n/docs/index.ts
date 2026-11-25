import type { Locale } from "../config";
import { DE_PAGES } from "./de";
import { EN_PAGES } from "./en";
import { DOCS_UI, type DocsUi } from "./ui";
import type { DocGroupId, DocPage } from "./types";

export type { DocBlock, DocGroupId, DocPage, DocSection } from "./types";
export type { DocsUi } from "./ui";

/** Order of the groups in the sidebar and on the docs index. */
export const DOC_GROUPS: readonly DocGroupId[] = ["start", "dashboard", "guides", "reference", "help"];

const PAGES: Record<Locale, readonly DocPage[]> = { en: EN_PAGES, de: DE_PAGES };

/** Pages in reading order for one language. Server side only: it pulls in the whole text of the language. */
export function getDocPages(lang: Locale): readonly DocPage[] {
  return PAGES[lang];
}

export function getDocsUi(lang: Locale): DocsUi {
  return DOCS_UI[lang];
}

/** Slugs are the same in both languages (the parity test enforces it). */
export const DOC_SLUGS: readonly string[] = EN_PAGES.map((page) => page.slug);
