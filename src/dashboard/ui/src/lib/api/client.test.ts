import { describe, expect, it } from 'vitest';
import { buildUrl, createHttpClient, type FetchLike } from './client';
import { ApiError, describeError, isConflict, isRouteMissing } from './errors';

function jsonResponse(status: number, body?: unknown): Response {
  if (body === undefined) return new Response(null, { status });
  return new Response(JSON.stringify(body), { status, headers: { 'Content-Type': 'application/json' } });
}

function recorder(reply: (url: string, init?: RequestInit) => Promise<Response> | Response) {
  const calls: Array<{ url: string; init: RequestInit | undefined }> = [];
  const fetchImpl: FetchLike = async (url, init) => {
    calls.push({ url, init });
    return reply(url, init);
  };
  return { fetchImpl, calls };
}

describe('buildUrl', () => {
  it('leaves out empty, null and undefined query values', () => {
    expect(buildUrl('/api/x', { a: 1, b: undefined, c: null, d: '', e: false })).toBe('/api/x?a=1&e=false');
  });

  it('returns the bare path when there is no query', () => {
    expect(buildUrl('/api/status')).toBe('/api/status');
    expect(buildUrl('/api/status', {})).toBe('/api/status');
  });

  it('prefixes a base url when one is given', () => {
    expect(buildUrl('/api/models', { limit: 5 }, 'http://127.0.0.1:8000')).toBe('http://127.0.0.1:8000/api/models?limit=5');
  });

  it('encodes values', () => {
    expect(buildUrl('/api/v1/sessions', { name: 'a b&c' })).toBe('/api/v1/sessions?name=a+b%26c');
  });
});

describe('request bodies', () => {
  it('sends JSON with a JSON content type', async () => {
    const { fetchImpl, calls } = recorder(() => jsonResponse(200, { ok: true }));
    const http = createHttpClient({ fetch: fetchImpl });
    await http.request('/api/camera/initialize', { method: 'POST', json: { index: 0 } });
    const init = calls[0].init as RequestInit;
    expect(init.method).toBe('POST');
    expect((init.headers as Record<string, string>)['Content-Type']).toBe('application/json');
    expect(init.body).toBe('{"index":0}');
  });

  it('sends raw bodies with the given content type', async () => {
    const { fetchImpl, calls } = recorder(() => jsonResponse(200, { detections: [], image: '' }));
    const http = createHttpClient({ fetch: fetchImpl });
    const blob = new Blob([new Uint8Array([1, 2, 3])], { type: 'image/png' });
    await http.request('/api/detect/image', { method: 'POST', raw: { body: blob, contentType: 'image/png' } });
    const init = calls[0].init as RequestInit;
    expect((init.headers as Record<string, string>)['Content-Type']).toBe('image/png');
    expect(init.body).toBe(blob);
  });

  it('leaves the Content-Type to the browser for FormData', async () => {
    const { fetchImpl, calls } = recorder(() => jsonResponse(202, { job_id: 'j', session_id: 's' }));
    const http = createHttpClient({ fetch: fetchImpl });
    const form = new FormData();
    form.append('model_name', 'mira_exp018.pt');
    await http.request('/api/v1/batch/video', { method: 'POST', form });
    const init = calls[0].init as RequestInit;
    expect((init.headers as Record<string, string>)['Content-Type']).toBeUndefined();
    expect(init.body).toBe(form);
  });
});

