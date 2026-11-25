/**
 * In-memory stand-in for the FastAPI server, used when VITE_MOCK=1. It answers the same routes
 * with the same status codes and error shapes as the backend (409 with `missing`, 422 with a
 * validation list or a detail string, 404 "Not Found" for an unknown route, 404 with a message
 * for an unknown id). It holds state: starting a stream makes the mock socket send frames, and
 * import jobs, benchmark runs and arm commands move forward with time (see tickMock).
 */
import {
  CLASS_NAMES,
  type ArmCommandAction,
  type ArmEvent,
  type ArmEventKind,
  type BatchAccepted,
  type BenchmarkConfig,
  type BenchmarkRun,
  type CameraConfig,
  type ClassCounts,
  type ClassName,
  type CompareRecord,
  type CompareResponse,
  type Detection,
  type Job,
  type ModelConfig,
  type SessionCreateBody,
  type SessionDetail,
  type SessionSource,
  type SessionStatus,
} from '../types';
import { defaultSessionName } from '../format';
import {
  MOCK_ARM_EVENTS,
  MOCK_BENCHMARKS,
  MOCK_COMPARISONS,
  MOCK_DATASET_PATH,
  MOCK_JOBS,
  MOCK_MODELS,
  MOCK_SESSIONS,
  MOCK_STATISTICS,
  benchmarkResultFor,
  countsForSeed,
  emptyClassCounts,
  hash,
  mockHardwareCurrent,
  mockHardwareHistory,
  mockMetricsHistory,
  mockRecentDetections,
  randomCompareDetections,
  rng,
  scaledCounts,
  sessionDetectionsFor,
  sessionTimelineFor,
  summaryOf,
  winnerHintFor,
} from './fixtures';
import { progressAt, progressMessage, type JobClock } from './job-clock';
import { annotateJpeg } from './annotate';
import { publishMockEvent } from './mock-events';

/** A running job's clock and what it writes when it moves. */
export interface MockJobRun {
  kind: 'benchmark' | 'batch_video' | 'batch_images';
  clock: JobClock;
  /** Models, frames or images: the unit the progress message counts. */
  total: number;
  sessionId?: string;
  targetCounts?: ClassCounts;
  runId?: string;
  models?: string[];
}

interface PendingArmCommand {
  dueMs: number;
  action: ArmCommandAction;
  requested: ArmEvent;
}

/** What the mock keeps between requests. Mutated by the handlers below. */
export interface MockState {
  camera: CameraConfig | null;
  model: ModelConfig | null;
  streaming: boolean;
  /** False simulates a board with no temperature sensor (temperature is null everywhere). */
  hardwareSensor: boolean;
  sessions: SessionDetail[];
  comparisons: CompareRecord[];
  benchmarks: BenchmarkRun[];
  jobs: Job[];
  jobRuns: Record<string, MockJobRun>;
  armEvents: ArmEvent[];
  armPending: PendingArmCommand[];
  nextId: number;
}

const ARM_COMMAND_MS = 1200;
const BENCHMARK_MS_PER_MODEL = 8000;
const VIDEO_JOB_MS = 90_000;
const IMAGE_JOB_MS = 30_000;

/** A benchmark model that reports labels it could not use, so the errors list has something to show. */
const MODEL_WITH_ERRORS = 'mira_exp014.pt';
const MODEL_ERROR_TEXT = '3 images had labels outside the five bin classes and were skipped.';

export function createMockState(now = Date.now()): MockState {
  const jobs: Job[] = structuredClone(MOCK_JOBS);
  const sessions: SessionDetail[] = structuredClone(MOCK_SESSIONS);
  // A video import that is still running. Its progress and its session counts follow the job clock.
  const importClock: JobClock = { startedMs: now - 120_000, durationMs: 240_000, startProgress: 0.42 };
  const importTarget = countsForSeed(hash('job-6d02'));
  const importProgress = progressAt(importClock, now);
  jobs.unshift({
    id: 'job-6d02',
    kind: 'batch_video',
    title: 'Video batch: bin B2 (stride 5)',
    status: 'running',
    progress: importProgress,
    message: progressMessage('batch_video', importProgress, 3000),
    created_at: new Date(now - 120_000).toISOString(),
    finished_at: null,
    result: null,
    error: null,
  });
  const running = sessions.find((session) => session.id === 's008b2run');
  if (running) {
    running.started_at = new Date(now - 240_000).toISOString();
    running.class_counts = scaledCounts(importTarget, importProgress);
    running.total_detections = CLASS_NAMES.reduce((sum, cls) => sum + running.class_counts[cls], 0);
  }
  return {
    camera: null,
    model: null,
    streaming: false,
    hardwareSensor: true,
    sessions,
    comparisons: structuredClone(MOCK_COMPARISONS),
    benchmarks: structuredClone(MOCK_BENCHMARKS),
    jobs,
    jobRuns: {
      'job-6d02': {
        kind: 'batch_video',
        clock: importClock,
        total: 3000,
        sessionId: 's008b2run',
        targetCounts: importTarget,
      },
    },
    armEvents: structuredClone(MOCK_ARM_EVENTS),
    armPending: [],
    nextId: 1000,
  };
}

export const state: MockState = createMockState();

export function resetMockState(): void {
  Object.assign(state, createMockState());
}

/** Dev hook: `__miraMock.hardwareSensor(false)` in the console removes the temperature reading. */
export function setHardwareSensor(on: boolean): void {
  state.hardwareSensor = on;
}

