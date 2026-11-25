import type { Locale } from "$i18n/config";
import { getDocsUi } from "$i18n/docs";
import { getPagesByGroup } from "$lib/docs-content-pages";
import type { LayoutServerLoad } from "./$types";

/**
 * Runs at build time only (the site is prerendered), so the text of both languages never reaches the
 * browser through this route: only the interface strings and the page list of the current language do.
 */
export const load: LayoutServerLoad = ({ params }) => {
  const lang = params.lang as Locale;
  const ui = getDocsUi(lang);
  return {
    ui,
    nav: getPagesByGroup(lang).map(({ group, pages }) => ({
      id: group,
      label: ui.groups[group],
      pages: pages.map((page) => ({ slug: page.slug, title: page.title })),
    })),
  };
};
