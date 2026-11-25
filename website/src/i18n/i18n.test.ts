import { describe, expect, it } from "vitest";
import {
  DEFAULT_LOCALE,
  LOCALES,
  alternatesFor,
  getDictionary,
  hasLocalePrefix,
  isLocale,
  localeFromTag,
  localePath,
  pickLocale,
  stripLocale,
  switchLocalePath,
} from "./index";
import { fmt, formatConfidence, formatInt, formatModelName, formatScoreLocale } from "./format";
import { de } from "./de";
import { en } from "./en";
import { DE_PAGES } from "./docs/de";
import { DOCS_UI } from "./docs/ui";
import { packageDe } from "./package/de";
import { de as deResearch } from "./research/de";

/** Flatten a dictionary to "a.b.0.c" -> string. */
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

describe("locale helpers", () => {
  it("supports English and German, English first", () => {
    expect(LOCALES).toEqual(["en", "de"]);
    expect(DEFAULT_LOCALE).toBe("en");
  });

  it("isLocale narrows only supported codes", () => {
    expect(isLocale("en")).toBe(true);
    expect(isLocale("de")).toBe(true);
    expect(isLocale("fr")).toBe(false);
    expect(isLocale("EN")).toBe(false);
    expect(isLocale("")).toBe(false);
    expect(isLocale(null)).toBe(false);
    expect(isLocale(undefined)).toBe(false);
  });

  it("maps a browser language tag to a locale (de* is German, everything else English)", () => {
    expect(localeFromTag("de")).toBe("de");
    expect(localeFromTag("de-DE")).toBe("de");
    expect(localeFromTag("de-AT")).toBe("de");
    expect(localeFromTag("DE-ch")).toBe("de");
    expect(localeFromTag("en-US")).toBe("en");
    expect(localeFromTag("fr-FR")).toBe("en");
    expect(localeFromTag("")).toBe("en");
    expect(localeFromTag(undefined)).toBe("en");
  });

  it("picks the first supported language of a preference list", () => {
    expect(pickLocale(["fr-FR", "de-DE", "en"])).toBe("de");
    expect(pickLocale(["en-GB", "de"])).toBe("en");
    expect(pickLocale([])).toBe("en");
    expect(pickLocale(null)).toBe("en");
  });

  it("adds, detects and strips the language prefix", () => {
    expect(localePath("de", "/")).toBe("/de");
    expect(localePath("en", "/docs/cli#train")).toBe("/en/docs/cli#train");
    expect(localePath("de", "docs")).toBe("/de/docs");
    expect(hasLocalePrefix("/de/docs")).toBe(true);
    expect(hasLocalePrefix("/docs")).toBe(false);
    expect(hasLocalePrefix("/delta")).toBe(false);
    expect(stripLocale("/de/docs/cli")).toBe("/docs/cli");
    expect(stripLocale("/de")).toBe("/");
    expect(stripLocale("/en/")).toBe("/");
    expect(stripLocale("/docs")).toBe("/docs");
  });

  it("links to the same page in the other language", () => {
    expect(switchLocalePath("/en/docs/cli", "de")).toBe("/de/docs/cli");
    expect(switchLocalePath("/de", "en")).toBe("/en");
    expect(switchLocalePath("/de/research", "de")).toBe("/de/research");
  });

  it("builds canonical, hreflang and x-default alternates", () => {
    expect(alternatesFor("de", "/")).toEqual({
      canonical: "/de",
      languages: { en: "/en", de: "/de", "x-default": "/" },
    });
    expect(alternatesFor("en", "/docs/cli")).toEqual({
      canonical: "/en/docs/cli",
      languages: { en: "/en/docs/cli", de: "/de/docs/cli", "x-default": "/en/docs/cli" },
    });
  });
});