/** What a handler receives. The body is already parsed: JSON, FormData, or a Blob for raw uploads. */
export interface MockRequest {
  method: string;
  path: string;
  query: URLSearchParams;
  json: unknown;
  form: FormData | null;
  raw: Blob | null;
  contentType: string;
  params: Record<string, string>;
}

/** A finished answer from a handler. `isReply` tells it apart from a record that also has a `status` field. */
export interface MockReply {
  isReply: true;
  status: number;
  body?: unknown;
}

type Handler = (request: MockRequest) => MockReply | Promise<MockReply>;

interface Route {
  method: string;
  pattern: RegExp;
  keys: string[];
  handler: Handler;
}

const routes: Route[] = [];

function route(method: string, path: string, handler: Handler): void {
  const keys: string[] = [];
  const source = path.replace(/:([a-zA-Z]+)/g, (_match, key: string) => {
    keys.push(key);
    return '([^/]+)';
  });
  routes.push({ method, pattern: new RegExp(`^${source}$`), keys, handler });
}

export function matchRoute(method: string, path: string): { route: Route; params: Record<string, string> } | null {
  for (const candidate of routes) {
    if (candidate.method !== method) continue;
    const match = candidate.pattern.exec(path);
    if (!match) continue;
    const params: Record<string, string> = {};
    candidate.keys.forEach((key, index) => {
      params[key] = decodeURIComponent(match[index + 1]);
    });
    return { route: candidate, params };
  }
  return null;
}

function reply(status: number, body?: unknown): MockReply {
  return body === undefined ? { isReply: true, status } : { isReply: true, status, body };
}
const ok = (body: unknown, status = 200): MockReply => reply(status, body);
const detail = (status: number, value: unknown): MockReply => reply(status, { detail: value });
const notFound = (message: string): MockReply => detail(404, message);
const unprocessable = (field: string, message: string): MockReply =>
  detail(422, [{ loc: ['body', field], msg: message, type: 'value_error' }]);

const iso = (ms = Date.now()) => new Date(ms).toISOString();
const newId = (prefix: string) => {
  state.nextId += 1;
  return `${prefix}-${state.nextId.toString(16)}`;
};
const nextEventId = () => (state.armEvents.length ? Math.max(...state.armEvents.map((e) => e.id)) + 1 : 1);

function statusPayload() {
  const camera = state.camera !== null;
  const model = state.model !== null;
  return {
    status: state.streaming ? 'running' : 'idle',
    message: state.streaming ? 'Streaming started' : 'System ready',
    camera_initialized: camera,
    model_loaded: model,
    streaming: state.streaming,
    timestamp: iso(),
  };
}

function intParam(request: MockRequest, name: string, fallback: number, min: number, max: number): number | MockReply {
  const raw = request.query.get(name);
  if (raw === null || raw === '') return fallback;
  const value = Number(raw);
  if (!Number.isInteger(value) || value < min || value > max) {
    return detail(400, `${name} must be between ${min} and ${max}`);
  }
  return value;
}

// ---------------------------------------------------------------------------
// Legacy routes
// ---------------------------------------------------------------------------

route('GET', '/api/status', () => ok(statusPayload()));

route('GET', '/api/models', () => ok({ models: MOCK_MODELS, count: MOCK_MODELS.length, timestamp: iso() }));

function validCamera(value: unknown): CameraConfig | MockReply {
  if (!value || typeof value !== 'object') return unprocessable('body', 'Expected a JSON object.');
  const v = value as Record<string, unknown>;
  const num = (key: string, min: number, max: number, fallback: number) => {
    const raw = v[key] ?? fallback;
    return typeof raw === 'number' && Number.isInteger(raw) && raw >= min && raw <= max ? raw : null;
  };
  const index = num('index', 0, 64, 0);
  const width = num('width', 1, 8192, 640);
  const height = num('height', 1, 8192, 360);
  const fps = num('fps', 1, 240, 30);
  if (index === null) return unprocessable('index', 'Input should be greater than or equal to 0');
  if (width === null) return unprocessable('width', 'Input should be between 1 and 8192');
  if (height === null) return unprocessable('height', 'Input should be between 1 and 8192');
  if (fps === null) return unprocessable('fps', 'Input should be between 1 and 240');
  return {
    index,
    width,
    height,
    fps,
    autofocus: v.autofocus === true,
    auto_exposure: v.auto_exposure !== false,
  };
}

route('POST', '/api/camera/initialize', (request) => {
  const config = validCamera(request.json);
  if ('isReply' in config) return config;
  if (state.streaming) return detail(409, 'Stop the stream before changing camera settings');
  state.camera = config;
  return ok({ success: true, message: 'Camera config updated', config });
});

function validModel(value: unknown): ModelConfig | MockReply {
  if (!value || typeof value !== 'object') return unprocessable('body', 'Expected a JSON object.');
  const v = value as Record<string, unknown>;
  if (typeof v.name !== 'string' || v.name.length === 0) return unprocessable('name', 'String should have at least 1 character');
  const unit = (key: string, fallback: number) => {
    const raw = v[key] ?? fallback;
    return typeof raw === 'number' && raw >= 0 && raw <= 1 ? raw : null;
  };
  const conf = unit('conf_threshold', 0.25);
  const reject = unit('reject_threshold', 0.25);
  const iou = unit('iou_threshold', 0.45);
  const latency = typeof v.target_latency_ms === 'number' ? v.target_latency_ms : 1000;
  if (conf === null) return unprocessable('conf_threshold', 'Input should be between 0 and 1');
  if (reject === null) return unprocessable('reject_threshold', 'Input should be between 0 and 1');
  if (iou === null) return unprocessable('iou_threshold', 'Input should be between 0 and 1');
  if (!Number.isInteger(latency) || latency <= 0) return unprocessable('target_latency_ms', 'Input should be greater than 0');
  return {
    name: v.name,
    conf_threshold: conf,
    reject_threshold: reject,
    iou_threshold: iou,
    enable_tracking: v.enable_tracking !== false,
    target_latency_ms: latency,
  };
}

