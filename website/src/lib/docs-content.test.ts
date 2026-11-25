import { describe, expect, it } from "vitest";
import { LOCALES, type Locale } from "../i18n/config";
import { DOC_SLUGS, getDocPages } from "../i18n/docs";
import { DE_PAGES } from "../i18n/docs/de";
import { EN_PAGES } from "../i18n/docs/en";
import {
  buildSearchIndex,
  docPath,
  fold,
  foldText,
  parseInline,
  searchDocs,
  SEARCH_LIMIT,
  isResultCapped,
  slugFromPathname,
  stripInline,
  type DocBlock,
  type DocPage,
  type SearchEntry,
} from "./docs-content";
import { getNeighbors } from "./docs-content-pages";

const fixturePages: DocPage[] = [
  {
    slug: "alpha",
    title: "Alpha guide",
    group: "start",
    summary: "Install the thing.",
    sections: [
      {
        id: "setup",
        title: "Setup",
        blocks: [{ type: "p", text: "Run `widget --go` to begin. The camera is optional." }],
      },
      {
        id: "camera",
        title: "Camera options",
        blocks: [{ type: "p", text: "Pick a camera index." }],
      },
    ],
  },
  {
    slug: "beta",
    title: "Camera reference",
    group: "reference",
    summary: "Everything about cameras.",
    sections: [
      {
        id: "flags",
        title: "Flags",
        blocks: [
          { type: "h3", id: "reject", text: "Reject threshold" },
          { type: "code", code: "tool --reject 0.5" },
        ],
      },
    ],
  },
];

const fixtureIndex = buildSearchIndex(fixturePages);

function allBlocks(page: DocPage): DocBlock[] {
  return page.sections.flatMap((section) => section.blocks);
}

/** Every visible string of a page. */
function allText(page: DocPage): string[] {
  const out: string[] = [page.title, page.summary];
  if (page.lead) out.push(page.lead);
  for (const section of page.sections) {
    out.push(section.title);
    for (const block of section.blocks) {
      switch (block.type) {
        case "p":
        case "h3":
          out.push(block.text);
          break;
        case "list":
          out.push(...block.items);
          break;
        case "callout":
          out.push(block.title, block.text);
          break;
        case "table":
          out.push(block.caption, ...block.head, ...block.rows.flat());
          break;
        case "endpoints":
          out.push(...block.items.map((item) => item.text));
          break;
        case "flow":
          out.push(block.label, ...block.steps.flatMap((step) => [step.title, step.detail]));
          break;
        default:
          break;
      }
    }
  }
  return out;
}

describe("parseInline", () => {
  it("splits text, code, bold and links", () => {
    expect(parseInline("Use `--conf` and **care**, see [Models](/docs/models).")).toEqual([
      { type: "text", value: "Use " },
      { type: "code", value: "--conf" },
      { type: "text", value: " and " },
      { type: "bold", value: "care" },
      { type: "text", value: ", see " },
      { type: "link", label: "Models", href: "/docs/models" },
      { type: "text", value: "." },
    ]);
  });

  it("returns a single text token when there is no markup", () => {
    expect(parseInline("plain words")).toEqual([{ type: "text", value: "plain words" }]);
    expect(parseInline("")).toEqual([]);
  });

  it("keeps brackets that are not links as text", () => {
    expect(stripInline("array [0] stays")).toBe("array [0] stays");
  });

  it("strips markup to plain text", () => {
    expect(stripInline("Run `mira live` with **care** ([docs](/docs/cli))")).toBe("Run mira live with care (docs)");
  });
});

describe("buildSearchIndex", () => {
  it("creates one page entry and one entry per section", () => {
    const kinds = fixtureIndex.map((entry) => `${entry.kind}:${entry.href}`);
    expect(kinds).toEqual([
      "page:/docs/alpha",
      "section:/docs/alpha#setup",
      "section:/docs/alpha#camera",
      "page:/docs/beta",
      "section:/docs/beta#flags",
    ]);
  });

  it("indexes code text and sub-headings", () => {
    const flags = fixtureIndex.find((entry) => entry.href === "/docs/beta#flags") as SearchEntry;
    expect(flags.body).toContain("--reject 0.5");
    expect(flags.subheadings).toContain("Reject threshold");
  });

  it("strips inline markup from the body", () => {
    const setup = fixtureIndex.find((entry) => entry.href === "/docs/alpha#setup") as SearchEntry;
    expect(setup.body).toContain("Run widget --go");
    expect(setup.body).not.toContain("`");
  });
});

