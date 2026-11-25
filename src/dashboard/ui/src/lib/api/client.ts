/**
 * Low-level HTTP: URL building, bodies, timeouts, JSON parsing. No endpoint names here.
 * Covered by client.test.ts. Endpoints live in endpoints.ts.
 */
import { ApiError, errorFromResponse } from './errors';

export type FetchLike = (input: string, init?: RequestInit) => Promise<Response>;

export type QueryValue = string | number | boolean | null | undefined;
export type QueryParams = Record<string, QueryValue>;

export interface RequestOptions {
  method?: 'GET' | 'POST' | 'PATCH' | 'DELETE';
  query?: QueryParams;
  /** Sent as application/json. */
  json?: unknown;
  /** Sent as the raw body with an explicit content type (the image endpoint needs this). */
  raw?: { body: Blob; contentType: string };
  /** Sent as multipart/form-data. The browser sets the boundary, so no Content-Type is set here. */
  form?: FormData;
  signal?: AbortSignal;
  timeoutMs?: number;
}

export interface HttpClientOptions {
  fetch: FetchLike;
  baseUrl?: string;
  defaultTimeoutMs?: number;
}

/** Builds `/path?a=1&b=true`. Empty, null and undefined query values are left out. */
export function buildUrl(path: string, query?: QueryParams, baseUrl = ''): string {
  const params = new URLSearchParams();
  if (query) {
    for (const [key, value] of Object.entries(query)) {
      if (value === undefined || value === null || value === '') continue;
      params.append(key, String(value));
    }
  }
  const search = params.toString();
  return `${baseUrl}${path}${search ? `?${search}` : ''}`;
}

export interface HttpClient {
  request<T>(path: string, options?: RequestOptions): Promise<T>;
}

export function createHttpClient(options: HttpClientOptions): HttpClient {
  const defaultTimeout = options.defaultTimeoutMs ?? 15_000;
  const baseUrl = options.baseUrl ?? '';

  return {
    async request<T>(path: string, request: RequestOptions = {}): Promise<T> {
      const url = buildUrl(path, request.query, baseUrl);
      const headers: Record<string, string> = { Accept: 'application/json' };
      let body: BodyInit | undefined;

      if (request.json !== undefined) {
        headers['Content-Type'] = 'application/json';
        body = JSON.stringify(request.json);
      } else if (request.raw) {
        headers['Content-Type'] = request.raw.contentType;
        body = request.raw.body;
      } else if (request.form) {
        body = request.form;
      }

      const controller = new AbortController();
      let timedOut = false;
      const timer = setTimeout(() => {
        timedOut = true;
        controller.abort();
      }, request.timeoutMs ?? defaultTimeout);
      const onExternalAbort = () => controller.abort();
      if (request.signal) {
        if (request.signal.aborted) controller.abort();
        else request.signal.addEventListener('abort', onExternalAbort, { once: true });
      }

      try {
        let response: Response;
        try {
          response = await options.fetch(url, {
            method: request.method ?? 'GET',
            headers,
            body,
            signal: controller.signal,
          });
        } catch (error) {
          if (timedOut) {
            throw new ApiError({ kind: 'timeout', path, message: 'The server took too long to answer.' });
          }
          if (request.signal?.aborted) {
            throw new ApiError({ kind: 'aborted', path, message: 'The request was cancelled.' });
          }
          if (error instanceof ApiError) throw error;
          throw new ApiError({ kind: 'network', path, message: 'The dashboard cannot reach the server.' });
        }

        if (response.status === 204) {
          return undefined as T;
        }

        const payload = await readBody(response, path, timedOut);

        if (!response.ok) {
          throw errorFromResponse(response.status, path, payload);
        }
        return payload as T;
      } finally {
        clearTimeout(timer);
        request.signal?.removeEventListener('abort', onExternalAbort);
      }
    },
  };
}

async function readBody(response: Response, path: string, timedOut: boolean): Promise<unknown> {
  const text = await response.text().catch((error: unknown) => {
    if (timedOut) throw new ApiError({ kind: 'timeout', path, message: 'The server took too long to answer.' });
    throw error;
  });
  if (!text) return undefined;
  try {
    return JSON.parse(text) as unknown;
  } catch {
    if (!response.ok) return undefined;
    throw new ApiError({ kind: 'invalid', path, status: response.status, message: 'The server sent invalid JSON.' });
  }
}