route('POST', '/api/model/load', (request) => {
  const config = validModel(request.json);
  if ('isReply' in config) return config;
  if (state.streaming) return detail(409, 'Stop the stream before changing models');
  if (!MOCK_MODELS.some((model) => model.name === config.name)) {
    return detail(500, `Failed to load model ${config.name}`);
  }
  state.model = config;
  return ok({ success: true, message: `Model ${config.name} loaded`, config });
});

route('POST', '/api/stream/start', () => {
  const missing: Array<'camera' | 'model'> = [];
  if (!state.camera) missing.push('camera');
  if (!state.model) missing.push('model');
  if (missing.length) {
    return detail(409, {
      message: 'Configure the camera and load a model before starting the stream.',
      missing,
    });
  }
  state.streaming = true;
  return ok({ success: true, status: 'running', message: 'Stream starting; waiting for the first frame', timestamp: iso() });
});

route('POST', '/api/stream/stop', () => {
  state.streaming = false;
  return ok({ success: true, status: 'idle', message: 'Stream stopped', timestamp: iso() });
});

/** Random detections inside a width x height frame, with a few tracks. */
export function randomDetections(width: number, height: number, count: number, random: () => number): Detection[] {
  const rows: Detection[] = [];
  for (let i = 0; i < count; i += 1) {
    const w = Math.round(width * (0.08 + random() * 0.18));
    const h = Math.round(height * (0.1 + random() * 0.2));
    const x1 = Math.round(random() * (width - w));
    const y1 = Math.round(random() * (height - h));
    rows.push({
      class_name: CLASS_NAMES[Math.floor(random() * CLASS_NAMES.length)],
      confidence: Math.round((0.35 + random() * 0.6) * 1000) / 1000,
      bbox: [x1, y1, x1 + w, y1 + h],
      track_id: random() > 0.2 ? Math.floor(random() * 12) + 1 : null,
      timestamp: iso(),
    });
  }
  return rows;
}

export async function imageSize(blob: Blob): Promise<{ width: number; height: number }> {
  try {
    if (typeof createImageBitmap === 'function') {
      const bitmap = await createImageBitmap(blob);
      const size = { width: bitmap.width, height: bitmap.height };
      bitmap.close();
      return size;
    }
  } catch {
    // Fall through to the default size.
  }
  return { width: 640, height: 480 };
}

export async function blobToDataUri(blob: Blob): Promise<string> {
  const bytes = new Uint8Array(await blob.arrayBuffer());
  let binary = '';
  const chunk = 0x8000;
  for (let i = 0; i < bytes.length; i += chunk) {
    binary += String.fromCharCode(...bytes.subarray(i, i + chunk));
  }
  const type = blob.type || 'image/jpeg';
  return `data:${type};base64,${btoa(binary)}`;
}

route('POST', '/api/detect/image', async (request) => {
  const contentType = request.contentType.split(';')[0].trim().toLowerCase();
  if (contentType !== 'image/jpeg' && contentType !== 'image/png') {
    return detail(415, 'Choose a JPEG or PNG image.');
  }
  const blob = request.raw;
  if (!blob) return detail(422, 'Send the image as the request body.');
  if (blob.size > 8 * 1024 * 1024) return detail(413, 'Choose an image no larger than 8 MB.');
  if (state.streaming) return detail(409, 'Stop the camera before detecting an image.');
  if (!state.model) return detail(409, 'Load a model in Settings first.');
  const confidence = Number(request.query.get('confidence') ?? '0.55');
  const size = await imageSize(blob);
  const random = rng(blob.size + Math.round(confidence * 100));
  const detections = randomDetections(size.width, size.height, 1 + Math.floor(random() * 4), random).filter(
    (d) => d.confidence >= confidence,
  );
  return ok({ image: await blobToDataUri(blob), detections });
});

route('GET', '/api/statistics', (request) => {
  const period = intParam(request, 'period', 60, 1, 86400);
  if (typeof period !== 'number') return period;
  return ok({ ...MOCK_STATISTICS, period_seconds: period });
});

route('GET', '/api/metrics/history', (request) => {
  const limit = intParam(request, 'limit', 100, 1, 1000);
  if (typeof limit !== 'number') return limit;
  return ok(mockMetricsHistory(limit));
});

route('GET', '/api/detections/recent', (request) => {
  const limit = intParam(request, 'limit', 50, 1, 1000);
  if (typeof limit !== 'number') return limit;
  const rows = mockRecentDetections(limit);
  return ok({ detections: rows, count: rows.length, timestamp: iso() });
});

// ---------------------------------------------------------------------------
// Sessions (v1)
// ---------------------------------------------------------------------------

const SOURCES: SessionSource[] = ['camera', 'image', 'video', 'batch'];

