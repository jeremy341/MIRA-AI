import { describe, expect, it } from 'vitest';
import type { ArmEvent, HardwarePoint } from '../../lib/types';
import {
  HARDWARE_RANGES,
  accuracyDetail,
  accuracySentence,
  canGiveFeedback,
  eventTitle,
  feedbackState,
  hasTemperature,
  mergeEvents,
  minutesFor,
} from './analytics-logic';

const point = (temperature: number | null): HardwarePoint => ({
  ts: '2026-11-25T10:00:00+00:00',
  cpu_percent: 40,
  memory_percent: 50,
  temperature_c: temperature,
});

const event = (id: number, kind: ArmEvent['kind'] = 'sort_completed', correct: boolean | null = null): ArmEvent => ({
  id,
  ts: '2026-11-25T10:00:00+00:00',
  kind,
  class_name: 'glass',
  track_id: 4,
  payload: {},
  correct,
});

describe('hardware ranges', () => {
  it('offers 15 minutes, 1 hour, 6 hours and 24 hours', () => {
    expect(HARDWARE_RANGES.map((range) => range.label)).toEqual(['15 min', '1 h', '6 h', '24 h']);
    expect(minutesFor('15')).toBe(15);
    expect(minutesFor('1440')).toBe(1440);
    expect(minutesFor('nonsense')).toBe(60);
  });

  it('detects whether any sample has a temperature', () => {
    expect(hasTemperature([point(null), point(null)])).toBe(false);
    expect(hasTemperature([point(null), point(55.2)])).toBe(true);
    expect(hasTemperature([])).toBe(false);
  });
});

describe('arm accuracy wording', () => {
  it('says no feedback yet until something has been judged', () => {
    expect(accuracySentence({ accuracy: null, total_feedback: 0 })).toBe('No feedback yet');
    expect(accuracySentence({ accuracy: 0.8, total_feedback: 5 })).toBe('80% correct');
    expect(accuracyDetail({ accuracy: null, correct: 0, total: 0 })).toMatch(/Mark/);
    expect(accuracyDetail({ accuracy: 0.8, correct: 4, total: 5 })).toBe('4 of 5 judged sorts were correct.');
  });
});

describe('arm events', () => {
  it('only lets a finished sort be judged', () => {
    expect(canGiveFeedback({ kind: 'sort_completed' })).toBe(true);
    expect(canGiveFeedback({ kind: 'sort_requested' })).toBe(false);
    expect(canGiveFeedback({ kind: 'home_completed' })).toBe(false);
  });

  it('reads the feedback state for the two buttons', () => {
    expect(feedbackState({ correct: null })).toBe('none');
    expect(feedbackState({ correct: true })).toBe('correct');
    expect(feedbackState({ correct: false })).toBe('incorrect');
  });

  it('writes a log line with the class and the track', () => {
    expect(eventTitle({ kind: 'sort_completed', class_name: 'glass', track_id: 4 })).toBe('Sort completed: glass, track 4');
    expect(eventTitle({ kind: 'home_completed', class_name: null, track_id: null })).toBe('Homed');
  });

  it('merges a live event with a fetched list without duplicates, newest first', () => {
    const merged = mergeEvents([event(3), event(2)], [event(4), event(2)]);
    expect(merged.map((e) => e.id)).toEqual([4, 3, 2]);
  });

  it('keeps the list to the limit', () => {
    const many = Array.from({ length: 10 }, (_, i) => event(i + 1));
    expect(mergeEvents([], many, 4).map((e) => e.id)).toEqual([10, 9, 8, 7]);
  });
});
