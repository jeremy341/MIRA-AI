/**
 * Rules for the Models page, pure. The limits mirror the server: compare takes 2 to 4 distinct models and
 * a JPEG or PNG up to 8 MB; benchmark takes 1 to 6 models, `max_images` 1 to 5000, confidence 0.05 to 1.
 * Covered by models-logic.test.ts.
 */
import type { BenchmarkStatus, CompareWinnerHint } from '../../lib/types';

export const COMPARE_MIN_MODELS = 2;
export const COMPARE_MAX_MODELS = 4;
export const BENCHMARK_MIN_MODELS = 1;
export const BENCHMARK_MAX_MODELS = 6;
export const IMAGE_LIMIT_BYTES = 8 * 1024 * 1024;
export const MAX_IMAGES_RANGE = { min: 1, max: 5000 } as const;
export const CONFIDENCE_RANGE = { min: 0.05, max: 1 } as const;
export const DEFAULT_MAX_IMAGES = 100;

export type ModelsErrors = Partial<Record<'models' | 'file' | 'confidence' | 'dataset' | 'maxImages', string>>;

export interface FileLike {
  name: string;
  size: number;
  type?: string;
}

/** Adds or removes a model from a selection, never above `max`. Returns the same list when nothing changes. */
export function toggleModel(selected: readonly string[], name: string, max: number): string[] {
  if (selected.includes(name)) return selected.filter((item) => item !== name);
  if (selected.length >= max) return [...selected];
  return [...selected, name];
}

/** True when the selection can still take another model. */
export function canSelectMore(selected: readonly string[], max: number): boolean {
  return selected.length < max;
}

export function isImageFile(file: FileLike): boolean {
  const type = (file.type ?? '').toLowerCase();
  if (type === 'image/jpeg' || type === 'image/png') return true;
  return /\.(jpe?g|png)$/i.test(file.name);
}

export function validateCompare(input: { models: readonly string[]; file: FileLike | null; confidence: number }): ModelsErrors {
  const errors: ModelsErrors = {};
  if (input.models.length < COMPARE_MIN_MODELS || input.models.length > COMPARE_MAX_MODELS) {
    errors.models = `Choose ${COMPARE_MIN_MODELS} to ${COMPARE_MAX_MODELS} models.`;
  }
  if (!input.file) {
    errors.file = 'Choose an image.';
  } else if (!isImageFile(input.file)) {
    errors.file = 'Choose a JPEG or PNG image.';
  } else if (input.file.size > IMAGE_LIMIT_BYTES) {
    errors.file = 'Choose an image no larger than 8 MB.';
  } else if (input.file.size === 0) {
    errors.file = 'That file is empty.';
  }
  if (!isValidConfidence(input.confidence)) errors.confidence = 'Confidence must be between 0.05 and 1.';
  return errors;
}

export function validateBenchmark(input: {
  models: readonly string[];
  dataset: string;
  confidence: number;
  maxImages: number | null;
}): ModelsErrors {
  const errors: ModelsErrors = {};
  if (input.models.length < BENCHMARK_MIN_MODELS || input.models.length > BENCHMARK_MAX_MODELS) {
    errors.models = `Choose ${BENCHMARK_MIN_MODELS} to ${BENCHMARK_MAX_MODELS} models.`;
  }
  const dataset = input.dataset.trim();
  if (dataset && /\.[a-z0-9]+$/i.test(dataset) && !/\.ya?ml$/i.test(dataset)) {
    errors.dataset = 'Use a YAML file (dataset.yaml) or a folder.';
  }
  if (!isValidConfidence(input.confidence)) errors.confidence = 'Confidence must be between 0.05 and 1.';
  if (input.maxImages === null || !Number.isInteger(input.maxImages) || input.maxImages < MAX_IMAGES_RANGE.min || input.maxImages > MAX_IMAGES_RANGE.max) {
    errors.maxImages = `Enter a whole number from ${MAX_IMAGES_RANGE.min} to ${MAX_IMAGES_RANGE.max}.`;
  }
  return errors;
}

export function hasModelsErrors(errors: ModelsErrors): boolean {
  return Object.keys(errors).length > 0;
}

function isValidConfidence(value: number): boolean {
  return Number.isFinite(value) && value >= CONFIDENCE_RANGE.min - 1e-9 && value <= CONFIDENCE_RANGE.max + 1e-9;
}

/** A metric as text: three decimals by default. Null, NaN and missing values show a dash, never a number. */
export function formatMetric(value: number | null | undefined, digits = 3): string {
  if (typeof value !== 'number' || !Number.isFinite(value)) return '-';
  return value.toFixed(digits);
}

/** The winner hint as plain sentences. A null highest-confidence model means no model found anything. */
export function winnerLines(hint: CompareWinnerHint): string[] {
  return [
    `Fastest: ${hint.fastest_model}.`,
    `Most objects: ${hint.most_objects_model}.`,
    hint.highest_avg_confidence_model
      ? `Highest average confidence: ${hint.highest_avg_confidence_model}.`
      : 'Highest average confidence: none, because no model found an object.',
  ];
}

/** A run that is still queued or running cannot be deleted. */
export function isBenchmarkDeletable(status: BenchmarkStatus): boolean {
  return status !== 'queued' && status !== 'running';
}

export function benchmarkStatusLabel(status: BenchmarkStatus): string {
  switch (status) {
    case 'queued':
      return 'Queued';
    case 'running':
      return 'Running';
    case 'completed':
      return 'Completed';
    case 'failed':
      return 'Failed';
    case 'cancelled':
      return 'Cancelled';
  }
}
