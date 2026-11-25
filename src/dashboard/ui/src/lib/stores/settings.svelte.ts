import { defaultDraft, parseStoredSettings, sameDraft, type SettingsDraft } from '../settings-model';

/** Per-browser memory of the last applied settings. The server has no GET for them yet (see README). */
export const SETTINGS_STORAGE_KEY = 'mira.dashboard.settings.v1';

function clone(draft: SettingsDraft): SettingsDraft {
  return structuredClone(draft);
}

function readStored(): SettingsDraft {
  try {
    return parseStoredSettings(globalThis.localStorage?.getItem(SETTINGS_STORAGE_KEY) ?? null);
  } catch {
    // Storage can be blocked (private windows, disabled cookies). Defaults are fine then.
    return defaultDraft();
  }
}

function writeStored(draft: SettingsDraft): void {
  try {
    globalThis.localStorage?.setItem(SETTINGS_STORAGE_KEY, JSON.stringify(draft));
  } catch {
    // Not persisted. The settings still work for this page visit.
  }
}

/**
 * The Settings page draft (edited freely) and the last applied settings (what the server accepted).
 * The Detect page uses `saved` for its "Connect camera" and "Load model" steps.
 */
class SettingsStore {
  saved = $state.raw<SettingsDraft>(readStored());
  draft = $state<SettingsDraft>(clone(readStored()));
  dirty = $derived(!sameDraft(this.draft, this.saved));

  /** Called after the server accepted the camera and model settings. */
  markApplied(draft: SettingsDraft): void {
    this.saved = clone(draft);
    writeStored(this.saved);
  }

  /** Puts the defaults into the draft. Nothing is applied until the person presses Apply. */
  resetDraft(): void {
    this.draft = defaultDraft(this.draft.model.name);
  }

  /** Discards unapplied edits. */
  revertDraft(): void {
    this.draft = clone(this.saved);
  }
}

export const settings = new SettingsStore();
