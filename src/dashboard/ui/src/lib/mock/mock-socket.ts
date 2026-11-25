/**
 * Fake WebSockets for mock mode. They follow the server protocol:
 *  - /ws/video: a "connected" status on open, "pong" for "ping", and while the mock stream runs,
 *    a frame about 4 times a second (random boxes over a generated frame) and metrics each second.
 *  - /ws/v1/events: a hello on open, a ping every 20 s, and a hardware sample every 5 s.
 * Only what the UI needs is implemented.
 */
import { randomDetections, state, tickMock } from './backend';
import { scenePool } from './scene';
import { rng } from './fixtures';
import { subscribeMockEvents } from './mock-events';

const FRAME_INTERVAL_MS = 250;
const METRICS_INTERVAL_MS = 1000;
const CLOCK_INTERVAL_MS = 1000;
const HARDWARE_INTERVAL_MS = 5000;
const EVENTS_PING_MS = 20000;

/** Minimal WebSocket look-alike. Cast to WebSocket by openMockSocket. */
class MockSocket {
  readyState = 0;
  onopen: ((event: Event) => void) | null = null;
  onmessage: ((event: MessageEvent) => void) | null = null;
  onclose: ((event: CloseEvent) => void) | null = null;
  onerror: ((event: Event) => void) | null = null;

  private timers: Array<ReturnType<typeof setInterval> | ReturnType<typeof setTimeout>> = [];
  private frameIndex = 0;
  private wasStreaming = false;
  private readonly random = rng(Date.now() & 0xffff);
  private unsubscribe: (() => void) | null = null;

  constructor(private readonly kind: 'video' | 'events') {
    this.timers.push(
      setTimeout(() => {
        if (this.readyState !== 0) return;
        this.readyState = 1;
        this.onopen?.(new Event('open'));
        if (kind === 'video') {
          this.emit({ type: 'status', status: 'connected', message: 'Video stream connected' });
          this.timers.push(setInterval(() => void this.tickVideo(), FRAME_INTERVAL_MS));
          this.timers.push(setInterval(() => this.tickMetrics(), METRICS_INTERVAL_MS));
        } else {
          this.emit({ type: 'hello', ts: new Date().toISOString(), data: { version: 1 } });
          // Job, arm and session events come from the mock backend, as the EventBus sends them.
          this.unsubscribe = subscribeMockEvents((type, data) => this.emit({ type, ts: new Date().toISOString(), data }));
          this.timers.push(setInterval(() => tickMock(), CLOCK_INTERVAL_MS));
          this.timers.push(setInterval(() => this.emit({ type: 'ping' }), EVENTS_PING_MS));
          this.timers.push(setInterval(() => this.tickHardware(), HARDWARE_INTERVAL_MS));
        }
      }, 60),
    );
  }

  send(data: string): void {
    if (this.readyState !== 1) throw new DOMException('The socket is not open.', 'InvalidStateError');
    if (this.kind === 'video' && data === 'ping') {
      this.deliver('pong');
    }
  }

  close(code = 1000, reason = ''): void {
    if (this.readyState === 3) return;
    this.readyState = 3;
    for (const timer of this.timers) {
      clearTimeout(timer);
      clearInterval(timer);
    }
    this.timers = [];
    this.unsubscribe?.();
    this.unsubscribe = null;
    this.onclose?.({ code, reason, wasClean: code === 1000 } as CloseEvent);
  }

  /** Used by the dev hook to simulate a dropped connection. */
  drop(): void {
    this.close(1006, 'mock drop');
  }

  private emit(message: object): void {
    this.deliver(JSON.stringify(message));
  }

  private deliver(text: string): void {
    if (this.readyState !== 1) return;
    this.onmessage?.({ data: text } as MessageEvent);
  }

  private async tickVideo(): Promise<void> {
    if (this.readyState !== 1) return;
    if (!state.streaming) {
      this.wasStreaming = false;
      return;
    }
    if (!this.wasStreaming) {
      this.wasStreaming = true;
      this.emit({ type: 'status', status: 'running', message: 'Streaming started' });
    }
    const pool = await scenePool();
    if (this.readyState !== 1 || pool.length === 0) return;
    const frame = pool[this.frameIndex % pool.length];
    this.frameIndex += 1;
    const detections = randomDetections(640, 360, Math.floor(this.random() * 4), this.random).map((d) => ({
      class: d.class_name,
      confidence: d.confidence,
      bbox: d.bbox,
      track_id: d.track_id,
      timestamp: d.timestamp,
    }));
    this.emit({
      type: 'frame',
      frame_id: this.frameIndex,
      frame,
      detections,
      timestamp: new Date().toISOString(),
    });
  }

  private tickMetrics(): void {
    if (this.readyState !== 1 || !state.streaming) return;
    const fps = Math.round((24 + this.random() * 6) * 10) / 10;
    this.emit({
      type: 'metrics',
      fps,
      inference_latency_ms: Math.round((38 + this.random() * 14) * 10) / 10,
      avg_latency_ms: 44.2,
      cpu_percent: Math.round((30 + this.random() * 25) * 10) / 10,
      memory_percent: Math.round((42 + this.random() * 4) * 10) / 10,
      temperature_celsius: Math.round((52 + this.random() * 6) * 10) / 10,
      detections_per_second: Math.round(this.random() * 40) / 10,
      skip_frames: false,
      timestamp: new Date().toISOString(),
    });
  }

  private tickHardware(): void {
    // The sampler's event carries its own epoch `ts` in seconds (hardware_sampler.py).
    this.emit({
      type: 'hardware_sample',
      ts: new Date().toISOString(),
      data: {
        ts: Date.now() / 1000,
        cpu_percent: Math.round((30 + this.random() * 25) * 10) / 10,
        memory_percent: Math.round((42 + this.random() * 4) * 10) / 10,
        temperature_c: state.hardwareSensor ? Math.round((52 + this.random() * 6) * 10) / 10 : null,
      },
    });
  }
}

const openSockets = new Set<MockSocket>();

export function openMockSocket(path: string): WebSocket {
  const kind = path.startsWith('/ws/v1/events') ? 'events' : 'video';
  const socket = new MockSocket(kind);
  openSockets.add(socket);
  const remove = socket.close.bind(socket);
  socket.close = (code?: number, reason?: string) => {
    openSockets.delete(socket);
    remove(code, reason);
  };
  registerDevHooks();
  return socket as unknown as WebSocket;
}

/**
 * Developer aid, mock mode only, in the browser console:
 *  - `__miraMock.dropSockets()` closes every open mock socket with code 1006, to check the reconnect states.
 *  - `__miraMock.hardwareSensor(false)` removes the temperature reading (a board without a sensor).
 */
function registerDevHooks(): void {
  if (typeof window === 'undefined') return;
  (window as unknown as { __miraMock?: unknown }).__miraMock = {
    dropSockets: () => {
      for (const socket of [...openSockets]) socket.drop();
    },
    openSockets: () => openSockets.size,
    hardwareSensor: (on: boolean) => {
      state.hardwareSensor = on;
    },
  };
}