describe("searchDocs", () => {
  it("returns nothing for an empty or whitespace query", () => {
    expect(searchDocs("", fixtureIndex)).toEqual([]);
    expect(searchDocs("   ", fixtureIndex)).toEqual([]);
  });

  it("returns nothing for a single character", () => {
    expect(searchDocs("c", fixtureIndex)).toEqual([]);
  });

  it("returns nothing when no entry matches", () => {
    expect(searchDocs("zzzxqv", fixtureIndex)).toEqual([]);
  });

  it("requires every term to match", () => {
    expect(searchDocs("camera zzzxqv", fixtureIndex)).toEqual([]);
    expect(searchDocs("camera index", fixtureIndex).map((r) => r.entry.href)).toContain("/docs/alpha#camera");
  });

  it("ranks a heading match above a body-only match", () => {
    const results = searchDocs("camera", fixtureIndex);
    const hrefs = results.map((result) => result.entry.href);
    const headingHit = hrefs.indexOf("/docs/alpha#camera");
    const bodyHit = hrefs.indexOf("/docs/alpha#setup");
    expect(headingHit).toBeGreaterThanOrEqual(0);
    expect(bodyHit).toBeGreaterThanOrEqual(0);
    expect(headingHit).toBeLessThan(bodyHit);
  });

  it("ranks the page whose title matches above sections that only mention the word", () => {
    const results = searchDocs("camera reference", fixtureIndex);
    expect(results[0].entry.href).toBe("/docs/beta");
  });

  it("finds command-line flags inside code", () => {
    const results = searchDocs("--reject", fixtureIndex);
    expect(results[0].entry.href).toBe("/docs/beta#flags");
  });

  it("matches case-insensitively and ignores diacritics", () => {
    expect(searchDocs("CAMERA", fixtureIndex).length).toBeGreaterThan(0);
    expect(searchDocs("cámera", fixtureIndex).length).toBeGreaterThan(0);
  });

  it("respects the result limit", () => {
    expect(searchDocs("camera", fixtureIndex, 1)).toHaveLength(1);
  });

  it("caps a broad query at SEARCH_LIMIT and flags the list as cut off", () => {
    const real = buildSearchIndex(getDocPages("en"));
    const results = searchDocs("mira", real);
    expect(results).toHaveLength(SEARCH_LIMIT);
    expect(isResultCapped(results.length)).toBe(true);
    expect(isResultCapped(SEARCH_LIMIT - 1)).toBe(false);
    expect(isResultCapped(0)).toBe(false);
  });

  it("builds a snippet around the match", () => {
    const [first] = searchDocs("optional", fixtureIndex);
    expect(first.snippet.toLowerCase()).toContain("optional");
    expect(first.matchRange).not.toBeNull();
    const [start, end] = first.matchRange as [number, number];
    expect(first.snippet.slice(start, end).toLowerCase()).toBe("optional");
  });
});

/* ---------------- German fixtures and folding ---------------- */

const germanFixture: DocPage[] = [
  {
    slug: "gamma",
    title: "Größe der Modelle",
    group: "reference",
    summary: "Wie groß die Dateien sind.",
    sections: [
      {
        id: "dateien",
        title: "Dateigrößen und Exporte",
        blocks: [
          {
            type: "p",
            text: "Die Gewichte sind klein. Über `--imgsz` wählst du die Eingabegröße. Straße, Fuß und Schwellenwert.",
          },
        ],
      },
      {
        id: "kamera",
        title: "Kamera ausführen",
        blocks: [{ type: "p", text: "Öffne die Kamera und prüfe den Schwellenwert." }],
      },
    ],
  },
];
const germanIndex = buildSearchIndex(germanFixture);

describe("folding", () => {
  it("lower-cases and strips diacritics", () => {
    expect(foldText("Café ÖL Über")).toBe("cafe ol uber");
  });

  it("folds the sharp s to ss and keeps a map to the source characters", () => {
    const { text, map } = fold("Größe");
    expect(text).toBe("grosse");
    expect(map).toHaveLength(text.length);
    // both s of "ss" point at the original sharp s (index 3)
    expect(map[3]).toBe(3);
    expect(map[4]).toBe(3);
    expect(map[5]).toBe(4);
  });
});

