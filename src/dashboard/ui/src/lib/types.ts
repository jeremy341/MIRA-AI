/*
  Wire types. Legacy routes (`/api/*`, `/ws/video`) match src/dashboard/backend/main.py and
  websocket_handler.py. v1 types (`/api/v1`, `/ws/v1/events`) match docs/dashboard-v2/CONTRACT.md section 7
  and the routers in src/dashboard/backend/v1/routers/ (checked against them in U2).
  JSON is snake_case. Timestamps in payloads are ISO-8601 strings.
  Where the contract or the routers leave a shape open, the type is marked `OPEN:` and listed in the UI README.
*/

export const CLASS_NAMES = ['glass', 'metal', 'paper', 'plastic', 'trash'] as const;
export type ClassName = (typeof CLASS_NAMES)[number];

/** Pixel box in the coordinate space of the image or frame: [x1, y1, x2, y2]. */
export type Bbox = [number, number, number, number];

export type IsoTimestamp = string;

/** Per-class counts as the legacy statistics payload returns them (only classes seen). */
export type PartialClassCounts = Partial<Record<ClassName, number>>;
/** Per-class counts as the v1 payloads return them (always all five keys). */
export type ClassCounts = Record<ClassName, number>;

// ---------------------------------------------------------------------------
// Legacy HTTP
// ---------------------------------------------------------------------------

/** `SystemStatus` in backend/models.py. */
export type ServerStatus = 'idle' | 'initializing' | 'running' | 'paused' | 'error';

/** GET /api/status */
export interface StatusResponse {
  status: ServerStatus;
  message: string;
  camera_initialized: boolean;
  model_loaded: boolean;
  streaming: boolean;
  timestamp: IsoTimestamp;
}

/** One entry of GET /api/models. `path` is a server-side path and is never shown. */
export interface ModelInfo {
  name: string;
  label: string;
  path: string;
  model_type: 'yolo_pt' | 'yolo_tflite';
  size_mb: number;
  is_tflite_int8: boolean;
  input_size: number;
  recommended: boolean;
}

export interface ModelsResponse {
  models: ModelInfo[];
  count: number;
  timestamp: IsoTimestamp;
}

/** Body of POST /api/camera/initialize (CameraConfig in backend/models.py). */
export interface CameraConfig {
  index: number;
  width: number;
  height: number;
  fps: number;
  autofocus: boolean;
  auto_exposure: boolean;
}

/** Body of POST /api/model/load (ModelConfig in backend/models.py). */
export interface ModelConfig {
  name: string;
  conf_threshold: number;
  reject_threshold: number;
  iou_threshold: number;
  enable_tracking: boolean;
  target_latency_ms: number;
}

export interface CameraInitializeResponse {
  success: true;
  message: string;
  config: CameraConfig;
}

export interface ModelLoadResponse {
  success: true;
  message: string;
  config: ModelConfig;
}

/** POST /api/stream/start and POST /api/stream/stop */
export interface StreamResponse {
  success: true;
  status: ServerStatus;
  message: string;
  timestamp: IsoTimestamp;
}

/** `detail` of the 409 from POST /api/stream/start when the camera or the model is missing. */
export interface StreamMissingDetail {
  message: string;
  missing: Array<'camera' | 'model'>;
}

/** A detection as the REST payloads return it (`Detection` in backend/models.py). */
export interface Detection {
  class_name: ClassName;
  confidence: number;
  bbox: Bbox;
  track_id: number | null;
  timestamp: IsoTimestamp;
}

/** POST /api/detect/image. `image` is a data URI of the resized original, without boxes. */
export interface DetectImageResponse {
  image: string;
  detections: Detection[];
}

export interface StatisticsSnapshot {
  period_start: IsoTimestamp;
  period_end: IsoTimestamp;
  total_detections: number;
  class_counts: PartialClassCounts;
  avg_confidence: PartialClassCounts;
  sorting_accuracy: number | null;
  average_confidence: number | null;
}

/** GET /api/statistics?period=60 */
export interface StatisticsResponse {
  statistics: StatisticsSnapshot;
  period_seconds: number;
}

