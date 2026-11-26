<script lang="ts">
  import type { Dictionary } from '$i18n';
  import type { Locale } from '$i18n/config';
  import { HF_URL } from '$lib/site';
  import type { HfDownloads } from '$lib/use-hf-downloads.svelte';
  import DownloadsStat from '../DownloadsStat.svelte';

  /** The download count as its own band, directly under the hero. */
  let { lang, dict, source }: { lang: Locale; dict: Dictionary; source: HfDownloads } = $props();

  const t = $derived(dict.home.downloads);
  const labels = $derived({
    ...t,
    statusLong: {
      checking: t.status.checkingLong,
      live: t.status.liveLong,
      cached: t.status.cachedLong,
      fallback: t.status.fallbackLong
    }
  });
</script>

<section id="downloads" aria-labelledby="downloads-title" class="scroll-mt-20 bg-tint pt-12 pb-16 sm:pt-16 sm:pb-24">
  <div class="shell text-center">
    <h2 id="downloads-title" class="section-title mx-auto max-w-[24ch] text-brand-ink">{t.title}</h2>
    <div class="mt-6">
      <DownloadsStat {lang} {labels} size="large" {source} />
    </div>
    <a href={HF_URL} target="_blank" rel="noopener noreferrer" class="btn btn-primary btn-lg mt-8">
      {t.cta}<span class="sr-only"> {dict.common.opensInNewTab}</span>
    </a>
  </div>
</section>
