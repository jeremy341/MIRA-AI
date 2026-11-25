import { describe, expect, it } from "vitest";
import { parseInline } from "../../lib/docs-content";
import { DE_PAGES } from "./de";
import { EN_PAGES } from "./en";
import { DOCS_UI } from "./ui";
import type { DocBlock, DocPage } from "./types";

/** English and German must have the same structure; only the words differ. */

const NO_DASHES = new RegExp("[" + String.fromCharCode(0x2013, 0x2014) + "]");

function strings(value: unknown, path = ""): [string, string][] {
  if (typeof value === "string") return [[path, value]];
  if (Array.isArray(value)) return value.flatMap((item, index) => strings(item, `${path}[${index}]`));
  if (value && typeof value === "object") {
    return Object.entries(value).flatMap(([key, child]) => strings(child, path ? `${path}.${key}` : key));
  }
  return [];
}

function codeSpans(text: string): string[] {
  return parseInline(text).flatMap((token) => (token.type === "code" ? [token.value] : []));
}

function hrefs(text: string): string[] {
  return parseInline(text)
    .flatMap((token) => (token.type === "link" ? [token.href] : []))
    .sort();
}

/**
 * Numbers in a string in a language-neutral form: "1,375", "1.375" and "1375" are one thousand three
 * hundred seventy-five; "0,906" and "0.906" are the same fraction. Version numbers such as "3.11" and
 * ids such as "014" stay as they are.
 */
