import { openWebSocket } from '../realtime/transport';
import { ReconnectingSocket, type LinkInfo, type LinkState } from '../realtime/reconnect';
import { clientFps, framesFresh, initialLiveState, parseVideoMessage, reduceLive, type LiveState } from '../realtime/video-state';

export const VIDEO_PATH = '/ws/video';
/** The server answers "ping" with "pong"; a steady ping keeps idle proxies from closing the socket. */
const HEARTBEAT_MS = 15_000;

/**
 * The live video socket. Started once by the app shell and kept open, so the status bar always
 * shows the connection state. Frames and metrics land in `state`.
 */
class LiveStore {
  state = $state.raw<LiveState>(initialLiveState());
  link = $state<LinkState>('closed');
  linkInfo = $state.raw<LinkInfo>({ attempt: 0, retryInMs: null });
  fps = $state(0);
  /** A frame arrived in the last few seconds. Updated twice a second. */
  fresh = $state(false);
  /** The last minute of client frame rates, sampled twice a second (for the trend line). */
  fpsHistory = $state.raw<number[]>([]);
  private socket: ReconnectingSocket | null = null;
  private fpsTimer: ReturnType<typeof setInterval> | null = null;

  start(): void {
    if (this.socket) return;
    this.socket = new ReconnectingSocket({
      path: VIDEO_PATH,
      open: openWebSocket,
      heartbeat: { text: 'ping', intervalMs: HEARTBEAT_MS },
      onMessage: (text) => this.handle(text),
      onState: (link, info) => {
        this.link = link;
        this.linkInfo = info;
      },
    });
    this.socket.start();
    this.fpsTimer = setInterval(() => {
      const now = Date.now();
      this.fps = clientFps(this.state.frameTimes, now);
      this.fresh = framesFresh(this.state.lastFrameAt, now);
      this.fpsHistory = [...this.fpsHistory, this.fps].slice(-120);
    }, 500);
  }

  stop(): void {
    this.socket?.stop();
    this.socket = null;
    if (this.fpsTimer !== null) clearInterval(this.fpsTimer);
    this.fpsTimer = null;
  }

  /** The "Reconnect now" button. */
  retry(): void {
    this.socket?.retryNow();
  }

  /** Frames are older than `ms` (or none has arrived). Used for the "no frames" hint. */
  framesStale(ms: number, now = Date.now()): boolean {
    return this.state.lastFrameAt === null || now - this.state.lastFrameAt > ms;
  }

  private handle(text: string): void {
    const message = parseVideoMessage(text);
    if (!message || message === 'pong') return;
    this.state = reduceLive(this.state, message, Date.now());
  }
}

export const live = new LiveStore();
