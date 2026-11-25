/**
 * The one typed API client the app uses. `api.legacy.*` covers the existing `/api/*` routes and
 * `api.v1.*` covers `/api/v1` (CONTRACT section 7). With VITE_MOCK=1 every call is answered by
 * the in-browser mock layer; the mock module is only imported in that mode.
 */
import { createHttpClient, type FetchLike } from './client';
import { createEndpoints } from './endpoints';

export const runtimeFetch: FetchLike = async (input, init) => {
  if (__MIRA_MOCK__) {
    const { mockFetch } = await import('../mock/mock-fetch');
    return mockFetch(input, init);
  }
  return fetch(input, init);
};

/** Builds an endpoint set on top of any fetch implementation (used by the tests). */
export function createApi(fetchImpl: FetchLike) {
  return createEndpoints(createHttpClient({ fetch: fetchImpl }));
}

export const api = createApi(runtimeFetch);

export type Api = typeof api;

export * from './errors';
export { sessionExportUrl, unwrapList, TIMEOUTS, LIMITS } from './endpoints';
export type { ExportFormat, SessionListParams, DetectionQuery } from './endpoints';
