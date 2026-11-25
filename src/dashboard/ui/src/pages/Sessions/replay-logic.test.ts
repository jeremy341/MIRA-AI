import { describe, expect, it } from 'vitest';
import type { SessionDetection } from '../../lib/types';
import {
  advancePosition,
  bucketCount,
  bucketIndexAt,
  chooseBucketSeconds,
  clampPosition,
  detectionsInWindow,
  formatClock,
  lowerBound,
} from './replay-logic';

const row = (offset: number, cls: SessionDetection['class_name'] = 'glass'): SessionDetection => ({
  ts: '2026-11-25T10:00:00+00:00',
  offset_seconds: offset,
  frame_index: 0,
  class_name: cls,
  confidence: 0.8,
  bbox: [0, 0, 10, 10],
  track_id: null,
});

describe('bucket maths', () => {
  it('picks the smallest bucket that keeps the timeline within the column budget', () => {
    expect(chooseBucketSeconds(200, 240)).toBe(1);
    expect(chooseBucketSeconds(480, 240)).toBe(2);
    // 15 s would give 256 columns, one over the budget, so the next step (30 s) is used.
    expect(chooseBucketSeconds(3840, 240)).toBe(30);
    expect(chooseBucketSeconds(10 * 86_400, 240)).toBe(3600);
  });

  it('counts the buckets that cover a duration, with at least one', () => {
    expect(bucketCount(100, 30)).toBe(4);
    expect(bucketCount(90, 30)).toBe(3);
    expect(bucketCount(0, 30)).toBe(1);
  });

  it('maps a position to its bucket and keeps the index inside the timeline', () => {
    expect(bucketIndexAt(0, 10, 5)).toBe(0);
    expect(bucketIndexAt(29.9, 10, 5)).toBe(2);
    expect(bucketIndexAt(999, 10, 5)).toBe(4);
    expect(bucketIndexAt(-4, 10, 5)).toBe(0);
    expect(bucketIndexAt(5, 10, 0)).toBe(0);
  });
});

describe('replay position', () => {
  it('clamps the position between zero and the duration', () => {
    expect(clampPosition(-3, 60)).toBe(0);
    expect(clampPosition(75, 60)).toBe(60);
    expect(clampPosition(Number.NaN, 60)).toBe(0);
  });

  it('advances by elapsed time times speed', () => {
    expect(advancePosition(10, 0.5, 1, 60)).toEqual({ position: 10.5, ended: false });
    expect(advancePosition(10, 0.5, 4, 60)).toEqual({ position: 12, ended: false });
  });

  it('stops at the end and reports it', () => {
    expect(advancePosition(59, 5, 1, 60)).toEqual({ position: 60, ended: true });
    expect(advancePosition(0, 1, 1, 0)).toEqual({ position: 0, ended: false });
  });

  it('ignores negative elapsed time', () => {
    expect(advancePosition(10, -5, 1, 60).position).toBe(10);
  });
});

describe('formatClock', () => {
  it('uses m:ss under an hour and h:mm:ss from an hour', () => {
    expect(formatClock(0)).toBe('0:00');
    expect(formatClock(65.9)).toBe('1:05');
    expect(formatClock(3725)).toBe('1:02:05');
    expect(formatClock(-4)).toBe('0:00');
  });
});

describe('detections in a time window', () => {
  const rows = [row(0), row(1.5), row(2), row(2), row(9.9), row(10), row(31)];

  it('finds the first row at or after a value with a binary search', () => {
    expect(lowerBound(rows, 0)).toBe(0);
    expect(lowerBound(rows, 2)).toBe(2);
    expect(lowerBound(rows, 2.1)).toBe(4);
    expect(lowerBound(rows, 100)).toBe(rows.length);
  });

  it('returns the rows in [from, to), so a row exactly at the end belongs to the next bucket', () => {
    expect(detectionsInWindow(rows, 0, 10).map((r) => r.offset_seconds)).toEqual([0, 1.5, 2, 2, 9.9]);
    expect(detectionsInWindow(rows, 10, 20).map((r) => r.offset_seconds)).toEqual([10]);
    expect(detectionsInWindow(rows, 40, 50)).toEqual([]);
  });
});
