<script lang="ts" module>
  /*
    Demo video: DemoVideo renders nothing (and the layout closes up) until it gets a video.
    To add it, fill `src` (a file under /static) or `youtubeId` below. See website/README.md.
  */
  const DEMO_VIDEO = {
    src: undefined as string | undefined,
    poster: undefined as string | undefined,
    captionsSrc: undefined as string | undefined,
    youtubeId: undefined as string | undefined
  };
</script>

<script lang="ts">
  import type { Dictionary } from '$i18n';
  import { localePath, type Locale } from '$i18n/config';
  import { hasDemoVideo } from '$lib/demo-video';
  import CopyCommand from '../CopyCommand.svelte';
  import DemoVideo from '../DemoVideo.svelte';
  import DownloadsStat from '../DownloadsStat.svelte';
  import Rich from '../Rich.svelte';
  import HomeSection from './HomeSection.svelte';

  let { lang, dict }: { lang: Locale; dict: Dictionary } = $props();

  const t = $derived(dict.home.tryit);
  const withVideo = hasDemoVideo(DEMO_VIDEO);
  const downloadsLabels = $derived({
    title: t.downloadsTitle,
    allTime: t.downloadsAllTime,
    last30: t.downloadsLast30,
    honest: t.downloadsHonest,
    status: {
      checking: t.status.checking,
      live: t.status.live,
      cached: t.status.cached,
      fallback: t.status.fallback
    },
    statusLong: {
      checking: t.status.checkingLong,
      live: t.status.liveLong,
      cached: t.status.cachedLong,
      fallback: t.status.fallbackLong
    }
  });
</script>

<HomeSection id="try" title={t.title} tone="tint" align="start">
  <div class="grid grid-cols-[minmax(0,1fr)] items-start gap-8 lg:grid-cols-[minmax(0,7fr)_minmax(0,5fr)] lg:gap-14">
    <div class="min-w-0 overflow-hidden rounded-2xl bg-night text-white shadow-[var(--shadow-overlay)]">
      <div aria-hidden="true" class="flex items-center gap-2 border-b border-white/10 px-5 py-3.5">
        <span class="size-3 rounded-full bg-white/25"></span>
        <span class="size-3 rounded-full bg-white/25"></span>
        <span class="size-3 rounded-full bg-white/25"></span>
      </div>
      <ol class="space-y-5 p-5 sm:p-7">
        {#each t.steps as step (step.command)}
          <li>
            <p class="mb-2 font-mono text-[0.8125rem] text-white/75"><span aria-hidden="true" class="mr-2">#</span>{step.label}</p>
            <CopyCommand command={step.command} labels={dict.common.copy} tone="night" />
          </li>
        {/each}
      </ol>
    </div>

    <div class="min-w-0">
      <p class="text-[1.125rem] leading-[1.65] text-ink-soft"><Rich text={t.p1} /></p>
      <p class="mt-5 border-l-2 border-brand pl-3 text-[0.9375rem] leading-[1.55] text-ink-soft">
        <Rich text={t.defaultNote} />
      </p>
      <a href={localePath(lang, '/docs')} class="btn btn-primary mt-7">{dict.nav.docs}</a>
      <div class="card mt-8 p-5 sm:p-6">
        <h3 class="text-[1.0625rem] font-bold text-ink">{t.downloadsTitle}</h3>
        <DownloadsStat {lang} labels={downloadsLabels} />
      </div>
    </div>

    {#if withVideo}
      <div class="min-w-0 lg:col-span-2">
        <DemoVideo
          {...DEMO_VIDEO}
          captionsLang={lang}
          labels={{
            title: t.video.title,
            videoCaption: t.video.videoCaption,
            unsupported: t.video.unsupported,
            playLabel: t.video.playLabel,
            privacyNote: t.video.privacyNote
          }}
        >
          {#snippet caption()}<Rich text={t.video.videoCaption} {lang} />{/snippet}
        </DemoVideo>
      </div>
    {/if}
  </div>
</HomeSection>
