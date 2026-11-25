/**
 * Typed endpoints. Every legacy `/api/*` route and every `/api/v1` route in CONTRACT section 7.
 * Paths are relative to the app origin; the dev proxy and FastAPI both serve them there.
 */
import type { HttpClient, QueryParams } from './client';
import { buildUrl } from './client';
import type {
  ArmAccuracy,
  ArmCommandBody,
  ArmEvent,
  ArmEventsResponse,
  ArmStatus,
  BatchAccepted,
  BatchImagesJsonBody,
  BatchVideoFields,
  BenchmarkRun,
  BenchmarkRunAccepted,
  BenchmarkRunCreateBody,
  CameraConfig,
  CameraInitializeResponse,
  CompareResponse,
  ComparisonSummary,
  DetectImageResponse,
  HardwareCurrent,
  HardwareHistoryResponse,
  Job,
  JobListResponse,
  MetricsHistoryResponse,
  ModelConfig,
  ModelLoadResponse,
  ModelsResponse,
  RecentDetectionsResponse,
  SessionCreateBody,
  SessionDetail,
  SessionDetectionsResponse,
  SessionListResponse,
  SessionPatchBody,
  SessionStatus,
  SessionTimelineResponse,
  StatisticsResponse,
  StatusResponse,
  StreamResponse,
  ClassName,
} from '../types';

export type ExportFormat = 'csv' | 'json' | 'report';

/** Default timeouts, in milliseconds. Uploads and inference get longer budgets. */
export const TIMEOUTS = {
  quick: 8_000,
  default: 15_000,
  stream: 20_000,
  image: 60_000,
  upload: 10 * 60_000,
} as const;

/** Uploads a single image or a video. Limits mirror the server (8 MB images, 500 MB videos). */
export const LIMITS = {
  imageBytes: 8 * 1024 * 1024,
  videoBytes: 500 * 1024 * 1024,
  batchImages: 200,
} as const;

export interface SessionListParams {
  limit?: number;
  offset?: number;
  status?: SessionStatus;
}

export interface DetectionQuery {
  limit?: number;
  offset?: number;
  class_name?: ClassName;
  min_confidence?: number;
}

/**
 * Returns the array from a list payload. The contract says some list endpoints return "a list"
 * and others return `{key: [...]}`. Both are accepted so the UI does not depend on which one a
 * given backend version uses.
 */
export function unwrapList<T>(payload: unknown, keys: readonly string[]): T[] {
  if (Array.isArray(payload)) return payload as T[];
  if (payload && typeof payload === 'object') {
    for (const key of keys) {
      const value = (payload as Record<string, unknown>)[key];
      if (Array.isArray(value)) return value as T[];
    }
  }
  return [];
}

/** A browser URL for an export. Opening it (or using it as a link `href`) downloads the file. */
export function sessionExportUrl(id: string, format: ExportFormat, options: { download?: boolean } = {}): string {
  const base = `/api/v1/sessions/${encodeURIComponent(id)}`;
  const path = format === 'csv' ? `${base}/export.csv` : format === 'json' ? `${base}/export.json` : `${base}/report.html`;
  const query: QueryParams = format === 'report' && options.download ? { download: 1 } : {};
  return buildUrl(path, query);
}

