import type { ClassName } from './types';

export const CLASS_LABELS: Record<ClassName, string> = {
  glass: 'Glass',
  metal: 'Metal',
  paper: 'Paper',
  plastic: 'Plastic',
  trash: 'Trash',
};

/** Bin colours as hex, for canvas drawing. Mirrors the --class-* tokens in styles/tokens.css. */
export const CLASS_COLORS: Record<ClassName, string> = {
  glass: '#2a7f45',
  metal: '#66778a',
  paper: '#2457c5',
  plastic: '#f2c230',
  trash: '#3a3a3a',
};

/** Label text colour that stays readable on each class fill. */
export const CLASS_INK: Record<ClassName, string> = {
  glass: '#ffffff',
  metal: '#ffffff',
  paper: '#ffffff',
  plastic: '#161616',
  trash: '#ffffff',
};

export function isClassName(value: unknown): value is ClassName {
  return value === 'glass' || value === 'metal' || value === 'paper' || value === 'plastic' || value === 'trash';
}
