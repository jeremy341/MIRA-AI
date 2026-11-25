/**
 * Locale configuration and path helpers. Framework-free so it can be unit tested.
 *
 * To add a language: add its code to LOCALES, add a dictionary file next to en.ts,
 * register it in index.ts. `tsc` then fails until every key exists. See website/README.md.
 */

export const LOCALES = ["en", "de"] as const;
export type Locale = (typeof LOCALES)[number];
export const DEFAULT_LOCALE: Locale = "en";

export function isLocale(value: string | null | undefined): value is Locale {
  return typeof value === "string" && (LOCALES as readonly string[]).includes(value);
}

/** `Accept-Language` style tags such as "de-DE", "de" or "en-GB" to a supported locale. */
export function localeFromTag(tag: string | null | undefined): Locale {
  const primary = (tag ?? "").toLowerCase().split("-")[0];
  return isLocale(primary) ? primary : DEFAULT_LOCALE;
}

/**
 * Pick a locale from the browser's preference list (navigator.languages, falling back
 * to navigator.language). The first entry that maps to a supported language wins, so
 * "de-AT" gets German. Everything else gets English.
 */
export function pickLocale(languages: readonly string[] | null | undefined): Locale {
  for (const tag of languages ?? []) {
    const primary = tag.toLowerCase().split("-")[0];
    if (isLocale(primary)) return primary;
  }
  return DEFAULT_LOCALE;
}

/** Internal path without a language prefix, always starting with "/" ("/" for home). */
export function normalizePath(path: string): string {
  if (!path.startsWith("/")) return `/${path}`;
  return path;
}

/** "/docs/cli#train" with "de" becomes "/de/docs/cli#train"; "/" becomes "/de". */
export function localePath(lang: Locale, path: string): string {
  const clean = normalizePath(path);
  if (clean === "/") return `/${lang}`;
  if (clean.startsWith("/#")) return `/${lang}${clean.slice(1)}`;
  return `/${lang}${clean}`;
}

/** True when the path already starts with a supported language segment. */
export function hasLocalePrefix(path: string): boolean {
  const first = normalizePath(path).split("/")[1] ?? "";
  return isLocale(first);
}

/** "/de/docs/cli" becomes "/docs/cli"; "/de" becomes "/". Paths without a prefix are returned unchanged. */
export function stripLocale(pathname: string): string {
  const parts = normalizePath(pathname).split("/");
  if (isLocale(parts[1])) {
    const rest = `/${parts.slice(2).join("/")}`;
    return rest === "/" ? "/" : rest.replace(/\/$/, "") || "/";
  }
  return normalizePath(pathname);
}

/** Same page in another language: "/en/docs/cli" to "/de/docs/cli". */
export function switchLocalePath(pathname: string, target: Locale): string {
  return localePath(target, stripLocale(pathname));
}

/**
 * Metadata `alternates` for one page: canonical, hreflang for every language and x-default.
 * `path` has no language prefix ("/" for home, "/docs/cli" for a doc).
 */
export function alternatesFor(lang: Locale, path: string) {
  const languages: Record<string, string> = {};
  for (const locale of LOCALES) languages[locale] = localePath(locale, path);
  languages["x-default"] = normalizePath(path) === "/" ? "/" : localePath(DEFAULT_LOCALE, path);
  return { canonical: localePath(lang, path), languages };
}
