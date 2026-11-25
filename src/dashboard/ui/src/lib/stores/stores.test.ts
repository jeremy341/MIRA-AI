import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { toasts } from './toasts.svelte';
import { settings } from './settings.svelte';
import { defaultDraft } from '../settings-model';
import { TOAST_DURATION_MS, MAX_TOASTS } from '../toast-queue';

describe('toasts store', () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
    for (const item of [...toasts.items]) toasts.dismiss(item.id);
  });

  it('shows a toast and removes it after its duration', () => {
    toasts.success('Saved');
    expect(toasts.items.at(-1)?.message).toBe('Saved');
    vi.advanceTimersByTime(TOAST_DURATION_MS.success + 1);
    expect(toasts.items.find((t) => t.message === 'Saved')).toBeUndefined();
  });

  it('keeps errors visible longer than successes', () => {
    toasts.error('Failed');
    vi.advanceTimersByTime(TOAST_DURATION_MS.success + 1);
    expect(toasts.items.some((t) => t.message === 'Failed')).toBe(true);
    vi.advanceTimersByTime(TOAST_DURATION_MS.error);
    expect(toasts.items.some((t) => t.message === 'Failed')).toBe(false);
  });

  it('limits the number of visible toasts', () => {
    for (let i = 0; i < MAX_TOASTS + 3; i += 1) toasts.info(`m${i}`);
    expect(toasts.items).toHaveLength(MAX_TOASTS);
    expect(toasts.items.at(-1)?.message).toBe(`m${MAX_TOASTS + 2}`);
  });

  it('dismisses by id', () => {
    const id = toasts.warning('Careful');
    toasts.dismiss(id);
    expect(toasts.items.some((t) => t.id === id)).toBe(false);
  });
});

describe('settings store', () => {
  it('starts clean and becomes dirty after an edit', () => {
    settings.revertDraft();
    expect(settings.dirty).toBe(false);
    settings.draft.camera.fps = 12;
    expect(settings.dirty).toBe(true);
    settings.revertDraft();
    expect(settings.dirty).toBe(false);
  });

  it('marks the draft as applied and resets the draft to defaults on request', () => {
    const draft = defaultDraft('mira_exp018.pt');
    draft.model.conf_threshold = 0.6;
    settings.draft = structuredClone(draft);
    settings.markApplied(draft);
    expect(settings.saved.model.conf_threshold).toBe(0.6);
    expect(settings.dirty).toBe(false);
    settings.resetDraft();
    expect(settings.draft.model.conf_threshold).toBe(0.25);
    expect(settings.draft.model.name).toBe('mira_exp018.pt');
    expect(settings.dirty).toBe(true);
  });
});
