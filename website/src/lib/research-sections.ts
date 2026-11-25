/** The research report is one page per section. This list is the order of the sidebar and of previous and next. */
export const RESEARCH_SECTION_IDS = ["question", "tried", "results", "runs", "photos", "edge", "limits", "data"] as const;

export type ResearchSectionId = (typeof RESEARCH_SECTION_IDS)[number];

export function isResearchSection(value: string): value is ResearchSectionId {
  return (RESEARCH_SECTION_IDS as readonly string[]).includes(value);
}

/** Path without a language prefix. */
export function researchPath(id: ResearchSectionId): string {
  return `/research/${id}`;
}
