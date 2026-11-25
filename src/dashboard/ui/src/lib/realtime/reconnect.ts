/**
 * A WebSocket that reconnects with capped, jittered exponential backoff.
 * No DOM globals are used here, so the tests can drive it with fake sockets.
 */

/** The part of WebSocket this module uses. A real WebSocket satisfies it. */
export type SocketHandle = Pick<WebSocket, 'readyState' | 'send' | 'close' | 'onopen' | 'onmessage' | 'onclose' | 'onerror'>;

export type LinkState = 'closed' | 'connecting' | 'open' | 'reconnecting' | 'unavailable';

export interface LinkInfo {
  /** Failed attempts since the last successful open. */
  attempt: number;
  /** Milliseconds until the next attempt while reconnecting, otherwise null. */
  retryInMs: number | null;
}

export interface ReconnectingSocketOptions {
  path: string;
  open: (path: string) => Promise<SocketHandle>;
  onMessage: (text: string) => void;
  onState?: (state: LinkState, info: LinkInfo) => void;
  /** Sent as text on this interval while open (the video socket expects "ping"). */
  heartbeat?: { text: string; intervalMs: number };
  baseDelayMs?: number;
  maxDelayMs?: number;
  /** After this many failed attempts the link is 'unavailable' and retries stop. */
  maxAttempts?: number;
  random?: () => number;
}

const OPEN = 1;

/**
 * Delay before retry number `attempt` (0 for the first retry). Doubles from `base` up to `max`,
 * with a jitter of plus or minus 20% so that many clients do not retry in lockstep.
 */
export function backoffDelay(attempt: number, base: number, max: number, random: () => number = Math.random): number {
  const exponential = Math.min(max, base * 2 ** Math.min(Math.max(attempt, 0), 20));
  const jitter = 0.8 + random() * 0.4;
  return Math.min(max, Math.round(exponential * jitter));
}

export class ReconnectingSocket {
  private readonly options: ReconnectingSocketOptions;
  private socket: SocketHandle | null = null;
  private retryTimer: ReturnType<typeof setTimeout> | null = null;
  private heartbeatTimer: ReturnType<typeof setInterval> | null = null;
  private failures = 0;
  private stopped = true;
  private currentState: LinkState = 'closed';
  private currentInfo: LinkInfo = { attempt: 0, retryInMs: null };

  constructor(options: ReconnectingSocketOptions) {
    this.options = options;
  }

  get state(): LinkState {
    return this.currentState;
  }

  get info(): LinkInfo {
    return this.currentInfo;
  }

  start(): void {
    if (!this.stopped) return;
    this.stopped = false;
    this.failures = 0;
    void this.connect();
  }

  stop(): void {
    this.stopped = true;
    this.clearTimers();
    const socket = this.socket;
    this.socket = null;
    if (socket) {
      socket.onclose = null;
      socket.onopen = null;
      socket.onmessage = null;
      socket.onerror = null;
      try {
        socket.close();
      } catch {
        // Closing an already closed socket can throw in some browsers. Nothing to do.
      }
    }
    this.setState('closed', { attempt: 0, retryInMs: null });
  }

  /** Retry now, skipping the backoff. Used by a "Reconnect" button. */
  retryNow(): void {
    if (this.stopped) {
      this.start();
      return;
    }
    if (this.socket?.readyState === OPEN) return;
    this.clearTimers();
    this.failures = 0;
    void this.connect();
  }

  send(text: string): boolean {
    if (!this.socket || this.socket.readyState !== OPEN) return false;
    try {
      this.socket.send(text);
      return true;
    } catch {
      return false;
    }
  }

  private async connect(): Promise<void> {
    if (this.stopped) return;
    this.setState(this.failures === 0 && this.currentState !== 'reconnecting' ? 'connecting' : 'reconnecting', {
      attempt: this.failures,
      retryInMs: null,
    });

    let socket: SocketHandle;
    try {
      socket = await this.options.open(this.options.path);
    } catch {
      this.scheduleRetry();
      return;
    }
    if (this.stopped) {
      socket.close();
      return;
    }

    this.socket = socket;
    socket.onopen = () => {
      if (this.socket !== socket) return;
      this.failures = 0;
      this.setState('open', { attempt: 0, retryInMs: null });
      this.startHeartbeat();
    };
    socket.onmessage = (event: MessageEvent) => {
      if (this.socket !== socket) return;
      if (typeof event.data === 'string') this.options.onMessage(event.data);
    };
    socket.onerror = () => {
      // The close event that follows does the reconnect work.
    };
    socket.onclose = () => {
      if (this.socket !== socket) return;
      this.socket = null;
      this.stopHeartbeat();
      if (!this.stopped) this.scheduleRetry();
    };
  }

  private scheduleRetry(): void {
    if (this.stopped) return;
    this.stopHeartbeat();
    this.failures += 1;
    const maxAttempts = this.options.maxAttempts ?? Number.POSITIVE_INFINITY;
    if (this.failures > maxAttempts) {
      this.setState('unavailable', { attempt: this.failures, retryInMs: null });
      return;
    }
    const delay = backoffDelay(
      this.failures - 1,
      this.options.baseDelayMs ?? 500,
      this.options.maxDelayMs ?? 10_000,
      this.options.random,
    );
    this.setState('reconnecting', { attempt: this.failures, retryInMs: delay });
    this.retryTimer = setTimeout(() => {
      this.retryTimer = null;
      void this.connect();
    }, delay);
  }

  private startHeartbeat(): void {
    this.stopHeartbeat();
    const heartbeat = this.options.heartbeat;
    if (!heartbeat) return;
    this.heartbeatTimer = setInterval(() => {
      this.send(heartbeat.text);
    }, heartbeat.intervalMs);
  }

  private stopHeartbeat(): void {
    if (this.heartbeatTimer !== null) {
      clearInterval(this.heartbeatTimer);
      this.heartbeatTimer = null;
    }
  }

  private clearTimers(): void {
    if (this.retryTimer !== null) {
      clearTimeout(this.retryTimer);
      this.retryTimer = null;
    }
    this.stopHeartbeat();
  }

  private setState(state: LinkState, info: LinkInfo): void {
    if (state === this.currentState && info.attempt === this.currentInfo.attempt && info.retryInMs === this.currentInfo.retryInMs) {
      return;
    }
    this.currentState = state;
    this.currentInfo = info;
    this.options.onState?.(state, info);
  }
}
