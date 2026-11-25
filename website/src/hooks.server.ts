import type { Handle } from "@sveltejs/kit";

/**
 * Fonts worth a <link rel="preload"> because they paint the first screen: the latin subsets of Plus Jakarta Sans
 * (text and display) and Space Mono (the install command and numbers above the fold). Every other subset
 * (latin-ext, cyrillic, ...) and any other weight stays lazy, so a page only fetches what it renders.
 */
const FIRST_PAINT_FONTS = [/plus-jakarta-sans-latin-wght-normal\./, /space-mono-latin-400-normal\./];

export const handle: Handle = ({ event, resolve }) => {
  const lang = event.url.pathname.split("/")[1] === "de" ? "de" : "en";
  return resolve(event, {
    transformPageChunk: ({ html }) => html.replace("%lang%", lang),
    preload: ({ type, path }) =>
      type === "js" || type === "css" || (type === "font" && FIRST_PAINT_FONTS.some((pattern) => pattern.test(path))),
  });
};
