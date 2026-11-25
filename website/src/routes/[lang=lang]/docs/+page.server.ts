import type { Locale } from "$i18n/config";
import { LOCALES } from "$i18n/config";
import { getPagesByGroup } from "$lib/docs-content-pages";
import type { EntryGenerator, PageServerLoad } from "./$types";

export const entries: EntryGenerator = () => LOCALES.map((lang) => ({ lang }));

/** The docs index lists every page with its summary, grouped. Build time only (prerendered). */
export const load: PageServerLoad = ({ params }) => {
  const groups = getPagesByGroup(params.lang as Locale).map(({ group, pages }) => ({
    group,
    pages: pages.map(({ slug, title, summary }) => ({ slug, title, summary })),
  }));
  return { groups };
};
