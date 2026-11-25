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
  import { onMount } from 'svelte';
  import type { Locale } from '$i18n/config';
  import { formatInt } from '$i18n/format';
  import { HfDownloads } from '$lib/use-hf-downloads.svelte';

  /**
   * The live Hugging Face download figure. The static HTML contains the built-in fallback value; in the
   * browser the number is replaced by the live count (or the last good one from localStorage). The 30-day
   * figure only appears for a live answer. It counts file fetches, not people, and says so.
   */
  let { lang, labels }: { lang: Locale; labels: DownloadsLabels } = $props();

  const downloads = new HfDownloads();
  onMount(() => downloads.start());

  const last30Parts = $derived(labels.last30.split('{n}'));
</script>

<div data-status={downloads.status} class="mt-2 text-sm text-muted-foreground">
  <p class="flex flex-wrap items-baseline gap-x-3 gap-y-1">
    <span><strong class="font-mono tabular text-ink">{formatInt(lang, downloads.value)}</strong> {labels.allTime}</span>
    {#if downloads.last30Days !== null}
      <span>{last30Parts[0]}<span class="font-mono tabular text-ink">{formatInt(lang, downloads.last30Days)}</span>{last30Parts[1]}</span>
    {/if}
    <span>{labels.status[downloads.status]}</span>
  </p>
  <p class="mt-1">{labels.honest}</p>
  <span role="status" class="sr-only">{labels.statusLong[downloads.status]} {labels.honest}</span>
</div>
