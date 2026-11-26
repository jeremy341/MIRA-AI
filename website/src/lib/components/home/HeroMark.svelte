<!--
  The MIRA logo at hero size, in 3D. The flat SVG below has the same paths as static/mira.svg, without the dark
  tile. It is what the static HTML contains, and it stays for readers who prefer reduced motion or save data, and for
  browsers without hardware-accelerated WebGL. Everyone else gets the three.js version, loaded after the page has painted.
  Decorative, so it is hidden from assistive technology.
-->
<script lang="ts">
  import { onMount } from 'svelte';
  import MarkPaths from '../MarkPaths.svelte';

  /** pending: the 3D logo may still come. 3d: it is on screen. flat: the SVG is the logo. */
  let mode = $state<'pending' | '3d' | 'flat'>('pending');
  let reason = $state<string | undefined>(undefined);
  let host = $state<HTMLElement | null>(null);
  let canvas = $state<HTMLCanvasElement | null>(null);

  /** If the 3D logo takes longer than this, the flat one has already faded in (see the CSS delay). */
  const FLAT_APPEARS_MS = 1600;

  onMount(() => {
    const element = host;
    const target = canvas;
    if (!element || !target) return;
    if (matchMedia('(prefers-reduced-motion: reduce)').matches) {
      mode = 'flat';
      reason = 'reduced-motion';
      return;
    }
    if ((navigator as Navigator & { connection?: { saveData?: boolean } }).connection?.saveData) {
      mode = 'flat';
      reason = 'save-data';
      return;
    }

    const mounted = performance.now();
    const cleanups: (() => void)[] = [];
    let gone = false;
    const flat = (why: string) => {
      mode = 'flat';
      reason = why;
      for (const cleanup of cleanups.splice(0)) cleanup();
    };

    async function load() {
      try {
        const { createHeroScene } = await import('$lib/hero3d/scene');
        if (gone || !element || !target) return;
        const hero = element.closest('section') ?? element;
        const scene = createHeroScene({
          canvas: target,
          // A late arrival would blow the already visible flat logo apart, so it starts assembled instead.
          entrance: performance.now() - mounted < FLAT_APPEARS_MS,
          spread: () => Math.max(0, -hero.getBoundingClientRect().top) / (hero.clientHeight * 0.7),
          onFirstFrame: () => (mode = '3d'),
          onContextLost: () => flat('context-lost')
        });
        cleanups.push(() => scene.dispose());

        let visible = true;
        const run = () => scene.setRunning(visible && !document.hidden);
        const observer = new IntersectionObserver((entries) => {
          visible = entries.some((entry) => entry.isIntersecting);
          run();
        });
        observer.observe(element);
        const sizes = new ResizeObserver(() => scene.resize());
        sizes.observe(target);
        // The logo follows the pointer only while the pointer is on it, and turns back when it leaves.
        const move = (event: PointerEvent) => {
          const box = element.getBoundingClientRect();
          scene.setPointer(
            ((event.clientX - box.left) / box.width) * 2 - 1,
            ((event.clientY - box.top) / box.height) * 2 - 1
          );
        };
        const leave = () => scene.setPointer(0, 0);
        element.addEventListener('pointermove', move, { passive: true });
        element.addEventListener('pointerleave', leave);
        element.addEventListener('pointercancel', leave);
        document.addEventListener('visibilitychange', run);
        cleanups.push(() => {
          observer.disconnect();
          sizes.disconnect();
          element.removeEventListener('pointermove', move);
          element.removeEventListener('pointerleave', leave);
          element.removeEventListener('pointercancel', leave);
          document.removeEventListener('visibilitychange', run);
        });
        run();
      } catch {
        flat('no-webgl');
      }
    }

    // three.js is large. It must not compete with the first paint, which waits for the web fonts, so it is
    // requested once the page has loaded, the text can be drawn and the browser reports its first paint.
    let waiting: (() => void) | undefined;
    const firstPaint = () =>
      new Promise<void>((resolve) => {
        if (!window.PerformanceObserver?.supportedEntryTypes?.includes('paint')) return resolve();
        const done = () => {
          observer.disconnect();
          clearTimeout(limit);
          resolve();
        };
        const observer = new PerformanceObserver((list) => {
          if (list.getEntries().some((entry) => entry.name === 'first-contentful-paint')) done();
        });
        // A tab opened in the background reports no paint, so there is a time limit.
        const limit = setTimeout(done, 3000);
        observer.observe({ type: 'paint', buffered: true });
      });
    const afterPaint = async () => {
      await document.fonts.ready;
      await firstPaint();
      if (gone) return;
      if ('requestIdleCallback' in window) {
        const handle = requestIdleCallback(() => void load(), { timeout: 600 });
        waiting = () => cancelIdleCallback(handle);
      } else {
        const handle = setTimeout(() => void load(), 100);
        waiting = () => clearTimeout(handle);
      }
    };
    if (document.readyState === 'complete') afterPaint();
    else addEventListener('load', afterPaint, { once: true });

    return () => {
      gone = true;
      removeEventListener('load', afterPaint);
      waiting?.();
      for (const cleanup of cleanups.splice(0)) cleanup();
    };
  });
</script>

<div bind:this={host} class="hero-logo" data-mode={mode} data-reason={reason} aria-hidden="true">
  <svg class="flat" viewBox="3 3 26 26" focusable="false">
    <MarkPaths />
  </svg>
  <!-- 150% of the logo box (BLEED in hero3d/scene.ts), centred on it. -->
  <canvas bind:this={canvas}></canvas>
</div>

<style>
  .hero-logo {
    position: relative;
    aspect-ratio: 1;
    width: 100%;
  }
  .flat,
  canvas {
    position: absolute;
    display: block;
    transition: opacity 0.35s ease;
  }
  .flat {
    inset: 0;
    width: 100%;
    height: 100%;
  }
  canvas {
    top: -25%;
    left: -25%;
    width: 150%;
    height: 150%;
    opacity: 0;
    pointer-events: none;
  }
  /* While the 3D logo loads, the flat one waits, so it does not flash up just before the entrance. */
  [data-mode='pending'] .flat {
    animation: appear 0.4s 1.6s both;
  }
  [data-mode='3d'] .flat {
    opacity: 0;
  }
  [data-mode='3d'] canvas {
    opacity: 1;
  }
  [data-mode='flat'] canvas {
    display: none;
  }
  @keyframes appear {
    from {
      opacity: 0;
    }
  }
  @media (prefers-reduced-motion: reduce) {
    [data-mode='pending'] .flat {
      animation: none;
    }
  }
</style>
