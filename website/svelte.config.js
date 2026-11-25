import adapter from "@sveltejs/adapter-static";
import { vitePreprocess } from "@sveltejs/vite-plugin-svelte";

/** @type {import('@sveltejs/kit').Config} */
export default {
  preprocess: vitePreprocess(),
  kit: {
    alias: { $i18n: "src/i18n" },
    // Absolute asset URLs (/_app/...) so a page behaves the same at /en and /en/ on any static host.
    paths: { relative: false },
    // Fully static site: every route is prerendered (see src/routes/+layout.ts), no server at runtime.
    // `strict` (the default) makes the build fail if a route is not prerendered.
    adapter: adapter({ pages: "build", assets: "build" }),
    prerender: {
      // A broken internal link or in-page anchor fails the build instead of shipping a dead link.
      handleHttpError: "fail",
      handleMissingId: "fail",
    },
  },
};
