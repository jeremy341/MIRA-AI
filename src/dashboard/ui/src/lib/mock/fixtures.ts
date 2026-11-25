/**
 * Mock fixtures for VITE_MOCK=1. Every value is typed against the wire types in lib/types.ts,
 * so `pnpm check` validates the shapes; fixtures.test.ts checks the values (ranges, ids, ISO times).
 * The data is invented: no real session, path or person is represented.
 */
import { CLASS_NAMES, type BenchmarkRun, type ClassCounts, type ClassName, type CompareResponse, type ComparisonSummary, type Detection, type HardwareCurrent, type HardwarePoint, type Job, type MetricsHistoryResponse, type ModelInfo, type SessionDetail, type SessionDetection, type SessionSummary, type SessionTimelineResponse, type StatisticsResponse, type SystemMetrics, type TimelineBucket, type ArmEvent, type ArmStatus, type ArmAccuracy } from '../types';

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

const ANCHOR = Date.UTC(2026, 10, 25, 11, 0, 0);
const iso = (ms: number) => new Date(ms).toISOString();

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

const SESSION_NAMES = [
  'Glass line test, morning',
  'Mixed bin, glass and paper',
  'Plastic cups, lamp on',
  'Night run, camera at 720p',
  'Metal cans, low light',
  'Video batch: bin B2',
  'Model check, Exp018',
];

/** Session details, newest first. The list endpoint returns the same records without `config` and `notes`. */
export const MOCK_SESSIONS: SessionDetail[] = SESSION_NAMES.map((name, index) => {
  const random = rng(100 + index);
  const sources: SessionSummary['source'][] = ['camera', 'camera', 'camera', 'camera', 'camera', 'batch', 'image'];
  const counts = emptyClassCounts();
  let total = 0;
  for (const cls of CLASS_NAMES) {
    counts[cls] = Math.floor(random() * 90);
    total += counts[cls];
  }
  const durationSeconds = 240 + Math.floor(random() * 3600);
  const startedMs = ANCHOR - (index + 1) * 86_400_000 * 0.6;
  const isActive = false;
  return {
    id: `s${String(index + 1).padStart(3, '0')}7f3a`,
    name,
    source: sources[index],
    model_name: index % 3 === 1 ? 'mira_exp019_int8.tflite' : 'mira_exp018.pt',
    status: isActive ? 'active' : index === 3 ? 'failed' : 'completed',
    started_at: iso(startedMs),
    ended_at: isActive ? null : iso(startedMs + durationSeconds * 1000),
    duration_seconds: durationSeconds,
    total_detections: total,
    class_counts: counts,
    avg_confidence: Math.round((0.6 + random() * 0.3) * 1000) / 1000,
    config: { source: sources[index], camera: { index: 0, width: 640, height: 360, fps: 30 }, model: 'mira_exp018.pt' },
    notes: index === 0 ? 'Belt speed at 0.4 m/s. Lighting from the left.' : null,
  } satisfies SessionDetail;
});

export function summaryOf(session: SessionDetail): SessionSummary {
  const { config: _config, notes: _notes, ...summary } = session;
  return summary;
}

/** Deterministic detections for one session. */
export function sessionDetectionsFor(session: SessionDetail, count = 40): SessionDetection[] {
  const random = rng(hash(session.id));
  const start = Date.parse(session.started_at);
  const rows: SessionDetection[] = [];
  for (let i = 0; i < count; i += 1) {
    const offset = Math.round(random() * session.duration_seconds * 10) / 10;
    const x1 = Math.round(random() * 500);
    const y1 = Math.round(random() * 260);
    rows.push({
      ts: iso(start + offset * 1000),
      offset_seconds: offset,
      frame_index: Math.floor(offset * 30),
      class_name: CLASS_NAMES[Math.floor(random() * CLASS_NAMES.length)],
      confidence: Math.round((0.3 + random() * 0.69) * 1000) / 1000,
      bbox: [x1, y1, x1 + 40 + Math.round(random() * 90), y1 + 40 + Math.round(random() * 70)],
      track_id: random() > 0.3 ? Math.floor(random() * 20) + 1 : null,
    });
  }
  return rows.sort((a, b) => a.offset_seconds - b.offset_seconds);
}