function findSession(id: string): SessionDetail | MockReply {
  const session = state.sessions.find((s) => s.id === id);
  return session ?? notFound('Session not found');
}

function toDetail(session: SessionDetail): SessionDetail {
  return structuredClone(session);
}

/** Sessions newest first, as the list is documented to return them in practice. */
function sortedSessions(): SessionDetail[] {
  return [...state.sessions].sort((a, b) => Date.parse(b.started_at) - Date.parse(a.started_at));
}

route('GET', '/api/v1/sessions', (request) => {
  const limit = intParam(request, 'limit', 50, 1, 500);
  if (typeof limit !== 'number') return limit;
  const offset = intParam(request, 'offset', 0, 0, 1_000_000);
  if (typeof offset !== 'number') return offset;
  const status = request.query.get('status');
  const matching = sortedSessions().filter((s) => !status || s.status === status);
  const page = matching.slice(offset, offset + limit).map(summaryOf);
  return ok({ sessions: page, total: matching.length });
});

route('POST', '/api/v1/sessions', (request) => {
  const body = (request.json ?? {}) as Partial<SessionCreateBody>;
  if (!body.source || !SOURCES.includes(body.source)) {
    return unprocessable('source', 'Input should be camera, image, video or batch');
  }
  if (body.source === 'camera' && state.sessions.some((s) => s.status === 'active' && s.source === 'camera')) {
    return detail(409, 'A camera session is already active. Stop it first.');
  }
  const started = new Date();
  const session: SessionDetail = {
    id: newId('s'),
    name: body.name?.trim() || defaultSessionName(started),
    source: body.source,
    model_name: body.model_name ?? state.model?.name ?? null,
    status: 'active',
    started_at: started.toISOString(),
    ended_at: null,
    duration_seconds: 0,
    total_detections: 0,
    class_counts: emptyClassCounts(),
    avg_confidence: null,
    config: { source: body.source, camera: state.camera },
    notes: null,
  };
  state.sessions.unshift(session);
  publishMockEvent('session_started', { session_id: session.id, source: session.source, name: session.name });
  return ok(toDetail(session), 201);
});

route('GET', '/api/v1/sessions/:id', (request) => {
  const found = findSession(request.params.id);
  return 'isReply' in found ? found : ok(toDetail(found));
});

route('PATCH', '/api/v1/sessions/:id', (request) => {
  const found = findSession(request.params.id);
  if ('isReply' in found) return found;
  const body = (request.json ?? {}) as { name?: unknown; notes?: unknown };
  if (typeof body.name === 'string') found.name = body.name.trim() || found.name;
  if (typeof body.notes === 'string') found.notes = body.notes;
  return ok(toDetail(found));
});

route('POST', '/api/v1/sessions/:id/stop', (request) => {
  const found = findSession(request.params.id);
  if ('isReply' in found) return found;
  if (found.status === 'active') {
    const endedMs = Date.now();
    found.status = 'completed' as SessionStatus;
    found.ended_at = iso(endedMs);
    found.duration_seconds = Math.max(0, Math.round((endedMs - Date.parse(found.started_at)) / 1000));
    publishMockEvent('session_stopped', { session_id: found.id, status: found.status });
  }
  return ok(toDetail(found));
});

route('DELETE', '/api/v1/sessions/:id', (request) => {
  const found = findSession(request.params.id);
  if ('isReply' in found) return found;
  if (found.status === 'active') return detail(409, 'Stop the session before deleting it.');
  state.sessions = state.sessions.filter((s) => s.id !== found.id);
  return reply(204);
});

route('GET', '/api/v1/sessions/:id/detections', (request) => {
  const found = findSession(request.params.id);
  if ('isReply' in found) return found;
  const limit = intParam(request, 'limit', 500, 1, 5000);
  if (typeof limit !== 'number') return limit;
  const offset = intParam(request, 'offset', 0, 0, 1_000_000);
  if (typeof offset !== 'number') return offset;
  const className = request.query.get('class_name');
  const minConfidence = Number(request.query.get('min_confidence') ?? '0');
  const all = sessionDetectionsFor(found).filter(
    (d) => (!className || d.class_name === className) && d.confidence >= minConfidence,
  );
  const rows = all.slice(offset, offset + limit).map((d) => ({ ...d }));
  return ok({ detections: rows, total: all.length });
});

route('GET', '/api/v1/sessions/:id/timeline', (request) => {
  const found = findSession(request.params.id);
  if ('isReply' in found) return found;
  const bucket = Number(request.query.get('bucket_seconds') ?? '1');
  if (!Number.isFinite(bucket) || bucket < 1 || bucket > 3600) {
    return detail(422, [{ loc: ['query', 'bucket_seconds'], msg: 'Input should be between 1 and 3600', type: 'value_error' }]);
  }
  return ok(sessionTimelineFor(found, bucket));
});

// ---------------------------------------------------------------------------
// Compare (v1)
// ---------------------------------------------------------------------------

/** The stored record keeps no images, as compare.py does. */
function storedCompareRecord(response: CompareResponse, createdMs: number): CompareRecord {
  return {
    id: response.id,
    created_at: iso(createdMs),
    input_name: response.input_name,
    models: response.models.map(({ annotated_image: _image, ...model }) => model),
    winner_hint: response.winner_hint,
  };
}

