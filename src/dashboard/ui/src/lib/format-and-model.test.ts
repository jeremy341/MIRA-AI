import { describe, expect, it } from 'vitest';
import { defaultSessionName, formatBytes, formatDuration, formatMegabytes, formatMs, formatNumber, formatPercent } from './format';
import {
  DEFAULT_CAMERA,
  defaultDraft,
  hasErrors,
  parseStoredSettings,
  payloadsOf,
  sameDraft,
  validateSettings,
} from './settings-model';
import { parseRoute, routeHref } from './router';
import { dismiss, enqueue, MAX_TOASTS, type Toast } from './toast-queue';
import { describeConnection, describeModel, describeSession, describeStream } from './status-summary';
import type { SessionSummary, StatusResponse } from './types';

describe('format', () => {
  it('formats percentages, numbers and milliseconds, with a dash for missing values', () => {
    expect(formatPercent(0.837)).toBe('84%');
    expect(formatPercent(null)).toBe('-');
    expect(formatNumber(24.46)).toBe('24.5');
    expect(formatNumber(Number.NaN)).toBe('-');
    expect(formatMs(41.6)).toBe('42 ms');
    expect(formatMs(undefined)).toBe('-');
  });

  it('formats durations in seconds, minutes and hours', () => {
    expect(formatDuration(42)).toBe('42 s');
    expect(formatDuration(61)).toBe('1 min 1 s');
    expect(formatDuration(3725)).toBe('1 h 2 min');
    expect(formatDuration(-5)).toBe('0 s');
  });

  it('formats sizes', () => {
    expect(formatBytes(512)).toBe('512 B');
    expect(formatBytes(1536)).toBe('1.5 KB');
    expect(formatBytes(2 * 1024 * 1024)).toBe('2.0 MB');
    expect(formatMegabytes(5.214)).toBe('5.2 MB');
  });

  it('builds the default session name in the backend pattern', () => {
    expect(defaultSessionName(new Date(2026, 10, 5, 7, 4))).toBe('Session 2026-11-05 07:04');
  });
});

describe('settings validation', () => {
  const names = ['mira_exp018.pt', 'mira_exp019_int8.tflite'];

  it('accepts the defaults with a chosen model', () => {
    expect(validateSettings(defaultDraft('mira_exp018.pt'), names)).toEqual({});
  });

  it('reports field errors inline and names the field', () => {
    const draft = defaultDraft('mira_exp018.pt');
    draft.camera.index = 12;
    draft.camera.fps = 0;
    draft.model.conf_threshold = 1.5;
    draft.model.target_latency_ms = 2.5;
    const errors = validateSettings(draft, names);
    expect(Object.keys(errors).sort()).toEqual(
      ['camera.fps', 'camera.index', 'model.conf_threshold', 'model.target_latency_ms'].sort(),
    );
    expect(hasErrors(errors)).toBe(true);
  });

  it('requires a model that exists in the list', () => {
    expect(validateSettings(defaultDraft(''), names)['model.name']).toMatch(/Choose a model/);
    expect(validateSettings(defaultDraft('unknown.pt'), names)['model.name']).toMatch(/Choose a model/);
  });

  it('rejects a resolution that is not a preset', () => {
    const draft = defaultDraft('mira_exp018.pt');
    draft.camera.width = 1000;
    expect(validateSettings(draft, names)['camera.resolution']).toBeDefined();
  });

  it('splits the draft into the two server payloads', () => {
    const draft = defaultDraft('mira_exp018.pt');
    const payload = payloadsOf(draft);
    expect(payload.camera).toEqual(DEFAULT_CAMERA);
    expect(payload.model.name).toBe('mira_exp018.pt');
    expect(payload.model).not.toBe(draft.model);
  });
});

