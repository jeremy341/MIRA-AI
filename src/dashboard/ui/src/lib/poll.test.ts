import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { startPolling } from './poll';

describe('startPolling', () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });
  afterEach(() => {
    vi.useRealTimers();
  });

  it('runs at once and then on each interval', async () => {
    const task = vi.fn(async () => undefined);
    const stop = startPolling(task, { intervalMs: 1000 });
    await vi.advanceTimersByTimeAsync(0);
    expect(task).toHaveBeenCalledTimes(1);
    await vi.advanceTimersByTimeAsync(2000);
    expect(task).toHaveBeenCalledTimes(3);
    stop();
  });

  it('waits for the first interval when immediate is false', async () => {
    const task = vi.fn(async () => undefined);
    const stop = startPolling(task, { intervalMs: 500, immediate: false });
    await vi.advanceTimersByTimeAsync(400);
    expect(task).not.toHaveBeenCalled();
    await vi.advanceTimersByTimeAsync(200);
    expect(task).toHaveBeenCalledTimes(1);
    stop();
  });

  it('never overlaps a slow call', async () => {
    let release: () => void = () => undefined;
    let inFlight = 0;
    let maxInFlight = 0;
    const task = vi.fn(
      () =>
        new Promise<void>((resolve) => {
          inFlight += 1;
          maxInFlight = Math.max(maxInFlight, inFlight);
          release = () => {
            inFlight -= 1;
            resolve();
          };
        }),
    );
    const stop = startPolling(task, { intervalMs: 100 });
    await vi.advanceTimersByTimeAsync(1000);
    expect(task).toHaveBeenCalledTimes(1);
    release();
    await vi.advanceTimersByTimeAsync(150);
    expect(task).toHaveBeenCalledTimes(2);
    expect(maxInFlight).toBe(1);
    release();
    stop();
  });

  it('reports errors and keeps polling', async () => {
    const onError = vi.fn();
    let calls = 0;
    const stop = startPolling(
      () => {
        calls += 1;
        if (calls === 1) throw new Error('offline');
      },
      { intervalMs: 100, onError },
    );
    await vi.advanceTimersByTimeAsync(250);
    expect(onError).toHaveBeenCalledTimes(1);
    expect(calls).toBeGreaterThanOrEqual(2);
    stop();
  });

  it('stops for good when asked', async () => {
    const task = vi.fn(async () => undefined);
    const stop = startPolling(task, { intervalMs: 100 });
    await vi.advanceTimersByTimeAsync(150);
    stop();
    const count = task.mock.calls.length;
    await vi.advanceTimersByTimeAsync(1000);
    expect(task.mock.calls.length).toBe(count);
  });
});
