/**
 * Mock job progress. A job's progress is a function of the time since it started, so the mock needs
 * no timers of its own: every read asks the clock where the job is. Pure, covered by job-clock.test.ts.
 */

export interface JobClock {
  startedMs: number;
  durationMs: number;
  /** Progress when the clock started (0 for a new job, 0.42 for a job that was already running). */
  startProgress: number;
}

/** Progress from 0 to 1, rounded to three decimals. Reaches exactly 1 once the duration has passed. */
export function progressAt(clock: JobClock, now: number): number {
  const elapsed = Math.max(0, now - clock.startedMs);
  const fraction = clock.durationMs > 0 ? elapsed / clock.durationMs : 1;
  const value = clock.startProgress + (1 - clock.startProgress) * Math.min(1, fraction);
  if (value >= 1) return 1;
  return Math.round(value * 1000) / 1000;
}

const count = (n: number) => n.toLocaleString('en-US');

/**
 * The status line of a running job. `total` is the number of units: frames for a video,
 * images for a folder, models for a benchmark.
 */
export function progressMessage(kind: string, progress: number, total: number): string {
  if (progress >= 1) return 'Finished';
  const done = Math.min(total, Math.floor(progress * total));
  if (kind === 'benchmark') {
    return `Benchmarked ${done} of ${total} model${total === 1 ? '' : 's'}`;
  }
  if (kind === 'batch_images') {
    return `Image ${count(Math.min(total, done + 1))} of ${count(total)}`;
  }
  return `Frame ${count(done)} of ${count(total)}`;
}
