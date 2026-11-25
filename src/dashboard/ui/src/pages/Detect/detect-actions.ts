/**
 * Actions behind the Detect page buttons. Each one sets a busy flag, calls the API, reports the
 * outcome (inline or as a toast), and refreshes the server status when it is done.
 */
import { ApiError, api, describeError, isAborted, isConflict, isRouteMissing } from '../../lib/api';
import { defaultSessionName } from '../../lib/format';
import { live } from '../../lib/stores/live.svelte';
import { detect } from '../../lib/stores/detect.svelte';
import { settings } from '../../lib/stores/settings.svelte';
import { system } from '../../lib/stores/system.svelte';
import { toasts } from '../../lib/stores/toasts.svelte';
import { normalizeDetections } from '../../lib/realtime/video-state';
import { defaultDraft } from '../../lib/settings-model';
import type { ModelConfig } from '../../lib/types';
import { imageContentType, streamStartHint, validateImageFile } from './detect-logic';

export async function connectCamera(): Promise<void> {
  detect.connectBusy = true;
  try {
    await api.legacy.initializeCamera(settings.saved.camera);
    toasts.success('Camera connected.');
  } catch (error) {
    toasts.error(`The camera could not be opened: ${describeError(error, 'check the settings and try again.')}`);
  } finally {
    detect.connectBusy = false;
    await system.refreshStatus();
  }
}

/** The model the Detect page loads: the saved one, or the recommended model until Settings is applied. */
export function modelToLoad(): ModelConfig | null {
  if (settings.saved.model.name) return settings.saved.model;
  const fallback = system.models?.find((m) => m.recommended) ?? system.models?.[0];
  return fallback ? defaultDraft(fallback.name).model : null;
}

export async function loadSavedModel(): Promise<void> {
  const config = modelToLoad();
  if (!config) {
    toasts.info('No model is available. Add one to the models folder, then reload.');
    return;
  }
  detect.loadBusy = true;
  try {
    await api.legacy.loadModel(config);
    // The first model loaded becomes the saved one, so the readiness steps and the top bar agree.
    if (!settings.saved.model.name) {
      settings.markApplied({ camera: settings.saved.camera, model: config });
    }
    toasts.success(`Model ${config.name} loaded.`);
  } catch (error) {
    toasts.error(describeError(error, 'The model could not be loaded.'));
  } finally {
    detect.loadBusy = false;
    await system.refreshStatus();
  }
}

export async function startStream(): Promise<void> {
  detect.streamAction = 'starting';
  detect.streamError = null;
  try {
    await api.legacy.startStream();
    toasts.success('Stream starting. Waiting for the first frame.');
  } catch (error) {
    // A 409 with `missing` names the steps still to do. Those are shown next to the buttons, not as a toast.
    if (isConflict(error) && error instanceof ApiError && error.missing.length > 0) {
      detect.streamError = streamStartHint(error.missing);
    } else {
      detect.streamError = describeError(error, 'The stream could not be started. Check the camera connection.');
    }
  } finally {
    detect.streamAction = 'idle';
    await system.refreshStatus();
  }
}

export async function stopStream(): Promise<void> {
  detect.streamAction = 'stopping';
  detect.streamError = null;
  try {
    await api.legacy.stopStream();
    toasts.info('Stream stopped.');
  } catch (error) {
    toasts.error(describeError(error, 'The stream did not stop cleanly.'));
  } finally {
    detect.streamAction = 'idle';
    await system.refreshStatus();
  }
}

/** Sends one image and shows the returned picture with its boxes. */
export async function detectImage(file: File): Promise<void> {
  const problem = validateImageFile(file);
  if (problem) {
    detect.imageError = problem;
    return;
  }
  detect.imageError = null;
  detect.imageBusy = true;
  const threshold = detect.minConfidence;
  try {
    const result = await api.legacy.detectImage(file, imageContentType(file), threshold);
    detect.imageFile = file;
    detect.imageResult = {
      src: result.image,
      fileName: file.name,
      detections: normalizeDetections(result.detections),
      threshold,
      receivedAt: Date.now(),
    };
  } catch (error) {
    if (isAborted(error)) return;
    detect.imageError = describeError(error, 'The image could not be checked.');
  } finally {
    detect.imageBusy = false;
  }
}

export async function startSession(): Promise<void> {
  detect.sessionBusy = true;
  detect.sessionError = null;
  const name = detect.sessionName.trim() || defaultSessionName();
  try {
    const session = await api.v1.createSession({
      name,
      source: detect.source === 'camera' ? 'camera' : 'image',
      model_name: settings.saved.model.name || undefined,
    });
    detect.sessionName = '';
    toasts.success(`Session "${session.name}" started.`);
    await system.refreshSession();
  } catch (error) {
    if (isRouteMissing(error)) {
      system.sessions = 'unavailable';
    } else {
      detect.sessionError = describeError(error, 'The session could not be started.');
    }
  } finally {
    detect.sessionBusy = false;
  }
}

export async function stopSession(id: string): Promise<void> {
  detect.sessionBusy = true;
  detect.sessionError = null;
  try {
    await api.v1.stopSession(id);
    toasts.success('Session stopped.');
  } catch (error) {
    detect.sessionError = describeError(error, 'The session could not be stopped.');
  } finally {
    detect.sessionBusy = false;
    await system.refreshSession();
  }
}

export function reconnectLive(): void {
  live.retry();
}
