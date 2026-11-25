import type { Locale } from "../config";
import { de } from "./de";
import { en, type ResearchDictionary } from "./en";

export type { ExperimentCopy, ResearchDictionary } from "./en";

const DICTIONARIES: Record<Locale, ResearchDictionary> = { en, de };

/** The research page copy for a language. Synchronous: both dictionaries are plain objects. */
export function getResearchDictionary(lang: Locale): ResearchDictionary {
  return DICTIONARIES[lang];
}
