import { describe, expect, it, vi, afterEach } from 'vitest';
import { backoffDelay, ReconnectingSocket, type LinkInfo, type LinkState, type SocketHandle } from './reconnect';

class FakeSocket {
  readyState = 0;
  closed = false;
  sent: string[] = [];
  onopen: (() => void) | null = null;
  onmessage: ((event: { data: unknown }) => void) | null = null;
  onclose: (() => void) | null = null;
  onerror: (() => void) | null = null;
  send(text: string) {
    this.sent.push(text);
  }
  close() {
    this.closed = true;
    this.readyState = 3;
  }
  open() {
    this.readyState = 1;
    this.onopen?.();
  }
  drop() {
    this.readyState = 3;
    this.onclose?.();
  }
  receive(data: unknown) {
    this.onmessage?.({ data });
  }
}

function setup(options: { maxAttempts?: number; heartbeat?: boolean; failOpen?: boolean } = {}) {
  const sockets: FakeSocket[] = [];
  const states: Array<[LinkState, LinkInfo]> = [];
  const messages: string[] = [];
  const open = vi.fn(async () => {
    if (options.failOpen) throw new Error('refused');
    const socket = new FakeSocket();
    sockets.push(socket);
    return socket as unknown as SocketHandle;
  });
  const socket = new ReconnectingSocket({
    path: '/ws/video',
    open,
    onMessage: (text) => messages.push(text),
    onState: (state, info) => states.push([state, info]),
    baseDelayMs: 100,
    maxDelayMs: 800,
    maxAttempts: options.maxAttempts,
    random: () => 0.5,
    heartbeat: options.heartbeat ? { text: 'ping', intervalMs: 1000 } : undefined,
  });
  return { socket, sockets, states, messages, open };
}

describe('backoffDelay', () => {
  it('doubles from the base and is capped', () => {
    const r = () => 0.5;
    expect(backoffDelay(0, 500, 10000, r)).toBe(500);
    expect(backoffDelay(1, 500, 10000, r)).toBe(1000);
    expect(backoffDelay(2, 500, 10000, r)).toBe(2000);
    expect(backoffDelay(10, 500, 10000, r)).toBe(10000);
  });

  it('keeps the jitter within plus or minus 20%', () => {
    expect(backoffDelay(0, 1000, 60000, () => 0)).toBe(800);
    expect(backoffDelay(0, 1000, 60000, () => 0.999999)).toBeLessThanOrEqual(1200);
  });
});

describe('ReconnectingSocket', () => {
  afterEach(() => {
    vi.useRealTimers();
  });

  it('connects, reports open, and forwards text messages only', async () => {
    const { socket, sockets, states, messages } = setup();
    socket.start();
    expect(states[0][0]).toBe('connecting');
    await vi.waitFor(() => expect(sockets.length).toBe(1));
    sockets[0].open();
    expect(socket.state).toBe('open');
    sockets[0].receive('{"type":"status"}');
    sockets[0].receive(new ArrayBuffer(2));
    expect(messages).toEqual(['{"type":"status"}']);
    socket.stop();
  });

  it('reconnects after a drop with a growing delay and reports the countdown', async () => {
    vi.useFakeTimers();
    const { socket, sockets, states } = setup();
    socket.start();
    await vi.advanceTimersByTimeAsync(0);
    sockets[0].open();
    sockets[0].drop();
    expect(states.at(-1)).toEqual(['reconnecting', { attempt: 1, retryInMs: 100 }]);
    await vi.advanceTimersByTimeAsync(100);
    expect(sockets.length).toBe(2);
    sockets[1].drop();
    expect(states.at(-1)?.[1]).toEqual({ attempt: 2, retryInMs: 200 });
    socket.stop();
  });

  it('becomes unavailable after the maximum number of failures', async () => {
    vi.useFakeTimers();
    const { socket, states } = setup({ failOpen: true, maxAttempts: 2 });
    socket.start();
    await vi.advanceTimersByTimeAsync(0);
    await vi.advanceTimersByTimeAsync(10_000);
    expect(socket.state).toBe('unavailable');
    expect(states.at(-1)?.[0]).toBe('unavailable');
    socket.stop();
  });

  it('stop() closes the socket and prevents any further reconnect', async () => {
    vi.useFakeTimers();
    const { socket, sockets, open } = setup();
    socket.start();
    await vi.advanceTimersByTimeAsync(0);
    sockets[0].open();
    socket.stop();
    expect(sockets[0].closed).toBe(true);
    expect(socket.state).toBe('closed');
    await vi.advanceTimersByTimeAsync(60_000);
    expect(open).toHaveBeenCalledTimes(1);
  });

  it('sends a heartbeat only while open, and send() reports false when closed', async () => {
    vi.useFakeTimers();
    const { socket, sockets } = setup({ heartbeat: true });
    socket.start();
    await vi.advanceTimersByTimeAsync(0);
    expect(socket.send('early')).toBe(false);
    sockets[0].open();
    await vi.advanceTimersByTimeAsync(2100);
    expect(sockets[0].sent).toEqual(['ping', 'ping']);
    sockets[0].drop();
    expect(socket.send('late')).toBe(false);
    socket.stop();
  });

  it('retryNow() reconnects without waiting for the backoff', async () => {
    vi.useFakeTimers();
    const { socket, sockets } = setup();
    socket.start();
    await vi.advanceTimersByTimeAsync(0);
    sockets[0].open();
    sockets[0].drop();
    socket.retryNow();
    await vi.advanceTimersByTimeAsync(0);
    expect(sockets.length).toBe(2);
    socket.stop();
  });
});
