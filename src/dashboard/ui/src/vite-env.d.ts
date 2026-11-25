/// <reference types="svelte" />
/// <reference types="vite/client" />

interface ImportMetaEnv {
  /** "1" routes every API and WebSocket call to the in-browser mock layer. */
  readonly VITE_MOCK?: string;
}
