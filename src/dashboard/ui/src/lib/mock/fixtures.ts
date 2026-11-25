/**
 * Mock fixtures for VITE_MOCK=1. Every value is typed against the wire types in lib/types.ts, so
 * `pnpm check` validates the shapes; mock.test.ts checks the values (ranges, ids, ISO times, totals).
 * Detections and timelines are generated from the class counts, so the totals always agree.
 * The data is invented: no real session, path or person is represented.
 */
import {
  CLASS_NAMES,
  type ArmEvent,
  type ArmStatus,
  type BenchmarkClassMetrics,
  type BenchmarkModelResult,
  type BenchmarkRun,
  type ClassCounts,
  type ClassName,
  type CompareDetection,
  type CompareRecord,
  type CompareWinnerHint,
  type HardwareCurrent,
  type HardwarePoint,
  type Job,
  type MetricsHistoryResponse,
  type ModelInfo,
  type SessionDetail,
  type SessionDetection,
  type SessionSource,
  type SessionStatus,
  type SessionSummary,
  type SessionTimelineResponse,
  type StatisticsResponse,
  type SystemMetrics,
  type TimelineBucket,
  type Detection,
  type ArmAccuracy,
} from '../types';

/** Appears in the bundle only when mock mode is on. A production build must not contain it. */
export const MOCK_MARKER = 'mira-mock-layer-v1';