export function createEndpoints(http: HttpClient) {
  const get = <T>(path: string, query?: QueryParams, timeoutMs?: number) =>
    http.request<T>(path, { query, timeoutMs });
  const post = <T>(path: string, json?: unknown, timeoutMs?: number) =>
    http.request<T>(path, { method: 'POST', json, timeoutMs });

  const legacy = {
    getStatus: () => get<StatusResponse>('/api/status', undefined, TIMEOUTS.quick),

    listModels: () => get<ModelsResponse>('/api/models', undefined, TIMEOUTS.default),

    initializeCamera: (config: CameraConfig) =>
      post<CameraInitializeResponse>('/api/camera/initialize', config, TIMEOUTS.stream),

    loadModel: (config: ModelConfig) => post<ModelLoadResponse>('/api/model/load', config, TIMEOUTS.stream),

    startStream: () => post<StreamResponse>('/api/stream/start', undefined, TIMEOUTS.stream),

    stopStream: () => post<StreamResponse>('/api/stream/stop', undefined, TIMEOUTS.stream),

    /** Raw image bytes with an image content type. The server returns 415 for anything else. */
    detectImage: (file: Blob, contentType: 'image/jpeg' | 'image/png', confidence: number, signal?: AbortSignal) =>
      http.request<DetectImageResponse>('/api/detect/image', {
        method: 'POST',
        query: { confidence },
        raw: { body: file, contentType },
        timeoutMs: TIMEOUTS.image,
        signal,
      }),

    getStatistics: (periodSeconds = 60) =>
      get<StatisticsResponse>('/api/statistics', { period: periodSeconds }, TIMEOUTS.default),

    getMetricsHistory: (limit = 100) =>
      get<MetricsHistoryResponse>('/api/metrics/history', { limit }, TIMEOUTS.default),

    getRecentDetections: (limit = 50) =>
      get<RecentDetectionsResponse>('/api/detections/recent', { limit }, TIMEOUTS.default),
  };

  const v1 = {
    // Sessions (CONTRACT 7, Sessions)
    listSessions: (params: SessionListParams = {}) =>
      get<SessionListResponse>(
        '/api/v1/sessions',
        { limit: params.limit, offset: params.offset, status: params.status },
        TIMEOUTS.default,
      ),

    createSession: (body: SessionCreateBody) => post<SessionDetail>('/api/v1/sessions', body, TIMEOUTS.default),

    getSession: (id: string) => get<SessionDetail>(`/api/v1/sessions/${encodeURIComponent(id)}`),

    patchSession: (id: string, body: SessionPatchBody) =>
      http.request<SessionDetail>(`/api/v1/sessions/${encodeURIComponent(id)}`, {
        method: 'PATCH',
        json: body,
        timeoutMs: TIMEOUTS.default,
      }),

    stopSession: (id: string) =>
      post<SessionDetail>(`/api/v1/sessions/${encodeURIComponent(id)}/stop`, undefined, TIMEOUTS.default),

    deleteSession: (id: string) =>
      http.request<void>(`/api/v1/sessions/${encodeURIComponent(id)}`, { method: 'DELETE', timeoutMs: TIMEOUTS.default }),

    getSessionDetections: (id: string, query: DetectionQuery = {}) =>
      get<SessionDetectionsResponse>(`/api/v1/sessions/${encodeURIComponent(id)}/detections`, { ...query }),

    getSessionTimeline: (id: string, bucketSeconds = 1) =>
      get<SessionTimelineResponse>(`/api/v1/sessions/${encodeURIComponent(id)}/timeline`, {
        bucket_seconds: bucketSeconds,
      }),

    // Compare (CONTRACT 7, Compare)
    runCompare: (form: FormData) =>
      http.request<CompareResponse>('/api/v1/compare', { method: 'POST', form, timeoutMs: TIMEOUTS.upload }),

    listComparisons: (limit = 20) =>
      get<ComparisonSummary[] | { comparisons: ComparisonSummary[] }>('/api/v1/compare', { limit }).then((payload) =>
        unwrapList<ComparisonSummary>(payload, ['comparisons', 'items']),
      ),

    getComparison: (id: string) => get<CompareResponse>(`/api/v1/compare/${encodeURIComponent(id)}`),

    deleteComparison: (id: string) =>
      http.request<void>(`/api/v1/compare/${encodeURIComponent(id)}`, { method: 'DELETE', timeoutMs: TIMEOUTS.default }),

    // Benchmark (CONTRACT 7, Benchmark)
    createBenchmarkRun: (body: BenchmarkRunCreateBody) =>
      post<BenchmarkRunAccepted>('/api/v1/benchmark/runs', body, TIMEOUTS.default),

    listBenchmarkRuns: (limit = 20) =>
      get<BenchmarkRun[] | { runs: BenchmarkRun[] }>('/api/v1/benchmark/runs', { limit }).then((payload) =>
        unwrapList<BenchmarkRun>(payload, ['runs', 'items']),
      ),

    getBenchmarkRun: (id: string) => get<BenchmarkRun>(`/api/v1/benchmark/runs/${encodeURIComponent(id)}`),

    deleteBenchmarkRun: (id: string) =>
      http.request<void>(`/api/v1/benchmark/runs/${encodeURIComponent(id)}`, {
        method: 'DELETE',
        timeoutMs: TIMEOUTS.default,
      }),

    // Batch and jobs (CONTRACT 7, Batch and jobs)
    uploadBatchVideo: (video: File, fields: BatchVideoFields) => {
      const form = new FormData();
      form.append('video', video);
      form.append('model_name', fields.model_name);
      if (fields.confidence !== undefined) form.append('confidence', String(fields.confidence));
      if (fields.frame_stride !== undefined) form.append('frame_stride', String(fields.frame_stride));
      if (fields.name) form.append('name', fields.name);
      return http.request<BatchAccepted>('/api/v1/batch/video', { method: 'POST', form, timeoutMs: TIMEOUTS.upload });
    },

    uploadBatchImages: (images: File[], fields: Omit<BatchVideoFields, 'frame_stride'>) => {
      const form = new FormData();
      for (const image of images) form.append('images', image);
      form.append('model_name', fields.model_name);
      if (fields.confidence !== undefined) form.append('confidence', String(fields.confidence));
      if (fields.name) form.append('name', fields.name);
      return http.request<BatchAccepted>('/api/v1/batch/images', { method: 'POST', form, timeoutMs: TIMEOUTS.upload });
    },

    startBatchFromDirectory: (body: BatchImagesJsonBody) =>
      post<BatchAccepted>('/api/v1/batch/images', body, TIMEOUTS.default),

    listJobs: (limit = 50) => get<JobListResponse>('/api/v1/jobs', { limit }),

    getJob: (id: string) => get<Job>(`/api/v1/jobs/${encodeURIComponent(id)}`),

    cancelJob: (id: string) => post<Job>(`/api/v1/jobs/${encodeURIComponent(id)}/cancel`),

    // Hardware (CONTRACT 7, Hardware)
    getHardwareCurrent: () => get<HardwareCurrent>('/api/v1/hardware/current'),

    getHardwareHistory: (minutes = 60, points = 240) =>
      get<HardwareHistoryResponse>('/api/v1/hardware/history', { minutes, points }),

    // Sorting arm (CONTRACT 7, Sorting arm): placeholder, no hardware
    getArmStatus: () => get<ArmStatus>('/api/v1/arm/status'),

    sendArmCommand: (body: ArmCommandBody) => post<ArmEvent>('/api/v1/arm/commands', body),

    listArmEvents: (limit = 100, kind?: string) =>
      get<ArmEventsResponse>('/api/v1/arm/events', { limit, kind }),

    setArmFeedback: (id: number, correct: boolean) =>
      post<ArmEvent>(`/api/v1/arm/events/${id}/feedback`, { correct }),

    getArmAccuracy: () => get<ArmAccuracy>('/api/v1/arm/accuracy'),
  };

  return { legacy, v1 };
}

export type Endpoints = ReturnType<typeof createEndpoints>;
