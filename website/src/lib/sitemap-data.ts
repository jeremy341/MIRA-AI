import { LOCALES, localePath } from "../i18n/config";
import { docPath } from "./docs-content";
import { DOC_SLUGS } from "./docs-content-pages";

/** Every page of the site as a path without a language prefix ("/" is the Home page). */
export function sitePaths(): string[] {
  return ["/", "/research", "/package", "/docs", ...DOC_SLUGS.map((slug) => docPath(slug))];
}

/** One sitemap entry per page and language, each listing all language versions as hreflang alternates. */
export function buildSitemap(baseUrl: string) {
  const base = baseUrl.replace(/\/$/, "");
  return sitePaths().flatMap((path) => {
    const languages = Object.fromEntries(LOCALES.map((lang) => [lang, `${base}${localePath(lang, path)}`]));
    return LOCALES.map((lang) => ({
      url: `${base}${localePath(lang, path)}`,
      alternates: { languages },
    }));
  });
}
