/**
 * Page lookups for the docs routes. Server components only: this module imports the full text of both
 * languages. Client components use the pure helpers in docs-content.ts and load a search index lazily.
 */

import type { Locale } from "../i18n/config";
import { DOC_GROUPS, DOC_SLUGS, getDocPages, type DocGroupId, type DocPage } from "../i18n/docs";

export { DOC_SLUGS };

export function getDocPage(lang: Locale, slug: string): DocPage | undefined {
  return getDocPages(lang).find((page) => page.slug === slug);
}

export function getPagesByGroup(lang: Locale): { group: DocGroupId; pages: DocPage[] }[] {
  const pages = getDocPages(lang);
  return DOC_GROUPS.map((group) => ({ group, pages: pages.filter((page) => page.group === group) }));
}

/** Previous and next page in reading order. */
export function getNeighbors(lang: Locale, slug: string): { prev?: DocPage; next?: DocPage } {
  const pages = getDocPages(lang);
  const index = pages.findIndex((page) => page.slug === slug);
  if (index === -1) return {};
  return { prev: pages[index - 1], next: pages[index + 1] };
}
