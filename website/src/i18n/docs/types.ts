/**
 * Shapes of the documentation content. English and German use exactly the same types and the same
 * structure (same slugs, section ids, block types and block counts); `docs.parity.test.ts` checks it.
 *
 * Inline markup inside text strings: `code`, **bold**, [label](href). Internal hrefs have no language
 * prefix ("/docs/models"); the renderer adds it.
 */

export type DocGroupId = "start" | "howto" | "reference";

export type DocBlock =
  | { type: "p"; text: string }
  | { type: "h3"; id: string; text: string }
  | { type: "code"; code: string; label?: string; output?: boolean }
  | { type: "list"; items: string[]; ordered?: boolean }
  | { type: "callout"; tone: "note" | "warning"; title: string; text: string }
  | { type: "table"; caption: string; head: string[]; rows: string[][] }
  | { type: "endpoints"; items: { method: "GET" | "POST" | "WS"; path: string; text: string }[] }
  | { type: "flow"; label: string; steps: { title: string; detail: string }[] }
  | { type: "classes" };

export type DocSection = {
  id: string;
  title: string;
  blocks: DocBlock[];
};

export type DocPage = {
  slug: string;
  title: string;
  group: DocGroupId;
  /** One sentence. Used for metadata, the docs index and search. */
  summary: string;
  /** Optional lead paragraph shown under the page title. */
  lead?: string;
  sections: DocSection[];
};
