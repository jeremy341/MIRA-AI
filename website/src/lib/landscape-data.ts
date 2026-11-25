/**
 * Data of the experiment landscape: one entry per documented experiment, read from experiments.ts (source:
 * results/experiments_log.md). Nothing is added or estimated here. Entries without a recorded score (`value: null`)
 * are drawn as flat tiles and listed in the table as "no score recorded".
 *
 * The 3D scene, the flat fallback and the table all read `landscapeRows(lang, copy)`, so they cannot disagree.
 */
import type { Dictionary } from "$i18n";
import type { Locale } from "$i18n/config";
import { fmt, formatInt, formatScoreLocale } from "$i18n/format";
import { EXPERIMENTS } from "./experiments";

export type LandscapeCopy = Dictionary["home"]["landscape"];

/** Experiments highlighted in the landscape (the three that ship in the package). */
export const HIGHLIGHT_IDS = ["EXP-014", "EXP-018", "EXP-019"] as const;

export type LandscapeRow = {
  id: string;
  /** "014" for "EXP-014". */
  short: string;
  stage: "A" | "B";
  /** Percentage 0 to 100, or null when the log records no score. */
  value: number | null;
  /** Localised metric name ("mAP50", "validation accuracy"), or the "no score recorded" text. */
  metric: string;
  /** Localised value ("90.58%"), or the "no score recorded" text. */
  valueText: string;
  /** Short model description. */
  model: string;
  /** Localised validation split including the image count. */
  split: string;
  highlight: boolean;
};

const HIGHLIGHT = new Set<string>(HIGHLIGHT_IDS);

export function landscapeRows(lang: Locale, t: LandscapeCopy): LandscapeRow[] {
  const splits: Record<string, string> = t.splits;
  const models: Record<string, string> = t.models;
  return EXPERIMENTS.map((experiment) => {
    const splitBase = splits[experiment.evaluation.split];
    if (splitBase === undefined) throw new Error(`No translation for split "${experiment.evaluation.split}"`);
    const images = experiment.evaluation.images;
    const result = experiment.result;
    return {
      id: experiment.id,
      short: experiment.id.slice(4),
      stage: experiment.stage,
      value: result ? result.value : null,
      metric: result ? (result.name === "mAP50" ? t.metricB : t.metricA) : t.noScore,
      valueText: result ? formatScoreLocale(lang, result.value, true) : t.noScore,
      model: models[experiment.id] ?? experiment.model,
      split: images === null ? splitBase : `${splitBase}, ${fmt(t.images, { n: formatInt(lang, images) })}`,
      highlight: HIGHLIGHT.has(experiment.id),
    };
  });
}
