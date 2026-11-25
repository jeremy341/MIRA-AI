/**
 * Tiny, safe renderer for the inline markup used in dictionary strings. It only produces plain data
 * (no HTML string), so the Svelte component can render it without `{@html}`:
 *   ==marker==       highlighter marker
 *   `code`           monospace; every word stays on one line
 *   [label](href)    link ("/..." is an internal page and gets the language prefix)
 * Experiment ids (EXP-019) and `mira-ai` outside code spans also stay on one line.
 */

export type RichWord = { text: string; nowrap: boolean };

export type RichPart =
  | { kind: "text"; text: string }
  | { kind: "mark"; text: string }
  | { kind: "code"; words: RichWord[] }
  | { kind: "nobreak"; text: string }
  | { kind: "link"; text: string; href: string; internal: boolean };

const TOKEN = /==(.+?)==|`([^`]+)`|\[([^\]]+)\]\(([^)\s]+)\)|(EXP-\d{3}|mira-ai)/g;

/** Longer words may still break anywhere, so a very long path cannot push a narrow screen sideways. */
const MAX_TOKEN = 32;

/**
 * Splits text into words that stay on one line (`mira-ai`, `--conf` or `mira_exp014.pt` never break at a hyphen).
 * Spaces stay normal, so a long command still wraps between words.
 */
export function splitNoBreak(text: string): RichWord[] {
  return text
    .split(/(\s+)/)
    .filter((part) => part !== "")
    .map((part) => ({ text: part, nowrap: !/^\s+$/.test(part) && part.length <= MAX_TOKEN }));
}

export function parseRich(text: string): RichPart[] {
  const out: RichPart[] = [];
  let last = 0;
  for (const match of text.matchAll(TOKEN)) {
    const index = match.index ?? 0;
    if (index > last) out.push({ kind: "text", text: text.slice(last, index) });
    if (match[1] !== undefined) {
      out.push({ kind: "mark", text: match[1] });
    } else if (match[2] !== undefined) {
      out.push({ kind: "code", words: splitNoBreak(match[2]) });
    } else if (match[5] !== undefined) {
      out.push({ kind: "nobreak", text: match[5] });
    } else {
      const href = match[4];
      out.push({ kind: "link", text: match[3], href, internal: href.startsWith("/") && !href.startsWith("//") });
    }
    last = index + match[0].length;
  }
  if (last < text.length) out.push({ kind: "text", text: text.slice(last) });
  return out;
}