export function numberTokens(text: string): string[] {
  const without = text.replace(/`[^`]*`/g, " ");
  const found = without.match(/\d+(?:[.,]\d+)*/g) ?? [];
  return found
    .map((token) => (/^[1-9]\d{0,2}([.,]\d{3})+$/.test(token) ? token.replace(/[.,]/g, "") : token.replace(",", ".")))
    .sort();
}

/** Text pairs (English, German) at the same position in the same block. */
function textPairs(en: DocBlock, de: DocBlock): [string, string][] {
  if (en.type !== de.type) return [];
  switch (en.type) {
    case "p":
      return [[en.text, (de as typeof en).text]];
    case "h3":
      return [[en.text, (de as typeof en).text]];
    case "list":
      return en.items.map((item, index): [string, string] => [item, (de as typeof en).items[index]]);
    case "callout":
      return [
        [en.title, (de as typeof en).title],
        [en.text, (de as typeof en).text],
      ];
    case "table": {
      const other = de as typeof en;
      return [
        [en.caption, other.caption],
        ...en.head.map((cell, index): [string, string] => [cell, other.head[index]]),
        ...en.rows.flatMap((row, r) => row.map((cell, c): [string, string] => [cell, other.rows[r][c]])),
      ];
    }
    case "endpoints":
      return en.items.map((item, index): [string, string] => [item.text, (de as typeof en).items[index].text]);
    case "flow": {
      const other = de as typeof en;
      return [
        [en.label, other.label],
        ...en.steps.flatMap((step, index): [string, string][] => [
          [step.title, other.steps[index].title],
          [step.detail, other.steps[index].detail],
        ]),
      ];
    }
    default:
      return [];
  }
}

describe("docs content parity (en, de)", () => {
  it("has the same pages in the same order with the same slug and group", () => {
    expect(DE_PAGES.map((page) => [page.slug, page.group])).toEqual(EN_PAGES.map((page) => [page.slug, page.group]));
    expect(DE_PAGES).toHaveLength(12);
  });

  it("has the same sections, headings ids, block types and block counts", () => {
    EN_PAGES.forEach((en: DocPage, pageIndex) => {
      const de = DE_PAGES[pageIndex];
      expect(
        de.sections.map((section) => section.id),
        en.slug,
      ).toEqual(en.sections.map((section) => section.id));
      expect(!!de.lead, `${en.slug}: lead`).toBe(!!en.lead);
      en.sections.forEach((section, sectionIndex) => {
        const other = de.sections[sectionIndex];
        const where = `${en.slug}#${section.id}`;
        expect(
          other.blocks.map((block) => block.type),
          where,
        ).toEqual(section.blocks.map((block) => block.type));
        section.blocks.forEach((block, blockIndex) => {
          const twin = other.blocks[blockIndex];
          const at = `${where} block ${blockIndex}`;
          if (block.type === "h3") expect((twin as typeof block).id, at).toBe(block.id);
          if (block.type === "list") {
            expect((twin as typeof block).items.length, at).toBe(block.items.length);
            expect(!!(twin as typeof block).ordered, at).toBe(!!block.ordered);
          }
          if (block.type === "callout") expect((twin as typeof block).tone, at).toBe(block.tone);
          if (block.type === "table") {
            const t = twin as typeof block;
            expect(t.head.length, at).toBe(block.head.length);
            expect(t.rows.length, at).toBe(block.rows.length);
            t.rows.forEach((row, index) => expect(row.length, `${at} row ${index}`).toBe(block.head.length));
          }
          if (block.type === "endpoints") {
            const t = twin as typeof block;
            expect(
              t.items.map((item) => [item.method, item.path]),
              at,
            ).toEqual(block.items.map((item) => [item.method, item.path]));
          }
          if (block.type === "flow") expect((twin as typeof block).steps.length, at).toBe(block.steps.length);
        });
      });
    });
  });

  it("has identical code blocks, byte for byte", () => {
    let checked = 0;
    EN_PAGES.forEach((en, pageIndex) => {
      en.sections.forEach((section, sectionIndex) => {
        section.blocks.forEach((block, blockIndex) => {
          if (block.type !== "code") return;
          const twin = DE_PAGES[pageIndex].sections[sectionIndex].blocks[blockIndex] as typeof block;
          expect(twin.code, `${en.slug}#${section.id} block ${blockIndex}`).toBe(block.code);
          expect(!!twin.output, `${en.slug}#${section.id} block ${blockIndex}`).toBe(!!block.output);
          expect(!!twin.label, `${en.slug}#${section.id} block ${blockIndex} label`).toBe(!!block.label);
          checked += 1;
        });
      });
    });
    expect(checked).toBeGreaterThan(30);
  });

  it("keeps every inline code span and every link of the English text in the German text", () => {
    EN_PAGES.forEach((en, pageIndex) => {
      const de = DE_PAGES[pageIndex];
      const pairs: [string, string][] = [
        [en.title, de.title],
        [en.summary, de.summary],
      ];
      if (en.lead && de.lead) pairs.push([en.lead, de.lead]);
      en.sections.forEach((section, sectionIndex) => {
        pairs.push([section.title, de.sections[sectionIndex].title]);
        section.blocks.forEach((block, blockIndex) => {
          pairs.push(...textPairs(block, de.sections[sectionIndex].blocks[blockIndex]));
        });
      });
      for (const [englishText, germanText] of pairs) {
        const german = codeSpans(germanText);
        for (const span of codeSpans(englishText)) {
          expect(german, `${en.slug}: "${span}" missing in "${germanText}"`).toContain(span);
        }
        // Counting: no English span may be dropped when it occurs more than once.
        for (const span of new Set(codeSpans(englishText))) {
          const wanted = codeSpans(englishText).filter((s) => s === span).length;
          const got = german.filter((s) => s === span).length;
          expect(got, `${en.slug}: "${span}" count in "${germanText}"`).toBeGreaterThanOrEqual(wanted);
        }
        expect(hrefs(germanText), `${en.slug}: links of "${germanText}"`).toEqual(hrefs(englishText));
        expect(germanText.includes("**"), `${en.slug}: bold markers`).toBe(englishText.includes("**"));
      }
    });
  });

  it("keeps the same numbers (decimal comma and thousands dots aside)", () => {
    EN_PAGES.forEach((en, pageIndex) => {
      const de = DE_PAGES[pageIndex];
      en.sections.forEach((section, sectionIndex) => {
        section.blocks.forEach((block, blockIndex) => {
          const twin = de.sections[sectionIndex].blocks[blockIndex];
          // Counting words ("30 consecutive") live in prose; the check is skipped for lists of examples.
          for (const [englishText, germanText] of textPairs(block, twin)) {
            expect(numberTokens(germanText), `${en.slug}#${section.id}: "${germanText}"`).toEqual(
              numberTokens(englishText),
            );
          }
        });
      });
    });
  });

  it("has no empty strings and no em or en dashes in either language", () => {
    for (const [name, pages] of [
      ["en", EN_PAGES],
      ["de", DE_PAGES],
    ] as const) {
      for (const [path, value] of strings(pages)) {
        if (path.endsWith(".code") && !value.trim()) throw new Error(`${name} ${path}: empty code`);
        if (!path.endsWith(".code")) expect(value.trim().length, `${name} ${path}`).toBeGreaterThan(0);
        expect(value, `${name} ${path}`).not.toMatch(NO_DASHES);
      }
    }
  });

  it("does not leave English sentences in the German text", () => {
    const suspicious = /\b(the|and|with|which|this|that|from|before|after|your|not)\b/i;
    for (const page of DE_PAGES) {
      for (const section of page.sections) {
        for (const block of section.blocks) {
          if (block.type !== "p") continue;
          const plain = block.text.replace(/`[^`]*`/g, "").replace(/\[[^\]]*\]\([^)]*\)/g, "");
          expect(plain, `${page.slug}#${section.id}`).not.toMatch(suspicious);
        }
      }
    }
  });
});

describe("docs interface strings parity (en, de)", () => {
  const placeholders = (text: string) => [...text.matchAll(/\{(\w+)\}/g)].map((match) => match[1]).sort();
  const en = strings(DOCS_UI.en);
  const de = strings(DOCS_UI.de);

  it("has the same keys", () => {
    expect(de.map(([key]) => key)).toEqual(en.map(([key]) => key));
  });

  it("has the same placeholders, no empty strings and no dashes", () => {
    en.forEach(([key, value], index) => {
      expect(placeholders(de[index][1]), key).toEqual(placeholders(value));
      expect(value.trim().length, `en ${key}`).toBeGreaterThan(0);
      expect(de[index][1].trim().length, `de ${key}`).toBeGreaterThan(0);
      expect(value + de[index][1], key).not.toMatch(NO_DASHES);
    });
  });

  it("has the same code spans", () => {
    en.forEach(([key, value], index) => {
      expect(codeSpans(de[index][1]), key).toEqual(codeSpans(value));
    });
  });
});
