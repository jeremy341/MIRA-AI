/**
 * Draws boxes and labels on a JPEG for the compare mock, the way compare.py annotates images.
 * Browser only: it needs a canvas. Where there is none (the node test runner), it returns null
 * and the caller falls back to the plain image.
 */
import { CLASS_COLORS, CLASS_INK } from '../classes';
import type { CompareDetection } from '../types';

const MAX_SIDE = 960;

export async function annotateJpeg(source: Blob, boxes: readonly CompareDetection[]): Promise<string | null> {
  if (typeof document === 'undefined' || typeof createImageBitmap !== 'function') return null;
  try {
    const bitmap = await createImageBitmap(source);
    const scale = Math.min(1, MAX_SIDE / Math.max(bitmap.width, bitmap.height));
    const canvas = document.createElement('canvas');
    canvas.width = Math.round(bitmap.width * scale);
    canvas.height = Math.round(bitmap.height * scale);
    const context = canvas.getContext('2d');
    if (!context) {
      bitmap.close();
      return null;
    }
    context.drawImage(bitmap, 0, 0, canvas.width, canvas.height);
    bitmap.close();

    const line = Math.max(2, Math.round(canvas.width / 200));
    const fontPx = Math.max(12, Math.round(canvas.width / 48));
    context.font = `600 ${fontPx}px sans-serif`;
    context.textBaseline = 'top';
    for (const box of boxes) {
      const [x1, y1, x2, y2] = box.bbox.map((value) => value * scale);
      const color = CLASS_COLORS[box.class_name];
      context.strokeStyle = color;
      context.lineWidth = line;
      context.strokeRect(x1, y1, x2 - x1, y2 - y1);
      const label = `${box.class_name} ${box.confidence.toFixed(2)}`;
      const width = context.measureText(label).width + 8;
      const height = fontPx + 6;
      const top = Math.max(0, y1 - height);
      context.fillStyle = color;
      context.fillRect(x1, top, width, height);
      context.fillStyle = CLASS_INK[box.class_name];
      context.fillText(label, x1 + 4, top + 3);
    }
    return canvas.toDataURL('image/jpeg', 0.85);
  } catch {
    return null;
  }
}
