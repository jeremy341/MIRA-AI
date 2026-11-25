import { describe, expect, it } from 'vitest';
import { progressAt, progressMessage, type JobClock } from './job-clock';

const clock: JobClock = { startedMs: 1_000_000, durationMs: 100_000, startProgress: 0 };

describe('progressAt', () => {
  it('is zero when the job has not moved and rises with elapsed time', () => {
    expect(progressAt(clock, 1_000_000)).toBe(0);
    expect(progressAt(clock, 1_050_000)).toBe(0.5);
    expect(progressAt(clock, 1_025_000)).toBe(0.25);
  });

  it('starts from the given progress, not from zero', () => {
    const resumed: JobClock = { ...clock, startProgress: 0.42 };
    expect(progressAt(resumed, 1_000_000)).toBe(0.42);
    // 0.42 + 0.58 * 0.5 = 0.71
    expect(progressAt(resumed, 1_050_000)).toBe(0.71);
  });

  it('is exactly 1 once the duration has passed, and never above 1', () => {
    expect(progressAt(clock, 1_100_000)).toBe(1);
    expect(progressAt(clock, 9_999_999)).toBe(1);
  });

  it('ignores times before the start', () => {
    expect(progressAt(clock, 500_000)).toBe(0);
  });

  it('treats a zero-length job as finished', () => {
    expect(progressAt({ ...clock, durationMs: 0 }, 1_000_000)).toBe(1);
  });

  it('rounds to three decimals', () => {
    const value = progressAt({ ...clock, durationMs: 3_000 }, 1_001_000);
    expect(value).toBe(0.333);
  });
});

describe('progressMessage', () => {
  it('counts frames of a video with thousands separators', () => {
    expect(progressMessage('batch_video', 0.42, 3000)).toBe('Frame 1,260 of 3,000');
  });

  it('counts images of a folder, one ahead of the finished ones', () => {
    expect(progressMessage('batch_images', 0, 40)).toBe('Image 1 of 40');
    expect(progressMessage('batch_images', 0.5, 40)).toBe('Image 21 of 40');
  });

  it('counts finished models of a benchmark, singular for one model', () => {
    expect(progressMessage('benchmark', 0.5, 2)).toBe('Benchmarked 1 of 2 models');
    expect(progressMessage('benchmark', 0, 1)).toBe('Benchmarked 0 of 1 model');
  });

  it('says Finished at 1', () => {
    expect(progressMessage('batch_video', 1, 3000)).toBe('Finished');
  });
});
