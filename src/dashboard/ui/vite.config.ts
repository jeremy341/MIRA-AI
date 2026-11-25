import { defineConfig, loadEnv } from 'vite';
import { svelte } from '@sveltejs/vite-plugin-svelte';

// MIRA_API_TARGET points the dev proxy at another backend (default: the FastAPI server on 8000).
// Mock mode (VITE_MOCK=1, or `pnpm dev:mock`) answers every API and WebSocket call in the browser.
export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, '.', '');
  const target = env.MIRA_API_TARGET || 'http://127.0.0.1:8000';
  const mock = mode === 'mock' || env.VITE_MOCK === '1' ? '1' : '';

  return {
    // Relative base: FastAPI serves the build from `/`, but asset paths stay relative.
    base: './',
    plugins: [svelte()],
    define: {
      'import.meta.env.VITE_MOCK': JSON.stringify(mock),
    },
    server: {
      host: '127.0.0.1',
      port: 5173,
      proxy: {
        '/api': { target, changeOrigin: false },
        '/ws': { target, ws: true, changeOrigin: false },
      },
    },
    build: {
      // Output goes where FastAPI serves the dashboard from. Gitignored (frontend/dist/).
      outDir: '../frontend/dist',
      emptyOutDir: true,
      target: 'es2022',
    },
    test: {
      environment: 'node',
      include: ['src/**/*.test.ts'],
      env: { VITE_MOCK: '' },
    },
  };
});