describe("German search", () => {
  it("finds umlaut words typed without umlauts", () => {
    expect(searchDocs("grosse", germanIndex).length).toBeGreaterThan(0);
    expect(searchDocs("kamera", germanIndex).length).toBeGreaterThan(0);
    expect(searchDocs("uber", germanIndex).length).toBeGreaterThan(0);
    expect(searchDocs("offne", germanIndex).length).toBeGreaterThan(0);
  });

  it("finds umlaut words typed with umlauts", () => {
    expect(searchDocs("Größe", germanIndex)[0].entry.slug).toBe("gamma");
    expect(searchDocs("Öffne", germanIndex).length).toBeGreaterThan(0);
    expect(searchDocs("Straße", germanIndex).length).toBeGreaterThan(0);
  });

  it("accepts ae, oe, ue and ss spellings", () => {
    expect(searchDocs("groesse", germanIndex).length).toBeGreaterThan(0);
    expect(searchDocs("ueber", germanIndex).length).toBeGreaterThan(0);
    expect(searchDocs("oeffne", germanIndex).length).toBeGreaterThan(0);
    expect(searchDocs("strasse", germanIndex).length).toBeGreaterThan(0);
    expect(searchDocs("fuss", germanIndex).length).toBeGreaterThan(0);
  });

  it("marks the match inside the original, unfolded snippet", () => {
    const result = searchDocs("schwellenwert", germanIndex).find((r) => r.entry.href.endsWith("#kamera"));
    expect(result).toBeDefined();
    const [start, end] = result!.matchRange as [number, number];
    expect(result!.snippet.slice(start, end)).toBe("Schwellenwert");
    const umlaut = searchDocs("Öffne", germanIndex)[0];
    const [from, to] = umlaut.matchRange as [number, number];
    expect(umlaut.snippet.slice(from, to)).toBe("Öffne");
  });

  it("keeps the match range right when the folded text is longer than the source", () => {
    const hit = searchDocs("fuss", germanIndex).find((r) => r.matchRange !== null);
    expect(hit).toBeDefined();
    const [start, end] = hit!.matchRange as [number, number];
    expect(hit!.snippet.slice(start, end)).toBe("Fuß");
  });
});

/* ---------------- The real content, per language ---------------- */

const LANGS: readonly Locale[] = LOCALES;

describe.each(LANGS)("search over the real docs (%s)", (lang) => {
  const index = buildSearchIndex(getDocPages(lang));

  it("finds flags, commands and API words", () => {
    expect(searchDocs("--target-latency", index).length).toBeGreaterThan(0);
    expect(searchDocs("tflite", index).length).toBeGreaterThan(0);
    expect(searchDocs("websocket", index)[0].entry.slug).toBe("dashboard-api");
    expect(searchDocs("mira dashboard", index)[0].entry.slug).toMatch(/dashboard|cli/);
    expect(searchDocs("--reject", index).length).toBeGreaterThan(0);
  });

  it("only returns pages of its own language", () => {
    const titles = new Set(getDocPages(lang).map((page) => page.title));
    for (const result of searchDocs("mira", index, 50)) {
      expect(titles.has(result.entry.pageTitle), result.entry.pageTitle).toBe(true);
    }
  });
});

describe("search languages are separate", () => {
  const en = buildSearchIndex(EN_PAGES);
  const de = buildSearchIndex(DE_PAGES);

  it("finds the page by its own title", () => {
    expect(searchDocs("quickstart", en)[0].entry.href).toBe("/docs/quickstart");
    expect(searchDocs("schnellstart", de)[0].entry.href).toBe("/docs/quickstart");
    expect(searchDocs("konfiguration", de)[0].entry.slug).toBe("configuration");
  });

  it("does not return English prose for a German query, or the reverse", () => {
    expect(searchDocs("virtuelle umgebung", en)).toEqual([]);
    expect(searchDocs("virtual environment", de)).toEqual([]);
  });

  it("finds German words with and without umlauts in the real German docs", () => {
    expect(searchDocs("Schwellenwert", de).length).toBeGreaterThan(0);
    expect(searchDocs("Größe", de).length).toBeGreaterThan(0);
    expect(searchDocs("grosse", de).length).toBeGreaterThan(0);
    expect(searchDocs("Datensätze", de)[0].entry.slug).toBe("datasets");
    expect(searchDocs("datensatze", de)[0].entry.slug).toBe("datasets");
    expect(searchDocs("Erkennung", de).length).toBeGreaterThan(0);
  });
});

