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
  import type { Locale } from '$i18n/config';
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

<HomeSection id="try" title={t.title}>
  <div class={withVideo ? 'grid grid-cols-[minmax(0,1fr)] gap-3 lg:grid-cols-[minmax(0,5fr)_minmax(0,6fr)]' : 'grid grid-cols-[minmax(0,1fr)] gap-3 lg:grid-cols-2'}>
    <div class="rounded-2xl border border-rule bg-surface p-5 shadow-[var(--shadow-raised)] sm:p-7">
      <p class="max-w-[56ch] text-[1rem] leading-[1.65] text-ink-soft"><Rich text={t.p1} /></p>
      <ol class="mt-6 max-w-[34rem] space-y-5">
        {#each t.steps as step (step.command)}
          <li>
            <p class="mb-1.5 text-[0.875rem] font-medium text-ink">{step.label}</p>
            <CopyCommand command={step.command} labels={dict.common.copy} />
          </li>
        {/each}
      </ol>
      <p class="mt-6 max-w-[34rem] border-l-2 border-accent pl-3 text-[0.875rem] leading-[1.5] text-ink-soft">
        <Rich text={t.defaultNote} />
      </p>
    </div>
    <div class="rounded-2xl border border-rule bg-surface p-5 shadow-[var(--shadow-raised)] sm:p-7">
      <h3 class="text-[1.0625rem] font-semibold text-ink">{t.downloadsTitle}</h3>
      <DownloadsStat {lang} labels={downloadsLabels} />
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
