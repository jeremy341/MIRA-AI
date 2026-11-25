/*
  Wire types. Legacy routes (`/api/*`, `/ws/video`) match src/dashboard/backend/main.py and
  websocket_handler.py. v1 types (`/api/v1`, `/ws/v1/events`) match docs/dashboard-v2/CONTRACT.md section 7.
  JSON is snake_case. Timestamps in payloads are ISO-8601 strings.
  Where the contract leaves a shape open, the type is marked `OPEN:` and listed in the UI README.
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

/** GET /api/v1/sessions/{id} adds `config` and `notes`. OPEN: POST returns this shape too (assumed). */
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

/** OPEN: the detection shape inside compare results is assumed to match `Detection`. */
export interface CompareModelResult {
  name: string;
  latency_ms: number;
  objects: number;
  class_counts: ClassCounts;
  avg_confidence: number | null;
  detections: Detection[];
  /** Data URI of the annotated JPEG. */
  annotated_image: string;
}

/** OPEN: `winner_hint` is not specified in the contract. */
export interface CompareResponse {
  id: string;
  input_name: string;
  models: CompareModelResult[];
  winner_hint: Record<string, unknown>;
}

/** OPEN: list item shape for GET /api/v1/compare (no images). */
export interface ComparisonSummary {
  id: string;
  created_at: IsoTimestamp;
  input_name: string;
  models: string[];
}

export type JobStatus = 'queued' | 'running' | 'completed' | 'failed' | 'cancelled';

/** OPEN: `per_class` and `errors` shapes are not specified, so they are typed loosely. */
export interface BenchmarkModelResult {
  model: string;
  map50: number | null;
  map50_95: number | null;
  precision: number | null;
  recall: number | null;
  f1: number | null;
  avg_latency_ms: number | null;
  fps: number | null;
  per_class: Record<string, unknown>;
  errors: string[] | null;
}

/** GET /api/v1/benchmark/runs/{id}. OPEN: list items are assumed to share this shape. */
export interface BenchmarkRun {
  id: string;
  /** OPEN: benchmark status values are assumed to match the job statuses. */
  status: JobStatus;
  config: Record<string, unknown>;
  results: BenchmarkModelResult[] | null;
  job_id: string | null;
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

export interface HardwarePoint {
  ts: IsoTimestamp;
  cpu_percent: number;
  memory_percent: number;
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

/** OPEN: the JSON shape of an arm event is not specified. `payload` is the parsed payload_json. */
export interface ArmEvent {
  id: number;
  ts: IsoTimestamp;
  kind: string;
  class_name: ClassName | null;
  track_id: number | null;
  payload: Record<string, unknown>;
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

/** Every EventBus event, fanned out as `{type, ts, data}`. Callers narrow `data` per event type. */
export interface BusEvent<T = Record<string, unknown>> {
  type: EventType;
  ts: IsoTimestamp;
  data: T;
}

export type EventsSocketMessage = HelloEvent | PingEvent | BusEvent;
