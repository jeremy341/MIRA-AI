import {
  EXP018_019_CLASSES,
  EXP014_CLASSES,
  EXP019_TFLITE_320,
  FIELD_BENCHMARK,
  PLANNED_EXPERIMENT as PLANNED,
  getExperiment,
} from "../../lib/experiments";
import { DATASET_ORIGINS_URL, EXPERIMENT_LOG_URL, FACTS, GITHUB_URL, HF_URL } from "../../lib/site";
import type { Locale } from "../config";
import { formatInt, formatScoreLocale } from "../format";

/** A decimal number with the language's decimal separator and a fixed number of digits. */
export function decimal(lang: Locale, value: number, digits = 1): string {
  const text = value.toFixed(digits);
  return lang === "de" ? text.replace(".", ",") : text;
}

function mapOf(rows: typeof EXP018_019_CLASSES, cls: string, key: "precision" | "recall" | "map50"): number {
  const row = rows.find((r) => r.cls === cls);
  if (!row) throw new Error(`Missing class row ${cls}`);
  return row[key];
}

function score(id: string): number {
  const run = getExperiment(id);
  if (!run.result) throw new Error(`No score for ${id}`);
  return run.result.value;
}

/**
 * Values that the research copy mentions as {placeholders}. They come from the experiment data
 * (experiments.ts, site.ts), so a number in the copy can never drift away from the data.
 */
export function researchVars(lang: Locale): Record<string, string> {
  const pct = (v: number) => formatScoreLocale(lang, v, true);
  return {
    exp014: pct(score("EXP-014")),
    exp017: pct(score("EXP-017")),
    exp018: pct(score("EXP-018")),
    exp019: pct(score("EXP-019")),
    plasticRecall: pct(FACTS.exp019PlasticRecall),
    plasticPrecision: pct(mapOf(EXP018_019_CLASSES, "plastic", "precision")),
    trashPrecision: pct(mapOf(EXP018_019_CLASSES, "trash", "precision")),
    trashBefore: pct(mapOf(EXP014_CLASSES, "trash", "map50")),
    trashAfter: pct(mapOf(EXP018_019_CLASSES, "trash", "map50")),
    val: formatInt(lang, FACTS.validationImages),
    test: formatInt(lang, FACTS.testImages),
    train: formatInt(lang, FACTS.trainImages),
    tflite320: pct(EXP019_TFLITE_320.map50),
    drop: decimal(lang, score("EXP-019") - EXP019_TFLITE_320.map50, 1),
    fieldConf: decimal(lang, FIELD_BENCHMARK.confidence, 1),
    fieldBest: pct(FIELD_BENCHMARK.bestF1),
    fieldInt8: pct(FIELD_BENCHMARK.bestInt8F1),
    originsUrl: DATASET_ORIGINS_URL,
    logUrl: EXPERIMENT_LOG_URL,
    hfUrl: HF_URL,
    githubUrl: GITHUB_URL,
    epochs: String(PLANNED.epochs),
    batch: String(PLANNED.batchSize),
    imgsz: String(PLANNED.imageSize),
    optimizer: PLANNED.optimizer,
    lr0: decimal(lang, PLANNED.lr0, 3),
    lrf: decimal(lang, PLANNED.lrf, 2),
    wd: decimal(lang, PLANNED.weightDecay, 4),
    patience: String(PLANNED.patience),
    seed: String(PLANNED.seed),
  };
}

/** Placeholders that components fill themselves, per text. */
export const COMPONENT_PLACEHOLDERS = ["shown", "total", "n", "conf", "predicted", "trueClass"] as const;
