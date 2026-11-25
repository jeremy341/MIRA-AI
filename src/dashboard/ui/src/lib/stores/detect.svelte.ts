import type { LiveDetection } from '../realtime/video-state';

export type DetectSource = 'camera' | 'image';

export interface ImageResult {
  /** A data URI of the resized original. Boxes are drawn on top in its pixel space. */
  src: string;
  fileName: string;
  detections: LiveDetection[];
  /** The confidence the run used. A change in the slider means the result is stale. */
  threshold: number;
  receivedAt: number;
}

/** Detect page state that survives navigating away and back. Actions live in pages/Detect/detect-actions.ts. */
class DetectStore {
  source = $state<DetectSource>('camera');
  /** Camera: filters the preview list. Image: the threshold for the next run. */
  minConfidence = $state(0.25);
  imageResult = $state.raw<ImageResult | null>(null);
  /** The file behind the last result, so "Run again" can send it without opening the picker. */
  imageFile = $state.raw<File | null>(null);
  imageBusy = $state(false);
  imageError = $state<string | null>(null);
  streamAction = $state<'idle' | 'starting' | 'stopping'>('idle');
  streamError = $state<string | null>(null);
  connectBusy = $state(false);
  loadBusy = $state(false);
  sessionName = $state('');
  sessionBusy = $state(false);
  sessionError = $state<string | null>(null);
}

export const detect = new DetectStore();
