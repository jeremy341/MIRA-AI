/**
 * Settings model for the Settings page and the Detect readiness steps. Pure: defaults, validation,
 * payload building and safe storage parsing. Covered by settings-model.test.ts.
 */
import type { CameraConfig, ModelConfig } from './types';

export interface SettingsDraft {
  camera: CameraConfig;
  model: ModelConfig;
}

export const DEFAULT_CAMERA: CameraConfig = {
  index: 0,
  width: 640,
  height: 360,
  fps: 30,
  autofocus: false,
  auto_exposure: true,
};

/** The server's own defaults (backend/models.py), so "Reset defaults" matches a fresh server. */
export const DEFAULT_MODEL_TUNING = {
  conf_threshold: 0.25,
  reject_threshold: 0.25,
  iou_threshold: 0.45,
  enable_tracking: true,
  target_latency_ms: 1000,
} as const;

export const RESOLUTION_PRESETS: ReadonlyArray<{ label: string; width: number; height: number }> = [
  { label: '640 × 360 (default)', width: 640, height: 360 },
  { label: '854 × 480', width: 854, height: 480 },
  { label: '1280 × 720', width: 1280, height: 720 },
  { label: '1920 × 1080', width: 1920, height: 1080 },
];

export const SETTING_LIMITS = {
  index: { min: 0, max: 10 },
  fps: { min: 1, max: 60 },
  latency: { min: 5, max: 1000 },
  unit: { min: 0, max: 1 },
} as const;

export type SettingsFieldKey =
  | 'camera.index'
  | 'camera.resolution'
  | 'camera.fps'
  | 'model.name'
  | 'model.conf_threshold'
  | 'model.reject_threshold'
  | 'model.iou_threshold'
  | 'model.target_latency_ms';

export type SettingsErrors = Partial<Record<SettingsFieldKey, string>>;

export function defaultDraft(modelName = ''): SettingsDraft {
  return {
    camera: { ...DEFAULT_CAMERA },
    model: { name: modelName, ...DEFAULT_MODEL_TUNING },
  };
}

const isWhole = (value: number) => Number.isInteger(value);
const inRange = (value: number, min: number, max: number) => Number.isFinite(value) && value >= min && value <= max;

/** Field-level messages. An empty object means the draft can be applied. */
export function validateSettings(draft: SettingsDraft, modelNames: readonly string[] = []): SettingsErrors {
  const errors: SettingsErrors = {};
  const { camera, model } = draft;

  if (!isWhole(camera.index) || !inRange(camera.index, SETTING_LIMITS.index.min, SETTING_LIMITS.index.max)) {
    errors['camera.index'] = `Use a whole number from ${SETTING_LIMITS.index.min} to ${SETTING_LIMITS.index.max}.`;
  }
  const preset = RESOLUTION_PRESETS.some((p) => p.width === camera.width && p.height === camera.height);
  if (!preset) {
    errors['camera.resolution'] = 'Choose one of the resolution presets.';
  }
  if (!isWhole(camera.fps) || !inRange(camera.fps, SETTING_LIMITS.fps.min, SETTING_LIMITS.fps.max)) {
    errors['camera.fps'] = `Use a whole number from ${SETTING_LIMITS.fps.min} to ${SETTING_LIMITS.fps.max} frames per second.`;
  }

  if (!model.name || (modelNames.length > 0 && !modelNames.includes(model.name))) {
    errors['model.name'] = 'Choose a model from the list.';
  }
  const unitMessage = `Use a value from ${SETTING_LIMITS.unit.min} to ${SETTING_LIMITS.unit.max}.`;
  if (!inRange(model.conf_threshold, SETTING_LIMITS.unit.min, SETTING_LIMITS.unit.max)) {
    errors['model.conf_threshold'] = unitMessage;
  }
  if (!inRange(model.reject_threshold, SETTING_LIMITS.unit.min, SETTING_LIMITS.unit.max)) {
    errors['model.reject_threshold'] = unitMessage;
  }
  if (!inRange(model.iou_threshold, SETTING_LIMITS.unit.min, SETTING_LIMITS.unit.max)) {
    errors['model.iou_threshold'] = unitMessage;
  }
  if (!isWhole(model.target_latency_ms) || !inRange(model.target_latency_ms, SETTING_LIMITS.latency.min, SETTING_LIMITS.latency.max)) {
    errors['model.target_latency_ms'] = `Use a whole number of milliseconds from ${SETTING_LIMITS.latency.min} to ${SETTING_LIMITS.latency.max}.`;
  }
  return errors;
}

export function hasErrors(errors: SettingsErrors): boolean {
  return Object.keys(errors).length > 0;
}

/** Copies the draft into the two payloads the server expects. */
export function payloadsOf(draft: SettingsDraft): { camera: CameraConfig; model: ModelConfig } {
  return {
    camera: { ...draft.camera },
    model: { ...draft.model },
  };
}

/** Stored settings are untrusted input (another version may have written them). Anything odd falls back to defaults. */
export function parseStoredSettings(raw: string | null, fallbackModel = ''): SettingsDraft {
  const base = defaultDraft(fallbackModel);
  if (!raw) return base;
  let value: unknown;
  try {
    value = JSON.parse(raw);
  } catch {
    return base;
  }
  if (!value || typeof value !== 'object') return base;
  const data = value as { camera?: Record<string, unknown>; model?: Record<string, unknown> };
  const num = (source: Record<string, unknown> | undefined, key: string, fallback: number) => {
    const raw = source?.[key];
    return typeof raw === 'number' && Number.isFinite(raw) ? raw : fallback;
  };
  const bool = (source: Record<string, unknown> | undefined, key: string, fallback: boolean) => {
    const raw = source?.[key];
    return typeof raw === 'boolean' ? raw : fallback;
  };
  const str = (source: Record<string, unknown> | undefined, key: string, fallback: string) => {
    const raw = source?.[key];
    return typeof raw === 'string' && raw.length > 0 ? raw : fallback;
  };
  const cam = data.camera;
  const mod = data.model;
  return {
    camera: {
      index: num(cam, 'index', base.camera.index),
      width: num(cam, 'width', base.camera.width),
      height: num(cam, 'height', base.camera.height),
      fps: num(cam, 'fps', base.camera.fps),
      autofocus: bool(cam, 'autofocus', base.camera.autofocus),
      auto_exposure: bool(cam, 'auto_exposure', base.camera.auto_exposure),
    },
    model: {
      name: str(mod, 'name', base.model.name),
      conf_threshold: num(mod, 'conf_threshold', base.model.conf_threshold),
      reject_threshold: num(mod, 'reject_threshold', base.model.reject_threshold),
      iou_threshold: num(mod, 'iou_threshold', base.model.iou_threshold),
      enable_tracking: bool(mod, 'enable_tracking', base.model.enable_tracking),
      target_latency_ms: num(mod, 'target_latency_ms', base.model.target_latency_ms),
    },
  };
}

export function sameDraft(a: SettingsDraft, b: SettingsDraft): boolean {
  return JSON.stringify(a) === JSON.stringify(b);
}
