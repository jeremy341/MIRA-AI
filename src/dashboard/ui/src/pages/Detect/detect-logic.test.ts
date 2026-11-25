import { describe, expect, it } from 'vitest';
import {
  confidenceLabel,
  imageContentType,
  MAX_IMAGE_BYTES,
  previewMessage,
  readinessSteps,
  streamStartHint,
  validateImageFile,
  type ReadinessInput,
} from './detect-logic';

const base: ReadinessInput = {
  source: 'camera',
  cameraReady: false,
  modelLoaded: false,
  streaming: false,
  savedModel: null,
  loadedModelName: null,
};

describe('readiness steps for the camera', () => {
  it('asks for the camera first, then a model, then the stream', () => {
    const steps = readinessSteps(base);
    expect(steps.map((s) => s.key)).toEqual(['camera', 'model', 'stream']);
    expect(steps[0]).toMatchObject({ state: 'next', action: 'connect' });
    expect(steps[1]).toMatchObject({ action: 'settings', state: 'waiting' });
    expect(steps[2]).toMatchObject({ state: 'waiting', action: null });
  });

  it('offers to load the saved model when one is saved', () => {
    const steps = readinessSteps({ ...base, cameraReady: true, savedModel: 'mira_exp018.pt' });
    expect(steps[1]).toMatchObject({ action: 'load', state: 'next' });
    expect(steps[1].detail).toContain('mira_exp018.pt');
  });

  it('allows the start button once camera and model are ready', () => {
    const steps = readinessSteps({ ...base, cameraReady: true, modelLoaded: true, loadedModelName: 'm.pt' });
    expect(steps[0].state).toBe('done');
    expect(steps[1]).toMatchObject({ state: 'done', detail: 'm.pt' });
    expect(steps[2]).toMatchObject({ action: 'start', state: 'next' });
  });

  it('offers stop while the stream runs', () => {
    const steps = readinessSteps({ ...base, cameraReady: true, modelLoaded: true, streaming: true });
    expect(steps[2]).toMatchObject({ action: 'stop', state: 'done', actionLabel: 'Stop stream' });
  });
});

describe('readiness steps for an image', () => {
  it('does not need the camera and reports the stream must be stopped', () => {
    const steps = readinessSteps({ ...base, source: 'image', modelLoaded: true });
    expect(steps[0].state).toBe('optional');
    expect(steps[2]).toMatchObject({ state: 'done', title: 'Ready for an image' });
    const streaming = readinessSteps({ ...base, source: 'image', modelLoaded: true, streaming: true });
    expect(streaming[2]).toMatchObject({ action: 'stop' });
  });
});

describe('image validation', () => {
  it('accepts JPEG and PNG up to 8 MB', () => {
    expect(validateImageFile({ type: 'image/jpeg', name: 'a.jpg', size: 1000 })).toBeNull();
    expect(validateImageFile({ type: 'image/png', name: 'a.png', size: MAX_IMAGE_BYTES })).toBeNull();
  });

  it('rejects other types, empty files and files over 8 MB', () => {
    expect(validateImageFile({ type: 'image/gif', name: 'a.gif', size: 10 })).toBe('Choose a JPEG or PNG image.');
    expect(validateImageFile({ type: 'image/png', name: 'a.png', size: 0 })).toMatch(/empty/);
    expect(validateImageFile({ type: 'image/png', name: 'a.png', size: MAX_IMAGE_BYTES + 1 })).toBe('Choose an image no larger than 8 MB.');
  });

  it('accepts a file with no browser type when the extension says JPEG or PNG', () => {
    expect(validateImageFile({ type: '', name: 'photo.JPG', size: 10 })).toBeNull();
    expect(validateImageFile({ type: '', name: 'notes.txt', size: 10 })).not.toBeNull();
  });

  it('picks the content type to send', () => {
    expect(imageContentType({ type: 'image/png', name: 'x', size: 1 })).toBe('image/png');
    expect(imageContentType({ type: '', name: 'x.png', size: 1 })).toBe('image/png');
    expect(imageContentType({ type: '', name: 'x.jpg', size: 1 })).toBe('image/jpeg');
  });
});

describe('preview wording', () => {
  const idle = { cameraReady: true, modelLoaded: true, streaming: false, hasFrame: false, stale: false };

  it('explains what is missing before the first frame', () => {
    expect(previewMessage({ ...idle, cameraReady: false }).title).toBe('Camera not connected');
    expect(previewMessage({ ...idle, modelLoaded: false }).title).toBe('No model loaded');
    expect(previewMessage(idle).title).toBe('Ready to stream');
  });

  it('separates a stream that is starting from one with no frames', () => {
    expect(previewMessage({ ...idle, streaming: true }).title).toBe('Waiting for the first frame');
    expect(previewMessage({ ...idle, streaming: true, stale: true }).title).toBe('No frames yet');
    expect(previewMessage({ ...idle, streaming: true, hasFrame: true }).title).toBe('Live');
  });
});

describe('small helpers', () => {
  it('formats confidence and explains missing prerequisites', () => {
    expect(confidenceLabel(0.25)).toBe('25%');
    expect(streamStartHint([])).toBeNull();
    expect(streamStartHint(['camera', 'model'])).toBe('Before you start: connect the camera and load a model.');
  });
});
