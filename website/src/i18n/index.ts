import { de } from "./de";
import type { Dictionary } from "./en";
import { en } from "./en";
import type { Locale } from "./config";

export type { Dictionary } from "./en";
export * from "./config";
export * from "./format";

const DICTIONARIES: Record<Locale, Dictionary> = { en, de };

/** The typed dictionary for a language. Synchronous: both dictionaries are plain objects. */
export function getDictionary(lang: Locale): Dictionary {
  return DICTIONARIES[lang];
}
