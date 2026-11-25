import { getDictionary } from "../i18n";
import { alternatesFor, type Locale } from "../i18n/config";
import { SITE_URL } from "./site";

/** Size of the share cards in `static/og-en.png` and `static/og-de.png`. */
export const OG_IMAGE_SIZE = { width: 1200, height: 630 } as const;

/** Static share card per language. A real `.png` file so every host serves it with an image content type. */
export function ogImagePath(lang: Locale): string {
  return `/og-${lang}.png`;
}

export type PageMeta = {
  title: string;
  description: string;
  /** Same as `title` on Home, otherwise "<title> | MIRA" (what `<title>`, og:title and twitter:title show). */
  shareTitle: string;
  /** Path-only canonical and hreflang map, as returned by `alternatesFor`. */
  alternates: ReturnType<typeof alternatesFor>;
  /** Absolute canonical URL. */
  canonicalUrl: string;
  /** hreflang to absolute URL (including "x-default"). */
  hreflang: Record<string, string>;
  openGraph: {
    type: "website";
    siteName: string;
    title: string;
    description: string;
    url: string;
    locale: string;
    alternateLocale: string[];
    image: { url: string; width: number; height: number; alt: string; type: "image/png" };
  };
  twitter: {
    card: "summary_large_image";
    title: string;
    description: string;
    image: { url: string; alt: string };
  };
};

const absolute = (path: string) => `${SITE_URL}${path === "/" ? "/" : path}`;

/**
 * Complete page metadata: title, description, canonical + hreflang, Open Graph and Twitter. Every page must
 * go through this helper (via `<Seo />`) so that image, locale and site name are never forgotten.
 * `path` has no language prefix ("/" for home, "/docs/cli" for a doc). All URLs in the result are absolute.
 */
export function pageMetadata(lang: Locale, path: string, title: string, description: string): PageMeta {
  const dict = getDictionary(lang);
  const alternates = alternatesFor(lang, path);
  // Home keeps its title as it is; every other page gets " | MIRA" in <title>, og:title and twitter:title.
  const shareTitle = path === "/" ? title : `${title} | ${dict.meta.siteName}`;
  const imageUrl = absolute(ogImagePath(lang));
  const alt = `${dict.meta.siteName}: ${dict.meta.ogTagline}`;
  return {
    title,
    description,
    shareTitle,
    alternates,
    canonicalUrl: absolute(alternates.canonical),
    hreflang: Object.fromEntries(Object.entries(alternates.languages).map(([key, href]) => [key, absolute(href)])),
    openGraph: {
      type: "website",
      siteName: dict.meta.siteName,
      title: shareTitle,
      description,
      url: absolute(alternates.canonical),
      locale: lang === "de" ? "de_DE" : "en_US",
      alternateLocale: lang === "de" ? ["en_US"] : ["de_DE"],
      image: { url: imageUrl, ...OG_IMAGE_SIZE, alt, type: "image/png" },
    },
    twitter: {
      card: "summary_large_image",
      title: shareTitle,
      description,
      image: { url: imageUrl, alt },
    },
  };
}
