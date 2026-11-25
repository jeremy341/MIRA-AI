import { beforeEach, describe, expect, it } from 'vitest';
import { CLASS_NAMES, type ArmEvent, type BusEvent, type ClassName, type Detection, type EventType, type SessionDetection } from '../types';
import {
  MOCK_ARM_EVENTS,
  MOCK_BENCHMARKS,
  MOCK_COMPARISONS,
  MOCK_JOBS,
  MOCK_MODELS,
  MOCK_SESSIONS,
  MOCK_STATISTICS,
  WINNER_NOTE,
  benchmarkResultFor,
  mockHardwareHistory,
  mockMetricsHistory,
  mockRecentDetections,
  scaledCounts,
  sessionDetectionsFor,
  sessionTimelineFor,
  winnerHintFor,
} from './fixtures';
import { advanceMockJobs, handleMockRequest, resetMockState, state, tickMock, type MockReply } from './backend';
import { subscribeMockEvents } from './mock-events';

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

const sumOf = (counts: Record<ClassName, number>) => CLASS_NAMES.reduce((total, cls) => total + counts[cls], 0);

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
      expect(sumOf(session.class_counts)).toBe(session.total_detections);
      expect(Object.keys(session.class_counts).sort()).toEqual([...CLASS_NAMES].sort());
    }
  });

  it('gives every session a few hundred detections at most and the mock list has a running import', () => {
    for (const session of MOCK_SESSIONS) expect(session.total_detections).toBeLessThanOrEqual(800);
    expect(MOCK_SESSIONS.some((s) => s.status === 'active')).toBe(true);
  });

  it('session detections follow the class counts, and the timeline adds up to the total', () => {
    const session = MOCK_SESSIONS[0];
    const rows = sessionDetectionsFor(session);
    expect(rows).toHaveLength(Math.min(800, session.total_detections));
    for (const row of rows) {
      checkDetection(row);
      expect(row.offset_seconds).toBeGreaterThanOrEqual(0);
      expect(row.offset_seconds).toBeLessThanOrEqual(session.duration_seconds);
      expect(ISO.test(row.ts)).toBe(true);
    }
    const byClass = { glass: 0, metal: 0, paper: 0, plastic: 0, trash: 0 };
    for (const row of rows) byClass[row.class_name] += 1;
    expect(byClass).toEqual(session.class_counts);

    const timeline = sessionTimelineFor(session, 5);
    expect(timeline.bucket_seconds).toBe(5);
    expect(timeline.buckets).toHaveLength(Math.ceil(session.duration_seconds / 5));
    expect(timeline.buckets.reduce((total, bucket) => total + bucket.objects, 0)).toBe(session.total_detections);
    for (const bucket of timeline.buckets) {
      expect(sumOf(bucket.class_counts)).toBe(bucket.objects);
      expect(bucket.avg_confidence === null || (bucket.avg_confidence >= 0 && bucket.avg_confidence <= 1)).toBe(true);
    }
  });

  it('scales the counts of a running import with its progress', () => {
    const target = { glass: 100, metal: 50, paper: 0, plastic: 9, trash: 1 };
    expect(scaledCounts(target, 0.5)).toEqual({ glass: 50, metal: 25, paper: 0, plastic: 4, trash: 0 });
    expect(scaledCounts(target, 1)).toEqual(target);
  });

  it('statistics, metrics and recent detections are in range', () => {
    expect(MOCK_STATISTICS.statistics.average_confidence).toBeLessThanOrEqual(1);
    for (const metric of mockMetricsHistory(50).metrics) {
      expect(metric.fps).toBeGreaterThan(0);
      expect(ISO.test(metric.timestamp)).toBe(true);
    }
    for (const row of mockRecentDetections(10)) checkDetection(row);
  });

  it('stored compare records have no images and a winner hint computed from their models', () => {
    for (const comparison of MOCK_COMPARISONS) {
      expect(comparison.models.length).toBeGreaterThanOrEqual(2);
      expect(comparison.models.length).toBeLessThanOrEqual(4);
      for (const model of comparison.models) {
        expect(Object.keys(model)).not.toContain('annotated_image');
        expect(sumOf(model.class_counts)).toBe(model.objects);
        expect(model.detections).toHaveLength(model.objects);
      }
      expect(winnerHintFor(comparison.models)).toEqual(comparison.winner_hint);
      expect(comparison.winner_hint.note).toBe(WINNER_NOTE);
    }
  });

  it('winner hint picks the first model on a tie and skips models without detections', () => {
    const hint = winnerHintFor([
      { name: 'a', latency_ms: 20, objects: 3, avg_confidence: null },
      { name: 'b', latency_ms: 20, objects: 3, avg_confidence: 0.5 },
    ]);
    expect(hint.fastest_model).toBe('a');
    expect(hint.most_objects_model).toBe('a');
    expect(hint.highest_avg_confidence_model).toBe('b');
  });

  it('benchmark results use the backend shape, with fps null and the per-class metrics', () => {
    for (const run of MOCK_BENCHMARKS) {
      expect(['queued', 'running', 'completed', 'failed', 'cancelled']).toContain(run.status);
      expect(ISO.test(run.created_at)).toBe(true);
      for (const result of run.results ?? []) {
        expect(result.map50).toBeGreaterThanOrEqual(0);
        expect(result.fps).toBeNull();
        expect(Array.isArray(result.errors)).toBe(true);
        expect(Object.keys(result.per_class).sort()).toEqual([...CLASS_NAMES].sort());
      }
    }
    const fresh = benchmarkResultFor('mira_exp018.pt');
    expect(fresh.per_class.glass.f1).toBeGreaterThan(0);
    expect(fresh.per_class.glass.f1).toBeLessThanOrEqual(1);
  });

  it('job fixtures stay in range and the running import is only created with the mock state', () => {
    for (const job of MOCK_JOBS) {
      expect(job.progress).toBeGreaterThanOrEqual(0);
      expect(job.progress).toBeLessThanOrEqual(1);
    }
    expect(MOCK_JOBS.some((job) => job.status === 'running')).toBe(false);
    expect(state.jobs.some((job) => job.status === 'running')).toBe(true);
  });

  it('hardware and arm fixtures stay in range', () => {
    for (const point of mockHardwareHistory(30, 20)) {
      expect(point.cpu_percent).toBeGreaterThanOrEqual(0);
      expect(point.memory_percent).toBeLessThanOrEqual(100);
      expect(point.temperature_c === null || point.temperature_c > 0).toBe(true);
    }
    for (const event of MOCK_ARM_EVENTS) {
      expect(event.correct === null || typeof event.correct === 'boolean').toBe(true);
      expect(event.kind.endsWith('_completed') || event.kind.endsWith('_requested')).toBe(true);
    }
    const completed = MOCK_ARM_EVENTS.filter((e) => e.kind === 'sort_completed' && e.correct !== null);
    expect(completed.length).toBeGreaterThan(0);
    for (const event of MOCK_ARM_EVENTS.filter((e) => e.kind !== 'sort_completed')) {
      expect(event.correct).toBeNull();
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

/** Collects the events the mock publishes while `run` executes. */
async function captureEvents(run: () => Promise<void> | void): Promise<BusEvent[]> {
  const seen: BusEvent[] = [];
  const stop = subscribeMockEvents((type: EventType, data) => seen.push({ type, ts: '', data: data as Record<string, unknown> }));
  try {
    await run();
  } finally {
    stop();
  }
  return seen;
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

  it('lists sessions newest first with a status filter and pagination', async () => {
    const reply = await call('GET', '/api/v1/sessions', { query: 'limit=2&offset=1' });
    const body = reply.body as { sessions: Array<{ started_at: string }>; total: number };
    expect(body.sessions).toHaveLength(2);
    expect(body.total).toBe(MOCK_SESSIONS.length);
    const starts = (await call('GET', '/api/v1/sessions', { query: 'limit=100' })).body as { sessions: Array<{ started_at: string }> };
    const times = starts.sessions.map((s) => Date.parse(s.started_at));
    expect([...times].sort((a, b) => b - a)).toEqual(times);
    const active = (await call('GET', '/api/v1/sessions', { query: 'status=active' })).body as { total: number };
    expect(active.total).toBe(MOCK_SESSIONS.filter((s) => s.status === 'active').length);
  });

  it('serves detections with a class filter and a timeline', async () => {
    const id = MOCK_SESSIONS[0].id;
    const detections = await call('GET', `/api/v1/sessions/${id}/detections`, { query: 'class_name=glass&limit=50' });
    const rows = (detections.body as { detections: SessionDetection[] }).detections;
    rows.forEach((row) => expect(row.class_name).toBe('glass'));
    expect((await call('GET', `/api/v1/sessions/${id}/timeline`, { query: 'bucket_seconds=5' })).status).toBe(200);
    expect((await call('GET', `/api/v1/sessions/${id}/timeline`, { query: 'bucket_seconds=0' })).status).toBe(422);
  });

  it('runs compare with 2 to 4 known models and stores the record without images', async () => {
    const form = new FormData();
    form.append('image', new File([new Uint8Array([1])], 'bin.jpg', { type: 'image/jpeg' }));
    form.append('models', MOCK_MODELS[0].name);
    expect((await call('POST', '/api/v1/compare', { form })).status).toBe(422);
    form.set('models', `${MOCK_MODELS[0].name},${MOCK_MODELS[0].name}`);
    expect((await call('POST', '/api/v1/compare', { form })).status).toBe(422);
    form.set('models', `${MOCK_MODELS[0].name},${MOCK_MODELS[1].name}`);
    const reply = await call('POST', '/api/v1/compare', { form });
    expect(reply.status).toBe(200);
    const body = reply.body as { id: string; models: Array<{ annotated_image: string }>; winner_hint: { note: string } };
    expect(body.models).toHaveLength(2);
    for (const model of body.models) expect(model.annotated_image.startsWith('data:image/')).toBe(true);
    expect(body.winner_hint.note).toBe(WINNER_NOTE);

    const listed = (await call('GET', '/api/v1/compare', { query: 'limit=5' })).body as { comparisons: Array<{ id: string }>; total: number };
    expect(listed.total).toBe(MOCK_COMPARISONS.length + 1);
    expect(listed.comparisons[0].id).toBe(body.id);
    const reopened = (await call('GET', `/api/v1/compare/${body.id}`)).body as { models: Array<Record<string, unknown>> };
    expect(reopened.models[0]).not.toHaveProperty('annotated_image');
    expect((await call('DELETE', `/api/v1/compare/${body.id}`)).status).toBe(204);
    expect((await call('GET', `/api/v1/compare/${body.id}`)).status).toBe(404);
  });

  it('queues a benchmark run, fills results as models finish and completes it', async () => {
    const models = [MOCK_MODELS[0].name, MOCK_MODELS[2].name];
    const reply = await call('POST', '/api/v1/benchmark/runs', { json: { models, confidence: 0.25 } });
    expect(reply.status).toBe(202);
    const ids = reply.body as { run_id: string; job_id: string };
    expect(Object.keys(ids).sort()).toEqual(['job_id', 'run_id']);

    const start = Date.now();
    advanceMockJobs(start + 1000);
    const early = (await call('GET', `/api/v1/benchmark/runs/${ids.run_id}`)).body as { status: string; results: unknown };
    expect(early.status).toBe('running');
    expect(early.results).toBeNull();

    const events = await captureEvents(() => advanceMockJobs(start + 60 * 60_000));
    expect(events.map((e) => e.type)).toContain('job_finished');
    const done = (await call('GET', `/api/v1/benchmark/runs/${ids.run_id}`)).body as { status: string; results: Array<{ model: string }> };
    expect(done.status).toBe('completed');
    expect(done.results.map((r) => r.model)).toEqual(models);
    const job = (await call('GET', `/api/v1/jobs/${ids.job_id}`)).body as { status: string; progress: number };
    expect(job.status).toBe('completed');
    expect(job.progress).toBe(1);
  });

  it('reports benchmark errors and refuses to delete a running run', async () => {
    const reply = await call('POST', '/api/v1/benchmark/runs', { json: { models: [MOCK_MODELS[2].name], confidence: 0.25 } });
    const ids = reply.body as { run_id: string };
    expect((await call('DELETE', `/api/v1/benchmark/runs/${ids.run_id}`)).status).toBe(409);
    advanceMockJobs(Date.now() + 60 * 60_000);
    const run = (await call('GET', `/api/v1/benchmark/runs/${ids.run_id}`)).body as { results: Array<{ errors: string[] }> };
    expect(run.results[0].errors.length).toBeGreaterThan(0);
    expect((await call('DELETE', `/api/v1/benchmark/runs/${ids.run_id}`)).status).toBe(204);
  });

  it('rejects benchmark inputs the server would refuse', async () => {
    expect((await call('POST', '/api/v1/benchmark/runs', { json: { models: [], confidence: 0.25 } })).status).toBe(422);
    expect((await call('POST', '/api/v1/benchmark/runs', { json: { models: ['nope.pt'], confidence: 0.25 } })).status).toBe(422);
    expect((await call('POST', '/api/v1/benchmark/runs', { json: { models: [MOCK_MODELS[0].name], confidence: 0.25, max_images: 0 } })).status).toBe(422);
    expect((await call('POST', '/api/v1/benchmark/runs', { json: { models: [MOCK_MODELS[0].name], dataset: 'data.csv', confidence: 0.25 } })).status).toBe(422);
  });

  it('cancels a running import, marks its session failed and refuses to cancel a finished job', async () => {
    const running = state.jobs.find((job) => job.status === 'running');
    expect(running).toBeDefined();
    expect((await call('POST', `/api/v1/jobs/${running?.id}/cancel`)).status).toBe(200);
    expect(state.sessions.find((s) => s.id === 's008b2run')?.status).toBe('failed');
    const finished = MOCK_JOBS.find((job) => job.status === 'completed');
    expect((await call('POST', `/api/v1/jobs/${finished?.id}/cancel`)).status).toBe(409);
  });

  it('runs an image import to completion with a session that holds the counted detections', async () => {
    const reply = await call('POST', '/api/v1/batch/images', { json: { directory: 'C:/bins/samples', recursive: false, model_name: MOCK_MODELS[1].name, confidence: 0.3 } });
    expect(reply.status).toBe(202);
    const accepted = reply.body as { job_id: string; session_id: string };
    expect((await call('GET', `/api/v1/sessions/${accepted.session_id}`)).body).toMatchObject({ status: 'active' });

    const events = await captureEvents(() => advanceMockJobs(Date.now() + 10 * 60_000));
    expect(events.some((e) => e.type === 'session_stopped')).toBe(true);
    const session = (await call('GET', `/api/v1/sessions/${accepted.session_id}`)).body as { status: string; total_detections: number; class_counts: Record<ClassName, number> };
    expect(session.status).toBe('completed');
    expect(session.total_detections).toBeGreaterThan(0);
    expect(sumOf(session.class_counts)).toBe(session.total_detections);
  });

  it('checks batch video inputs with the server messages', async () => {
    const form = new FormData();
    form.append('video', new File([new Uint8Array([1])], 'clip.gif', { type: 'image/gif' }));
    form.append('model_name', MOCK_MODELS[0].name);
    const wrongType = await call('POST', '/api/v1/batch/video', { form });
    expect(wrongType.status).toBe(415);
    form.set('video', new File([new Uint8Array([1])], 'clip.mp4', { type: 'video/mp4' }));
    form.set('frame_stride', '0');
    const badStride = await call('POST', '/api/v1/batch/video', { form });
    expect(badStride.status).toBe(422);
    expect((badStride.body as { detail: string }).detail).toBe('frame_stride must be between 1 and 120.');
    form.set('frame_stride', '5');
    expect((await call('POST', '/api/v1/batch/video', { form })).status).toBe(202);
  });

  it('validates arm commands against the action and class lists', async () => {
    expect((await call('POST', '/api/v1/arm/commands', { json: { action: 'fly' } })).status).toBe(422);
    expect((await call('POST', '/api/v1/arm/commands', { json: { action: 'sort', class_name: 'cardboard' } })).status).toBe(422);
    expect((await call('POST', '/api/v1/arm/commands', { json: { action: 'sort' } })).status).toBe(422);
    const accepted = await call('POST', '/api/v1/arm/commands', { json: { action: 'sort', class_name: 'glass' } });
    expect(accepted.status).toBe(202);
    expect((accepted.body as ArmEvent).kind).toBe('sort_requested');
    expect((accepted.body as ArmEvent).payload).toEqual({ action: 'sort' });
    expect((await call('POST', '/api/v1/arm/commands', { json: { action: 'home' } })).status).toBe(409);
  });

  it('completes a simulated sort with a sort_completed event that can take feedback', async () => {
    const accepted = (await call('POST', '/api/v1/arm/commands', { json: { action: 'sort', class_name: 'paper' } })).body as ArmEvent;
    const events = await captureEvents(() => tickMock(Date.now() + 5000));
    const completed = events.find((e) => e.type === 'arm_event') as BusEvent<ArmEvent> | undefined;
    expect(completed?.data.kind).toBe('sort_completed');
    expect(completed?.data.payload).toEqual({ request_id: accepted.id, message: 'Simulated: sort' });
    const id = completed?.data.id as number;
    expect((await call('POST', `/api/v1/arm/events/${id}/feedback`, { json: { correct: true } })).status).toBe(200);
    expect((await call('POST', `/api/v1/arm/events/${accepted.id}/feedback`, { json: { correct: true } })).status).toBe(409);
    const accuracy = (await call('GET', '/api/v1/arm/accuracy')).body as { total: number; correct: number };
    expect(accuracy.total).toBe(MOCK_ARM_EVENTS.filter((e) => e.kind === 'sort_completed' && e.correct !== null).length + 1);
  });

  it('records arm feedback on a sort_completed event and reports accuracy', async () => {
    const pending = MOCK_ARM_EVENTS.find((e) => e.kind === 'sort_completed' && e.correct === null);
    expect(pending).toBeDefined();
    expect((await call('POST', `/api/v1/arm/events/${pending?.id}/feedback`, { json: { correct: false } })).status).toBe(200);
    const accuracy = (await call('GET', '/api/v1/arm/accuracy')).body as { total: number };
    expect(accuracy.total).toBeGreaterThan(0);
  });

  it('answers hardware routes with the contract fields and honours the sensor switch', async () => {
    const current = (await call('GET', '/api/v1/hardware/current')).body as Record<string, unknown>;
    expect(current).toHaveProperty('is_raspberry_pi');
    const history = (await call('GET', '/api/v1/hardware/history', { query: 'minutes=10&points=10' })).body as { points: Array<{ temperature_c: number | null }>; minutes: number };
    expect(history.minutes).toBe(10);
    expect(history.points).toHaveLength(10);
    expect(history.points.some((p) => p.temperature_c !== null)).toBe(true);
    state.hardwareSensor = false;
    const noSensor = (await call('GET', '/api/v1/hardware/history', { query: 'minutes=10&points=10' })).body as { points: Array<{ temperature_c: number | null }> };
    expect(noSensor.points.every((p) => p.temperature_c === null)).toBe(true);
    expect(((await call('GET', '/api/v1/hardware/current')).body as { temperature_c: unknown }).temperature_c).toBeNull();
    expect((await call('GET', '/api/v1/hardware/history', { query: 'points=5' })).status).toBe(400);
  });
});

describe('mock events', () => {
  beforeEach(() => {
    resetMockState();
  });

  it('publishes job progress while an import moves', async () => {
    const events = await captureEvents(() => tickMock(Date.now() + 30_000));
    const progress = events.find((e) => e.type === 'job_progress');
    expect(progress?.data).toMatchObject({ job_id: 'job-6d02' });
  });

  it('exposes the arm event kinds in the fixture log', () => {
    const kinds = new Set(MOCK_ARM_EVENTS.map((e) => e.kind));
    expect([...kinds].every((kind) => /^(sort|home|stop)_(requested|completed|failed)$/.test(kind))).toBe(true);
  });
});

describe('benchmark result builder', () => {
  it('is deterministic per model name', () => {
    expect(benchmarkResultFor('a.pt')).toEqual(benchmarkResultFor('a.pt'));
    expect(benchmarkResultFor('a.pt').map50).not.toBe(benchmarkResultFor('b.pt').map50);
  });
});
