import { describe, expect, it } from "vitest";
import { getDictionary, LOCALES } from "../i18n";
import { ogImagePath, pageMetadata } from "./metadata";
import { SITE_URL } from "./site";

describe("pageMetadata", () => {
  for (const lang of LOCALES) {
    it(`gives every ${lang} page canonical, hreflang, Open Graph and Twitter data`, () => {
      const meta = pageMetadata(lang, "/docs/cli", "CLI", "The command line.");
      expect(meta.title).toBe("CLI");
      expect(meta.alternates.canonical).toBe(`/${lang}/docs/cli`);
      expect(meta.canonicalUrl).toBe(`${SITE_URL}/${lang}/docs/cli`);
      expect(meta.hreflang).toMatchObject({
        en: `${SITE_URL}/en/docs/cli`,
        de: `${SITE_URL}/de/docs/cli`,
        "x-default": `${SITE_URL}/en/docs/cli`,
      });

      const og = meta.openGraph;
      expect(og.type).toBe("website");
      expect(og.siteName).toBe(getDictionary(lang).meta.siteName);
      expect(og.locale).toBe(lang === "de" ? "de_DE" : "en_US");
      expect(og.url).toBe(`${SITE_URL}/${lang}/docs/cli`);
      expect(og.title).toBe("CLI | MIRA");
      expect(og.description).toBe("The command line.");
      expect(og.image).toMatchObject({ url: `${SITE_URL}${ogImagePath(lang)}`, width: 1200, height: 630 });

      const tw = meta.twitter;
      expect(tw.card).toBe("summary_large_image");
      expect(tw.title).toBe("CLI | MIRA");
      expect(tw.description).toBe("The command line.");
      expect(tw.image.url).toBe(`${SITE_URL}${ogImagePath(lang)}`);
    });
  }

  it("does not add the site name to the Home title", () => {
    const meta = pageMetadata("en", "/", "MIRA: Machine Intelligence", "d");
    expect(meta.shareTitle).toBe("MIRA: Machine Intelligence");
    expect(meta.openGraph.title).toBe("MIRA: Machine Intelligence");
  });

  it("points home at the language root", () => {
    const meta = pageMetadata("de", "/", "t", "d");
    expect(meta.alternates.canonical).toBe("/de");
    expect(meta.canonicalUrl).toBe(`${SITE_URL}/de`);
    expect(meta.hreflang["x-default"]).toBe(`${SITE_URL}/`);
  });

  it("uses a static png per language", () => {
    expect(ogImagePath("en")).toBe("/og-en.png");
    expect(ogImagePath("de")).toBe("/og-de.png");
  });
});
