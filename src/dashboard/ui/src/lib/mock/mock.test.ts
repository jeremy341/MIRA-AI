import { beforeEach, describe, expect, it } from 'vitest';
import { CLASS_NAMES, type ClassName, type Detection, type SessionDetection } from '../types';
import {
  MOCK_ARM_EVENTS,
  MOCK_BENCHMARKS,
  MOCK_COMPARISONS,
  MOCK_JOBS,
  MOCK_MODELS,
  MOCK_SESSIONS,
  MOCK_STATISTICS,
  mockHardwareHistory,
  mockMetricsHistory,
  mockRecentDetections,
  sessionDetectionsFor,
  sessionTimelineFor,
} from './fixtures';
import { handleMockRequest, resetMockState, state, type MockReply } from './backend';

const ISO = /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?(Z|[+-]\d{2}:\d{2})$/;
const isBox = (bbox: unknown): boolean =>
  Array.isArray(bbox) && bbox.length === 4 && bbox.every((n) => typeof n === 'number' && Number.isFinite(n));

function checkDetection(d: Detection | SessionDetection) {
  expect(CLASS_NAMES).toContain(('class_name' in d ? d.class_name : '') as ClassName);
  expect(d.confidence).toBeGreaterThanOrEqual(0);
  expect(d.confidence).toBeLessThanOrEqual(1);
  expect(isBox(d.bbox)).toBe(true);
  const [x1, y1, x2, y2] = d.bbox;
  expect(x2).toBeGreaterThan(x1);
  expect(y2).toBeGreaterThan(y1);
}

describe('fixtures validate against the contract', () => {
  it('models have valid names, sizes and input sizes', () => {
    for (const model of MOCK_MODELS) {
      expect(model.name).toMatch(/\.(pt|tflite)$/);
      expect(model.size_mb).toBeGreaterThan(0);
      expect([320, 416, 640]).toContain(model.input_size);
    }
    expect(MOCK_MODELS.filter((m) => m.recommended)).toHaveLength(1);
  });

  it('sessions have unique ids, valid statuses and consistent totals', () => {
    const ids = new Set(MOCK_SESSIONS.map((s) => s.id));
    expect(ids.size).toBe(MOCK_SESSIONS.length);
    for (const session of MOCK_SESSIONS) {
      expect(['camera', 'image', 'video', 'batch']).toContain(session.source);
      expect(['active', 'completed', 'failed']).toContain(session.status);
      expect(ISO.test(session.started_at)).toBe(true);
      const sum = CLASS_NAMES.reduce((total, cls) => total + session.class_counts[cls], 0);
      expect(sum).toBe(session.total_detections);
      expect(Object.keys(session.class_counts).sort()).toEqual([...CLASS_NAMES].sort());
    }
  });

  it('session detections and timelines follow the shapes', () => {
    const session = MOCK_SESSIONS[0];
    const rows = sessionDetectionsFor(session, 25);
    expect(rows).toHaveLength(25);
    for (const row of rows) {
      checkDetection(row);
      expect(row.offset_seconds).toBeGreaterThanOrEqual(0);
      expect(ISO.test(row.ts)).toBe(true);
    }
    const timeline = sessionTimelineFor(session, 5);
    expect(timeline.bucket_seconds).toBe(5);
    expect(timeline.buckets.length).toBeGreaterThan(0);
    for (const bucket of timeline.buckets) {
      expect(bucket.avg_confidence === null || (bucket.avg_confidence >= 0 && bucket.avg_confidence <= 1)).toBe(true);
    }
  });

  it('statistics, metrics and recent detections are in range', () => {
    expect(MOCK_STATISTICS.statistics.average_confidence).toBeLessThanOrEqual(1);
    for (const metric of mockMetricsHistory(50).metrics) {
      expect(metric.fps).toBeGreaterThan(0);
      expect(ISO.test(metric.timestamp)).toBe(true);
    }
    for (const row of mockRecentDetections(10)) checkDetection(row);
  });

  it('compare, benchmark and job fixtures are internally consistent', () => {
    for (const comparison of MOCK_COMPARISONS) {
      expect(comparison.models.length).toBeGreaterThanOrEqual(2);
      for (const model of comparison.models) {
        expect(model.annotated_image.startsWith('data:image/jpeg;base64,')).toBe(true);
      }
    }
    for (const run of MOCK_BENCHMARKS) {
      expect(['queued', 'running', 'completed', 'failed', 'cancelled']).toContain(run.status);
      if (run.results) {
        for (const result of run.results) expect(result.map50).toBeGreaterThanOrEqual(0);
      }
    }
    for (const job of MOCK_JOBS) {
      expect(job.progress).toBeGreaterThanOrEqual(0);
      expect(job.progress).toBeLessThanOrEqual(1);
    }
  });

  it('hardware and arm fixtures stay in range', () => {
    for (const point of mockHardwareHistory(30, 20)) {
      expect(point.cpu_percent).toBeGreaterThanOrEqual(0);
      expect(point.memory_percent).toBeLessThanOrEqual(100);
    }
    for (const event of MOCK_ARM_EVENTS) {
      expect(event.correct === null || typeof event.correct === 'boolean').toBe(true);
    }
  });
});

