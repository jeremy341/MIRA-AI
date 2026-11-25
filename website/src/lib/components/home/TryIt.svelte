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
  import Chapter from '../Chapter.svelte';
  import CopyCommand from '../CopyCommand.svelte';
  import DemoVideo from '../DemoVideo.svelte';
  import DownloadsStat from '../DownloadsStat.svelte';
  import MarginNote from '../MarginNote.svelte';
  import Prose from '../Prose.svelte';
  import Rich from '../Rich.svelte';

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

<Chapter id="try" title={t.title}>
  <div class={withVideo ? 'grid gap-12 lg:grid-cols-[minmax(0,5fr)_minmax(0,6fr)] lg:gap-16' : ''}>
    <div>
      <Prose>
        <p><Rich text={t.p1} /></p>
      </Prose>
      <ol class="mt-6 max-w-[34rem] space-y-5">
        {#each t.steps as step (step.command)}
          <li>
            <p class="mb-1.5 text-[0.875rem] font-medium text-ink">{step.label}</p>
            <CopyCommand command={step.command} labels={dict.common.copy} />
          </li>
        {/each}
      </ol>
      <MarginNote inline class="mt-6 max-w-[34rem]"><Rich text={t.defaultNote} /></MarginNote>

      <div class="mt-8 max-w-[34rem] border-t border-rule pt-5">
        <h3 class="font-serif text-title text-ink">{t.downloadsTitle}</h3>
        <DownloadsStat {lang} labels={downloadsLabels} />
      </div>
    </div>
    {#if withVideo}
      <div class="min-w-0">
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
</Chapter>
