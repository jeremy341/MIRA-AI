/**
 * A `fetch` replacement for mock mode. It turns a request into a MockRequest, runs the mock
 * backend, and returns a real Response, so the typed client's error handling runs unchanged.
 */
import { handleMockRequest } from './backend';
import { MOCK_MARKER } from './fixtures';

/** Simulated network time. Long enough for loading states to be visible in screenshots. */
export const MOCK_LATENCY_MS = 140;

function delay(ms: number, signal?: AbortSignal | null): Promise<void> {
  return new Promise((resolve, reject) => {
    if (signal?.aborted) {
      reject(new DOMException('The operation was aborted.', 'AbortError'));
      return;
    }
    const timer = setTimeout(() => {
      signal?.removeEventListener('abort', onAbort);
      resolve();
    }, ms);
    const onAbort = () => {
      clearTimeout(timer);
      reject(new DOMException('The operation was aborted.', 'AbortError'));
    };
    signal?.addEventListener('abort', onAbort, { once: true });
  });
}

function headerValue(headers: HeadersInit | undefined, name: string): string {
  if (!headers) return '';
  if (headers instanceof Headers) return headers.get(name) ?? '';
  if (Array.isArray(headers)) {
    const pair = headers.find(([key]) => key.toLowerCase() === name.toLowerCase());
    return pair?.[1] ?? '';
  }
  const key = Object.keys(headers).find((k) => k.toLowerCase() === name.toLowerCase());
  return key ? String((headers as Record<string, string>)[key]) : '';
}

export async function mockFetch(input: string, init?: RequestInit): Promise<Response> {
  const url = new URL(input, 'http://mock.local');
  const method = (init?.method ?? 'GET').toUpperCase();
  const contentType = headerValue(init?.headers, 'Content-Type');

  await delay(MOCK_LATENCY_MS, init?.signal);

  let json: unknown = undefined;
  let form: FormData | null = null;
  let raw: Blob | null = null;
  const body = init?.body;
  if (body instanceof FormData) {
    form = body;
  } else if (body instanceof Blob) {
    raw = body;
  } else if (typeof body === 'string') {
    try {
      json = JSON.parse(body) as unknown;
    } catch {
      json = undefined;
    }
  }

  const reply = await handleMockRequest({
    method,
    path: url.pathname,
    query: url.searchParams,
    json,
    form,
    raw,
    contentType,
  });

  if (reply.body === undefined) {
    return new Response(null, { status: reply.status, headers: { 'X-Mira-Mock': MOCK_MARKER } });
  }
  return new Response(JSON.stringify(reply.body), {
    status: reply.status,
    headers: { 'Content-Type': 'application/json', 'X-Mira-Mock': MOCK_MARKER },
  });
}
