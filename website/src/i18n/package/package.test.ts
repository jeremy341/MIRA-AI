import { describe, expect, it } from "vitest";
import { packageDe } from "./de";
import { packageEn } from "./en";
import { getPackageCopy } from "./index";

/** Flatten copy to "a.b.0.c" -> string. */
function flatten(value: unknown, prefix = ""): Record<string, string> {
  if (typeof value === "string") return { [prefix]: value };
  if (value === null || typeof value !== "object") return {};
  const out: Record<string, string> = {};
  for (const [key, child] of Object.entries(value)) {
    Object.assign(out, flatten(child, prefix ? `${prefix}.${key}` : key));
  }
  return out;
}

const placeholders = (s: string) => [...s.matchAll(/\{(\w+)\}/g)].map((m) => m[1]).sort();
const markers = (s: string) => (s.match(/==/g) ?? []).length;
const codeSpans = (s: string) => (s.match(/`/g) ?? []).length;
const links = (s: string) => [...s.matchAll(/\]\(([^)\s]+)\)/g)].map((m) => m[1]);

describe("package page copy", () => {
  const flatEn = flatten(packageEn);
  const flatDe = flatten(packageDe);

  it("is returned per language", () => {
    expect(getPackageCopy("en")).toBe(packageEn);
    expect(getPackageCopy("de")).toBe(packageDe);
  });

  it("has exactly the same keys in both languages", () => {
    expect(Object.keys(flatDe).sort()).toEqual(Object.keys(flatEn).sort());
  });

  it("has no empty strings", () => {
    for (const [key, value] of [...Object.entries(flatEn), ...Object.entries(flatDe)]) {
      expect(value.trim().length, key).toBeGreaterThan(0);
    }
  });

  it("uses the same placeholders, markers, code spans and link targets in both languages", () => {
    for (const key of Object.keys(flatEn)) {
      expect(placeholders(flatDe[key]), `placeholders of ${key}`).toEqual(placeholders(flatEn[key]));
      expect(markers(flatDe[key]), `markers of ${key}`).toBe(markers(flatEn[key]));
      expect(codeSpans(flatDe[key]), `code spans of ${key}`).toBe(codeSpans(flatEn[key]));
      expect(links(flatDe[key]), `links of ${key}`).toEqual(links(flatEn[key]));
    }
  });

  it("contains no em dashes or en dashes", () => {
    for (const [key, value] of [...Object.entries(flatEn), ...Object.entries(flatDe)]) {
      expect(/[–—]/.test(value), key).toBe(false);
    }
  });

  it("never hard-codes the unreleased repository version", () => {
    for (const value of [...Object.values(flatEn), ...Object.values(flatDe)]) {
      expect(value.includes("1.0.3")).toBe(false);
    }
  });
});