describe("dictionaries", () => {
  const flatEn = flatten(en);
  const flatDe = flatten(de);

  it("getDictionary returns the dictionary of each language", () => {
    expect(getDictionary("en")).toBe(en);
    expect(getDictionary("de")).toBe(de);
  });

  it("have exactly the same keys in both languages", () => {
    expect(Object.keys(flatDe).sort()).toEqual(Object.keys(flatEn).sort());
  });

  it("have no empty strings", () => {
    for (const [key, value] of [...Object.entries(flatEn), ...Object.entries(flatDe)]) {
      expect(value.trim().length, key).toBeGreaterThan(0);
    }
  });

  it("use the same placeholders, markers and code spans in both languages", () => {
    for (const key of Object.keys(flatEn)) {
      expect(placeholders(flatDe[key]), `placeholders of ${key}`).toEqual(placeholders(flatEn[key]));
      expect(markers(flatDe[key]), `markers of ${key}`).toBe(markers(flatEn[key]));
      expect(codeSpans(flatDe[key]), `code spans of ${key}`).toBe(codeSpans(flatEn[key]));
    }
  });

  it("contain no em dashes or en dashes", () => {
    for (const [key, value] of [...Object.entries(flatEn), ...Object.entries(flatDe)]) {
      expect(/[–—]/.test(value), key).toBe(false);
    }
  });

  it("keep the version claim honest: no 1.0.3 anywhere", () => {
    for (const value of [...Object.values(flatEn), ...Object.values(flatDe)]) {
      expect(value.includes("1.0.3")).toBe(false);
    }
  });

  it("keep the demo video texts (used only once a video exists) in both languages", () => {
    expect(en.home.tryit.video.title.toLowerCase()).toContain("demo");
    expect(de.home.tryit.video.title.toLowerCase()).toContain("demo");
    expect(Object.keys(en.home.tryit.video)).not.toContain("placeholder");
  });

  it("address the reader formally (Sie) on the redirect, and not at all on Home", () => {
    expect(de.redirect.note).toBe("Sie werden zur bevorzugten Sprache Ihres Browsers weitergeleitet.");
    const home = JSON.stringify(de.home);
    // "Sie" is left out on purpose: Home says "Sie sagen nichts ..." (they say nothing), which is not an address.
    // (The Next.js original had literal backspace characters instead of word boundaries here, so it never matched.)
    expect(home).not.toMatch(/\b(du|dir|dich|dein\w*|Ihr\w*|Ihnen)\b/);
  });
});

describe("formatting", () => {
  it("fills placeholders and leaves unknown ones visible", () => {
    expect(fmt("{a} and {b}", { a: 1, b: "x" })).toBe("1 and x");
    expect(fmt("{a} {missing}", { a: 1 })).toBe("1 {missing}");
  });

  it("formats scores with the log's digits and a decimal comma in German", () => {
    expect(formatScoreLocale("en", 90.58, true)).toBe("90.58%");
    expect(formatScoreLocale("en", 61)).toBe("61.0");
    expect(formatScoreLocale("de", 60.7, true)).toBe("60,7 %");
    expect(formatScoreLocale("de", 90.58)).toBe("90,58");
  });

  it("formats integers, confidences and model names", () => {
    expect(formatInt("en", 10096)).toBe("10,096");
    expect(formatInt("de", 10096)).toBe("10.096");
    expect(formatConfidence("en", 0.9)).toBe("0.90");
    expect(formatConfidence("de", 0.925)).toMatch(/^0,9[23]$/);
    expect(formatModelName("mira_exp019")).toBe("MIRA EXP-019");
    expect(formatModelName("something-else")).toBe("something-else");
    expect(formatModelName("")).toBe("MIRA");
  });
});

describe("German register on the other pages", () => {
  /** Every string in a copy tree, except code samples (they stay identical in both languages). */
  const flat = (v: unknown): string[] =>
    typeof v === "string"
      ? [v]
      : v && typeof v === "object"
        ? Object.entries(v).flatMap(([key, child]) => (key === "code" ? [] : flat(child)))
        : [];
  const du = /\b(du|dir|dich|dein\w*|deine[nmrs]?)\b/;
  const imperativeDu =
    /\b(Probiere|Nutze|Führe|Wähle|Öffne|Klicke|Lies|Nimm|Gib|Setze|Prüfe|Stelle|Starte|Installiere|Kopiere|Behalte|Übergib|Stoppe|Sende|Lass|Erhöhe|Verwende|Versuche|Eröffne|Erzeuge|Lade|Arbeite)\b/;

  it("uses Sie, never du, in the package, research and docs interface texts", () => {
    for (const raw of [...flat(packageDe), ...flat(deResearch), ...flat(DOCS_UI.de), ...flat(DE_PAGES)]) {
      const text = raw.replace(/`[^`]*`/g, "");
      expect(text).not.toMatch(du);
      expect(text).not.toMatch(imperativeDu);
    }
    expect(DOCS_UI.de.warning).toBe("Warnung");
  });
});
