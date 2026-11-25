/**
 * Pure helpers for the /docs section: inline markup, paths and client-side search.
 *
 * The content itself lives in `src/i18n/docs/{en,de}.ts` (typed data, no JSX). This module does not
 * import it, so client components can use it without bundling the text of both languages. Server
 * components get pages from `docs-content-pages.ts`; the search loads one language lazily
 * (`loadSearchIndex`).
 *
 * Inline markup inside text strings: `code`, **bold**, [label](href).
 */

import type { Locale } from "../i18n/config";
import type { DocBlock, DocGroupId, DocPage } from "../i18n/docs/types";

export type { DocBlock, DocGroupId, DocPage, DocSection } from "../i18n/docs/types";

/* ------------------------------------------------------------------ */
/* Inline markup                                                       */
/* ------------------------------------------------------------------ */

export type InlineToken =
  | { type: "text"; value: string }
  | { type: "code"; value: string }
  | { type: "bold"; value: string }
  | { type: "link"; label: string; href: string };

const INLINE_PATTERN = /`([^`]+)`|\*\*([^*]+)\*\*|\[([^\]]+)\]\(([^)\s]+)\)/g;

/** Split a text string into text, code, bold and link tokens. */
export function parseInline(source: string): InlineToken[] {
  const tokens: InlineToken[] = [];
  let cursor = 0;
  for (const match of source.matchAll(INLINE_PATTERN)) {
    const start = match.index ?? 0;
    if (start > cursor) tokens.push({ type: "text", value: source.slice(cursor, start) });
    if (match[1] !== undefined) tokens.push({ type: "code", value: match[1] });
    else if (match[2] !== undefined) tokens.push({ type: "bold", value: match[2] });
    else tokens.push({ type: "link", label: match[3], href: match[4] });
    cursor = start + match[0].length;
  }
  if (cursor < source.length) tokens.push({ type: "text", value: source.slice(cursor) });
  return tokens;
}

/** Plain text of an inline string, markup removed. Used by search. */
export function stripInline(source: string): string {
  return parseInline(source)
    .map((token) => (token.type === "link" ? token.label : token.value))
    .join("");
}

/* ------------------------------------------------------------------ */
/* Paths                                                               */
/* ------------------------------------------------------------------ */

/** Path without a language prefix. Add the prefix with `localePath(lang, docPath(...))`. */
export function docPath(slug: string, sectionId?: string): string {
  return sectionId ? `/docs/${slug}#${sectionId}` : `/docs/${slug}`;
}

/** Page slug for a pathname without language such as `/docs/cli` or `/docs/cli/`. Undefined for the docs index. */
export function slugFromPathname(pathname: string): string | undefined {
  const match = /^\/docs\/([^/]+)\/?$/.exec(pathname);
  return match ? match[1] : undefined;
}

/* ------------------------------------------------------------------ */
/* Search                                                              */
/* ------------------------------------------------------------------ */

export type SearchEntry = {
  /** Path without language prefix, with section hash. */
  href: string;
  slug: string;
  pageTitle: string;
  group: DocGroupId;
  kind: "page" | "section";
  /** Section title, or the page title for page entries. */
  heading: string;
  /** Sub-headings (h3) inside the section. */
  subheadings: string;
  /** Plain text of the section body, used for matching and snippets. */
  body: string;
};

export type SearchResult = {
  entry: SearchEntry;
  score: number;
  /** Text around the first body match, or the start of the body. */
  snippet: string;
  /** Character range of the match inside `snippet`, or null. */
  matchRange: [number, number] | null;
};

function blockText(block: DocBlock): { body: string; sub: string } {
  switch (block.type) {
    case "p":
      return { body: stripInline(block.text), sub: "" };
    case "h3":
      return { body: "", sub: block.text };
    case "code":
      return { body: block.code, sub: "" };
    case "list":
      return { body: block.items.map(stripInline).join(" "), sub: "" };
    case "callout":
      return { body: `${block.title} ${stripInline(block.text)}`, sub: "" };
    case "table":
      return {
        body: [block.caption, ...block.head, ...block.rows.flat()].map(stripInline).join(" "),
        sub: "",
      };
    case "endpoints":
      return { body: block.items.map((item) => `${item.method} ${item.path} ${item.text}`).join(" "), sub: "" };
    case "flow":
      return { body: block.steps.map((step) => `${step.title} ${step.detail}`).join(" "), sub: "" };
    case "classes":
      return { body: "glass metal paper plastic trash", sub: "" };
  }
}

