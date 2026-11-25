/**
 * Pure parts of the docs search box, kept out of the component so they can be unit tested:
 * the shortcut check, wrap-around arrow navigation, the spoken status line and the hint split.
 */

import type { DocsUi } from "$i18n/docs/ui";
import { fmt } from "$i18n/format";
import { isResultCapped } from "$lib/docs-content";

export const MIN_QUERY_LENGTH = 2;

export type SearchLabels = DocsUi["search"];

type KeyLike = { key: string; code?: string; altKey: boolean; ctrlKey: boolean; metaKey: boolean };

/**
 * Alt + "/" focuses the search. It is a chord, so it never fires while someone types (WCAG 2.1.4).
 * `code` covers layouts where "/" needs Shift (German) and macOS, where Option + "/" produces another character.
 */
export function isSearchShortcut(event: KeyLike): boolean {
  // Ctrl+K or Cmd+K, the shortcut people know from other docs sites.
  if ((event.ctrlKey || event.metaKey) && !event.altKey && event.key.toLowerCase() === "k") return true;
  // Alt+/ stays as the second chord (it also works on layouts where Ctrl+K is taken).
  if (!event.altKey || event.ctrlKey || event.metaKey) return false;
  return event.key === "/" || event.code === "Slash";
}

/** Next active index with wrap-around. `delta` is +1 (ArrowDown) or -1 (ArrowUp). */
export function moveActive(current: number, delta: 1 | -1, length: number): number {
  if (length === 0) return 0;
  return (current + delta + length) % length;
}

/** The text of the polite live region: empty until the index is loaded and the query is long enough. */
export function searchStatus(labels: SearchLabels, query: string, count: number, ready: boolean): string {
  const trimmed = query.trim();
  if (trimmed.length < MIN_QUERY_LENGTH || !ready) return "";
  if (count === 0) return fmt(labels.noResultsStatus, { query: trimmed });
  const template = isResultCapped(count) ? labels.resultCapped : count === 1 ? labels.resultOne : labels.resultMany;
  return fmt(template, { count });
}

/** `tryHint` holds {flag} and {words}; the component renders the flag as code, so it needs the pieces. */
export function splitTryHint(template: string): { head: string; middle: string; tail: string } {
  const [before, tail = ""] = template.split("{words}");
  const [head, middle = ""] = before.split("{flag}");
  return { head, middle, tail };
}