async function call(method: string, path: string, options: { json?: unknown; query?: string; form?: FormData; raw?: Blob; contentType?: string } = {}): Promise<MockReply> {
  return handleMockRequest({
    method,
    path,
    query: new URLSearchParams(options.query ?? ''),
    json: options.json,
    form: options.form ?? null,
    raw: options.raw ?? null,
    contentType: options.contentType ?? '',
  });
}

describe('mock backend routes', () => {
  beforeEach(() => {
    resetMockState();
  });

  it('answers every legacy route', async () => {
    expect((await call('GET', '/api/status')).status).toBe(200);
    expect((await call('GET', '/api/models')).status).toBe(200);
    expect((await call('GET', '/api/statistics', { query: 'period=60' })).status).toBe(200);
    expect((await call('GET', '/api/metrics/history', { query: 'limit=5' })).status).toBe(200);
    expect((await call('GET', '/api/detections/recent', { query: 'limit=5' })).status).toBe(200);
  });

  it('answers unknown routes with 404 "Not Found", as FastAPI does', async () => {
    const reply = await call('GET', '/api/v1/unknown');
    expect(reply.status).toBe(404);
    expect(reply.body).toEqual({ detail: 'Not Found' });
  });

  it('requires camera and model before the stream starts (409 with missing)', async () => {
    const reply = await call('POST', '/api/stream/start');
    expect(reply.status).toBe(409);
    expect((reply.body as { detail: { missing: string[] } }).detail.missing).toEqual(['camera', 'model']);
  });

  it('configures the camera and the model, then starts and stops the stream', async () => {
    expect((await call('POST', '/api/camera/initialize', { json: { index: 0, width: 640, height: 360, fps: 30 } })).status).toBe(200);
    expect((await call('POST', '/api/model/load', { json: { name: MOCK_MODELS[0].name, conf_threshold: 0.25 } })).status).toBe(200);
    expect((await call('POST', '/api/stream/start')).status).toBe(200);
    expect(state.streaming).toBe(true);
    expect((await call('POST', '/api/camera/initialize', { json: { index: 0 } })).status).toBe(409);
    expect((await call('POST', '/api/stream/stop')).status).toBe(200);
    expect(state.streaming).toBe(false);
  });

  it('validates camera input with a 422 list', async () => {
    const reply = await call('POST', '/api/camera/initialize', { json: { index: -1 } });
    expect(reply.status).toBe(422);
    expect(Array.isArray((reply.body as { detail: unknown[] }).detail)).toBe(true);
  });

  it('rejects an image of the wrong type with 415 and needs a model with 409', async () => {
    const png = new Blob([new Uint8Array([1])], { type: 'image/png' });
    expect((await call('POST', '/api/detect/image', { raw: png, contentType: 'text/plain' })).status).toBe(415);
    expect((await call('POST', '/api/detect/image', { raw: png, contentType: 'image/png' })).status).toBe(409);
  });

  it('detects on an uploaded image once a model is loaded', async () => {
    await call('POST', '/api/model/load', { json: { name: MOCK_MODELS[0].name } });
    const png = new Blob([new Uint8Array([1, 2, 3])], { type: 'image/png' });
    const reply = await call('POST', '/api/detect/image', { raw: png, contentType: 'image/png', query: 'confidence=0.1' });
    expect(reply.status).toBe(200);
    const body = reply.body as { image: string; detections: Detection[] };
    expect(body.image.startsWith('data:image/png;base64,')).toBe(true);
    body.detections.forEach(checkDetection);
  });

  it('creates, stops and deletes sessions with the contract statuses', async () => {
    const created = await call('POST', '/api/v1/sessions', { json: { source: 'image', name: 'Desk test' } });
    expect(created.status).toBe(201);
    const id = (created.body as { id: string }).id;
    expect((created.body as { status: string }).status).toBe('active');
    expect((await call('DELETE', `/api/v1/sessions/${id}`)).status).toBe(409);
    expect((await call('POST', `/api/v1/sessions/${id}/stop`)).status).toBe(200);
    expect((await call('DELETE', `/api/v1/sessions/${id}`)).status).toBe(204);
    expect((await call('GET', `/api/v1/sessions/${id}`)).status).toBe(404);
  });

  it('allows one active camera session at a time', async () => {
    await call('POST', '/api/v1/sessions', { json: { source: 'camera' } });
    expect((await call('POST', '/api/v1/sessions', { json: { source: 'camera' } })).status).toBe(409);
  });

  it('lists sessions with status filter and pagination', async () => {
    const reply = await call('GET', '/api/v1/sessions', { query: 'limit=2&offset=1' });
    const body = reply.body as { sessions: unknown[]; total: number };
    expect(body.sessions).toHaveLength(2);
    expect(body.total).toBe(MOCK_SESSIONS.length);
    const active = await call('GET', '/api/v1/sessions', { query: 'status=active' });
    expect((active.body as { total: number }).total).toBe(0);
  });

  it('serves detections with a class filter and a timeline', async () => {
    const id = MOCK_SESSIONS[0].id;
    const detections = await call('GET', `/api/v1/sessions/${id}/detections`, { query: 'class_name=glass&limit=50' });
    const rows = (detections.body as { detections: SessionDetection[] }).detections;
    rows.forEach((row) => expect(row.class_name).toBe('glass'));
    expect((await call('GET', `/api/v1/sessions/${id}/timeline`, { query: 'bucket_seconds=5' })).status).toBe(200);
    expect((await call('GET', `/api/v1/sessions/${id}/timeline`, { query: 'bucket_seconds=0' })).status).toBe(422);
  });

  it('runs compare with 2 to 4 known models', async () => {
    const form = new FormData();
    form.append('image', new File([new Uint8Array([1])], 'bin.jpg', { type: 'image/jpeg' }));
    form.append('models', MOCK_MODELS[0].name);
    expect((await call('POST', '/api/v1/compare', { form })).status).toBe(422);
    form.set('models', `${MOCK_MODELS[0].name},${MOCK_MODELS[1].name}`);
    const reply = await call('POST', '/api/v1/compare', { form });
    expect(reply.status).toBe(200);
    expect((reply.body as { models: unknown[] }).models).toHaveLength(2);
    expect((await call('GET', '/api/v1/compare', { query: 'limit=5' })).body).toBeInstanceOf(Array);
    expect(MOCK_COMPARISONS.length).toBeGreaterThan(0);
  });

  it('queues a benchmark run and returns 202 with the ids', async () => {
    const reply = await call('POST', '/api/v1/benchmark/runs', { json: { models: [MOCK_MODELS[0].name], confidence: 0.25 } });
    expect(reply.status).toBe(202);
    expect(Object.keys(reply.body as object).sort()).toEqual(['job_id', 'run_id']);
  });

  it('cancels a running job and refuses to cancel a finished one', async () => {
    const running = MOCK_JOBS.find((job) => job.status === 'running');
    expect(running).toBeDefined();
    expect((await call('POST', `/api/v1/jobs/${running?.id}/cancel`)).status).toBe(200);
    const finished = MOCK_JOBS.find((job) => job.status === 'completed');
    expect((await call('POST', `/api/v1/jobs/${finished?.id}/cancel`)).status).toBe(409);
  });

  it('validates arm commands against the action and class lists', async () => {
    expect((await call('POST', '/api/v1/arm/commands', { json: { action: 'fly' } })).status).toBe(422);
    expect((await call('POST', '/api/v1/arm/commands', { json: { action: 'sort', class_name: 'cardboard' } })).status).toBe(422);
    const accepted = await call('POST', '/api/v1/arm/commands', { json: { action: 'sort', class_name: 'glass' } });
    expect(accepted.status).toBe(202);
    expect((accepted.body as { kind: string }).kind).toBe('sort_requested');
  });

  it('records arm feedback and reports accuracy', async () => {
    const id = MOCK_ARM_EVENTS[1].id;
    expect((await call('POST', `/api/v1/arm/events/${id}/feedback`, { json: { correct: true } })).status).toBe(200);
    const accuracy = await call('GET', '/api/v1/arm/accuracy');
    expect((accuracy.body as { total: number }).total).toBeGreaterThan(0);
  });

  it('answers hardware routes with the contract fields', async () => {
    const current = (await call('GET', '/api/v1/hardware/current')).body as Record<string, unknown>;
    expect(current).toHaveProperty('is_raspberry_pi');
    const history = (await call('GET', '/api/v1/hardware/history', { query: 'minutes=10&points=5' })).body as { points: unknown[]; minutes: number };
    expect(history.minutes).toBe(10);
    expect(history.points.length).toBeLessThanOrEqual(5);
  });
});
