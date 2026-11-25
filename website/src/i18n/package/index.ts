import type { Locale } from "../config";
import { packageDe } from "./de";
import type { PackageCopy } from "./en";
import { packageEn } from "./en";

export type { PackageCopy } from "./en";

const COPY: Record<Locale, PackageCopy> = { en: packageEn, de: packageDe };

/** The typed Package page copy for a language. */
export function getPackageCopy(lang: Locale): PackageCopy {
  return COPY[lang];
}
