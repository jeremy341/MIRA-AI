/**
 * Detect page rules, pure: readiness steps, image validation and the preview wording.
 * Covered by detect-logic.test.ts. No DOM, no API calls.
 */
import type { DetectSource } from '../../lib/stores/detect.svelte';

export const MAX_IMAGE_BYTES = 8 * 1024 * 1024;
export const IMAGE_ACCEPT = 'image/jpeg,image/png';

export type StepKey = 'camera' | 'model' | 'stream';
export type StepState = 'done' | 'next' | 'waiting' | 'optional';
export type StepAction = 'connect' | 'load' | 'start' | 'stop' | 'settings';

export interface ReadinessStep {
  key: StepKey;
  title: string;
  detail: string;
  state: StepState;
  action: StepAction | null;
  actionLabel: string | null;
}

export interface ReadinessInput {
  source: DetectSource;
  cameraReady: boolean;
  modelLoaded: boolean;
  streaming: boolean;
  /** The model the Settings page last applied, or null. */
  savedModel: string | null;
  /** Shown in the model step once a model is loaded. */
  loadedModelName: string | null;
}

/** The three steps: camera, model, stream. For image files the camera step is optional. */
export function readinessSteps(input: ReadinessInput): ReadinessStep[] {
  if (input.source === 'image') {
    return [
      {
        key: 'camera',
        title: 'Camera not needed',
        detail: 'Image files do not use the camera.',
        state: 'optional',
        action: null,
        actionLabel: null,
      },
      modelStep(input),
      input.streaming
        ? {
            key: 'stream',
            title: 'Stop the stream',
            detail: 'Image detection runs only while the stream is stopped.',
            state: 'next',
            action: 'stop',
            actionLabel: 'Stop stream',
          }
        : {
            key: 'stream',
            title: 'Ready for an image',
            detail: input.modelLoaded ? 'Choose or drop a JPEG or PNG below.' : 'Load a model first.',
            state: input.modelLoaded ? 'done' : 'waiting',
            action: null,
            actionLabel: null,
          },
    ];
  }

  const cameraStep: ReadinessStep = input.cameraReady
    ? { key: 'camera', title: 'Camera ready', detail: 'Connected with the saved camera settings.', state: 'done', action: null, actionLabel: null }
    : {
        key: 'camera',
        title: 'Connect camera',
        detail: 'Uses the camera settings saved in Settings.',
        state: 'next',
        action: 'connect',
        actionLabel: 'Connect camera',
      };

  let streamStep: ReadinessStep;
  if (input.streaming) {
    streamStep = { key: 'stream', title: 'Stream running', detail: 'Detections update as frames arrive.', state: 'done', action: 'stop', actionLabel: 'Stop stream' };
  } else if (input.cameraReady && input.modelLoaded) {
    streamStep = { key: 'stream', title: 'Start stream', detail: 'Starts live detection from the camera.', state: 'next', action: 'start', actionLabel: 'Start stream' };
  } else {
    streamStep = { key: 'stream', title: 'Start stream', detail: 'Needs the camera and a model first.', state: 'waiting', action: null, actionLabel: null };
  }

  return [cameraStep, modelStep(input), streamStep];
}

function modelStep(input: ReadinessInput): ReadinessStep {
  if (input.modelLoaded) {
    return {
      key: 'model',
      title: 'Model loaded',
      detail: input.loadedModelName ?? 'A model is loaded on the server.',
      state: 'done',
      action: null,
      actionLabel: null,
    };
  }
  if (input.savedModel) {
    return {
      key: 'model',
      title: 'Load model',
      detail: `Loads ${input.savedModel} with the saved settings.`,
      state: 'next',
      action: 'load',
      actionLabel: 'Load model',
    };
  }
  return {
    key: 'model',
    title: 'Choose a model',
    detail: 'Pick a model in Settings first.',
    state: 'waiting',
    action: 'settings',
    actionLabel: 'Open Settings',
  };
}

export interface ImageCheckInput {
  type: string;
  name: string;
  size: number;
}

/** Returns a sentence for the person when the file cannot be used, or null when it can. */
export function validateImageFile(file: ImageCheckInput): string | null {
  const lower = file.name.toLowerCase();
  const typeOk = file.type === 'image/jpeg' || file.type === 'image/png';
  const extensionOk = /\.(jpe?g|png)$/.test(lower);
  if (!typeOk && !(file.type === '' && extensionOk)) {
    return 'Choose a JPEG or PNG image.';
  }
  if (file.size === 0) return 'That file is empty. Choose another image.';
  if (file.size > MAX_IMAGE_BYTES) return 'Choose an image no larger than 8 MB.';
  return null;
}

/** The content type to send with the raw body. Falls back to the extension when the browser sent none. */
export function imageContentType(file: ImageCheckInput): 'image/jpeg' | 'image/png' {
  if (file.type === 'image/png' || file.type === 'image/jpeg') return file.type;
  return /\.png$/i.test(file.name) ? 'image/png' : 'image/jpeg';
}

export interface PreviewInput {
  cameraReady: boolean;
  modelLoaded: boolean;
  streaming: boolean;
  hasFrame: boolean;
  /** No frame for a while during a running stream. */
  stale: boolean;
}

export function previewMessage(input: PreviewInput): { title: string; description: string } {
  if (!input.cameraReady) {
    return { title: 'Camera not connected', description: 'Connect the camera to see the preview here.' };
  }
  if (!input.modelLoaded) {
    return { title: 'No model loaded', description: 'Load a model to start detecting.' };
  }
  if (!input.streaming) {
    return { title: 'Ready to stream', description: 'Press Start stream to see live boxes here.' };
  }
  if (!input.hasFrame) {
    return input.stale
      ? { title: 'No frames yet', description: 'Still waiting. Check that the camera is free and the server log shows no errors.' }
      : { title: 'Waiting for the first frame', description: 'The camera is starting up.' };
  }
  return { title: 'Live', description: '' };
}

export function confidenceLabel(value: number): string {
  return `${Math.round(value * 100)}%`;
}

export function objectCountLabel(count: number): string {
  return count === 1 ? '1 object' : `${count} objects`;
}

/** Turns an error from starting the stream into what to do next. */
export function streamStartHint(missing: readonly string[]): string | null {
  if (missing.length === 0) return null;
  const parts = missing.map((item) => (item === 'camera' ? 'connect the camera' : 'load a model'));
  return `Before you start: ${parts.join(' and ')}.`;
}