/** One sample of the system metrics (`SystemMetrics` in backend/models.py). */
export interface SystemMetrics {
  timestamp: IsoTimestamp;
  fps: number;
  inference_latency_ms: number;
  avg_latency_ms: number;
  cpu_percent: number;
  memory_percent: number;
  temperature_celsius: number | null;
  detections_per_second: number;
  skip_frames: boolean;
}

/** GET /api/metrics/history?limit=100 */
export interface MetricsHistoryResponse {
  metrics: SystemMetrics[];
  count: number;
  timestamp: IsoTimestamp;
}

/** GET /api/detections/recent?limit=50 */
export interface RecentDetectionsResponse {
  detections: Detection[];
  count: number;
  timestamp: IsoTimestamp;
}

// ---------------------------------------------------------------------------
// Legacy WebSocket: /ws/video (websocket_handler.py)
// ---------------------------------------------------------------------------

/** Detection inside a video frame. The key is `class`, not `class_name`. */
export interface WsDetection {
  class: ClassName;
  confidence: number;
  bbox: Bbox;
  track_id: number | null;
  timestamp: IsoTimestamp;
}

export interface WsStatusMessage {
  type: 'status';
  status: ServerStatus | 'connected';
  message: string;
  timestamp?: IsoTimestamp;
}

export interface WsFrameMessage {
  type: 'frame';
  frame_id: number;
  /** Base64 JPEG, without a `data:` prefix. */
  frame: string;
  detections: WsDetection[];
  timestamp: IsoTimestamp;
}

export interface WsMetricsMessage {
  type: 'metrics';
  fps: number;
  inference_latency_ms: number;
  avg_latency_ms: number;
  cpu_percent: number;
  memory_percent: number;
  temperature_celsius: number | null;
  detections_per_second: number;
  skip_frames: boolean;
  timestamp: IsoTimestamp;
}

/** The client sends the text "ping" and the server answers with the text "pong". */
export type VideoSocketMessage = WsStatusMessage | WsFrameMessage | WsMetricsMessage;

// ---------------------------------------------------------------------------
// v1 HTTP (CONTRACT section 7)
// ---------------------------------------------------------------------------

export type SessionSource = 'camera' | 'image' | 'video' | 'batch';
export type SessionStatus = 'active' | 'completed' | 'failed';

/** One item of GET /api/v1/sessions. */
export interface SessionSummary {
  id: string;
  name: string;
  source: SessionSource;
  model_name: string | null;
  status: SessionStatus;
  started_at: IsoTimestamp;
  ended_at: IsoTimestamp | null;
  duration_seconds: number;
  total_detections: number;
  class_counts: ClassCounts;
  avg_confidence: number | null;
}

/**
 * GET /api/v1/sessions/{id} adds `config` and `notes`.
 * OPEN: the contract says POST /sessions returns "session" without listing its fields. It is typed as this
 * detail shape. The sessions router is still a stub on this branch, so this is unconfirmed.
 */
export interface SessionDetail extends SessionSummary {
  config: Record<string, unknown> | null;
  notes: string | null;
}

export interface SessionListResponse {
  sessions: SessionSummary[];
  total: number;
}

export interface SessionCreateBody {
  name?: string;
  source: SessionSource;
  model_name?: string;
}

export interface SessionPatchBody {
  name?: string;
  notes?: string;
}

export interface SessionDetection {
  ts: IsoTimestamp;
  offset_seconds: number;
  frame_index: number;
  class_name: ClassName;
  confidence: number;
  bbox: Bbox;
  track_id: number | null;
}

export interface SessionDetectionsResponse {
  detections: SessionDetection[];
  total: number;
}

export interface TimelineBucket {
  start_offset: number;
  objects: number;
  class_counts: ClassCounts;
  avg_confidence: number | null;
  fps: number | null;
  latency_ms: number | null;
}

export interface SessionTimelineResponse {
  duration_seconds: number;
  bucket_seconds: number;
  buckets: TimelineBucket[];
}

/** One detection inside a compare result. Compare detections carry no timestamp (compare router). */
export interface CompareDetection {
  class_name: ClassName;
  confidence: number;
  bbox: Bbox;
  track_id: number | null;
}

