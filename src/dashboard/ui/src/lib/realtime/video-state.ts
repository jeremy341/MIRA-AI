/**
 * State for the live video socket (`/ws/video`). Pure reducers: no DOM, no timers.
 * The live store wraps these. Covered by video-state.test.ts.
 */
import { isClassName } from '../classes';
import type { Bbox, ClassName, ServerStatus, VideoSocketMessage } from '../types';

/** A base64 JPEG longer than this is skipped (about 6 MB of JPEG). Protects the page from huge frames. */
export const MAX_FRAME_CHARS = 8_000_000;

/** Frame timestamps kept for the client-side frame rate. */
const FRAME_WINDOW = 30;

export interface LiveDetection {
  className: ClassName;
  confidence: number;
  bbox: Bbox;
  trackId: number | null;
}

export interface LiveMetrics {
  fps: number;
  latencyMs: number;
  avgLatencyMs: number;
  cpuPercent: number;
  memoryPercent: number;
  temperatureC: number | null;
  detectionsPerSecond: number;
  skipFrames: boolean;
  receivedAt: number;
}

export interface LiveFrame {
  /** A `data:image/jpeg;base64,...` URI, ready for an <img> or a canvas. */
  src: string;
  frameId: number;
  receivedAt: number;
  detections: LiveDetection[];
  /** Length of the base64 payload, for the "too large" notice and for debugging. */
  chars: number;
}

export interface LiveState {
  frame: LiveFrame | null;
  metrics: LiveMetrics | null;
  serverStatus: ServerStatus | 'connected' | null;
  serverMessage: string | null;
  /** A short note for the person, such as "A frame was too large to show". */
  notice: string | null;
  /** Receive times of the last frames, for `clientFps`. */
  frameTimes: number[];
  framesReceived: number;
  lastFrameAt: number | null;
}

export function initialLiveState(): LiveState {
  return {
    frame: null,
    metrics: null,
    serverStatus: null,
    serverMessage: null,
    notice: null,
    frameTimes: [],
    framesReceived: 0,
    lastFrameAt: null,
  };
}

export function frameSrc(base64: string): string {
  return base64.startsWith('data:') ? base64 : `data:image/jpeg;base64,${base64}`;
}

/** Parses one text message from the video socket. Returns null for anything it does not recognise. */
export function parseVideoMessage(text: string): VideoSocketMessage | 'pong' | null {
  if (text === 'pong') return 'pong';
  let value: unknown;
  try {
    value = JSON.parse(text);
  } catch {
    return null;
  }
  if (!value || typeof value !== 'object') return null;
  const type = (value as { type?: unknown }).type;
  if (type === 'frame' || type === 'metrics' || type === 'status') {
    return value as VideoSocketMessage;
  }
  return null;
}

/** Keeps only well-formed detections. The live payload uses `class`, the REST payloads use `class_name`. */
export function normalizeDetections(list: unknown): LiveDetection[] {
  if (!Array.isArray(list)) return [];
  const result: LiveDetection[] = [];
  for (const item of list) {
    if (!item || typeof item !== 'object') continue;
    const record = item as Record<string, unknown>;
    const className = record.class ?? record.class_name;
    const bbox = record.bbox;
    const confidence = record.confidence;
    if (!isClassName(className)) continue;
    if (!Array.isArray(bbox) || bbox.length !== 4 || !bbox.every((n) => typeof n === 'number' && Number.isFinite(n))) {
      continue;
    }
    if (typeof confidence !== 'number' || !Number.isFinite(confidence)) continue;
    result.push({
      className,
      confidence,
      bbox: [bbox[0], bbox[1], bbox[2], bbox[3]],
      trackId: typeof record.track_id === 'number' ? record.track_id : null,
    });
  }
  return result;
}

export function reduceLive(state: LiveState, message: VideoSocketMessage, now: number): LiveState {
  switch (message.type) {
    case 'status':
      return { ...state, serverStatus: message.status, serverMessage: message.message };

    case 'metrics':
      return {
        ...state,
        metrics: {
          fps: message.fps,
          latencyMs: message.inference_latency_ms,
          avgLatencyMs: message.avg_latency_ms,
          cpuPercent: message.cpu_percent,
          memoryPercent: message.memory_percent,
          temperatureC: message.temperature_celsius,
          detectionsPerSecond: message.detections_per_second,
          skipFrames: message.skip_frames,
          receivedAt: now,
        },
      };

    case 'frame': {
      const chars = typeof message.frame === 'string' ? message.frame.length : 0;
      const frameTimes = [...state.frameTimes, now].slice(-FRAME_WINDOW);
      const base = {
        ...state,
        frameTimes,
        framesReceived: state.framesReceived + 1,
        lastFrameAt: now,
      };
      if (chars === 0) {
        return { ...base, frame: null, notice: 'A frame arrived empty and was skipped.' };
      }
      if (chars > MAX_FRAME_CHARS) {
        const megabytes = (chars * 0.75) / (1024 * 1024);
        return {
          ...base,
          frame: null,
          notice: `A frame was too large to show (about ${megabytes.toFixed(1)} MB) and was skipped.`,
        };
      }
      return {
        ...base,
        notice: null,
        frame: {
          src: frameSrc(message.frame),
          frameId: message.frame_id,
          receivedAt: now,
          detections: normalizeDetections(message.detections),
          chars,
        },
      };
    }
  }
}

/** Frames per second over the last `windowMs`, from the receive times in `frameTimes`. */
/** A wide window: a Raspberry Pi stream can run at well under 1 frame per second. */
export const FPS_WINDOW_MS = 3000;
/** A frame this recent means the stream is live. Slow streams still count as live. */
export const FRESH_FRAME_MS = 5000;

/** Frames per second over the last `windowMs`, from the receive times in `frameTimes`. */
export function clientFps(frameTimes: readonly number[], now: number, windowMs = FPS_WINDOW_MS): number {
  const recent = frameTimes.filter((t) => now - t <= windowMs && t <= now);
  if (recent.length < 2) return 0;
  const span = (recent[recent.length - 1] - recent[0]) / 1000;
  if (span <= 0) return 0;
  return (recent.length - 1) / span;
}

/** True when a frame arrived within `maxAgeMs`. Independent of the frame rate. */
export function framesFresh(lastFrameAt: number | null, now: number, maxAgeMs = FRESH_FRAME_MS): boolean {
  return lastFrameAt !== null && now - lastFrameAt <= maxAgeMs;
}