describe.each(LANGS)("docs content integrity (%s)", (lang) => {
  const pages = getDocPages(lang);

  it("has the same slugs in the same order in every language", () => {
    expect(pages.map((page) => page.slug)).toEqual([...DOC_SLUGS]);
  });

  it("has unique page slugs and section ids per page", () => {
    expect(new Set(DOC_SLUGS).size).toBe(DOC_SLUGS.length);
    for (const page of pages) {
      const ids = page.sections.map((section) => section.id);
      const h3Ids = allBlocks(page).flatMap((block) => (block.type === "h3" ? [block.id] : []));
      const all = [...ids, ...h3Ids];
      expect(new Set(all).size, `duplicate ids on ${page.slug}`).toBe(all.length);
    }
  });

  it("uses only internal links that resolve to a page and section", () => {
    const sectionIds = new Map(
      pages.map((page) => [
        page.slug,
        new Set([
          ...page.sections.map((s) => s.id),
          ...allBlocks(page).flatMap((b) => (b.type === "h3" ? [b.id] : [])),
        ]),
      ]),
    );
    for (const text of pages.flatMap(allText)) {
      for (const token of parseInline(text)) {
        if (token.type !== "link" || !token.href.startsWith("/docs")) continue;
        const [path, hash] = token.href.split("#");
        const slug = path.replace(/^\/docs\/?/, "");
        if (slug === "") continue;
        expect(DOC_SLUGS, `broken link ${token.href}`).toContain(slug);
        if (hash) expect(sectionIds.get(slug)?.has(hash), `broken anchor ${token.href}`).toBe(true);
      }
    }
  });

  it("never prefixes internal links with a language (the renderer adds it)", () => {
    for (const text of pages.flatMap(allText)) {
      for (const token of parseInline(text)) {
        if (token.type === "link") expect(token.href, token.href).not.toMatch(/^\/(en|de)(\/|$)/);
      }
    }
  });

  it("contains no em dashes or en dashes", () => {
    const serialized = JSON.stringify(pages);
    expect(serialized).not.toMatch(new RegExp("[" + String.fromCharCode(0x2013, 0x2014) + "]"));
  });

  it("has non-empty code blocks, tables with matching columns, and a summary per page", () => {
    for (const page of pages) {
      expect(page.summary.length, page.slug).toBeGreaterThan(20);
      for (const block of allBlocks(page)) {
        if (block.type === "code") expect(block.code.trim().length).toBeGreaterThan(0);
        if (block.type === "table") {
          for (const row of block.rows) {
            expect(row.length, `${page.slug}: ${block.caption}`).toBe(block.head.length);
          }
        }
      }
    }
  });

  it("keeps the known corrections", () => {
    const text = JSON.stringify(pages);
    expect(text).not.toContain("mira diagnostics");
    expect(text).toContain("mira download");
    expect(text).toContain(">=3.11,<3.13");
    expect(text).toContain("1.0.2");
  });
});

describe("navigation helpers", () => {
  it("builds paths with and without a section", () => {
    expect(docPath("cli")).toBe("/docs/cli");
    expect(docPath("cli", "train")).toBe("/docs/cli#train");
  });

  it("returns previous and next pages in reading order, in both languages", () => {
    for (const lang of LANGS) {
      expect(getNeighbors(lang, DOC_SLUGS[0]).prev).toBeUndefined();
      expect(getNeighbors(lang, DOC_SLUGS[0]).next?.slug).toBe(DOC_SLUGS[1]);
      const last = DOC_SLUGS[DOC_SLUGS.length - 1];
      expect(getNeighbors(lang, last).next).toBeUndefined();
      expect(getNeighbors(lang, last).prev?.slug).toBe(DOC_SLUGS[DOC_SLUGS.length - 2]);
      expect(getNeighbors(lang, "missing")).toEqual({});
    }
  });

  it("maps pathnames to slugs", () => {
    expect(slugFromPathname("/docs/cli")).toBe("cli");
    expect(slugFromPathname("/docs/cli/")).toBe("cli");
    expect(slugFromPathname("/docs")).toBeUndefined();
    expect(slugFromPathname("/docs/cli/extra")).toBeUndefined();
  });
});
