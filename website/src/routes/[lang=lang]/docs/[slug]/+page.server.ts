import { error } from "@sveltejs/kit";
import type { Locale } from "$i18n/config";
import { LOCALES } from "$i18n/config";
import { DOC_SLUGS, getDocPage, getNeighbors } from "$lib/docs-content-pages";
import type { EntryGenerator, PageServerLoad } from "./$types";

// Static site: only the languages and slugs below are prerendered, anything else is a 404.
export const entries: EntryGenerator = () => LOCALES.flatMap((lang) => DOC_SLUGS.map((slug) => ({ lang, slug })));

/** Build time only (prerendered): the page text of the one language travels with the page, not in the JS bundle. */
export const load: PageServerLoad = ({ params }) => {
  const lang = params.lang as Locale;
  const doc = getDocPage(lang, params.slug);
  if (!doc) error(404, "Not found");
  const { prev, next } = getNeighbors(lang, doc.slug);
  return {
    doc,
    prev: prev && { slug: prev.slug, title: prev.title },
    next: next && { slug: next.slug, title: next.title },
  };
};
