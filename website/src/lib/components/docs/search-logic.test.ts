import { describe, expect, it } from "vitest";
import { DOCS_UI } from "../../../i18n/docs/ui";
import { buildSearchIndex, searchDocs, SEARCH_LIMIT } from "../../docs-content";
import type { DocPage } from "../../docs-content";
import { DE_PAGES } from "../../../i18n/docs/de";
import { EN_PAGES } from "../../../i18n/docs/en";
import { isSearchShortcut, MIN_QUERY_LENGTH, moveActive, searchStatus, splitTryHint } from "./search-logic";

const key = (over: Partial<Parameters<typeof isSearchShortcut>[0]> = {}) => ({
  key: "/",
  code: "Slash",
  altKey: true,
  ctrlKey: false,
  metaKey: false,
  ...over,
});

describe("isSearchShortcut", () => {
  it("accepts Alt + / by key", () => {
    expect(isSearchShortcut(key({ code: "" }))).toBe(true);
  });

  it("accepts the Slash code when the key is another character (German layout, macOS Option)", () => {
    expect(isSearchShortcut(key({ key: "7" }))).toBe(true);
    expect(isSearchShortcut(key({ key: "÷" }))).toBe(true);
  });

  it("needs Alt, and ignores Ctrl and Meta chords", () => {
    expect(isSearchShortcut(key({ altKey: false }))).toBe(false);
    expect(isSearchShortcut(key({ ctrlKey: true }))).toBe(false);
    expect(isSearchShortcut(key({ metaKey: true }))).toBe(false);
  });

  it("ignores other keys", () => {
    expect(isSearchShortcut(key({ key: "k", code: "KeyK" }))).toBe(false);
  });
});

describe("moveActive", () => {
  it("wraps in both directions", () => {
    expect(moveActive(0, 1, 3)).toBe(1);
    expect(moveActive(2, 1, 3)).toBe(0);
    expect(moveActive(0, -1, 3)).toBe(2);
    expect(moveActive(1, -1, 3)).toBe(0);
  });

  it("stays at 0 without results", () => {
    expect(moveActive(0, 1, 0)).toBe(0);
    expect(moveActive(0, -1, 0)).toBe(0);
  });
});

describe("searchStatus", () => {
  const en = DOCS_UI.en.search;
  const de = DOCS_UI.de.search;

  it("is empty for a short query or before the index has loaded", () => {
    expect(searchStatus(en, "a".repeat(MIN_QUERY_LENGTH - 1), 3, true)).toBe("");
    expect(searchStatus(en, "camera", 3, false)).toBe("");
  });

  it("says how many results, singular and plural", () => {
    expect(searchStatus(en, "camera", 1, true)).toBe("1 result");
    expect(searchStatus(en, "camera", 3, true)).toBe("3 results");
    expect(searchStatus(de, "kamera", 3, true)).toBe("3 Treffer");
  });

  it("says 'First N results' once the list is cut off at the limit", () => {
    expect(searchStatus(en, "camera", SEARCH_LIMIT, true)).toBe(`First ${SEARCH_LIMIT} results`);
    expect(searchStatus(de, "kamera", SEARCH_LIMIT, true)).toBe(`Die ersten ${SEARCH_LIMIT} Treffer`);
  });

  it("names the query when nothing matches", () => {
    expect(searchStatus(en, "  zzzz ", 0, true)).toBe("No results for zzzz");
  });
});

describe("splitTryHint", () => {
  it("splits the template around {flag} and {words}", () => {
    expect(splitTryHint("Try a flag such as {flag} or a word such as {words}.")).toEqual({
      head: "Try a flag such as ",
      middle: " or a word such as ",
      tail: ".",
    });
  });
});

describe("search against the real docs, one language at a time", () => {
  const en = buildSearchIndex(EN_PAGES as DocPage[]);
  const de = buildSearchIndex(DE_PAGES as DocPage[]);

  it("finds the camera section in English and not for a German query", () => {
    expect(searchDocs("camera", en).length).toBeGreaterThan(0);
    expect(searchDocs("Kamera", en)).toEqual([]);
  });

  it("finds German pages with umlaut, ue spelling and ss spelling alike", () => {
    const withUmlaut = searchDocs("Prüfung", de).map((r) => r.entry.href);
    const withUe = searchDocs("Pruefung", de).map((r) => r.entry.href);
    expect(withUmlaut.length).toBeGreaterThan(0);
    expect(withUe).toEqual(withUmlaut);
    expect(searchDocs("grosse", de).map((r) => r.entry.href)).toEqual(searchDocs("Größe", de).map((r) => r.entry.href));
  });

  it("caps at SEARCH_LIMIT", () => {
    expect(searchDocs("mira", en).length).toBe(SEARCH_LIMIT);
  });
});
