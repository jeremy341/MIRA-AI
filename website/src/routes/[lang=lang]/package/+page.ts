import { LOCALES } from "$i18n/config";
import type { EntryGenerator } from "./$types";

export const entries: EntryGenerator = () => LOCALES.map((lang) => ({ lang }));
