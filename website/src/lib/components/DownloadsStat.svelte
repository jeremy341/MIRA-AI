<script lang="ts" module>
  import type { DownloadStatus } from '$lib/use-hf-downloads.svelte';

  export type DownloadsLabels = {
    title: string;
    allTime: string;
    /** Contains {n}. */
    last30: string;
    honest: string;
    status: Record<DownloadStatus, string>;
    statusLong: Record<DownloadStatus, string>;
  };
</script>

<script lang="ts">
  import { onMount, untrack } from 'svelte';
  import type { Locale } from '$i18n/config';
  import { formatInt } from '$i18n/format';
  import { HfDownloads } from '$lib/use-hf-downloads.svelte';

  /**
   * The live Hugging Face download figure. The static HTML contains the built-in fallback value; in the
   * browser the number is replaced by the live count (or the last good one from localStorage). The 30-day
   * figure only appears for a live answer. It counts file fetches, not people, and says so.
   *
   * `size="large"` is the homepage band. Pass `source` when the page already runs a counter, so that one
   * request feeds every place that shows it.
   */
  let {
    lang,
    labels,
    size = 'compact',
    source
  }: { lang: Locale; labels: DownloadsLabels; size?: 'compact' | 'large'; source?: HfDownloads } = $props();

  const own = new HfDownloads();
  const downloads = $derived(source ?? own);
  onMount(() => (source ? undefined : own.start()));

  const last30Parts = $derived(labels.last30.split('{n}'));

  /** The number on screen. It counts across to a new value, unless the reader prefers reduced motion. */
  let counted = $state(untrack(() => downloads.value));
  $effect(() => {
    const target = downloads.value;
    const from = untrack(() => counted);
    if (from === target) return;
    if (matchMedia('(prefers-reduced-motion: reduce)').matches) {
      counted = target;
      return;
    }
    const began = performance.now();
    let frame = requestAnimationFrame(function step(now) {
      const left = 1 - Math.min(1, Math.max(0, (now - began) / 900));
      counted = Math.round(target - (target - from) * left ** 3);
      if (left > 0) frame = requestAnimationFrame(step);
    });
    return () => cancelAnimationFrame(frame);
  });
</script>

{#if size === 'large'}
  <div data-status={downloads.status} class="text-center">
    <p class="inline-flex items-center gap-2.5 text-[0.9375rem] font-semibold text-ink-soft" aria-hidden="true">
      <span class="dot" class:is-live={downloads.status === 'live'}></span>
      {labels.status[downloads.status]}
    </p>
    <p class="big tabular mt-3 text-brand-ink">{formatInt(lang, counted)}</p>
    <p class="mt-4 text-[clamp(1.25rem,1rem+1vw,1.75rem)] font-semibold text-ink">{labels.allTime}</p>
    {#if downloads.last30Days !== null}
      <p class="mt-5 inline-block rounded-lg bg-app px-4 py-2 text-[1.0625rem] text-ink-soft">
        {last30Parts[0]}<strong class="tabular font-bold text-brand-ink">{formatInt(lang, downloads.last30Days)}</strong
        >{last30Parts[1]}
      </p>
    {/if}
    <p class="mx-auto mt-5 max-w-[60ch] text-[0.875rem] leading-[1.55] text-ink-soft">{labels.honest}</p>
    <span role="status" class="sr-only">{labels.statusLong[downloads.status]}</span>
  </div>
{:else}
  <div data-status={downloads.status} class="mt-2 text-sm text-muted-foreground">
    <p class="flex flex-wrap items-baseline gap-x-3 gap-y-1">
      <span><strong class="font-mono tabular text-ink">{formatInt(lang, counted)}</strong> {labels.allTime}</span>
      {#if downloads.last30Days !== null}
        <span>{last30Parts[0]}<span class="font-mono tabular text-ink">{formatInt(lang, downloads.last30Days)}</span>{last30Parts[1]}</span>
      {/if}
      <span>{labels.status[downloads.status]}</span>
    </p>
    <p class="mt-1">{labels.honest}</p>
    <span role="status" class="sr-only">{labels.statusLong[downloads.status]} {labels.honest}</span>
  </div>
{/if}

<style>
  .big {
    font-size: clamp(4.25rem, 1rem + 15vw, 12rem);
    font-weight: 800;
    line-height: 1;
    letter-spacing: -0.045em;
  }
  .dot {
    width: 0.625rem;
    height: 0.625rem;
    border-radius: 50%;
    background: #8a93ab;
  }
  .dot.is-live {
    background: #1f9d62;
    animation: pulse 2.4s ease-out infinite;
  }
  @keyframes pulse {
    0% {
      box-shadow: 0 0 0 0 rgb(31 157 98 / 55%);
    }
    70%,
    100% {
      box-shadow: 0 0 0 0.6rem rgb(31 157 98 / 0%);
    }
  }
  @media (prefers-reduced-motion: reduce) {
    .dot.is-live {
      animation: none;
    }
  }
</style>