route('POST', '/api/v1/compare', async (request) => {
  const image = request.form?.get('image');
  const models = String(request.form?.get('models') ?? '')
    .split(',')
    .map((name) => name.trim());
  if (!(image instanceof Blob)) return unprocessable('image', 'Field required');
  const type = (image.type || '').split(';')[0].trim().toLowerCase();
  if (type !== 'image/jpeg' && type !== 'image/png') return detail(415, 'Choose a JPEG or PNG image.');
  if (image.size > 8 * 1024 * 1024) return detail(413, 'Choose an image no larger than 8 MB.');
  if (models.some((name) => name === '')) return detail(422, 'Provide 2 to 4 model names separated by commas.');
  if (models.length < 2 || models.length > 4) return detail(422, 'Compare requires between 2 and 4 models.');
  const duplicate = models.find((name, index) => models.indexOf(name) !== index);
  if (duplicate) return detail(422, `Duplicate model name: ${duplicate}`);
  const unknown = models.find((name) => !MOCK_MODELS.some((model) => model.name === name));
  if (unknown) return detail(422, `Invalid model '${unknown}': model not found`);
  const confidence = Number(request.form?.get('confidence') ?? '0.25');
  if (!Number.isFinite(confidence) || confidence < 0.05 || confidence > 1) {
    return unprocessable('confidence', 'Input should be between 0.05 and 1');
  }

  const size = await imageSize(image);
  const random = rng(image.size + models.length);
  const fallback = await blobToDataUri(image);
  const results: CompareResponse['models'] = [];
  for (const name of models) {
    const detections = randomCompareDetections(size.width, size.height, 2 + Math.floor(random() * 4), random);
    const counts = emptyClassCounts();
    for (const d of detections) counts[d.class_name] += 1;
    const average = detections.reduce((sum, d) => sum + d.confidence, 0) / Math.max(1, detections.length);
    results.push({
      name,
      latency_ms: Math.round((18 + random() * 50) * 10) / 10,
      objects: detections.length,
      class_counts: counts,
      avg_confidence: detections.length ? Math.round(average * 10_000) / 10_000 : null,
      detections,
      annotated_image: (await annotateJpeg(image, detections)) ?? fallback,
    });
  }
  const response: CompareResponse = {
    id: newId('cmp'),
    input_name: image instanceof File ? image.name : 'upload',
    models: results,
    winner_hint: winnerHintFor(results),
  };
  state.comparisons.unshift(storedCompareRecord(response, Date.now()));
  return ok(response);
});

route('GET', '/api/v1/compare', (request) => {
  const limit = intParam(request, 'limit', 20, 1, 100);
  if (typeof limit !== 'number') return limit;
  const sorted = [...state.comparisons].sort((a, b) => Date.parse(b.created_at) - Date.parse(a.created_at));
  return ok({ comparisons: sorted.slice(0, limit).map((c) => structuredClone(c)), total: state.comparisons.length });
});

function findComparison(id: string): CompareRecord | MockReply {
  return state.comparisons.find((c) => c.id === id) ?? notFound('Comparison not found.');
}

route('GET', '/api/v1/compare/:id', (request) => {
  const found = findComparison(request.params.id);
  return 'isReply' in found ? found : ok(structuredClone(found));
});

route('DELETE', '/api/v1/compare/:id', (request) => {
  const found = findComparison(request.params.id);
  if ('isReply' in found) return found;
  state.comparisons = state.comparisons.filter((c) => c.id !== found.id);
  return reply(204);
});

// ---------------------------------------------------------------------------
// Benchmark (v1)
// ---------------------------------------------------------------------------

route('POST', '/api/v1/benchmark/runs', (request) => {
  const body = (request.json ?? {}) as { models?: unknown; dataset?: unknown; confidence?: unknown; max_images?: unknown };
  if (!Array.isArray(body.models) || body.models.length === 0 || body.models.length > 6) {
    return unprocessable('models', 'List should have at least 1 item and at most 6');
  }
  const unknown = body.models.find((name) => typeof name !== 'string' || !MOCK_MODELS.some((m) => m.name === name));
  if (unknown !== undefined) return detail(422, `Unknown benchmark model '${String(unknown)}'.`);
  const models = body.models as string[];
  const confidence = typeof body.confidence === 'number' ? body.confidence : 0.25;
  if (confidence < 0.05 || confidence > 1) return unprocessable('confidence', 'Input should be between 0.05 and 1');
  const maxImages = typeof body.max_images === 'number' ? body.max_images : 100;
  if (!Number.isInteger(maxImages) || maxImages < 1 || maxImages > 5000) {
    return unprocessable('max_images', 'Input should be between 1 and 5000');
  }
  const dataset = typeof body.dataset === 'string' && body.dataset.trim() ? body.dataset.trim() : MOCK_DATASET_PATH;
  if (/\.[a-z]+$/i.test(dataset) && !/\.ya?ml$/i.test(dataset)) {
    return detail(422, 'Dataset file must be a YAML file.');
  }

  const now = Date.now();
  const runId = newId('bench');
  const jobId = newId('job');
  const config: BenchmarkConfig = { models, dataset, confidence, max_images: maxImages };
  state.benchmarks.unshift({ id: runId, created_at: iso(now), status: 'running', config, results: null, job_id: jobId });
  state.jobs.unshift({
    id: jobId,
    kind: 'benchmark',
    title: `Benchmark: ${models.length} model${models.length === 1 ? '' : 's'}`,
    status: 'running',
    progress: 0,
    message: progressMessage('benchmark', 0, models.length),
    created_at: iso(now),
    finished_at: null,
    result: null,
    error: null,
  });
  state.jobRuns[jobId] = {
    kind: 'benchmark',
    clock: { startedMs: now, durationMs: models.length * BENCHMARK_MS_PER_MODEL, startProgress: 0 },
    total: models.length,
    runId,
    models,
  };
  return ok({ run_id: runId, job_id: jobId }, 202);
});