/** A model's result as it is stored and listed: the annotated image is never stored. */
export interface CompareModelRecord {
  name: string;
  latency_ms: number;
  objects: number;
  class_counts: ClassCounts;
  avg_confidence: number | null;
  detections: CompareDetection[];
}

/** The `winner_hint` of a compare run (compare.py `_winner_hint`). These are observations, not accuracy. */
export interface CompareWinnerHint {
  fastest_model: string;
  most_objects_model: string;
  highest_avg_confidence_model: string | null;
  note: string;
}

/** POST /api/v1/compare. Only the run that just happened carries `annotated_image`. */
export interface CompareModelResult extends CompareModelRecord {
  /** Data URI of the annotated JPEG. */
  annotated_image: string;
}

export interface CompareResponse {
  id: string;
  input_name: string;
  models: CompareModelResult[];
  winner_hint: CompareWinnerHint;
}

/** GET /api/v1/compare/{id} and each item of the list. The router stores no images, so there is no `annotated_image`. */
export interface CompareRecord {
  id: string;
  created_at: IsoTimestamp;
  input_name: string;
  models: CompareModelRecord[];
  winner_hint: CompareWinnerHint;
}

/** GET /api/v1/compare?limit=20 */
export interface CompareListResponse {
  comparisons: CompareRecord[];
  total: number;
}

export type JobStatus = 'queued' | 'running' | 'completed' | 'failed' | 'cancelled';

/** Benchmark run status. The router reuses the job statuses. */
export type BenchmarkStatus = JobStatus;

/** Per-class counts from `PerClassMetrics.to_dict()` (src/pipeline/benchmark.py). Keys are dataset class names. */
export interface BenchmarkClassMetrics {
  tp: number;
  fp: number;
  fn: number;
  precision: number;
  recall: number;
  f1: number;
}

/** One model's row in a benchmark run (`_result_to_api` in benchmark.py). */
export interface BenchmarkModelResult {
  model: string;
  map50: number;
  map50_95: number;
  precision: number;
  recall: number;
  f1: number;
  avg_latency_ms: number;
  /** Always null on this backend: the benchmark does not measure FPS. Show a dash. */
  fps: number | null;
  per_class: Record<string, BenchmarkClassMetrics>;
  /** Messages for models or images that could not be evaluated. An empty list means no errors. */
  errors: string[];
}

/** The `config` a run was started with, as stored by benchmark.py (`dataset` is the resolved path). */
export interface BenchmarkConfig {
  models: string[];
  dataset: string;
  confidence: number;
  max_images: number | null;
}

/** GET /api/v1/benchmark/runs/{id} and each item of the list. `results` fills in as each model finishes. */
export interface BenchmarkRun {
  id: string;
  created_at: IsoTimestamp;
  status: BenchmarkStatus;
  config: BenchmarkConfig;
  results: BenchmarkModelResult[] | null;
  job_id: string | null;
}

/** GET /api/v1/benchmark/runs?limit=20 */
export interface BenchmarkRunListResponse {
  runs: BenchmarkRun[];
  total: number;
}

export interface BenchmarkRunCreateBody {
  models: string[];
  dataset?: string;
  confidence: number;
  max_images?: number;
}

export interface BenchmarkRunAccepted {
  run_id: string;
  job_id: string;
}

export interface BatchAccepted {
  job_id: string;
  session_id: string;
}

export interface BatchVideoFields {
  model_name: string;
  confidence?: number;
  frame_stride?: number;
  name?: string;
}

export interface BatchImagesJsonBody {
  directory: string;
  recursive: false;
  model_name: string;
  confidence?: number;
  name?: string;
}

export interface Job {
  id: string;
  kind: string;
  title: string;
  status: JobStatus;
  /** 0.0 to 1.0. */
  progress: number;
  message: string;
  created_at: IsoTimestamp;
  finished_at: IsoTimestamp | null;
  /** OPEN: batch jobs return their own shape (not specified). Benchmark jobs return `{run_id, results}`. */
  result: Record<string, unknown> | null;
  error: string | null;
}

export interface JobListResponse {
  jobs: Job[];
}

