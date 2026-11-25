<script lang="ts">
  import { CLASS_COLORS, CLASS_INK, CLASS_LABELS } from '../classes';
  import type { LiveDetection } from '../realtime/video-state';

  interface Props {
    /** A data URI (or a bare base64 JPEG, which is wrapped). The canvas shows nothing without it. */
    src: string;
    detections: readonly LiveDetection[];
    /** Boxes below this confidence are not drawn. */
    minConfidence: number;
    /** Accessible name, for example "Live preview: 2 objects". */
    label: string;
    /** Called once the image size is known, so the parent can report it. */
    onsize?: (width: number, height: number) => void;
  }

  let { src, detections, minConfidence, label, onsize }: Props = $props();

  let canvas: HTMLCanvasElement | undefined = $state();
  let image = $state.raw<HTMLImageElement | null>(null);
  let loadError = $state<string | null>(null);

  // Decode the picture before drawing, so a slow decode never shows a half-drawn frame.
  $effect(() => {
    const url = src.startsWith('data:') ? src : `data:image/jpeg;base64,${src}`;
    let cancelled = false;
    loadError = null;
    const element = new Image();
    element.onload = () => {
      if (cancelled) return;
      image = element;
      onsize?.(element.naturalWidth, element.naturalHeight);
    };
    element.onerror = () => {
      if (cancelled) return;
      image = null;
      loadError = 'This picture could not be shown.';
    };
    element.src = url;
    return () => {
      cancelled = true;
      element.onload = null;
      element.onerror = null;
    };
  });

  // Draw whenever the picture, the boxes or the threshold change.
  $effect(() => {
    const element = canvas;
    const picture = image;
    if (!element || !picture) return;
    const width = picture.naturalWidth;
    const height = picture.naturalHeight;
    if (width === 0 || height === 0) return;
    element.width = width;
    element.height = height;
    const ctx = element.getContext('2d');
    if (!ctx) return;
    ctx.clearRect(0, 0, width, height);
    ctx.drawImage(picture, 0, 0, width, height);

    const stroke = Math.max(2, Math.round(width / 260));
    const fontSize = Math.max(12, Math.round(width / 55));
    ctx.font = `${fontSize}px "Space Mono", ui-monospace, monospace`;
    ctx.textBaseline = 'top';

    for (const detection of detections) {
      if (detection.confidence < minConfidence) continue;
      const [x1, y1, x2, y2] = detection.bbox;
      const w = Math.max(1, x2 - x1);
      const h = Math.max(1, y2 - y1);
      // Dark outline first, so a box stays visible on a dark belt and on a light wall.
      ctx.lineWidth = stroke + 2;
      ctx.strokeStyle = 'rgba(22, 22, 22, 0.85)';
      ctx.strokeRect(x1, y1, w, h);
      ctx.lineWidth = stroke;
      ctx.strokeStyle = CLASS_COLORS[detection.className];
      ctx.strokeRect(x1, y1, w, h);

      const text = `${CLASS_LABELS[detection.className]} ${Math.round(detection.confidence * 100)}%`;
      const padding = Math.round(fontSize * 0.3);
      const textWidth = ctx.measureText(text).width;
      const tagHeight = fontSize + padding * 2;
      const tagTop = y1 - tagHeight >= 0 ? y1 - tagHeight : y1;
      ctx.fillStyle = CLASS_COLORS[detection.className];
      ctx.fillRect(x1, tagTop, textWidth + padding * 2, tagHeight);
      ctx.fillStyle = CLASS_INK[detection.className];
      ctx.fillText(text, x1 + padding, tagTop + padding);
    }
  });
</script>

{#if loadError}
  <p class="error" role="alert">{loadError}</p>
{:else}
  <div class="frame" role="img" aria-label={label}>
    <canvas bind:this={canvas} class="canvas"></canvas>
  </div>
{/if}

<style>
  .canvas {
    display: block;
    width: 100%;
    height: auto;
    border-radius: var(--radius-control);
    background: #161616;
  }
  .error {
    padding: var(--space-4);
    color: var(--destructive);
    font-size: var(--text-small);
  }
</style>
