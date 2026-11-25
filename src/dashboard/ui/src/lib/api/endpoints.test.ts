import { describe, expect, it } from 'vitest';
import { createApi, sessionExportUrl, unwrapList } from './index';
import type { FetchLike } from './client';

function capture(body: unknown = {}, status = 200) {
  const calls: Array<{ url: string; init?: RequestInit }> = [];
  const fetchImpl: FetchLike = async (url, init) => {
    calls.push({ url, init });
    return status === 204
      ? new Response(null, { status })
      : new Response(JSON.stringify(body), { status, headers: { 'Content-Type': 'application/json' } });
  };
  return { api: createApi(fetchImpl), calls };
}

describe('legacy endpoints', () => {
  it('uses the existing routes and query names', async () => {
    const { api, calls } = capture({});
    await api.legacy.getStatistics(60);
    await api.legacy.getMetricsHistory(100);
    await api.legacy.getRecentDetections(50);
    await api.legacy.startStream();
    expect(calls.map((c) => c.url)).toEqual([
      '/api/statistics?period=60',
      '/api/metrics/history?limit=100',
      '/api/detections/recent?limit=50',
      '/api/stream/start',
    ]);
    expect(calls[3].init?.method).toBe('POST');
  });

  it('sends the image confidence as a query value with the raw image content type', async () => {
    const { api, calls } = capture({ image: 'data:image/png;base64,', detections: [] });
    const blob = new Blob([new Uint8Array([0x89])], { type: 'image/png' });
    await api.legacy.detectImage(blob, 'image/png', 0.55);
    expect(calls[0].url).toBe('/api/detect/image?confidence=0.55');
    expect((calls[0].init?.headers as Record<string, string>)['Content-Type']).toBe('image/png');
  });
});

describe('v1 endpoints', () => {
  it('lists sessions with filters', async () => {
    const { api, calls } = capture({ sessions: [], total: 0 });
    await api.v1.listSessions({ status: 'active', limit: 1 });
    expect(calls[0].url).toBe('/api/v1/sessions?limit=1&status=active');
  });

  it('encodes session ids in paths', async () => {
    const { api, calls } = capture({});
    await api.v1.getSession('a/b c');
    expect(calls[0].url).toBe('/api/v1/sessions/a%2Fb%20c');
  });

  it('sends the timeline bucket size', async () => {
    const { api, calls } = capture({ duration_seconds: 0, bucket_seconds: 2, buckets: [] });
    await api.v1.getSessionTimeline('s1', 2);
    expect(calls[0].url).toBe('/api/v1/sessions/s1/timeline?bucket_seconds=2');
  });

  it('sends compare as multipart with no manual content type', async () => {
    const { api, calls } = capture({});
    const form = new FormData();
    form.append('models', 'a.pt,b.pt');
    await api.v1.runCompare(form);
    expect(calls[0].url).toBe('/api/v1/compare');
    expect((calls[0].init?.headers as Record<string, string>)['Content-Type']).toBeUndefined();
  });

  it('accepts a bare array or a wrapped list for compare and benchmark listings', async () => {
    const bare = capture([{ id: 'c1', created_at: '2026-11-25T00:00:00Z', input_name: 'x.jpg', models: [] }]);
    expect(await bare.api.v1.listComparisons(5)).toHaveLength(1);
    const wrapped = capture({ runs: [{ id: 'b1' }] });
    expect(await wrapped.api.v1.listBenchmarkRuns(5)).toEqual([{ id: 'b1' }]);
  });

  it('posts arm commands and feedback', async () => {
    const { api, calls } = capture({ id: 3 }, 202);
    await api.v1.sendArmCommand({ action: 'home' });
    await api.v1.setArmFeedback(3, true);
    expect(calls[0].url).toBe('/api/v1/arm/commands');
    expect(calls[1].url).toBe('/api/v1/arm/events/3/feedback');
    expect(calls[1].init?.body).toBe('{"correct":true}');
  });

  it('deletes with 204 and resolves to undefined', async () => {
    const { api } = capture({}, 204);
    await expect(api.v1.deleteSession('s1')).resolves.toBeUndefined();
  });
});

describe('unwrapList', () => {
  it('returns arrays as they are', () => {
    expect(unwrapList([1, 2], ['items'])).toEqual([1, 2]);
  });

  it('finds the first matching key in a wrapped object', () => {
    expect(unwrapList({ other: [9], runs: [1] }, ['runs'])).toEqual([1]);
  });

  it('returns an empty list when nothing matches', () => {
    expect(unwrapList({ nothing: true }, ['runs'])).toEqual([]);
    expect(unwrapList(null, ['runs'])).toEqual([]);
  });
});

describe('sessionExportUrl', () => {
  it('builds the three export URLs', () => {
    expect(sessionExportUrl('s1', 'csv')).toBe('/api/v1/sessions/s1/export.csv');
    expect(sessionExportUrl('s1', 'json')).toBe('/api/v1/sessions/s1/export.json');
    expect(sessionExportUrl('s1', 'report')).toBe('/api/v1/sessions/s1/report.html');
  });

  it('adds download=1 only for the report', () => {
    expect(sessionExportUrl('s1', 'report', { download: true })).toBe('/api/v1/sessions/s1/report.html?download=1');
    expect(sessionExportUrl('s1', 'csv', { download: true })).toBe('/api/v1/sessions/s1/export.csv');
  });
});
