/**
 * Replay timeline maths, pure. The scrubber works in session seconds: `position` runs from 0 to the
 * session's duration, and the buckets from `/sessions/{id}/timeline` cover it in `bucketSeconds` steps.
 * Covered by replay-logic.test.ts.
 */
import type { SessionDetection } from '../../lib/types';

/** Bucket widths the page may ask the server for, smallest first. */
export const BUCKET_STEPS = [1, 2, 5, 10, 15, 30, 60, 120, 300, 600, 900, 1800, 3600] as const;

/** Replay speeds. 1x plays at the pace the session was recorded at. */
export const REPLAY_SPEEDS = [1, 2, 4] as const;
export type ReplaySpeed = (typeof REPLAY_SPEEDS)[number];

/** The smallest bucket width that keeps the timeline at or under `maxBuckets` columns. */
export function chooseBucketSeconds(durationSeconds: number, maxBuckets = 240): number {
  for (const step of BUCKET_STEPS) {
    if (Math.ceil(durationSeconds / step) <= maxBuckets) return step;
  }
  return BUCKET_STEPS[BUCKET_STEPS.length - 1];
}

/** How many buckets cover the duration. A session always has at least one. */
export function bucketCount(durationSeconds: number, bucketSeconds: number): number {
  if (!(durationSeconds > 0) || !(bucketSeconds > 0)) return 1;
  return Math.max(1, Math.ceil(durationSeconds / bucketSeconds));
}

/** The bucket a position falls in, kept inside the timeline. */
export function bucketIndexAt(position: number, bucketSeconds: number, count: number): number {
  if (count <= 0) return 0;
  const index = Math.floor(Math.max(0, position) / bucketSeconds);
  return Math.min(count - 1, Math.max(0, index));
}

/** Keeps a position between 0 and the duration. */
export function clampPosition(position: number, durationSeconds: number): number {
  if (!Number.isFinite(position)) return 0;
  return Math.min(Math.max(0, durationSeconds), Math.max(0, position));
}

/**
 * Moves the replay on by the wall-clock time that passed. At 2x a real second is two session seconds.
 * `ended` is true once the position reaches the end, so the caller can pause there.
 */
export function advancePosition(
  position: number,
  elapsedSeconds: number,
  speed: number,
  durationSeconds: number,
): { position: number; ended: boolean } {
  const elapsed = Math.max(0, elapsedSeconds);
  const next = clampPosition(position + elapsed * speed, durationSeconds);
  return { position: next, ended: next >= durationSeconds && durationSeconds > 0 };
}

/** `m:ss` under an hour, `h:mm:ss` from an hour up. */
export function formatClock(seconds: number): string {
  const total = Math.max(0, Math.floor(Number.isFinite(seconds) ? seconds : 0));
  const hours = Math.floor(total / 3600);
  const minutes = Math.floor((total % 3600) / 60);
  const secs = total % 60;
  const pad = (n: number) => String(n).padStart(2, '0');
  return hours > 0 ? `${hours}:${pad(minutes)}:${pad(secs)}` : `${minutes}:${pad(secs)}`;
}

/**
 * The detections whose offset falls in [from, to), from a list sorted by `offset_seconds`.
 * Binary search, so a long session stays cheap to scrub.
 */
export function detectionsInWindow(sorted: readonly SessionDetection[], from: number, to: number): SessionDetection[] {
  const start = lowerBound(sorted, from);
  const out: SessionDetection[] = [];
  for (let i = start; i < sorted.length && sorted[i].offset_seconds < to; i += 1) out.push(sorted[i]);
  return out;
}

/** The first index whose offset is at least `value`. */
export function lowerBound(sorted: readonly SessionDetection[], value: number): number {
  let low = 0;
  let high = sorted.length;
  while (low < high) {
    const mid = (low + high) >>> 1;
    if (sorted[mid].offset_seconds < value) low = mid + 1;
    else high = mid;
  }
  return low;
}