describe('responses', () => {
  it('returns undefined for 204', async () => {
    const { fetchImpl } = recorder(() => jsonResponse(204));
    const http = createHttpClient({ fetch: fetchImpl });
    await expect(http.request('/api/v1/sessions/x', { method: 'DELETE' })).resolves.toBeUndefined();
  });

  it('maps a 409 with missing prerequisites to a message and a missing list', async () => {
    const { fetchImpl } = recorder(() =>
      jsonResponse(409, {
        detail: { message: 'Configure the camera and load a model before starting the stream.', missing: ['camera', 'model'] },
      }),
    );
    const http = createHttpClient({ fetch: fetchImpl });
    const error = await http.request('/api/stream/start', { method: 'POST' }).catch((e: unknown) => e);
    expect(error).toBeInstanceOf(ApiError);
    expect((error as ApiError).status).toBe(409);
    expect((error as ApiError).missing).toEqual(['camera', 'model']);
    expect((error as ApiError).message).toMatch(/Configure the camera/);
    expect(isConflict(error)).toBe(true);
  });

  it('maps a string detail to the message', async () => {
    const { fetchImpl } = recorder(() => jsonResponse(409, { detail: 'Stop the stream before changing camera settings' }));
    const http = createHttpClient({ fetch: fetchImpl });
    const error = await http.request('/api/camera/initialize', { method: 'POST', json: {} }).catch((e: unknown) => e);
    expect(describeError(error)).toBe('Stop the stream before changing camera settings');
  });

  it('turns a FastAPI validation list into a readable sentence', async () => {
    const { fetchImpl } = recorder(() =>
      jsonResponse(422, { detail: [{ loc: ['body', 'fps'], msg: 'Input should be less than or equal to 240' }] }),
    );
    const http = createHttpClient({ fetch: fetchImpl });
    const error = await http.request('/api/x', { method: 'POST', json: {} }).catch((e: unknown) => e);
    expect((error as ApiError).message).toBe('fps: Input should be less than or equal to 240');
  });

  it('falls back to a status message when the body has no detail', async () => {
    const { fetchImpl } = recorder(() => new Response('oops', { status: 500 }));
    const http = createHttpClient({ fetch: fetchImpl });
    const error = await http.request('/api/x').catch((e: unknown) => e);
    expect((error as ApiError).status).toBe(500);
    expect((error as ApiError).message).toBe('Request failed (HTTP 500).');
  });

  it('reports invalid JSON on a successful response as an invalid error', async () => {
    const { fetchImpl } = recorder(() => new Response('<html>', { status: 200 }));
    const http = createHttpClient({ fetch: fetchImpl });
    const error = await http.request('/api/x').catch((e: unknown) => e);
    expect((error as ApiError).kind).toBe('invalid');
  });
});

describe('transport failures', () => {
  it('reports a network failure as a network error', async () => {
    const fetchImpl: FetchLike = async () => {
      throw new TypeError('Failed to fetch');
    };
    const http = createHttpClient({ fetch: fetchImpl });
    const error = await http.request('/api/status').catch((e: unknown) => e);
    expect((error as ApiError).kind).toBe('network');
    expect(describeError(error)).toMatch(/cannot reach the server/);
  });

  it('times out when the server does not answer in time', async () => {
    const fetchImpl: FetchLike = (_url, init) =>
      new Promise((_resolve, reject) => {
        init?.signal?.addEventListener('abort', () => reject(new DOMException('aborted', 'AbortError')));
      });
    const http = createHttpClient({ fetch: fetchImpl });
    const error = await http.request('/api/status', { timeoutMs: 20 }).catch((e: unknown) => e);
    expect((error as ApiError).kind).toBe('timeout');
    expect(describeError(error)).toMatch(/too long/);
  });

  it('reports a cancelled request as aborted, not as a network error', async () => {
    const controller = new AbortController();
    const fetchImpl: FetchLike = (_url, init) =>
      new Promise((_resolve, reject) => {
        init?.signal?.addEventListener('abort', () => reject(new DOMException('aborted', 'AbortError')));
      });
    const http = createHttpClient({ fetch: fetchImpl });
    const pending = http.request('/api/status', { signal: controller.signal, timeoutMs: 5000 }).catch((e: unknown) => e);
    controller.abort();
    const error = await pending;
    expect((error as ApiError).kind).toBe('aborted');
  });
});

describe('404 degradation', () => {
  it('treats FastAPI "Not Found" as a missing route', async () => {
    const { fetchImpl } = recorder(() => jsonResponse(404, { detail: 'Not Found' }));
    const http = createHttpClient({ fetch: fetchImpl });
    const error = await http.request('/api/v1/sessions').catch((e: unknown) => e);
    expect(isRouteMissing(error)).toBe(true);
    expect(describeError(error)).toBe('This is not available on the server yet.');
  });

  it('does not treat an unknown id as a missing route', async () => {
    const { fetchImpl } = recorder(() => jsonResponse(404, { detail: 'Session not found' }));
    const http = createHttpClient({ fetch: fetchImpl });
    const error = await http.request('/api/v1/sessions/nope').catch((e: unknown) => e);
    expect(isRouteMissing(error)).toBe(false);
    expect(describeError(error)).toBe('Session not found');
  });

  it('treats 501 and 405 as not available yet', async () => {
    for (const status of [501, 405]) {
      const { fetchImpl } = recorder(() => jsonResponse(status, { detail: 'stub' }));
      const http = createHttpClient({ fetch: fetchImpl });
      const error = await http.request('/api/v1/arm/status').catch((e: unknown) => e);
      expect(isRouteMissing(error)).toBe(true);
    }
  });

  it('describeError falls back for unknown error values', () => {
    expect(describeError('boom', 'Fallback text')).toBe('Fallback text');
    expect(describeError(new Error('Plain message'))).toBe('Plain message');
  });
});
