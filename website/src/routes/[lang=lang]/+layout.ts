import type { Locale } from "$i18n/config";
import type { LayoutLoad } from "./$types";

// The `lang` matcher (src/params/lang.ts) only lets "en" and "de" through, so anything else is a 404.
export const load: LayoutLoad = ({ params }) => ({ lang: params.lang as Locale });