export function sessionTimelineFor(session: SessionDetail, bucketSeconds: number): SessionTimelineResponse {
  const random = rng(hash(session.id) + 7);
  const duration = session.duration_seconds;
  const bucketCount = Math.min(600, Math.max(1, Math.ceil(duration / bucketSeconds)));
  const buckets: TimelineBucket[] = [];
  for (let b = 0; b < bucketCount; b += 1) {
    const counts = emptyClassCounts();
    const objects = Math.floor(random() * 6);
    for (let i = 0; i < objects; i += 1) {
      counts[CLASS_NAMES[Math.floor(random() * CLASS_NAMES.length)]] += 1;
    }
    buckets.push({
      start_offset: b * bucketSeconds,
      objects,
      class_counts: counts,
      avg_confidence: objects ? Math.round((0.45 + random() * 0.45) * 1000) / 1000 : null,
      fps: Math.round((24 + random() * 8) * 10) / 10,
      latency_ms: Math.round(38 + random() * 22),
    });
  }
  return { duration_seconds: duration, bucket_seconds: bucketSeconds, buckets };
}

export const MOCK_STATISTICS: StatisticsResponse = {
  statistics: {
    period_start: iso(ANCHOR - 60_000),
    period_end: iso(ANCHOR),
    total_detections: 17,
    class_counts: { glass: 6, paper: 4, plastic: 4, metal: 2, trash: 1 },
    avg_confidence: { glass: 0.84, paper: 0.79, plastic: 0.71, metal: 0.9, trash: 0.58 },
    sorting_accuracy: null,
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
      fps: Math.round((24 + random() * 6) * 10) / 10,
      inference_latency_ms: Math.round((38 + random() * 14) * 10) / 10,
      avg_latency_ms: 44.2,
      cpu_percent: Math.round((30 + random() * 25) * 10) / 10,
      memory_percent: Math.round((42 + random() * 4) * 10) / 10,
      temperature_celsius: Math.round((52 + random() * 6) * 10) / 10,
      detections_per_second: Math.round(random() * 40) / 10,
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
      confidence: Math.round((0.4 + random() * 0.59) * 1000) / 1000,
      bbox: [x1, y1, x1 + 70, y1 + 60],
      track_id: i % 4 === 0 ? null : (i % 9) + 1,
      timestamp: iso(ANCHOR - i * 4000),
    });
  }
  return rows;
}

/** A 1x1 grey JPEG, used where a compare result needs an annotated image. */
export const TINY_JPEG_DATA_URI =
  'data:image/jpeg;base64,/9j/4AAQSkZJRgABAQEASABIAAD/2wBDAP//////////////////////////////////////////////////////////////////////////////////////wgALCAABAAEBAREA/8QAFBABAAAAAAAAAAAAAAAAAAAAAP/aAAgBAQABPxA=';

export const MOCK_COMPARISONS: CompareResponse[] = [
  {
    id: 'cmp-7f31a2',
    input_name: 'bin-sample-01.jpg',
    models: [
      {
        name: 'mira_exp018.pt',
        latency_ms: 61.4,
        objects: 4,
        class_counts: { glass: 2, metal: 0, paper: 1, plastic: 1, trash: 0 },
        avg_confidence: 0.81,
        detections: [],
        annotated_image: TINY_JPEG_DATA_URI,
      },
      {
        name: 'mira_exp019_int8.tflite',
        latency_ms: 22.9,
        objects: 3,
        class_counts: { glass: 2, metal: 0, paper: 0, plastic: 1, trash: 0 },
        avg_confidence: 0.76,
        detections: [],
        annotated_image: TINY_JPEG_DATA_URI,
      },
    ],
    winner_hint: { model: 'mira_exp019_int8.tflite', reason: 'Lower latency at a similar count' },
  },
];

export const MOCK_COMPARISON_SUMMARIES: ComparisonSummary[] = MOCK_COMPARISONS.map((c) => ({
  id: c.id,
  created_at: iso(ANCHOR - 3_600_000),
  input_name: c.input_name,
  models: c.models.map((m) => m.name),
}));

