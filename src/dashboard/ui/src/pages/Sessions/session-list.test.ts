import { describe, expect, it } from 'vitest';
import type { SessionSummary } from '../../lib/types';
import { canDelete, deleteBlockedReason, hasMore, isLive, mergeSessionPages, sortNewestFirst, statusLabel } from './session-list';

const session = (id: string, started: string, extra: Partial<SessionSummary> = {}): SessionSummary => ({
  id,
  name: id,
  source: 'camera',
  model_name: null,
  status: 'completed',
  started_at: started,
  ended_at: null,
  duration_seconds: 0,
  total_detections: 0,
  class_counts: { glass: 0, metal: 0, paper: 0, plastic: 0, trash: 0 },
  avg_confidence: null,
  ...extra,
});

describe('session list rules', () => {
  it('sorts newest first, whatever order the server gave', () => {
    const rows = [
      session('old', '2026-11-20T10:00:00+00:00'),
      session('new', '2026-11-25T10:00:00+00:00'),
      session('mid', '2026-11-22T10:00:00+00:00'),
    ];
    expect(sortNewestFirst(rows).map((r) => r.id)).toEqual(['new', 'mid', 'old']);
  });

  it('merges pages without duplicates and keeps the newest first', () => {
    const first = [session('a', '2026-11-25T10:00:00+00:00'), session('b', '2026-11-24T10:00:00+00:00')];
    const second = [session('b', '2026-11-24T10:00:00+00:00'), session('c', '2026-11-23T10:00:00+00:00')];
    expect(mergeSessionPages(first, second).map((r) => r.id)).toEqual(['a', 'b', 'c']);
  });

  it('marks only an active camera session as live', () => {
    expect(isLive(session('x', '', { source: 'camera', status: 'active' }))).toBe(true);
    expect(isLive(session('x', '', { source: 'video', status: 'active' }))).toBe(false);
    expect(isLive(session('x', '', { source: 'camera', status: 'completed' }))).toBe(false);
  });

  it('refuses to delete an active session, with a reason that matches the kind', () => {
    expect(canDelete({ status: 'completed' })).toBe(true);
    expect(canDelete({ status: 'active' })).toBe(false);
    expect(deleteBlockedReason({ source: 'camera', status: 'active' })).toMatch(/live/);
    expect(deleteBlockedReason({ source: 'video', status: 'active' })).toMatch(/import/);
    expect(deleteBlockedReason({ source: 'camera', status: 'completed' })).toBeNull();
  });

  it('offers more while the list is shorter than the total', () => {
    expect(hasMore(20, 45)).toBe(true);
    expect(hasMore(45, 45)).toBe(false);
  });

  it('labels every status in plain words', () => {
    expect(statusLabel('active')).toBe('Running');
    expect(statusLabel('failed')).toBe('Failed');
  });
});
