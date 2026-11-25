/**
 * Calls `task` every `intervalMs`, but only while the page is visible: a hidden tab stops polling and
 * polls once more as soon as it is shown again. A call never overlaps the one before it. Errors go to
 * `onError` and polling carries on. Returns a function that stops everything.
 */
export interface PollOptions {
  intervalMs: number;
  /** Run once right away instead of waiting for the first interval. Default true. */
  immediate?: boolean;
  onError?: (error: unknown) => void;
}

function isVisible(): boolean {
  return typeof document === 'undefined' || document.visibilityState !== 'hidden';
}

export function startPolling(task: () => unknown, options: PollOptions): () => void {
  const { intervalMs, immediate = true, onError } = options;
  let timer: ReturnType<typeof setTimeout> | undefined;
  let stopped = false;
  let running = false;

  const schedule = () => {
    if (stopped) return;
    clearTimeout(timer);
    timer = setTimeout(() => void run(), intervalMs);
  };

  const run = async (): Promise<void> => {
    if (stopped) return;
    clearTimeout(timer);
    // A hidden page waits; the visibility listener restarts the cycle when it is shown again.
    if (!isVisible() || running) return;
    running = true;
    try {
      await task();
    } catch (error) {
      onError?.(error);
    } finally {
      running = false;
    }
    schedule();
  };

  const onVisibility = () => {
    if (!stopped && isVisible()) void run();
  };
  if (typeof document !== 'undefined') document.addEventListener('visibilitychange', onVisibility);

  if (immediate) void run();
  else schedule();

  return () => {
    stopped = true;
    clearTimeout(timer);
    if (typeof document !== 'undefined') document.removeEventListener('visibilitychange', onVisibility);
  };
}
