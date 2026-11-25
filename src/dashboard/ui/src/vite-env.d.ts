/// <reference types="svelte" />
/// <reference types="vite/client" />

/**
 * Build-time flag from vite.config.ts. "true" only in mock mode (VITE_MOCK=1 or `pnpm dev:mock`).
 * Replaced by a literal at build time, so the mock modules are not bundled into the real build.
 */
declare const __MIRA_MOCK__: boolean;
