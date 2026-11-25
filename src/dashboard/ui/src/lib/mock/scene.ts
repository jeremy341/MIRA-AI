/**
 * Generated camera frames for the mock stream. Drawn once on a canvas in the browser and reused,
 * so the mock costs little CPU. The UI draws the mock boxes over these frames.
 * Browser only: outside a DOM this returns no frames and the mock socket sends none.
 */
import { rng } from './fixtures';

const WIDTH = 640;
const HEIGHT = 360;
const FRAME_COUNT = 4;

let pool: Promise<string[]> | null = null;

/** Base64 JPEG frames (no data: prefix), the same encoding the server uses on `/ws/video`. */
export function scenePool(): Promise<string[]> {
  if (!pool) {
    pool = Promise.resolve()
      .then(() => drawFrames(FRAME_COUNT))
      .catch(() => []);
  }
  return pool;
}

function drawFrames(count: number): string[] {
  if (typeof document === 'undefined') return [];
  const frames: string[] = [];
  for (let index = 0; index < count; index += 1) {
    const canvas = document.createElement('canvas');
    canvas.width = WIDTH;
    canvas.height = HEIGHT;
    const ctx = canvas.getContext('2d');
    if (!ctx) return [];
    const random = rng(31 + index * 17);

    // Background: a cool grey floor with a lighter wall at the top.
    const wall = ctx.createLinearGradient(0, 0, 0, HEIGHT);
    wall.addColorStop(0, '#d9dde3');
    wall.addColorStop(0.45, '#c8cdd4');
    wall.addColorStop(0.46, '#7d8290');
    wall.addColorStop(1, '#5c616d');
    ctx.fillStyle = wall;
    ctx.fillRect(0, 0, WIDTH, HEIGHT);

    // Conveyor belt across the middle.
    ctx.fillStyle = '#2f333b';
    ctx.fillRect(0, 170, WIDTH, 70);
    ctx.fillStyle = '#41464f';
    for (let x = 0; x < WIDTH; x += 36) {
      ctx.fillRect(x + ((index * 9) % 36), 172, 18, 66);
    }

    // Items on the belt: rounded shapes in bin-like colours.
    const palette = ['#2a7f45', '#66778a', '#2457c5', '#e7b72a', '#5a5a5a'];
    for (let i = 0; i < 7; i += 1) {
      const w = 40 + random() * 60;
      const h = 30 + random() * 50;
      const x = random() * (WIDTH - w);
      const y = 150 + random() * 60;
      ctx.fillStyle = palette[Math.floor(random() * palette.length)];
      ctx.globalAlpha = 0.92;
      roundRect(ctx, x, y, w, h, 8);
      ctx.fill();
      ctx.globalAlpha = 1;
    }

    ctx.fillStyle = 'rgba(31,31,31,0.55)';
    ctx.font = '12px monospace';
    ctx.fillText('MOCK FEED, generated frame', 12, HEIGHT - 12);

    const url = canvas.toDataURL('image/jpeg', 0.8);
    frames.push(url.slice(url.indexOf(',') + 1));
  }
  return frames;
}

function roundRect(ctx: CanvasRenderingContext2D, x: number, y: number, w: number, h: number, r: number): void {
  ctx.beginPath();
  ctx.moveTo(x + r, y);
  ctx.arcTo(x + w, y, x + w, y + h, r);
  ctx.arcTo(x + w, y + h, x, y + h, r);
  ctx.arcTo(x, y + h, x, y, r);
  ctx.arcTo(x, y, x + w, y, r);
  ctx.closePath();
}
