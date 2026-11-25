import type { Locale } from "./config";

/** Fill {name} placeholders. Unknown placeholders are left as they are so a typo is visible. */
export function fmt(template: string, vars: Record<string, string | number>): string {
  return template.replace(/\{(\w+)\}/g, (match, key: string) => (key in vars ? String(vars[key]) : match));
}

/** Whole number with the language's thousands separator: 10096 becomes "10,096" or "10.096". */
export function formatInt(lang: Locale, value: number): string {
  return new Intl.NumberFormat(lang === "de" ? "de-DE" : "en-US").format(value);
}

/**
 * Score with the digits the experiment log uses (61 becomes "61.0", 90.58 stays "90.58"),
 * with a decimal comma in German. Pass `percent` for "90.58%" / "90,58 %".
 */
export function formatScoreLocale(lang: Locale, value: number, percent = false): string {
  const text = Number.isInteger(value) ? value.toFixed(1) : String(value);
  const local = lang === "de" ? text.replace(".", ",") : text;
  if (!percent) return local;
  return lang === "de" ? `${local} %` : `${local}%`;
}

/** Confidence 0..1 with two decimals: "0.91" or "0,91". */
export function formatConfidence(lang: Locale, value: number): string {
  const text = value.toFixed(2);
  return lang === "de" ? text.replace(".", ",") : text;
}

/** "mira_exp019" becomes "MIRA EXP-019"; anything else is returned as it is. */
export function formatModelName(model: string): string {
  const match = /exp[_-]?(\d{3})/i.exec(model);
  return match ? `MIRA EXP-${match[1]}` : model || "MIRA";
}
