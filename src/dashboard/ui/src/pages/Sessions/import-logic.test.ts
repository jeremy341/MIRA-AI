import { describe, expect, it } from 'vitest';
import {
  VIDEO_LIMIT_BYTES,
  hasErrors,
  isValidConfidence,
  isValidStride,
  parseWholeNumber,
  validateFolderImport,
  validateImageUpload,
  validateVideoImport,
} from './import-logic';

const common = { modelName: 'mira_exp019_int8.tflite', confidence: 0.25, name: '' };
const video = (name: string, size = 1024) => ({ name, size });

describe('video import validation', () => {
  it('accepts a supported video with a model, confidence and stride in range', () => {
    expect(hasErrors(validateVideoImport({ ...common, file: video('bin.MP4'), frameStride: 5 }))).toBe(false);
  });

  it('rejects other types, empty files and files over the limit', () => {
    expect(validateVideoImport({ ...common, file: video('clip.gif'), frameStride: 5 }).file).toMatch(/MP4, AVI, MOV or MKV/);
    expect(validateVideoImport({ ...common, file: video('clip.mkv', 0), frameStride: 5 }).file).toMatch(/empty/);
    expect(validateVideoImport({ ...common, file: video('clip.mkv', VIDEO_LIMIT_BYTES + 1), frameStride: 5 }).file).toMatch(/500 MB/);
  });

  it('asks for a file when none is chosen', () => {
    expect(validateVideoImport({ ...common, file: null, frameStride: 5 }).file).toMatch(/Choose a video/);
  });

  it('checks the frame stride is a whole number from 1 to 120', () => {
    expect(validateVideoImport({ ...common, file: video('a.avi'), frameStride: 0 }).stride).toBeDefined();
    expect(validateVideoImport({ ...common, file: video('a.avi'), frameStride: 121 }).stride).toBeDefined();
    expect(validateVideoImport({ ...common, file: video('a.avi'), frameStride: 2.5 }).stride).toBeDefined();
    expect(validateVideoImport({ ...common, file: video('a.avi'), frameStride: 120 }).stride).toBeUndefined();
  });

  it('needs a model and a confidence between 0.05 and 1', () => {
    expect(validateVideoImport({ ...common, modelName: '', file: video('a.avi'), frameStride: 5 }).model).toBeDefined();
    expect(validateVideoImport({ ...common, confidence: 0.01, file: video('a.avi'), frameStride: 5 }).confidence).toBeDefined();
    expect(validateVideoImport({ ...common, confidence: 1.2, file: video('a.avi'), frameStride: 5 }).confidence).toBeDefined();
  });
});

describe('image upload validation', () => {
  it('accepts up to 200 JPEG or PNG files', () => {
    const files = Array.from({ length: 200 }, (_, i) => video(`img-${i}.jpeg`));
    expect(hasErrors(validateImageUpload({ ...common, files }))).toBe(false);
  });

  it('refuses an empty list, too many files and any file that is not an image', () => {
    expect(validateImageUpload({ ...common, files: [] }).files).toMatch(/at least one/);
    const many = Array.from({ length: 201 }, (_, i) => video(`img-${i}.png`));
    expect(validateImageUpload({ ...common, files: many }).files).toMatch(/at most 200/);
    expect(validateImageUpload({ ...common, files: [video('a.png'), video('notes.txt')] }).files).toBe(
      'notes.txt is not a JPEG or PNG image.',
    );
  });
});

describe('folder import validation', () => {
  it('needs a non-empty path without control characters', () => {
    expect(validateFolderImport({ ...common, folder: '   ' }).folder).toMatch(/Enter the folder path/);
    expect(validateFolderImport({ ...common, folder: 'C:/bins\u0007' }).folder).toMatch(/cannot be used/);
    expect(hasErrors(validateFolderImport({ ...common, folder: ' C:/bins/samples ' }))).toBe(false);
  });
});

describe('import number helpers', () => {
  it('reads whole numbers only', () => {
    expect(parseWholeNumber(' 12 ')).toBe(12);
    expect(parseWholeNumber('1.5')).toBeNull();
    expect(parseWholeNumber('abc')).toBeNull();
    expect(parseWholeNumber('')).toBeNull();
  });

  it('checks stride and confidence ranges at the edges', () => {
    expect(isValidStride(1)).toBe(true);
    expect(isValidStride(0)).toBe(false);
    expect(isValidConfidence(0.05)).toBe(true);
    expect(isValidConfidence(0.049)).toBe(false);
    expect(isValidConfidence(1)).toBe(true);
    expect(isValidConfidence(Number.NaN)).toBe(false);
  });
});
