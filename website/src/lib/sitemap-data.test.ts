import { describe, expect, it } from "vitest";
import { DOC_SLUGS } from "./docs-content-pages";
import { buildSitemap, sitePaths } from "./sitemap-data";

describe("sitemap", () => {
  const entries = buildSitemap("https://example.test/");

  it("lists every page in both languages", () => {
    expect(sitePaths()).toHaveLength(4 + DOC_SLUGS.length);
    expect(entries).toHaveLength(sitePaths().length * 2);
    const urls = entries.map((entry) => entry.url);
    expect(urls).toContain("https://example.test/en");
    expect(urls).toContain("https://example.test/de");
    expect(urls).toContain("https://example.test/de/research");
    expect(urls).toContain("https://example.test/en/docs");
    for (const slug of DOC_SLUGS) {
      expect(urls).toContain(`https://example.test/en/docs/${slug}`);
      expect(urls).toContain(`https://example.test/de/docs/${slug}`);
    }
    expect(new Set(urls).size).toBe(urls.length);
  });

  it("gives each entry hreflang alternates for all languages and no trailing slash", () => {
    for (const entry of entries) {
      expect(entry.url.endsWith("/")).toBe(false);
      expect(Object.keys(entry.alternates?.languages ?? {})).toEqual(["en", "de"]);
    }
  });
});
