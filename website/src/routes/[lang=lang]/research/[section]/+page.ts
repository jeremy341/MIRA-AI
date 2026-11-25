import { error } from "@sveltejs/kit";
import { LOCALES } from "$i18n/config";
import { isResearchSection, RESEARCH_SECTION_IDS } from "$lib/research-sections";
import type { EntryGenerator, PageLoad } from "./$types";

// Static site: one page per language and section, anything else is a 404.
export const entries: EntryGenerator = () =>
  LOCALES.flatMap((lang) => RESEARCH_SECTION_IDS.map((section) => ({ lang, section })));

export const load: PageLoad = ({ params }) => {
  if (!isResearchSection(params.section)) error(404, "Not found");
  const index = RESEARCH_SECTION_IDS.indexOf(params.section);
  return {
    section: params.section,
    prev: RESEARCH_SECTION_IDS[index - 1] ?? null,
    next: RESEARCH_SECTION_IDS[index + 1] ?? null,
  };
};
