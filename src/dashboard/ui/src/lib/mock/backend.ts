/**
 * In-memory stand-in for the FastAPI server, used when VITE_MOCK=1. It answers the same routes
 * with the same status codes and error shapes as the contract (409 with `missing`, 422 with a
 * validation list, 404 "Not Found" for an unknown route, 404 with a message for an unknown id).
 * It holds state, so starting a stream in the UI makes the mock socket send frames.
 */
import { CLASS_NAMES, type ArmCommandAction, type ArmEvent, type BatchAccepted, type BenchmarkRun, type CameraConfig, type CompareResponse, type Detection, type Job, type ModelConfig, type SessionCreateBody, type SessionDetail, type SessionSource, type SessionStatus } from '../types';
import { defaultSessionName } from '../format';
import {
  MOCK_ARM_ACCURACY,
  MOCK_ARM_EVENTS,
  MOCK_ARM_STATUS,
  MOCK_BENCHMARKS,
  MOCK_COMPARISONS,
  MOCK_COMPARISON_SUMMARIES,
  MOCK_HARDWARE_CURRENT,
  MOCK_JOBS,
  MOCK_MODELS,
  MOCK_SESSIONS,
  MOCK_STATISTICS,
  mockHardwareHistory,
  mockMetricsHistory,
  mockRecentDetections,
  rng,
  sessionDetectionsFor,
  sessionTimelineFor,
  summaryOf,
} from './fixtures';

/** What the mock keeps between requests. Mutated by the handlers below. */
export interface MockState {
  camera: CameraConfig | null;
  model: ModelConfig | null;
  streaming: boolean;
  sessions: SessionDetail[];
  comparisons: CompareResponse[];
  benchmarks: BenchmarkRun[];
  jobs: Job[];
  armEvents: ArmEvent[];
  nextId: number;
}

export function createMockState(): MockState {
  return {
    camera: null,
    model: null,
    streaming: false,
    sessions: structuredClone(MOCK_SESSIONS),
    comparisons: structuredClone(MOCK_COMPARISONS),
    benchmarks: structuredClone(MOCK_BENCHMARKS),
    jobs: structuredClone(MOCK_JOBS),
    armEvents: structuredClone(MOCK_ARM_EVENTS),
    nextId: 1000,
  };
}

export const state: MockState = createMockState();

