import type { Dictionary } from "$i18n";
import type { Locale } from "$i18n/config";
import { fmt } from "$i18n/format";
import type { ResearchDictionary } from "$i18n/research";

/** What every section of the paper receives. */
export type SectionProps = {
  lang: Locale;
  /** Research copy. */
  t: ResearchDictionary;
  /** Site-wide copy (class names, "Figure", "Table", link hints). */
  common: Dictionary["common"];
  /** Figure labels, for DetectionFigure. */
  figures: Dictionary["figures"];
  /** Placeholder values from the experiment data. */
  vars: Record<string, string>;
};

/** Fill {placeholders} from the data (and any extra values) into a dictionary string. */
export function fill(vars: Record<string, string>, text: string, extra?: Record<string, string | number>): string {
  return fmt(text, { ...vars, ...extra });
}