export const MOCK_BENCHMARKS: BenchmarkRun[] = [
  {
    id: 'bench-41c0',
    status: 'completed',
    config: { models: ['mira_exp018.pt', 'mira_exp019_int8.tflite'], confidence: 0.25, max_images: 200 },
    results: [
      {
        model: 'mira_exp018.pt',
        map50: 0.812,
        map50_95: 0.583,
        precision: 0.861,
        recall: 0.774,
        f1: 0.815,
        avg_latency_ms: 58.2,
        fps: 17.2,
        per_class: { glass: { ap50: 0.88 }, paper: { ap50: 0.82 } },
        errors: null,
      },
      {
        model: 'mira_exp019_int8.tflite',
        map50: 0.79,
        map50_95: 0.55,
        precision: 0.84,
        recall: 0.751,
        f1: 0.793,
        avg_latency_ms: 21.4,
        fps: 46.7,
        per_class: { glass: { ap50: 0.86 }, paper: { ap50: 0.8 } },
        errors: null,
      },
    ],
    job_id: 'job-b41c0',
  },
  {
    id: 'bench-9a2e',
    status: 'running',
    config: { models: ['mira_exp014.pt'], confidence: 0.25 },
    results: null,
    job_id: 'job-9a2e',
  },
];

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
    id: 'job-6d02',
    kind: 'batch_video',
    title: 'Video batch: bin B2 (stride 5)',
    status: 'running',
    progress: 0.42,
    message: 'Frame 1,260 of 3,000',
    created_at: iso(ANCHOR - 600_000),
    finished_at: null,
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
    created_at: iso(ANCHOR - 86_400_000),
    finished_at: iso(ANCHOR - 86_000_000),
    result: null,
    error: 'One image could not be decoded. Remove it and run the folder again.',
  },
];

export const MOCK_HARDWARE_CURRENT: HardwareCurrent = {
  ts: iso(ANCHOR),
  cpu_percent: 41.8,
  memory_percent: 47.2,
  memory_used_mb: 3_780.4,
  memory_total_mb: 8_010.0,
  temperature_c: 58.4,
  load_1m: 1.12,
  platform: 'Linux 6.6 (aarch64)',
  is_raspberry_pi: true,
  cpu_count: 4,
};

export function mockHardwareHistory(minutes: number, points: number): HardwarePoint[] {
  const random = rng(77);
  const count = Math.max(1, Math.min(points, minutes * 2));
  const rows: HardwarePoint[] = [];
  for (let i = 0; i < count; i += 1) {
    rows.push({
      ts: iso(ANCHOR - (count - i) * ((minutes * 60_000) / count)),
      cpu_percent: Math.round((35 + random() * 20) * 10) / 10,
      memory_percent: Math.round((46 + random() * 3) * 10) / 10,
      temperature_c: Math.round((55 + random() * 8) * 10) / 10,
    });
  }
  return rows;
}

export const MOCK_ARM_STATUS: ArmStatus = {
  connected: false,
  mode: 'simulated',
  state: 'idle',
  queue_length: 0,
  last_event_at: iso(ANCHOR - 120_000),
  accuracy: 0.8,
  total_feedback: 5,
};

export const MOCK_ARM_EVENTS: ArmEvent[] = [
  {
    id: 1,
    ts: iso(ANCHOR - 120_000),
    kind: 'sort_completed',
    class_name: 'glass',
    track_id: 4,
    payload: { bin: 'glass', simulated: true },
    correct: true,
  },
  {
    id: 2,
    ts: iso(ANCHOR - 150_000),
    kind: 'sort_requested',
    class_name: 'glass',
    track_id: 4,
    payload: { source: 'detect' },
    correct: null,
  },
  {
    id: 3,
    ts: iso(ANCHOR - 300_000),
    kind: 'sort_completed',
    class_name: 'paper',
    track_id: 9,
    payload: { bin: 'paper', simulated: true },
    correct: false,
  },
];

export const MOCK_ARM_ACCURACY: ArmAccuracy = { accuracy: 0.8, correct: 4, total: 5 };

/** A class name for the mock detection stream (random boxes drawn over generated frames). */
export function randomClass(random: () => number): ClassName {
  return CLASS_NAMES[Math.floor(random() * CLASS_NAMES.length)];
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

export function mockJobById(id: string): Job | undefined {
  return MOCK_JOBS.find((job) => job.id === id);
}

export type MockDetection = Detection;
export type MockBucket = TimelineBucket;
export type MockMetric = SystemMetrics;
export type MockJob = Job;