/** One entry per page (title, summary, lead) and one per section. Text is that of the pages passed in, i.e. one language. */
export function buildSearchIndex(pages: readonly DocPage[]): SearchEntry[] {
  const entries: SearchEntry[] = [];
  for (const page of pages) {
    entries.push({
      href: docPath(page.slug),
      slug: page.slug,
      pageTitle: page.title,
      group: page.group,
      kind: "page",
      heading: page.title,
      subheadings: page.sections.map((section) => section.title).join(" "),
      body: [page.summary, page.lead ? stripInline(page.lead) : ""].join(" ").trim(),
    });
    for (const section of page.sections) {
      const parts = section.blocks.map(blockText);
      entries.push({
        href: docPath(page.slug, section.id),
        slug: page.slug,
        pageTitle: page.title,
        group: page.group,
        kind: "section",
        heading: section.title,
        subheadings: parts
          .map((part) => part.sub)
          .filter(Boolean)
          .join(" "),
        body: parts
          .map((part) => part.body)
          .filter(Boolean)
          .join(" "),
      });
    }
  }
  return entries;
}

const searchIndexCache = new Map<Locale, Promise<SearchEntry[]>>();

/** Build (once) and cache the search index of one language. Loads that language's text on demand. */
export function loadSearchIndex(lang: Locale): Promise<SearchEntry[]> {
  let cached = searchIndexCache.get(lang);
  if (!cached) {
    cached = (
      lang === "de"
        ? import("../i18n/docs/de").then((module) => module.DE_PAGES)
        : import("../i18n/docs/en").then((module) => module.EN_PAGES)
    ).then(buildSearchIndex);
    searchIndexCache.set(lang, cached);
  }
  return cached;
}

/* ------------------------------------------------------------------ */
/* Folding: lower case, no diacritics, ss for the sharp s              */
/* ------------------------------------------------------------------ */

type Folded = { text: string; /** For every folded character, the index of its source character. */ map: number[] };

/**
 * Case and diacritic folding that keeps a map back to the original text, so a match can be marked in
 * the unfolded snippet. "Größe" becomes "grosse", "über" becomes "uber", "Café" becomes "cafe".
 */
export function fold(value: string): Folded {
  let text = "";
  const map: number[] = [];
  for (let index = 0; index < value.length; index += 1) {
    const char = value[index];
    const folded = char === "ß" || char === "ẞ" ? "ss" : char.normalize("NFD").replace(/\p{M}/gu, "").toLowerCase();
    for (const piece of folded) {
      text += piece;
      map.push(index);
    }
  }
  return { text, map };
}

/** Plain folded string, for queries. */
export function foldText(value: string): string {
  return fold(value).text;
}

/**
 * Spellings of a typed term that should match the same text. People without umlaut keys write "ae",
 * "oe", "ue" for "ä", "ö", "ü"; the index folds those to "a", "o", "u", so the alternative drops the e.
 */
function termVariants(term: string): string[] {
  const variants = new Set([term]);
  const transliterated = term.replace(/([aou])e/g, "$1");
  if (transliterated !== term) variants.add(transliterated);
  return [...variants];
}

function isWordStart(haystack: string, term: string): boolean {
  let from = 0;
  for (;;) {
    const at = haystack.indexOf(term, from);
    if (at === -1) return false;
    if (at === 0 || /[^a-z0-9]/.test(haystack[at - 1])) return true;
    from = at + 1;
  }
}

function countOccurrences(haystack: string, term: string): number {
  let count = 0;
  let from = 0;
  for (;;) {
    const at = haystack.indexOf(term, from);
    if (at === -1) return count;
    count += 1;
    from = at + term.length;
  }
}

type Prepared = { entry: SearchEntry; heading: string; pageTitle: string; sub: string; body: Folded };

function prepare(entry: SearchEntry): Prepared {
  return {
    entry,
    heading: foldText(entry.heading),
    pageTitle: foldText(entry.pageTitle),
    sub: foldText(entry.subheadings),
    body: fold(entry.body),
  };
}

/** Score one term against one entry. Zero means the term is absent everywhere. */
function scoreTerm(term: string, item: Prepared, isPage: boolean): number {
  let score = 0;
  if (item.heading === term) score += 60;
  else if (isWordStart(item.heading, term)) score += 40;
  else if (item.heading.includes(term)) score += 20;

  // Section hits also earn a little for living on a page whose title matches.
  if (!isPage) {
    if (isWordStart(item.pageTitle, term)) score += 12;
    else if (item.pageTitle.includes(term)) score += 6;
  }

  if (isWordStart(item.sub, term)) score += 14;
  else if (item.sub.includes(term)) score += 7;

  if (item.body.text.includes(term)) {
    const occurrences = countOccurrences(item.body.text, term);
    score += (isWordStart(item.body.text, term) ? 4 : 2) + Math.min(occurrences - 1, 3);
  }
  return score;
}

/** Best score of a term over its spellings, and the spelling that scored best. */
function scoreBest(variants: string[], item: Prepared, isPage: boolean): { score: number; term: string } {
  let best = { score: 0, term: variants[0] };
  for (const variant of variants) {
    const score = scoreTerm(variant, item, isPage);
    if (score > best.score) best = { score, term: variant };
  }
  return best;
}