describe('stored settings', () => {
  it('returns defaults for missing, broken or non-object input', () => {
    expect(parseStoredSettings(null, 'a.pt')).toEqual(defaultDraft('a.pt'));
    expect(parseStoredSettings('{broken', 'a.pt')).toEqual(defaultDraft('a.pt'));
    expect(parseStoredSettings('42')).toEqual(defaultDraft(''));
  });

  it('keeps valid stored values and ignores wrong types', () => {
    const parsed = parseStoredSettings(
      JSON.stringify({ camera: { index: 2, width: '640', fps: 15, autofocus: 'yes' }, model: { name: 'x.pt', enable_tracking: false } }),
    );
    expect(parsed.camera.index).toBe(2);
    expect(parsed.camera.width).toBe(DEFAULT_CAMERA.width);
    expect(parsed.camera.fps).toBe(15);
    expect(parsed.camera.autofocus).toBe(false);
    expect(parsed.model.name).toBe('x.pt');
    expect(parsed.model.enable_tracking).toBe(false);
  });

  it('compares drafts by value', () => {
    expect(sameDraft(defaultDraft('a'), defaultDraft('a'))).toBe(true);
    expect(sameDraft(defaultDraft('a'), defaultDraft('b'))).toBe(false);
  });
});

describe('routes', () => {
  it('parses known hashes and falls back to detect', () => {
    expect(parseRoute('#/sessions')).toBe('sessions');
    expect(parseRoute('#/Settings')).toBe('settings');
    expect(parseRoute('#/analytics?x=1')).toBe('analytics');
    expect(parseRoute('')).toBe('detect');
    expect(parseRoute('#/nope')).toBe('detect');
    expect(parseRoute('#/')).toBe('detect');
  });

  it('builds hrefs', () => {
    expect(routeHref('models')).toBe('#/models');
  });
});

describe('toast queue', () => {
  const toast = (id: number): Toast => ({ id, kind: 'info', message: `m${id}` });

  it('keeps only the newest toasts', () => {
    let list: Toast[] = [];
    for (let i = 1; i <= MAX_TOASTS + 2; i += 1) list = enqueue(list, toast(i));
    expect(list).toHaveLength(MAX_TOASTS);
    expect(list[0].id).toBe(3);
  });

  it('dismisses by id without touching the others', () => {
    expect(dismiss([toast(1), toast(2)], 1).map((t) => t.id)).toEqual([2]);
  });
});

describe('status summaries', () => {
  const status = (overrides: Partial<StatusResponse> = {}): StatusResponse => ({
    status: 'idle',
    message: '',
    camera_initialized: false,
    model_loaded: false,
    streaming: false,
    timestamp: '2026-11-25T00:00:00Z',
    ...overrides,
  });

  it('describes the model', () => {
    expect(describeModel(status(), null, null)).toEqual({ text: 'No model', tone: 'neutral' });
    expect(describeModel(status({ model_loaded: true }), 'mira_exp018.pt', null)).toEqual({ text: 'mira_exp018.pt', tone: 'success' });
    expect(describeModel(status({ model_loaded: true }), null, null).text).toBe('Model loaded');
    expect(describeModel(null, null, 'down')).toEqual({ text: 'Server offline', tone: 'danger' });
  });

  it('describes the connection, including the countdown', () => {
    expect(describeConnection('open', { attempt: 0, retryInMs: null }, null).text).toBe('Connected');
    expect(describeConnection('reconnecting', { attempt: 2, retryInMs: 1600 }, null).text).toBe('Reconnecting in 2 s');
    expect(describeConnection('unavailable', { attempt: 6, retryInMs: null }, null).tone).toBe('danger');
    expect(describeConnection('closed', { attempt: 0, retryInMs: null }, 'down').text).toBe('Server offline');
  });

  it('describes the stream, where "Starting" means no frame yet', () => {
    expect(describeStream(status({ streaming: true }), false).text).toBe('Starting');
    expect(describeStream(status({ streaming: true }), true).text).toBe('Live');
    expect(describeStream(status(), false).text).toBe('Stopped');
  });

  it('describes the session, with "No session" when there is none or the route is missing', () => {
    const session = { name: 'Line A' } as SessionSummary;
    expect(describeSession(session, 'ready').text).toBe('Line A');
    expect(describeSession(null, 'unavailable').text).toBe('No session');
    expect(describeSession(null, 'unknown').text).toBe('Checking');
  });
});