export function resetMockState(): void {
  Object.assign(state, createMockState());
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

const iso = () => new Date().toISOString();
const newId = (prefix: string) => {
  state.nextId += 1;
  return `${prefix}-${state.nextId.toString(16)}`;
};

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

route('GET', '/api/v1/sessions', (request) => {
  const limit = intParam(request, 'limit', 50, 1, 500);
  if (typeof limit !== 'number') return limit;
  const offset = intParam(request, 'offset', 0, 0, 1_000_000);
  if (typeof offset !== 'number') return offset;
  const status = request.query.get('status');
  const matching = state.sessions.filter((s) => !status || s.status === status);
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
    class_counts: { glass: 0, metal: 0, paper: 0, plastic: 0, trash: 0 },
    avg_confidence: null,
    config: { source: body.source, camera: state.camera },
    notes: null,
  };
  state.sessions.unshift(session);
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
    found.status = 'completed' as SessionStatus;
    found.ended_at = iso();
    const started = Date.parse(found.started_at);
    found.duration_seconds = Math.max(0, Math.round((Date.parse(found.ended_at) - started) / 1000));
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

route('POST', '/api/v1/compare', async (request) => {
  const image = request.form?.get('image');
  const models = String(request.form?.get('models') ?? '')
    .split(',')
    .map((name) => name.trim())
    .filter(Boolean);
  if (!(image instanceof Blob)) return unprocessable('image', 'Field required');
  if (models.length < 2 || models.length > 4) return unprocessable('models', 'Choose 2 to 4 models');
  if (models.some((name) => !MOCK_MODELS.some((model) => model.name === name))) {
    return detail(404, 'Unknown model in the list');
  }
  const confidence = Number(request.form?.get('confidence') ?? '0.25');
  if (!Number.isFinite(confidence) || confidence < 0.05 || confidence > 1) {
    return unprocessable('confidence', 'Input should be between 0.05 and 1');
  }
  const size = await imageSize(image);
  const annotated = await blobToDataUri(image);
  const random = rng(image.size);
  const result: CompareResponse = {
    id: newId('cmp'),
    input_name: image instanceof File ? image.name : 'upload',
    models: models.map((name) => {
      const detections = randomDetections(size.width, size.height, 2 + Math.floor(random() * 3), random);
      const counts = { glass: 0, metal: 0, paper: 0, plastic: 0, trash: 0 };
      for (const d of detections) counts[d.class_name] += 1;
      const average = detections.reduce((sum, d) => sum + d.confidence, 0) / Math.max(1, detections.length);
      return {
        name,
        latency_ms: Math.round((20 + random() * 50) * 10) / 10,
        objects: detections.length,
        class_counts: counts,
        avg_confidence: Math.round(average * 1000) / 1000,
        detections,
        annotated_image: annotated,
      };
    }),
    winner_hint: { model: models[0], reason: 'Mock comparison' },
  };
  state.comparisons.unshift(result);
  return ok(result);
});

route('GET', '/api/v1/compare', (request) => {
  const limit = intParam(request, 'limit', 20, 1, 200);
  if (typeof limit !== 'number') return limit;
  const summaries = state.comparisons.slice(0, limit).map((c) => {
    const found = MOCK_COMPARISON_SUMMARIES.find((s) => s.id === c.id);
    return found ?? { id: c.id, created_at: iso(), input_name: c.input_name, models: c.models.map((m) => m.name) };
  });
  return ok(summaries);
});

function findComparison(id: string): CompareResponse | MockReply {
  return state.comparisons.find((c) => c.id === id) ?? notFound('Comparison not found');
}

route('GET', '/api/v1/compare/:id', (request) => {
  const found = findComparison(request.params.id);
  return 'isReply' in found ? found : ok(found);
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
  const body = (request.json ?? {}) as { models?: unknown; confidence?: unknown };
  if (!Array.isArray(body.models) || body.models.length === 0) {
    return unprocessable('models', 'Choose at least one model');
  }
  if (body.models.some((name) => typeof name !== 'string' || !MOCK_MODELS.some((m) => m.name === name))) {
    return detail(422, 'Unknown model in the list');
  }
  const confidence = typeof body.confidence === 'number' ? body.confidence : 0.25;
  const runId = newId('bench');
  const jobId = newId('job');
  const run: BenchmarkRun = {
    id: runId,
    status: 'queued',
    config: { models: body.models, confidence },
    results: null,
    job_id: jobId,
  };
  state.benchmarks.unshift(run);
  state.jobs.unshift({
    id: jobId,
    kind: 'benchmark',
    title: `Benchmark: ${body.models.length} model${body.models.length === 1 ? '' : 's'}`,
    status: 'queued',
    progress: 0,
    message: 'Waiting to start',
    created_at: iso(),
    finished_at: null,
    result: null,
    error: null,
  });
  return ok({ run_id: runId, job_id: jobId }, 202);
});

route('GET', '/api/v1/benchmark/runs', (request) => {
  const limit = intParam(request, 'limit', 20, 1, 200);
  if (typeof limit !== 'number') return limit;
  return ok(state.benchmarks.slice(0, limit));
});

function findBenchmark(id: string): BenchmarkRun | MockReply {
  return state.benchmarks.find((b) => b.id === id) ?? notFound('Benchmark run not found');
}

route('GET', '/api/v1/benchmark/runs/:id', (request) => {
  const found = findBenchmark(request.params.id);
  return 'isReply' in found ? found : ok(found);
});

route('DELETE', '/api/v1/benchmark/runs/:id', (request) => {
  const found = findBenchmark(request.params.id);
  if ('isReply' in found) return found;
  state.benchmarks = state.benchmarks.filter((b) => b.id !== found.id);
  return reply(204);
});

// ---------------------------------------------------------------------------
// Batch and jobs (v1)
// ---------------------------------------------------------------------------

function queueBatchJob(kind: string, title: string, sessionSource: SessionSource, name?: string): BatchAccepted {
  const jobId = newId('job');
  const sessionId = newId('s');
  state.jobs.unshift({
    id: jobId,
    kind,
    title,
    status: 'running',
    progress: 0.05,
    message: 'Starting',
    created_at: iso(),
    finished_at: null,
    result: null,
    error: null,
  });
  state.sessions.unshift({
    id: sessionId,
    name: name?.trim() || defaultSessionName(),
    source: sessionSource,
    model_name: state.model?.name ?? null,
    status: 'active',
    started_at: iso(),
    ended_at: null,
    duration_seconds: 0,
    total_detections: 0,
    class_counts: { glass: 0, metal: 0, paper: 0, plastic: 0, trash: 0 },
    avg_confidence: null,
    config: { source: sessionSource },
    notes: null,
  });
  return { job_id: jobId, session_id: sessionId };
}

route('POST', '/api/v1/batch/video', (request) => {
  const video = request.form?.get('video');
  const modelName = request.form?.get('model_name');
  if (!(video instanceof File)) return unprocessable('video', 'Field required');
  if (!/\.(mp4|avi|mov|mkv)$/i.test(video.name)) return detail(415, 'Choose an mp4, avi, mov or mkv video.');
  if (video.size > 500 * 1024 * 1024) return detail(413, 'Choose a video no larger than 500 MB.');
  if (typeof modelName !== 'string' || !MOCK_MODELS.some((m) => m.name === modelName)) {
    return unprocessable('model_name', 'Choose a model from the list');
  }
  const name = request.form?.get('name');
  return ok(queueBatchJob('batch_video', `Video batch: ${video.name}`, 'video', typeof name === 'string' ? name : undefined), 202);
});

route('POST', '/api/v1/batch/images', (request) => {
  if (request.form) {
    const images = request.form.getAll('images').filter((item): item is File => item instanceof File);
    if (images.length === 0) return unprocessable('images', 'Choose at least one image');
    if (images.length > 200) return detail(422, 'Choose at most 200 images at a time.');
    return ok(queueBatchJob('batch_images', `Image batch: ${images.length} files`, 'batch'), 202);
  }
  const body = (request.json ?? {}) as { directory?: unknown; recursive?: unknown };
  if (typeof body.directory !== 'string' || body.directory.trim() === '') {
    return unprocessable('directory', 'Enter a folder path');
  }
  if (body.recursive === true) return unprocessable('recursive', 'Recursive folders are not supported yet');
  return ok(queueBatchJob('batch_images', `Image folder: ${body.directory.split(/[\\/]/).pop() ?? 'folder'}`, 'batch'), 202);
});

route('GET', '/api/v1/jobs', (request) => {
  const limit = intParam(request, 'limit', 50, 1, 500);
  if (typeof limit !== 'number') return limit;
  return ok({ jobs: state.jobs.slice(0, limit) });
});

function findJob(id: string): Job | MockReply {
  return state.jobs.find((job) => job.id === id) ?? notFound('Job not found');
}

route('GET', '/api/v1/jobs/:id', (request) => {
  const found = findJob(request.params.id);
  return 'isReply' in found ? found : ok(found);
});

route('POST', '/api/v1/jobs/:id/cancel', (request) => {
  const found = findJob(request.params.id);
  if ('isReply' in found) return found;
  if (found.status === 'completed' || found.status === 'failed' || found.status === 'cancelled') {
    return detail(409, 'The job has already finished.');
  }
  found.status = 'cancelled';
  found.message = 'Cancelled';
  found.finished_at = iso();
  return ok(found);
});

// ---------------------------------------------------------------------------
// Hardware and sorting arm (v1)
// ---------------------------------------------------------------------------

route('GET', '/api/v1/hardware/current', () => ok({ ...MOCK_HARDWARE_CURRENT, ts: iso() }));

route('GET', '/api/v1/hardware/history', (request) => {
  const minutes = intParam(request, 'minutes', 60, 1, 1440);
  if (typeof minutes !== 'number') return minutes;
  const points = intParam(request, 'points', 240, 1, 2000);
  if (typeof points !== 'number') return points;
  return ok({ points: mockHardwareHistory(minutes, points), minutes });
});

route('GET', '/api/v1/arm/status', () => {
  const accuracy = accuracyOf(state.armEvents);
  return ok({
    ...MOCK_ARM_STATUS,
    accuracy: accuracy.accuracy,
    total_feedback: accuracy.total,
    last_event_at: state.armEvents[0]?.ts ?? null,
  });
});

const ARM_ACTIONS: ArmCommandAction[] = ['sort', 'home', 'stop'];

route('POST', '/api/v1/arm/commands', (request) => {
  const body = (request.json ?? {}) as { action?: unknown; class_name?: unknown; track_id?: unknown };
  if (typeof body.action !== 'string' || !ARM_ACTIONS.includes(body.action as ArmCommandAction)) {
    return unprocessable('action', 'Input should be sort, home or stop');
  }
  if (body.class_name !== undefined && !CLASS_NAMES.includes(body.class_name as (typeof CLASS_NAMES)[number])) {
    return unprocessable('class_name', 'Unknown class name');
  }
  const event: ArmEvent = {
    id: state.armEvents.length ? Math.max(...state.armEvents.map((e) => e.id)) + 1 : 1,
    ts: iso(),
    kind: body.action === 'sort' ? 'sort_requested' : `${body.action}_requested`,
    class_name: (body.class_name as ArmEvent['class_name']) ?? null,
    track_id: typeof body.track_id === 'number' ? body.track_id : null,
    payload: { simulated: true },
    correct: null,
  };
  state.armEvents.unshift(event);
  return ok(event, 202);
});

route('GET', '/api/v1/arm/events', (request) => {
  const limit = intParam(request, 'limit', 100, 1, 1000);
  if (typeof limit !== 'number') return limit;
  const kind = request.query.get('kind');
  const events = state.armEvents.filter((e) => !kind || e.kind === kind).slice(0, limit);
  return ok({ events });
});

route('POST', '/api/v1/arm/events/:id/feedback', (request) => {
  const id = Number(request.params.id);
  const event = state.armEvents.find((e) => e.id === id);
  if (!event) return notFound('Arm event not found');
  const body = (request.json ?? {}) as { correct?: unknown };
  if (typeof body.correct !== 'boolean') return unprocessable('correct', 'Input should be a valid boolean');
  event.correct = body.correct;
  return ok(event);
});

function accuracyOf(events: ArmEvent[]) {
  const judged = events.filter((e) => e.correct !== null);
  const correct = judged.filter((e) => e.correct === true).length;
  return {
    accuracy: judged.length ? Math.round((correct / judged.length) * 1000) / 1000 : null,
    correct,
    total: judged.length,
  };
}

route('GET', '/api/v1/arm/accuracy', () => {
  const computed = accuracyOf(state.armEvents);
  return ok(computed.total ? computed : MOCK_ARM_ACCURACY);
});

/** Resolves a request to a reply. Unknown routes answer 404 "Not Found", as FastAPI does. */
export async function handleMockRequest(request: Omit<MockRequest, 'params'>): Promise<MockReply> {
  const match = matchRoute(request.method, request.path);
  if (!match) return reply(404, { detail: 'Not Found' });
  return match.route.handler({ ...request, params: match.params });
}

export const MOCK_ROUTE_COUNT = routes.length;