function makeSnippet(item: Prepared, terms: string[]): Pick<SearchResult, "snippet" | "matchRange"> {
  const plain = item.entry.body;
  const radius = 70;
  for (const term of terms) {
    const at = item.body.text.indexOf(term);
    if (at === -1) continue;
    const matchFrom = item.body.map[at];
    const matchTo = item.body.map[at + term.length - 1] + 1;
    const start = Math.max(0, matchFrom - radius);
    const end = Math.min(plain.length, matchTo + radius);
    const prefix = start > 0 ? "..." : "";
    const suffix = end < plain.length ? "..." : "";
    // Collapse whitespace piece by piece so the match range stays correct.
    const before = plain.slice(start, matchFrom).replace(/\s+/g, " ");
    const hit = plain.slice(matchFrom, matchTo).replace(/\s+/g, " ");
    const after = plain.slice(matchTo, end).replace(/\s+/g, " ");
    const matchStart = prefix.length + before.length;
    return {
      snippet: `${prefix}${before}${hit}${after}${suffix}`,
      matchRange: [matchStart, matchStart + hit.length],
    };
  }
  const head = plain
    .slice(0, radius * 2)
    .replace(/\s+/g, " ")
    .trim();
  return { snippet: plain.length > radius * 2 ? `${head}...` : head, matchRange: null };
}

/** Most results `searchDocs` returns. When a list is this long, more pages may match and the status says so. */
export const SEARCH_LIMIT = 8;

/** True when a result list has reached the cap, so it may be cut off. */
export function isResultCapped(count: number, limit = SEARCH_LIMIT): boolean {
  return count >= limit;
}

/**
 * Search the docs of one language (the index holds that language only). Every whitespace-separated term
 * must appear somewhere in an entry (title, headings or body); entries are ranked by where the terms hit.
 * Case and diacritics do not matter. An empty or one-character query returns no results.
 */
export function searchDocs(query: string, index: readonly SearchEntry[], limit = SEARCH_LIMIT): SearchResult[] {
  const normalized = foldText(query).trim();
  if (normalized.length < 2) return [];
  const terms = normalized.split(/\s+/).filter(Boolean);
  const variants = terms.map(termVariants);

  const results: SearchResult[] = [];
  index.forEach((entry, position) => {
    const item = prepare(entry);
    const isPage = entry.kind === "page";
    let total = 0;
    const matched: string[] = [];
    for (const termVariantsOfOne of variants) {
      const { score, term } = scoreBest(termVariantsOfOne, item, isPage);
      if (score === 0) return;
      total += score;
      matched.push(term);
    }
    if (terms.length > 1) {
      if (item.heading.includes(normalized)) total += 25;
      if (item.body.text.includes(normalized)) total += 8;
    }
    // Prefer the page entry over its own sections when both match equally.
    if (isPage) total += 10;
    // Stable tie-break by reading order.
    results.push({ entry, score: total - position * 1e-6, ...makeSnippet(item, matched) });
  });

  results.sort((a, b) => b.score - a.score);
  return results.slice(0, limit);
}

/* ------------------------------------------------------------------ */
/* Markdown                                                            */
/* ------------------------------------------------------------------ */

const CLASS_NAMES_FOR_MARKDOWN = ["glass", "metal", "paper", "plastic", "trash"] as const;

function blockToMarkdown(block: DocBlock): string {
  switch (block.type) {
    case "p":
      return block.text;
    case "h3":
      return `### ${block.text}`;
    case "code":
      return "```\n" + block.code + "\n```";
    case "list":
      return block.items.map((item, index) => `${block.ordered ? `${index + 1}.` : "-"} ${item}`).join("\n");
    case "callout":
      return `> **${block.title}**\n> ${block.text}`;
    case "table": {
      const row = (cells: string[]) => `| ${cells.map((cell) => cell.replace(/\|/g, "\|")).join(" | ")} |`;
      return [`*${block.caption}*`, "", row(block.head), row(block.head.map(() => "---")), ...block.rows.map(row)].join("\n");
    }
    case "endpoints":
      return block.items.map((item) => `- \`${item.method} ${item.path}\`: ${item.text}`).join("\n");
    case "flow":
      return [`**${block.label}**`, ...block.steps.map((step, index) => `${index + 1}. **${step.title}**: ${step.detail}`)].join("\n");
    case "classes":
      return CLASS_NAMES_FOR_MARKDOWN.map((name, index) => `- ${index}: ${name}`).join("\n");
  }
}

/** One docs page as Markdown, for the "Copy as Markdown" action. Inline markup is already Markdown. */
export function docToMarkdown(page: DocPage): string {
  const parts = [`# ${page.title}`, page.lead ?? page.summary];
  for (const section of page.sections) {
    parts.push(`## ${section.title}`);
    for (const block of section.blocks) parts.push(blockToMarkdown(block));
  }
  return parts.join("\n\n") + "\n";
}
