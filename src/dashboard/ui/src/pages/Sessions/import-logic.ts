/**
 * Validation for the Import panel, pure. The rules mirror the server (batch.py, CONTRACT section 7):
 * video types and size, frame stride 1 to 120, confidence 0.05 to 1, up to 200 uploaded images,
 * JPEG or PNG only for images, and a folder path that is not empty. The server stays the authority;
 * these checks only spare a round trip. Covered by import-logic.test.ts.
 */

export const VIDEO_EXTENSIONS = ['mp4', 'avi', 'mov', 'mkv'] as const;
export const VIDEO_LIMIT_BYTES = 500 * 1024 * 1024;
export const IMAGE_EXTENSIONS = ['jpg', 'jpeg', 'png'] as const;
export const IMAGE_LIMIT_COUNT = 200;
export const FOLDER_LIMIT_COUNT = 2000;
export const STRIDE_RANGE = { min: 1, max: 120 } as const;
export const CONFIDENCE_RANGE = { min: 0.05, max: 1 } as const;

/** Errors keyed by field name. An empty object means the input can be sent. */
export type ImportErrors = Partial<Record<'file' | 'files' | 'folder' | 'model' | 'stride' | 'confidence' | 'name', string>>;

export interface FileLike {
  name: string;
  size: number;
}

export interface ImportCommon {
  modelName: string;
  confidence: number;
  name: string;
}

export function extensionOf(name: string): string {
  const dot = name.lastIndexOf('.');
  return dot < 0 ? '' : name.slice(dot + 1).toLowerCase();
}

export function isVideoFile(file: FileLike): boolean {
  return (VIDEO_EXTENSIONS as readonly string[]).includes(extensionOf(file.name));
}

export function isImageFile(file: FileLike): boolean {
  return (IMAGE_EXTENSIONS as readonly string[]).includes(extensionOf(file.name));
}

export function isValidStride(value: number): boolean {
  return Number.isInteger(value) && value >= STRIDE_RANGE.min && value <= STRIDE_RANGE.max;
}

export function isValidConfidence(value: number): boolean {
  return Number.isFinite(value) && value >= CONFIDENCE_RANGE.min - 1e-9 && value <= CONFIDENCE_RANGE.max + 1e-9;
}

/** The shared fields: a model must be chosen, confidence in range, and the name (optional) is short. */
function commonErrors(input: ImportCommon): ImportErrors {
  const errors: ImportErrors = {};
  if (!input.modelName) errors.model = 'Choose a model.';
  if (!isValidConfidence(input.confidence)) errors.confidence = 'Confidence must be between 0.05 and 1.';
  if (input.name.trim().length > 120) errors.name = 'Keep the name under 120 characters.';
  return errors;
}

export function validateVideoImport(input: ImportCommon & { file: FileLike | null; frameStride: number }): ImportErrors {
  const errors = commonErrors(input);
  if (!input.file) {
    errors.file = 'Choose a video file.';
  } else if (!isVideoFile(input.file)) {
    errors.file = 'Choose an MP4, AVI, MOV or MKV video.';
  } else if (input.file.size > VIDEO_LIMIT_BYTES) {
    errors.file = 'Choose a video no larger than 500 MB.';
  } else if (input.file.size === 0) {
    errors.file = 'That file is empty.';
  }
  if (!isValidStride(input.frameStride)) errors.stride = 'Frame stride must be a whole number from 1 to 120.';
  return errors;
}

export function validateImageUpload(input: ImportCommon & { files: readonly FileLike[] }): ImportErrors {
  const errors = commonErrors(input);
  if (input.files.length === 0) {
    errors.files = 'Choose at least one JPEG or PNG image.';
  } else if (input.files.length > IMAGE_LIMIT_COUNT) {
    errors.files = `Choose at most ${IMAGE_LIMIT_COUNT} images at a time.`;
  } else {
    const wrong = input.files.find((file) => !isImageFile(file));
    if (wrong) errors.files = `${wrong.name} is not a JPEG or PNG image.`;
  }
  return errors;
}

/** A folder on the machine running the dashboard. The server checks that it exists and holds images. */
export function validateFolderImport(input: ImportCommon & { folder: string }): ImportErrors {
  const errors = commonErrors(input);
  const folder = input.folder.trim();
  if (!folder) errors.folder = 'Enter the folder path.';
  else if (/[\u0000-\u001f]/.test(folder)) errors.folder = 'The folder path has characters that cannot be used.';
  return errors;
}

export function hasErrors(errors: ImportErrors): boolean {
  return Object.keys(errors).length > 0;
}

/** Reads a text field as a whole number, or null when it is not one. */
export function parseWholeNumber(text: string): number | null {
  const trimmed = text.trim();
  if (!/^-?\d+$/.test(trimmed)) return null;
  return Number(trimmed);
}
