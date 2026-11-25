import type { Locale } from "$i18n/config";

/** A decimal number with a fixed number of digits and the language's decimal separator: 5.46 becomes "5,46" in German. */
export function formatDecimal(lang: Locale, value: number, digits = 2): string {
  const text = value.toFixed(digits);
  return lang === "de" ? text.replace(".", ",") : text;
}