/** Deterministic pseudo-random numbers (mulberry32), so fixtures do not change between loads. */
export function rng(seed: number): () => number {
  let state = seed >>> 0;
  return () => {
    state = (state + 0x6d2b79f5) >>> 0;
    let t = state;
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

/** Used for session ids and seeds. A small string hash, not for security. */
export function hash(text: string): number {
  let h = 2166136261;
  for (let i = 0; i < text.length; i += 1) {
    h ^= text.charCodeAt(i);
    h = Math.imul(h, 16777619);
  }
  return h >>> 0;
}

const ANCHOR = Date.UTC(2026, 10, 25, 11, 0, 0);
const DAY_MS = 86_400_000;
const iso = (ms: number) => new Date(ms).toISOString();
const round = (value: number, digits = 1) => {
  const factor = 10 ** digits;
  return Math.round(value * factor) / factor;
};

export function emptyClassCounts(): ClassCounts {
  return { glass: 0, metal: 0, paper: 0, plastic: 0, trash: 0 };
}

export const MOCK_MODELS: ModelInfo[] = [
  {
    name: 'mira_exp018.pt',
    label: 'Mira Exp018.Pt',
    path: 'models/detection/mira_exp018.pt',
    model_type: 'yolo_pt',
    size_mb: 5.21,
    is_tflite_int8: false,
    input_size: 640,
    recommended: false,
  },
  {
    name: 'mira_exp019_int8.tflite',
    label: 'Mira Exp019 Int8.Tflite',
    path: 'models/detection/mira_exp019_int8.tflite',
    model_type: 'yolo_tflite',
    size_mb: 3.14,
    is_tflite_int8: true,
    input_size: 320,
    recommended: true,
  },
  {
    name: 'mira_exp014.pt',
    label: 'Mira Exp014.Pt',
    path: 'models/detection/mira_exp014.pt',
    model_type: 'yolo_pt',
    size_mb: 5.02,
    is_tflite_int8: false,
    input_size: 640,
    recommended: false,
  },
];

// ---------------------------------------------------------------------------
// Sessions
// ---------------------------------------------------------------------------

interface SessionSeed {
  id: string;
  name: string;
  source: SessionSource;
  model: string;
  status: SessionStatus;
  /** Start time, in days before the anchor. */
  ageDays: number;
  durationSeconds: number;
  notes: string | null;
}

/** Ids follow the `s<nnn>` pattern, newest first. The last one is an import that is still running. */
const SESSION_SEEDS: SessionSeed[] = [
  { id: 's001a7f3', name: 'Glass line test, morning', source: 'camera', model: 'mira_exp018.pt', status: 'completed', ageDays: 0.4, durationSeconds: 1850, notes: 'Belt speed at 0.4 m/s. Lighting from the left.' },
  { id: 's002a7f3', name: 'Mixed bin, glass and paper', source: 'camera', model: 'mira_exp019_int8.tflite', status: 'completed', ageDays: 1.2, durationSeconds: 3260, notes: null },
  { id: 's003a7f3', name: 'Plastic cups, lamp on', source: 'camera', model: 'mira_exp018.pt', status: 'completed', ageDays: 2.1, durationSeconds: 980, notes: null },
  { id: 's004a7f3', name: 'Night run, camera at 720p', source: 'camera', model: 'mira_exp018.pt', status: 'failed', ageDays: 3.4, durationSeconds: 420, notes: 'The camera disconnected after 7 minutes.' },
  { id: 's005a7f3', name: 'Metal cans, low light', source: 'camera', model: 'mira_exp019_int8.tflite', status: 'completed', ageDays: 4.5, durationSeconds: 2400, notes: null },
  { id: 's006a7f3', name: 'Video batch: bin B1', source: 'video', model: 'mira_exp019_int8.tflite', status: 'completed', ageDays: 5.6, durationSeconds: 3600, notes: 'Recorded on the bench camera, stride 5.' },
  { id: 's007a7f3', name: 'Model check, Exp018', source: 'image', model: 'mira_exp018.pt', status: 'completed', ageDays: 6.8, durationSeconds: 240, notes: null },
  { id: 's008b2run', name: 'Video batch: bin B2 (stride 5)', source: 'video', model: 'mira_exp019_int8.tflite', status: 'active', ageDays: 0, durationSeconds: 0, notes: null },
];

/** Class counts for a seed. Totals run from about 100 to about 700 detections. */
export function countsForSeed(seed: number): ClassCounts {
  const random = rng(seed);
  const counts = emptyClassCounts();
  for (const cls of CLASS_NAMES) counts[cls] = 20 + Math.floor(random() * 120);
  return counts;
}

function totalOf(counts: ClassCounts): number {
  return CLASS_NAMES.reduce((sum, cls) => sum + counts[cls], 0);
}

function sessionDetailFromSeed(seed: SessionSeed, index: number, counts: ClassCounts, now: number): SessionDetail {
  const startedMs = seed.ageDays === 0 ? now - 4 * 60_000 : ANCHOR - seed.ageDays * DAY_MS;
  const active = seed.status === 'active';
  const total = totalOf(counts);
  const random = rng(500 + index);
  return {
    id: seed.id,
    name: seed.name,
    source: seed.source,
    model_name: seed.model,
    status: seed.status,
    started_at: iso(startedMs),
    ended_at: active ? null : iso(startedMs + seed.durationSeconds * 1000),
    duration_seconds: active ? Math.round((now - startedMs) / 1000) : seed.durationSeconds,
    total_detections: total,
    class_counts: counts,
    avg_confidence: round(0.6 + random() * 0.3, 3),
    config: { source: seed.source, model: seed.model, camera: seed.source === 'camera' ? { index: 0, width: 640, height: 360, fps: 30 } : null },
    notes: seed.notes,
  } satisfies SessionDetail;
}

/** Session details, newest first. The list endpoint returns the same records without `config` and `notes`. */
export const MOCK_SESSIONS: SessionDetail[] = SESSION_SEEDS.map((seed, index) =>
  sessionDetailFromSeed(seed, index, seed.status === 'active' ? emptyClassCounts() : countsForSeed(100 + index), ANCHOR),
);

export function summaryOf(session: SessionDetail): SessionSummary {
  const { config: _config, notes: _notes, ...summary } = session;
  return summary;
}

/**
 * Detections for one session, sorted by time. The class of each row follows `class_counts`, so the
 * list always adds up to `total_detections`. Capped at 800 rows to keep the mock light.
 */
export function sessionDetectionsFor(
  session: Pick<SessionSummary, 'id' | 'started_at' | 'duration_seconds' | 'class_counts'>,
): SessionDetection[] {
  const random = rng(hash(session.id));
  const labels: ClassName[] = [];
  for (const cls of CLASS_NAMES) {
    for (let i = 0; i < session.class_counts[cls]; i += 1) labels.push(cls);
  }
  // Fisher-Yates shuffle, so the classes are spread over the whole run.
  for (let i = labels.length - 1; i > 0; i -= 1) {
    const j = Math.floor(random() * (i + 1));
    [labels[i], labels[j]] = [labels[j], labels[i]];
  }
  const start = Date.parse(session.started_at);
  const rows: SessionDetection[] = labels.slice(0, 800).map((cls) => {
    const offset = round(random() * session.duration_seconds, 1);
    const x1 = Math.round(random() * 500);
    const y1 = Math.round(random() * 260);
    return {
      ts: iso(start + offset * 1000),
      offset_seconds: offset,
      frame_index: Math.floor(offset * 30),
      class_name: cls,
      confidence: round(0.3 + random() * 0.69, 3),
      bbox: [x1, y1, x1 + 40 + Math.round(random() * 90), y1 + 40 + Math.round(random() * 70)],
      track_id: random() > 0.3 ? Math.floor(random() * 20) + 1 : null,
    };
  });
  return rows.sort((a, b) => a.offset_seconds - b.offset_seconds);
}

/**
 * Timeline buckets for a session, counted from its detections. Buckets are `bucketSeconds` wide and
 * cover the whole duration; a detection at the exact end falls into the last bucket.
 */
export function sessionTimelineFor(
  session: Pick<SessionSummary, 'id' | 'started_at' | 'duration_seconds' | 'class_counts'>,
  bucketSeconds: number,
): SessionTimelineResponse {
  const duration = session.duration_seconds;
  const count = Math.max(1, Math.ceil(duration / bucketSeconds));
  const random = rng(hash(session.id) + 7);
  const buckets: TimelineBucket[] = [];
  for (let b = 0; b < count; b += 1) {
    buckets.push({
      start_offset: b * bucketSeconds,
      objects: 0,
      class_counts: emptyClassCounts(),
      avg_confidence: null,
      fps: round(24 + random() * 8, 1),
      latency_ms: Math.round(38 + random() * 22),
    });
  }
  const confidenceSums = new Array<number>(count).fill(0);
  for (const row of sessionDetectionsFor(session)) {
    const index = Math.min(count - 1, Math.floor(row.offset_seconds / bucketSeconds));
    const bucket = buckets[index];
    bucket.objects += 1;
    bucket.class_counts[row.class_name] += 1;
    confidenceSums[index] += row.confidence;
  }
  buckets.forEach((bucket, index) => {
    bucket.avg_confidence = bucket.objects ? round(confidenceSums[index] / bucket.objects, 3) : null;
  });
  return { duration_seconds: duration, bucket_seconds: bucketSeconds, buckets };
}

/** Class counts scaled to a progress fraction, for a session whose import is still running. */
export function scaledCounts(target: ClassCounts, fraction: number): ClassCounts {
  const out = emptyClassCounts();
  for (const cls of CLASS_NAMES) out[cls] = Math.floor(target[cls] * Math.min(1, Math.max(0, fraction)));
  return out;
}

export const MOCK_STATISTICS: StatisticsResponse = {
  statistics: {
    period_start: iso(ANCHOR - 60_000),
    period_end: iso(ANCHOR),
    total_detections: 17,
    class_counts: { glass: 6, paper: 4, plastic: 4, metal: 2, trash: 1 },
    avg_confidence: { glass: 0.84, paper: 0.79, plastic: 0.71, metal: 0.9, trash: 0.58 },
    sorting_accuracy: 0.8,
    average_confidence: 0.78,
  },
  period_seconds: 60,
};

export function mockMetricsHistory(limit: number): MetricsHistoryResponse {
  const random = rng(42);
  const metrics: SystemMetrics[] = [];
  for (let i = 0; i < Math.min(limit, 120); i += 1) {
    metrics.push({
      timestamp: iso(ANCHOR - (120 - i) * 1000),
      fps: round(24 + random() * 6),
      inference_latency_ms: round(38 + random() * 14),
      avg_latency_ms: 44.2,
      cpu_percent: round(30 + random() * 25),
      memory_percent: round(42 + random() * 4),
      temperature_celsius: round(52 + random() * 6),
      detections_per_second: round(random() * 4),
      skip_frames: false,
    });
  }
  return { metrics, count: metrics.length, timestamp: iso(ANCHOR) };
}

export function mockRecentDetections(limit: number): Detection[] {
  const random = rng(9);
  const rows: Detection[] = [];
  for (let i = 0; i < Math.min(limit, 30); i += 1) {
    const x1 = Math.round(random() * 480);
    const y1 = Math.round(random() * 240);
    rows.push({
      class_name: CLASS_NAMES[i % CLASS_NAMES.length],
      confidence: round(0.4 + random() * 0.59, 3),
      bbox: [x1, y1, x1 + 70, y1 + 60],
      track_id: i % 4 === 0 ? null : (i % 9) + 1,
      timestamp: iso(ANCHOR - i * 4000),
    });
  }
  return rows;
}

// ---------------------------------------------------------------------------
// Compare and benchmark
// ---------------------------------------------------------------------------

/** The same wording as compare.py `_winner_hint`, so the mock and the server say the same thing. */
export const WINNER_NOTE = 'These are observations for this image only; they do not establish detection accuracy without ground truth.';

/** Computes the `winner_hint` the way compare.py does: first model wins a tie, confidence skips empty models. */
export function winnerHintFor(
  models: ReadonlyArray<{ name: string; latency_ms: number; objects: number; avg_confidence: number | null }>,
): CompareWinnerHint {
  const fastest = models.reduce((best, model) => (model.latency_ms < best.latency_ms ? model : best));
  const most = models.reduce((best, model) => (model.objects > best.objects ? model : best));
  const withConfidence = models.filter((model) => model.avg_confidence !== null);
  const highest = withConfidence.length
    ? withConfidence.reduce((best, model) => ((model.avg_confidence ?? 0) > (best.avg_confidence ?? 0) ? model : best))
    : null;
  return {
    fastest_model: fastest.name,
    most_objects_model: most.name,
    highest_avg_confidence_model: highest ? highest.name : null,
    note: WINNER_NOTE,
  };
}

/** Random boxes for a compare run. Compare detections have no timestamp. */
export function randomCompareDetections(width: number, height: number, count: number, random: () => number): CompareDetection[] {
  const rows: CompareDetection[] = [];
  for (let i = 0; i < count; i += 1) {
    const w = Math.round(width * (0.1 + random() * 0.2));
    const h = Math.round(height * (0.12 + random() * 0.22));
    const x1 = Math.round(random() * (width - w));
    const y1 = Math.round(random() * (height - h));
    rows.push({
      class_name: CLASS_NAMES[Math.floor(random() * CLASS_NAMES.length)],
      confidence: round(0.35 + random() * 0.6, 4),
      bbox: [x1, y1, x1 + w, y1 + h],
      track_id: null,
    });
  }
  return rows;
}

/** One stored compare record (no images), with `winner_hint` computed from its models. */
export function compareRecordFor(
  id: string,
  inputName: string,
  modelNames: string[],
  createdMs: number,
  seed: number,
): CompareRecord {
  const random = rng(seed);
  const models: CompareRecord['models'] = modelNames.map((name) => {
    const detections = randomCompareDetections(640, 480, 2 + Math.floor(random() * 4), random);
    const counts = emptyClassCounts();
    for (const d of detections) counts[d.class_name] += 1;
    const average = detections.reduce((sum, d) => sum + d.confidence, 0) / Math.max(1, detections.length);
    return {
      name,
      latency_ms: round(18 + random() * 50),
      objects: detections.length,
      class_counts: counts,
      avg_confidence: detections.length ? round(average, 4) : null,
      detections,
    };
  });
  return { id, created_at: iso(createdMs), input_name: inputName, models, winner_hint: winnerHintFor(models) };
}

export const MOCK_COMPARISONS: CompareRecord[] = [
  compareRecordFor('cmp-7f31a2', 'bin-sample-01.jpg', ['mira_exp018.pt', 'mira_exp019_int8.tflite'], ANCHOR - 3_600_000, 11),
  compareRecordFor('cmp-2b90c4', 'belt-frame-0412.png', ['mira_exp018.pt', 'mira_exp019_int8.tflite', 'mira_exp014.pt'], ANCHOR - 86_400_000, 12),
];

/** One model's benchmark row, deterministic per model name. Mirrors `_result_to_api` in benchmark.py. */
export function benchmarkResultFor(model: string, errors: string[] = []): BenchmarkModelResult {
  const random = rng(hash(model) + 3);
  const per_class: Record<string, BenchmarkClassMetrics> = {};
  let precisionSum = 0;
  let recallSum = 0;
  let f1Sum = 0;
  for (const cls of CLASS_NAMES) {
    const tp = 40 + Math.floor(random() * 160);
    const fp = Math.floor(random() * 30);
    const fn = Math.floor(random() * 40);
    const precision = round(tp / (tp + fp), 3);
    const recall = round(tp / (tp + fn), 3);
    const f1 = round((2 * precision * recall) / (precision + recall), 3);
    per_class[cls] = { tp, fp, fn, precision, recall, f1 };
    precisionSum += precision;
    recallSum += recall;
    f1Sum += f1;
  }
  const count = CLASS_NAMES.length;
  const map50 = round(0.7 + random() * 0.15, 3);
  return {
    model,
    map50,
    map50_95: round(map50 * 0.7, 3),
    precision: round(precisionSum / count, 3),
    recall: round(recallSum / count, 3),
    f1: round(f1Sum / count, 3),
    avg_latency_ms: round(15 + random() * 50),
    // The benchmark does not measure FPS, so the server sends null. The UI shows a dash.
    fps: null,
    per_class,
    errors,
  };
}

export const MOCK_DATASET_PATH = 'data/yolo/dataset.yaml';

export const MOCK_BENCHMARKS: BenchmarkRun[] = [
  {
    id: 'bench-41c0',
    created_at: iso(ANCHOR - 7_200_000),
    status: 'completed',
    config: { models: ['mira_exp018.pt', 'mira_exp019_int8.tflite'], dataset: MOCK_DATASET_PATH, confidence: 0.25, max_images: 200 },
    results: [benchmarkResultFor('mira_exp018.pt'), benchmarkResultFor('mira_exp019_int8.tflite')],
    job_id: 'job-b41c0',
  },
  {
    id: 'bench-9a2e',
    created_at: iso(ANCHOR - 3_600_000),
    status: 'cancelled',
    config: { models: ['mira_exp014.pt', 'mira_exp018.pt'], dataset: MOCK_DATASET_PATH, confidence: 0.3, max_images: 100 },
    results: [benchmarkResultFor('mira_exp014.pt', ['3 images had labels outside the five bin classes and were skipped.'])],
    job_id: 'job-9a2e',
  },
];

// ---------------------------------------------------------------------------
// Jobs
// ---------------------------------------------------------------------------

export const MOCK_JOBS: Job[] = [
  {
    id: 'job-b41c0',
    kind: 'benchmark',
    title: 'Benchmark: 2 models',
    status: 'completed',
    progress: 1,
    message: 'Finished',
    created_at: iso(ANCHOR - 7_200_000),
    finished_at: iso(ANCHOR - 7_000_000),
    result: { run_id: 'bench-41c0' },
    error: null,
  },
  {
    id: 'job-9a2e',
    kind: 'benchmark',
    title: 'Benchmark: 2 models',
    status: 'cancelled',
    progress: 0.5,
    message: 'Cancelled',
    created_at: iso(ANCHOR - 3_600_000),
    finished_at: iso(ANCHOR - 3_550_000),
    result: null,
    error: null,
  },
  {
    id: 'job-3c7a',
    kind: 'batch_images',
    title: 'Image folder: samples',
    status: 'failed',
    progress: 0.3,
    message: 'Stopped',
    created_at: iso(ANCHOR - DAY_MS),
    finished_at: iso(ANCHOR - DAY_MS + 400_000),
    result: null,
    error: 'One image could not be decoded. Remove it and run the folder again.',
  },
];

// ---------------------------------------------------------------------------
// Hardware and sorting arm
// ---------------------------------------------------------------------------

export function mockHardwareCurrent(now: number, sensor: boolean): HardwareCurrent {
  const wave = Math.sin(now / 41_000);
  return {
    ts: iso(now),
    cpu_percent: round(42 + wave * 9),
    memory_percent: round(47 + Math.cos(now / 90_000) * 1.5),
    memory_used_mb: 3780.4,
    memory_total_mb: 8010,
    temperature_c: sensor ? round(58 + wave * 2.5) : null,
    load_1m: round(1.1 + wave * 0.3, 2),
    platform: 'Linux 6.6 (aarch64)',
    is_raspberry_pi: true,
    cpu_count: 4,
  };
}

/** Hardware history ending at `now`, evenly spaced over `minutes`. `points` is the requested bucket count. */
export function mockHardwareHistory(minutes: number, points: number, now = Date.now(), sensor = true): HardwarePoint[] {
  const random = rng(77);
  const count = Math.max(1, points);
  const span = (minutes * 60_000) / count;
  const rows: HardwarePoint[] = [];
  for (let i = 0; i < count; i += 1) {
    const phase = i / Math.max(1, count - 1);
    rows.push({
      ts: iso(now - (count - 1 - i) * span),
      cpu_percent: round(36 + Math.sin(phase * 9) * 8 + random() * 4),
      memory_percent: round(46 + Math.sin(phase * 3) * 1.4 + random() * 0.8),
      temperature_c: sensor ? round(56 + Math.sin(phase * 6) * 2.5 + random() * 0.8) : null,
    });
  }
  return rows;
}

/** Arm events, newest first, as GET /arm/events returns them. Feedback is only set on sort_completed. */
export const MOCK_ARM_EVENTS: ArmEvent[] = [
  { id: 11, ts: iso(ANCHOR - 40_000), kind: 'sort_completed', class_name: 'plastic', track_id: 12, payload: { request_id: 10, message: 'Simulated: bin plastic' }, correct: null },
  { id: 10, ts: iso(ANCHOR - 41_000), kind: 'sort_requested', class_name: 'plastic', track_id: 12, payload: { action: 'sort' }, correct: null },
  { id: 9, ts: iso(ANCHOR - 120_000), kind: 'sort_completed', class_name: 'glass', track_id: 4, payload: { request_id: 8, message: 'Simulated: bin glass' }, correct: true },
  { id: 8, ts: iso(ANCHOR - 121_000), kind: 'sort_requested', class_name: 'glass', track_id: 4, payload: { action: 'sort' }, correct: null },
  { id: 7, ts: iso(ANCHOR - 300_000), kind: 'sort_completed', class_name: 'paper', track_id: 9, payload: { request_id: 6, message: 'Simulated: bin paper' }, correct: false },
  { id: 6, ts: iso(ANCHOR - 301_000), kind: 'sort_requested', class_name: 'paper', track_id: 9, payload: { action: 'sort' }, correct: null },
  { id: 5, ts: iso(ANCHOR - 480_000), kind: 'sort_completed', class_name: 'metal', track_id: 2, payload: { request_id: 4, message: 'Simulated: bin metal' }, correct: true },
  { id: 4, ts: iso(ANCHOR - 481_000), kind: 'sort_requested', class_name: 'metal', track_id: 2, payload: { action: 'sort' }, correct: null },
  { id: 3, ts: iso(ANCHOR - 600_000), kind: 'sort_completed', class_name: 'trash', track_id: 7, payload: { request_id: 2, message: 'Simulated: bin trash' }, correct: true },
  { id: 2, ts: iso(ANCHOR - 601_000), kind: 'sort_requested', class_name: 'trash', track_id: 7, payload: { action: 'sort' }, correct: null },
  { id: 1, ts: iso(ANCHOR - 720_000), kind: 'sort_completed', class_name: 'glass', track_id: 1, payload: { request_id: 0, message: 'Simulated: bin glass' }, correct: true },
];

/** Accuracy over sort_completed events that have feedback: 4 correct out of 5. */
export const MOCK_ARM_ACCURACY: ArmAccuracy = { accuracy: 0.8, correct: 4, total: 5 };

export const MOCK_ARM_STATUS: ArmStatus = {
  connected: false,
  mode: 'simulated',
  state: 'idle',
  queue_length: 0,
  last_event_at: MOCK_ARM_EVENTS[0].ts,
  accuracy: MOCK_ARM_ACCURACY.accuracy,
  total_feedback: MOCK_ARM_ACCURACY.total,
};

/** A class name for the mock detection stream (random boxes drawn over generated frames). */
export function randomClass(random: () => number): ClassName {
  return CLASS_NAMES[Math.floor(random() * CLASS_NAMES.length)];
}

export type MockDetection = Detection;
export type MockBucket = TimelineBucket;
export type MockMetric = SystemMetrics;
export type MockJob = Job;
