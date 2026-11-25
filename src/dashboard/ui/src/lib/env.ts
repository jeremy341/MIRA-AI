/**
 * Build-time mode flag. Vite replaces `import.meta.env.VITE_MOCK` with a literal, so the mock
 * modules are dead code (and absent from the bundle) in a normal build.
 */
export const MOCK_MODE: boolean = import.meta.env.VITE_MOCK === '1';
