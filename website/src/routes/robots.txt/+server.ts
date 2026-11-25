import { SITE_URL } from "$lib/site";

export const prerender = true;

export function GET() {
  return new Response(`User-agent: *\nAllow: /\nSitemap: ${SITE_URL}/sitemap.xml\n`, {
    headers: { "content-type": "text/plain; charset=utf-8" },
  });
}