route('GET', '/api/v1/benchmark/runs', (request) => {
  const limit = intParam(request, 'limit', 20, 1, 100);
  if (typeof limit !== 'number') return limit;
  return ok({ runs: state.benchmarks.slice(0, limit).map((b) => structuredClone(b)), total: state.benchmarks.length });
});

function findBenchmark(id: string): BenchmarkRun | MockReply {
  return state.benchmarks.find((b) => b.id === id) ?? notFound('Benchmark run not found');
}

route('GET', '/api/v1/benchmark/runs/:id', (request) => {
  const found = findBenchmark(request.params.id);
  return 'isReply' in found ? found : ok(structuredClone(found));
});

route('DELETE', '/api/v1/benchmark/runs/:id', (request) => {
  const found = findBenchmark(request.params.id);
  if ('isReply' in found) return found;
  if (found.status === 'queued' || found.status === 'running') {
    return detail(409, 'A queued or running benchmark cannot be deleted.');
  }
  state.benchmarks = state.benchmarks.filter((b) => b.id !== found.id);
  return reply(204);
});

// ---------------------------------------------------------------------------
// Batch and jobs (v1)
// ---------------------------------------------------------------------------

function parseBatchFields(modelName: unknown, confidence: unknown, stride?: unknown): MockReply | null {
  if (typeof modelName !== 'string' || !MOCK_MODELS.some((m) => m.name === modelName)) {
    return detail(422, 'Choose a model from the list.');
  }
  if (confidence !== undefined && confidence !== null && confidence !== '') {
    const value = Number(confidence);
    if (!Number.isFinite(value) || value < 0.05 || value > 1) return detail(422, 'confidence must be between 0.05 and 1.');
  }
  if (stride !== undefined) {
    const value = Number(stride);
    if (!Number.isInteger(value) || value < 1 || value > 120) return detail(422, 'frame_stride must be between 1 and 120.');
  }
  return null;
}

/** Starts an import: a running job, and a session that fills up as the job moves. */
function queueBatchJob(
  kind: MockJobRun['kind'],
  title: string,
  source: SessionSource,
  name: string | undefined,
  total: number,
  durationMs: number,
): BatchAccepted {
  const now = Date.now();
  const jobId = newId('job');
  const sessionId = newId('s');
  const session: SessionDetail = {
    id: sessionId,
    name: name?.trim() || defaultSessionName(new Date(now)),
    source,
    model_name: state.model?.name ?? null,
    status: 'active',
    started_at: iso(now),
    ended_at: null,
    duration_seconds: 0,
    total_detections: 0,
    class_counts: emptyClassCounts(),
    avg_confidence: null,
    config: { source },
    notes: null,
  };
  state.sessions.unshift(session);
  state.jobs.unshift({
    id: jobId,
    kind,
    title,
    status: 'running',
    progress: 0,
    message: progressMessage(kind, 0, total),
    created_at: iso(now),
    finished_at: null,
    result: null,
    error: null,
  });
  state.jobRuns[jobId] = {
    kind,
    clock: { startedMs: now, durationMs, startProgress: 0 },
    total,
    sessionId,
    targetCounts: countsForSeed(hash(jobId)),
  };
  publishMockEvent('session_started', { session_id: sessionId, source, name: session.name });
  return { job_id: jobId, session_id: sessionId };
}

route('POST', '/api/v1/batch/video', (request) => {
  const video = request.form?.get('video');
  if (!(video instanceof File)) return unprocessable('video', 'Field required');
  if (!/\.(mp4|avi|mov|mkv)$/i.test(video.name)) return detail(415, 'Choose an MP4, AVI, MOV, or MKV video.');
  if (video.size > 500 * 1024 * 1024) return detail(413, 'Choose a video no larger than 500 MB.');
  const invalid = parseBatchFields(request.form?.get('model_name'), request.form?.get('confidence'), request.form?.get('frame_stride') ?? undefined);
  if (invalid) return invalid;
  const name = request.form?.get('name');
  const accepted = queueBatchJob('batch_video', `Video batch: ${video.name}`, 'video', typeof name === 'string' ? name : undefined, 3000, VIDEO_JOB_MS);
  return ok(accepted, 202);
});

route('POST', '/api/v1/batch/images', (request) => {
  if (request.form) {
    const items = request.form.getAll('images');
    const images = items.filter((item): item is File => item instanceof File);
    if (images.length === 0) return detail(422, 'Upload at least one JPEG or PNG image.');
    if (images.length > 200) return detail(413, 'A multipart batch can contain at most 200 images.');
    const wrong = images.find((image) => !/\.(jpe?g|png)$/i.test(image.name));
    if (wrong) return detail(415, `${wrong.name} is not a JPEG or PNG image.`);
    const invalid = parseBatchFields(request.form.get('model_name'), request.form.get('confidence'));
    if (invalid) return invalid;
    const name = request.form.get('name');
    return ok(queueBatchJob('batch_images', `Image batch: ${images.length} files`, 'batch', typeof name === 'string' ? name : undefined, images.length, IMAGE_JOB_MS), 202);
  }
  const body = (request.json ?? {}) as { directory?: unknown; recursive?: unknown; model_name?: unknown; confidence?: unknown; name?: unknown };
  if (typeof body.directory !== 'string' || body.directory.trim() === '') return detail(422, 'directory is required.');
  const invalid = parseBatchFields(body.model_name, body.confidence);
  if (invalid) return invalid;
  const folder = body.directory.split(/[\\/]/).filter(Boolean).pop() ?? 'folder';
  const accepted = queueBatchJob(
    'batch_images',
    `Image folder: ${folder}`,
    'batch',
    typeof body.name === 'string' ? body.name : undefined,
    24,
    IMAGE_JOB_MS,
  );
  return ok(accepted, 202);
});

