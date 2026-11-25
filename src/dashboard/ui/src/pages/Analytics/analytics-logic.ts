/**
 * Rules for the Analytics page, pure. Covered by analytics-logic.test.ts.
 */
import type { ArmAccuracy, ArmEvent, ArmEventKind, ArmStatus, HardwarePoint } from '../../lib/types';

/** Hardware history windows. Each one asks the server for about this many points. */
export const HARDWARE_RANGES = [
  { value: '15', label: '15 min', minutes: 15 },
  { value: '60', label: '1 h', minutes: 60 },
  { value: '360', label: '6 h', minutes: 360 },
  { value: '1440', label: '24 h', minutes: 1440 },
] as const;
export const HARDWARE_POINTS = 240;

export function minutesFor(value: string): number {
  return HARDWARE_RANGES.find((range) => range.value === value)?.minutes ?? 60;
}

/** True when at least one sample has a temperature. Without one the page says there is no sensor. */
export function hasTemperature(points: readonly HardwarePoint[]): boolean {
  return points.some((point) => typeof point.temperature_c === 'number' && Number.isFinite(point.temperature_c));
}

/** The arm's accuracy as a sentence. Accuracy is only known once someone has given feedback. */
export function accuracySentence(status: Pick<ArmStatus, 'accuracy' | 'total_feedback'>): string {
  if (status.accuracy === null || status.total_feedback === 0) return 'No feedback yet';
  return `${Math.round(status.accuracy * 100)}% correct`;
}

export function accuracyDetail(accuracy: ArmAccuracy): string {
  if (accuracy.total === 0) return 'Mark sorted items as correct or incorrect to build this number.';
  return `${accuracy.correct} of ${accuracy.total} judged sorts were correct.`;
}

/** Only a finished sort can be judged. Other events are log lines. */
export function canGiveFeedback(event: Pick<ArmEvent, 'kind'>): boolean {
  return event.kind === 'sort_completed';
}

export function feedbackState(event: Pick<ArmEvent, 'correct'>): 'none' | 'correct' | 'incorrect' {
  if (event.correct === true) return 'correct';
  if (event.correct === false) return 'incorrect';
  return 'none';
}

const KIND_WORDS: Record<ArmEventKind, string> = {
  sort_requested: 'Sort requested',
  sort_completed: 'Sort completed',
  sort_failed: 'Sort failed',
  home_requested: 'Home requested',
  home_completed: 'Homed',
  home_failed: 'Home failed',
  stop_requested: 'Stop requested',
  stop_completed: 'Stopped',
  stop_failed: 'Stop failed',
};

/** A log line: "Sort completed: glass, track 4". */
export function eventTitle(event: Pick<ArmEvent, 'kind' | 'class_name' | 'track_id'>): string {
  const base = KIND_WORDS[event.kind] ?? event.kind;
  const parts: string[] = [];
  if (event.class_name) parts.push(event.class_name);
  if (event.track_id !== null) parts.push(`track ${event.track_id}`);
  return parts.length ? `${base}: ${parts.join(', ')}` : base;
}

/** The newest events first, without duplicates. Used when the live feed and a fetch overlap. */
export function mergeEvents(current: readonly ArmEvent[], incoming: readonly ArmEvent[], limit = 100): ArmEvent[] {
  const byId = new Map<number, ArmEvent>();
  for (const event of [...incoming, ...current]) {
    if (!byId.has(event.id)) byId.set(event.id, event);
  }
  return [...byId.values()].sort((a, b) => b.id - a.id).slice(0, limit);
}

/** Clock time for chart axes, "14:05". */
export function clockLabel(timestampMs: number): string {
  const date = new Date(timestampMs);
  const pad = (n: number) => String(n).padStart(2, '0');
  return `${pad(date.getHours())}:${pad(date.getMinutes())}`;
}

/** ISO timestamp to epoch milliseconds, or NaN when it is not a time. */
export function timeMs(iso: string): number {
  return Date.parse(iso);
}