export interface HardwareCurrent {
  ts: IsoTimestamp;
  cpu_percent: number;
  memory_percent: number;
  memory_used_mb: number;
  memory_total_mb: number;
  temperature_c: number | null;
  load_1m: number | null;
  platform: string;
  is_raspberry_pi: boolean;
  cpu_count: number;
}

/** One bucket of GET /api/v1/hardware/history. Values are averages; `temperature_c` is null without a sensor. */
export interface HardwarePoint {
  ts: IsoTimestamp;
  cpu_percent: number | null;
  memory_percent: number | null;
  temperature_c: number | null;
}

export interface HardwareHistoryResponse {
  points: HardwarePoint[];
  minutes: number;
}

export type ArmState = 'idle' | 'busy';
export type ArmCommandAction = 'sort' | 'home' | 'stop';

/** GET /api/v1/arm/status */
export interface ArmStatus {
  connected: boolean;
  mode: string;
  state: ArmState;
  queue_length: number;
  last_event_at: IsoTimestamp | null;
  accuracy: number | null;
  total_feedback: number;
}

export interface ArmCommandBody {
  action: ArmCommandAction;
  class_name?: ClassName;
  track_id?: number;
}

/** Event kinds the simulator writes: `<action>_requested`, then `<action>_completed` or `<action>_failed`. */
export type ArmEventKind =
  | 'sort_requested'
  | 'sort_completed'
  | 'sort_failed'
  | 'home_requested'
  | 'home_completed'
  | 'home_failed'
  | 'stop_requested'
  | 'stop_completed'
  | 'stop_failed';

/**
 * The `payload` of an arm event (arm.py). `*_requested` carries `action`. `*_completed` and `*_failed`
 * carry `request_id` (the id of the requested event) and `message`.
 */
export interface ArmEventPayload {
  action?: ArmCommandAction;
  request_id?: number;
  message?: string;
}

/** An arm event as the router serialises it (`_serialize_event`). `correct` is only set on `sort_completed` events. */
export interface ArmEvent {
  id: number;
  ts: IsoTimestamp;
  kind: ArmEventKind;
  class_name: ClassName | null;
  track_id: number | null;
  payload: ArmEventPayload;
  correct: boolean | null;
}

export interface ArmEventsResponse {
  events: ArmEvent[];
}

export interface ArmAccuracy {
  accuracy: number | null;
  correct: number;
  total: number;
}

// ---------------------------------------------------------------------------
// v1 WebSocket: /ws/v1/events
// ---------------------------------------------------------------------------

export type EventType =
  | 'session_started'
  | 'session_stopped'
  | 'job_progress'
  | 'job_finished'
  | 'arm_event'
  | 'hardware_sample'
  | 'detection_batch';

export interface HelloEvent {
  type: 'hello';
  ts: IsoTimestamp;
  data: { version: number };
}

export interface PingEvent {
  type: 'ping';
}

/** `data` of `job_progress` (jobs.py). The job is keyed by `job_id`, not `id`. */
export interface JobProgressEventData {
  job_id: string;
  progress: number;
  message: string;
}

/** `data` of `job_finished`. */
export interface JobFinishedEventData {
  job_id: string;
  status: JobStatus;
  error: string | null;
}

/** `data` of `session_started` (batch_runner.py). */
export interface SessionStartedEventData {
  session_id: string;
  source: SessionSource;
  name: string;
}

/** `data` of `session_stopped`. */
export interface SessionStoppedEventData {
  session_id: string;
  status: SessionStatus;
}

/**
 * `data` of `hardware_sample` (hardware_sampler.py). OPEN: `ts` here is a raw epoch number from the sampler,
 * not an ISO string like the envelope and the HTTP payloads. The UI does not use this event for charts.
 */
export interface HardwareSampleEventData {
  ts: number;
  cpu_percent: number;
  memory_percent: number;
  temperature_c: number | null;
}

/** Every EventBus event, fanned out as `{type, ts, data}`. Callers narrow `data` per event type. */
export interface BusEvent<T = Record<string, unknown>> {
  type: EventType;
  ts: IsoTimestamp;
  data: T;
}

export type EventsSocketMessage = HelloEvent | PingEvent | BusEvent;
