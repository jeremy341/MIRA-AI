import { buildSitemap } from "$lib/sitemap-data";
import { SITE_URL } from "$lib/site";

export const prerender = true;

export function GET() {
  const urls = buildSitemap(SITE_URL).map(
    ({ url, alternates }) =>
      `<url><loc>${url}</loc>${Object.entries(alternates.languages)
        .map(([lang, href]) => `<xhtml:link rel="alternate" hreflang="${lang}" href="${href}"/>`)
        .join("")}</url>`,
  );
  return new Response(
    `<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:xhtml="http://www.w3.org/1999/xhtml">${urls.join("")}</urlset>`,
    {
      headers: { "content-type": "application/xml; charset=utf-8" },
    },
  );
}