route('GET', '/api/v1/jobs', (request) => {
  const limit = intParam(request, 'limit', 50, 1, 1000);
  if (typeof limit !== 'number') return limit;
  const sorted = [...state.jobs].sort((a, b) => Date.parse(b.created_at) - Date.parse(a.created_at));
  return ok({ jobs: sorted.slice(0, limit).map((job) => structuredClone(job)) });
});

function findJob(id: string): Job | MockReply {
  return state.jobs.find((job) => job.id === id) ?? notFound('Job not found.');
}

route('GET', '/api/v1/jobs/:id', (request) => {
  const found = findJob(request.params.id);
  return 'isReply' in found ? found : ok(structuredClone(found));
});

route('POST', '/api/v1/jobs/:id/cancel', (request) => {
  const found = findJob(request.params.id);
  if ('isReply' in found) return found;
  if (found.status !== 'queued' && found.status !== 'running') {
    return detail(409, 'Job has already finished.');
  }
  const run = state.jobRuns[found.id];
  const now = iso();
  found.status = 'cancelled';
  found.message = 'Cancelled';
  found.finished_at = now;
  if (run?.sessionId) {
    const session = state.sessions.find((s) => s.id === run.sessionId);
    if (session) {
      session.status = 'failed';
      session.ended_at = now;
      session.duration_seconds = Math.round((Date.parse(now) - Date.parse(session.started_at)) / 1000);
      publishMockEvent('session_stopped', { session_id: session.id, status: 'failed' });
    }
  }
  delete state.jobRuns[found.id];
  publishMockEvent('job_finished', { job_id: found.id, status: 'cancelled', error: null });
  return ok(structuredClone(found));
});

// ---------------------------------------------------------------------------
// The clock: import jobs, benchmark runs, arm commands and running sessions move with time.
// ---------------------------------------------------------------------------

/** Moves every running job to where its clock says it should be, and publishes what changed. */
export function advanceMockJobs(now = Date.now()): void {
  for (const job of state.jobs) {
    const run = state.jobRuns[job.id];
    if (!run || job.status !== 'running') continue;
    const progress = progressAt(run.clock, now);
    const finished = progress >= 1;
    job.progress = progress;
    job.message = progressMessage(run.kind, progress, run.total);
    if (run.kind === 'benchmark') {
      const done = Math.min(run.total, Math.floor(progress * run.total));
      const bench = state.benchmarks.find((b) => b.id === run.runId);
      if (bench) {
        const models = run.models ?? [];
        bench.results = done === 0 ? null : models.slice(0, finished ? models.length : done).map(benchmarkResultForRun);
        if (finished) bench.status = 'completed';
      }
    }
    if (run.sessionId && run.targetCounts) {
      const session = state.sessions.find((s) => s.id === run.sessionId);
      if (session) {
        session.class_counts = scaledCounts(run.targetCounts, progress);
        session.total_detections = CLASS_NAMES.reduce((sum, cls) => sum + session.class_counts[cls], 0);
      }
    }
    publishMockEvent('job_progress', { job_id: job.id, progress, message: job.message });
    if (finished) finishMockJob(job, run, now);
  }
}

function benchmarkResultForRun(model: string) {
  return benchmarkResultFor(model, model === MODEL_WITH_ERRORS ? [MODEL_ERROR_TEXT] : []);
}

function finishMockJob(job: Job, run: MockJobRun, now: number): void {
  job.status = 'completed';
  job.progress = 1;
  job.message = 'Finished';
  job.finished_at = iso(now);
  if (run.kind === 'benchmark') {
    const bench = state.benchmarks.find((b) => b.id === run.runId);
    job.result = { run_id: run.runId ?? null, models: run.total };
    if (bench) job.result = { run_id: bench.id, results: bench.results ?? [] };
  } else if (run.sessionId) {
    job.result = { session_id: run.sessionId, units: run.total };
    const session = state.sessions.find((s) => s.id === run.sessionId);
    if (session) {
      session.status = 'completed';
      session.ended_at = iso(now);
      session.duration_seconds = Math.round((now - Date.parse(session.started_at)) / 1000);
      const rows = sessionDetectionsFor(session);
      session.avg_confidence = rows.length
        ? Math.round((rows.reduce((sum, row) => sum + row.confidence, 0) / rows.length) * 1000) / 1000
        : null;
      publishMockEvent('session_stopped', { session_id: session.id, status: 'completed' });
    }
  }
  delete state.jobRuns[job.id];
  publishMockEvent('job_finished', { job_id: job.id, status: job.status, error: null });
}

/** Keeps active sessions' durations growing while they run. */
function refreshActiveSessions(now: number): void {
  for (const session of state.sessions) {
    if (session.status === 'active') {
      session.duration_seconds = Math.max(0, Math.round((now - Date.parse(session.started_at)) / 1000));
    }
  }
}

