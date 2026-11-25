import { describe, expect, it } from 'vitest';
import {
  IMAGE_LIMIT_BYTES,
  canSelectMore,
  formatMetric,
  hasModelsErrors,
  isBenchmarkDeletable,
  isImageFile,
  toggleModel,
  validateBenchmark,
  validateCompare,
  winnerLines,
} from './models-logic';

const image = (name: string, size = 2048, type = 'image/jpeg') => ({ name, size, type });

describe('model selection', () => {
  it('adds and removes models without going over the limit', () => {
    expect(toggleModel([], 'a.pt', 2)).toEqual(['a.pt']);
    expect(toggleModel(['a.pt'], 'b.pt', 2)).toEqual(['a.pt', 'b.pt']);
    expect(toggleModel(['a.pt', 'b.pt'], 'c.pt', 2)).toEqual(['a.pt', 'b.pt']);
    expect(toggleModel(['a.pt', 'b.pt'], 'a.pt', 2)).toEqual(['b.pt']);
  });

  it('says when another model still fits', () => {
    expect(canSelectMore(['a', 'b', 'c'], 4)).toBe(true);
    expect(canSelectMore(['a', 'b', 'c', 'd'], 4)).toBe(false);
  });
});

describe('compare validation', () => {
  it('accepts 2 to 4 models with a JPEG or PNG image', () => {
    expect(hasModelsErrors(validateCompare({ models: ['a', 'b'], file: image('bin.jpg'), confidence: 0.25 }))).toBe(false);
    expect(hasModelsErrors(validateCompare({ models: ['a', 'b', 'c', 'd'], file: image('bin.png', 10, 'image/png'), confidence: 1 }))).toBe(false);
  });

  it('needs at least two models and at most four', () => {
    expect(validateCompare({ models: ['a'], file: image('x.jpg'), confidence: 0.25 }).models).toMatch(/2 to 4/);
    expect(validateCompare({ models: ['a', 'b', 'c', 'd', 'e'], file: image('x.jpg'), confidence: 0.25 }).models).toMatch(/2 to 4/);
  });

  it('rejects other image types, empty files and files over 8 MB', () => {
    expect(validateCompare({ models: ['a', 'b'], file: image('x.gif', 5, 'image/gif'), confidence: 0.25 }).file).toMatch(/JPEG or PNG/);
    expect(validateCompare({ models: ['a', 'b'], file: image('x.jpg', 0), confidence: 0.25 }).file).toMatch(/empty/);
    expect(validateCompare({ models: ['a', 'b'], file: image('x.jpg', IMAGE_LIMIT_BYTES + 1), confidence: 0.25 }).file).toMatch(/8 MB/);
    expect(validateCompare({ models: ['a', 'b'], file: null, confidence: 0.25 }).file).toMatch(/Choose an image/);
  });

  it('recognises the file type from the extension when the browser gives none', () => {
    expect(isImageFile({ name: 'frame.PNG', size: 1 })).toBe(true);
    expect(isImageFile({ name: 'frame.webp', size: 1 })).toBe(false);
  });
});

describe('benchmark validation', () => {
  const base = { models: ['a'], dataset: '', confidence: 0.25, maxImages: 100 };

  it('accepts the defaults', () => {
    expect(hasModelsErrors(validateBenchmark(base))).toBe(false);
    expect(hasModelsErrors(validateBenchmark({ ...base, dataset: 'data/dataset.yaml' }))).toBe(false);
    expect(hasModelsErrors(validateBenchmark({ ...base, dataset: 'data/images' }))).toBe(false);
  });

  it('limits the models to 1 to 6', () => {
    expect(validateBenchmark({ ...base, models: [] }).models).toMatch(/1 to 6/);
    expect(validateBenchmark({ ...base, models: ['a', 'b', 'c', 'd', 'e', 'f', 'g'] }).models).toMatch(/1 to 6/);
  });

  it('wants a YAML file for a dataset file, not another extension', () => {
    expect(validateBenchmark({ ...base, dataset: 'labels.csv' }).dataset).toMatch(/YAML/);
  });

  it('keeps max images to whole numbers from 1 to 5000', () => {
    expect(validateBenchmark({ ...base, maxImages: 0 }).maxImages).toBeDefined();
    expect(validateBenchmark({ ...base, maxImages: 5001 }).maxImages).toBeDefined();
    expect(validateBenchmark({ ...base, maxImages: 12.5 }).maxImages).toBeDefined();
    expect(validateBenchmark({ ...base, maxImages: null }).maxImages).toBeDefined();
    expect(validateBenchmark({ ...base, maxImages: 5000 }).maxImages).toBeUndefined();
  });
});

describe('metric text', () => {
  it('shows a dash for anything that is not a number, never an invented value', () => {
    expect(formatMetric(null)).toBe('-');
    expect(formatMetric(undefined)).toBe('-');
    expect(formatMetric(Number.NaN)).toBe('-');
    expect(formatMetric(0)).toBe('0.000');
    expect(formatMetric(0.81234)).toBe('0.812');
    expect(formatMetric(58.2, 1)).toBe('58.2');
  });
});

describe('winner wording', () => {
  it('names the models and says when no model found anything', () => {
    const lines = winnerLines({ fastest_model: 'b.tflite', most_objects_model: 'a.pt', highest_avg_confidence_model: null, note: '' });
    expect(lines[0]).toBe('Fastest: b.tflite.');
    expect(lines[2]).toMatch(/none/);
  });
});

describe('benchmark deletion', () => {
  it('refuses to delete a queued or running run', () => {
    expect(isBenchmarkDeletable('queued')).toBe(false);
    expect(isBenchmarkDeletable('running')).toBe(false);
    expect(isBenchmarkDeletable('cancelled')).toBe(true);
    expect(isBenchmarkDeletable('completed')).toBe(true);
  });
});
