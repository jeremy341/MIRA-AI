import type { DocBlock } from "./types";

/** Small constructors so the content files read like documents instead of object literals. */

export const lines = (...rows: string[]) => rows.join("\n");

export const p = (text: string): DocBlock => ({ type: "p", text });
export const h3 = (id: string, text: string): DocBlock => ({ type: "h3", id, text });
export const code = (source: string, label?: string): DocBlock => ({ type: "code", code: source, label });
export const output = (source: string, label: string): DocBlock => ({
  type: "code",
  code: source,
  label,
  output: true,
});
export const list = (items: string[], ordered = false): DocBlock => ({ type: "list", items, ordered });
export const note = (title: string, text: string): DocBlock => ({ type: "callout", tone: "note", title, text });
export const warning = (title: string, text: string): DocBlock => ({
  type: "callout",
  tone: "warning",
  title,
  text,
});
export const table = (caption: string, head: string[], rows: string[][]): DocBlock => ({
  type: "table",
  caption,
  head,
  rows,
});