/** Completes arm commands whose simulated travel time has passed. */
function advanceArm(now: number): void {
  const due = state.armPending.filter((pending) => pending.dueMs <= now);
  if (due.length === 0) return;
  state.armPending = state.armPending.filter((pending) => pending.dueMs > now);
  for (const pending of due) {
    const completed: ArmEvent = {
      id: nextEventId(),
      ts: iso(now),
      kind: `${pending.action}_completed` as ArmEventKind,
      class_name: pending.requested.class_name,
      track_id: pending.requested.track_id,
      payload: { request_id: pending.requested.id, message: `Simulated: ${pending.action}` },
      correct: null,
    };
    state.armEvents.unshift(completed);
    publishMockEvent('arm_event', completed);
  }
}

/** One step of the mock clock. Runs before every request and once a second on the events socket. */
export function tickMock(now = Date.now()): void {
  advanceArm(now);
  advanceMockJobs(now);
  refreshActiveSessions(now);
}

// ---------------------------------------------------------------------------
// Hardware and sorting arm (v1)
// ---------------------------------------------------------------------------

route('GET', '/api/v1/hardware/current', () => ok(mockHardwareCurrent(Date.now(), state.hardwareSensor)));

route('GET', '/api/v1/hardware/history', (request) => {
  const minutes = intParam(request, 'minutes', 60, 1, 1440);
  if (typeof minutes !== 'number') return minutes;
  const points = intParam(request, 'points', 240, 10, 1000);
  if (typeof points !== 'number') return points;
  return ok({ points: mockHardwareHistory(minutes, points, Date.now(), state.hardwareSensor), minutes });
});

route('GET', '/api/v1/arm/status', () => {
  const accuracy = accuracyOf(state.armEvents);
  return ok({
    connected: false,
    mode: 'simulated',
    state: state.armPending.length ? 'busy' : 'idle',
    queue_length: 0,
    last_event_at: state.armEvents[0]?.ts ?? null,
    accuracy: accuracy.accuracy,
    total_feedback: accuracy.total,
  });
});

const ARM_ACTIONS: ArmCommandAction[] = ['sort', 'home', 'stop'];

route('POST', '/api/v1/arm/commands', (request) => {
  const body = (request.json ?? {}) as { action?: unknown; class_name?: unknown; track_id?: unknown };
  if (typeof body.action !== 'string' || !ARM_ACTIONS.includes(body.action as ArmCommandAction)) {
    return unprocessable('action', 'Input should be sort, home or stop');
  }
  const action = body.action as ArmCommandAction;
  if (body.class_name !== undefined && !CLASS_NAMES.includes(body.class_name as ClassName)) {
    return unprocessable('class_name', `class_name must be one of: ${CLASS_NAMES.join(', ')}`);
  }
  if (action === 'sort' && body.class_name === undefined) {
    return unprocessable('class_name', 'class_name is required for sort commands');
  }
  if (state.armPending.length) return detail(409, 'The sorting arm is busy');
  const now = Date.now();
  const requested: ArmEvent = {
    id: nextEventId(),
    ts: iso(now),
    kind: `${action}_requested` as ArmEventKind,
    class_name: (body.class_name as ClassName | undefined) ?? null,
    track_id: typeof body.track_id === 'number' ? body.track_id : null,
    payload: { action },
    correct: null,
  };
  state.armEvents.unshift(requested);
  state.armPending.push({ dueMs: now + ARM_COMMAND_MS, action, requested });
  publishMockEvent('arm_event', requested);
  return ok(requested, 202);
});

route('GET', '/api/v1/arm/events', (request) => {
  const limit = intParam(request, 'limit', 100, 1, 1000);
  if (typeof limit !== 'number') return limit;
  const kind = request.query.get('kind');
  const events = state.armEvents.filter((e) => !kind || e.kind === kind).slice(0, limit);
  return ok({ events: events.map((e) => structuredClone(e)) });
});

route('POST', '/api/v1/arm/events/:id/feedback', (request) => {
  const id = Number(request.params.id);
  const event = state.armEvents.find((e) => e.id === id);
  if (!event) return notFound('Arm event not found');
  const body = (request.json ?? {}) as { correct?: unknown };
  if (typeof body.correct !== 'boolean') return unprocessable('correct', 'Input should be a valid boolean');
  if (event.kind !== 'sort_completed') return detail(409, 'Feedback is only accepted for sort_completed events');
  event.correct = body.correct;
  return ok(structuredClone(event));
});

function accuracyOf(events: ArmEvent[]) {
  const judged = events.filter((e) => e.kind === 'sort_completed' && e.correct !== null);
  const correct = judged.filter((e) => e.correct === true).length;
  return {
    accuracy: judged.length ? Math.round((correct / judged.length) * 1000) / 1000 : null,
    correct,
    total: judged.length,
  };
}

route('GET', '/api/v1/arm/accuracy', () => ok(accuracyOf(state.armEvents)));

/** Resolves a request to a reply. Unknown routes answer 404 "Not Found", as FastAPI does. */
export async function handleMockRequest(request: Omit<MockRequest, 'params'>): Promise<MockReply> {
  tickMock();
  const match = matchRoute(request.method, request.path);
  if (!match) return reply(404, { detail: 'Not Found' });
  return match.route.handler({ ...request, params: match.params });
}

export const MOCK_ROUTE_COUNT = routes.length;
