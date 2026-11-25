<script lang="ts" module>
  export type DemoVideoLabels = {
    /** Accessible title of the video or the embedded player. */
    title: string;
    /** Caption under a real video (plain text; use the `caption` snippet for markup). */
    videoCaption: string;
    /** Fallback text inside <video> for browsers that cannot play it. */
    unsupported: string;
    /** Text of the button that loads the YouTube player. */
    playLabel: string;
    /** Tells the visitor that YouTube is only contacted after the button is pressed. */
    privacyNote: string;
  };
</script>

<script lang="ts">
  import type { Snippet } from 'svelte';
  import { isYouTubeId } from '$lib/demo-video';
  import YouTubeEmbed from './YouTubeEmbed.svelte';

  /**
   * Demo video slot.
   *
   * - `src` set: a native `<video controls preload="metadata">` (optionally with a poster and a captions track).
   * - `youtubeId` set (and no `src`): a play button; the youtube-nocookie.com iframe is created on click.
   * - Neither: nothing is rendered (no box, no heading, no "coming soon"). Use `hasDemoVideo()` from
   *   `$lib/demo-video` to close up the surrounding layout.
   */
  let {
    src,
    poster,
    captionsSrc,
    captionsLang = 'en',
    youtubeId,
    labels,
    caption,
    class: className = ''
  }: {
    /** Path to a self-hosted video under /static, e.g. "/media/mira-live-demo.mp4". Takes priority over `youtubeId`. */
    src?: string;
    /** Poster image under /static shown before playback. */
    poster?: string;
    /** WebVTT captions for the self-hosted video (recommended for speech or on-screen text, WCAG 1.2.2). */
    captionsSrc?: string;
    /** Language of the captions file, e.g. "en" or "de". */
    captionsLang?: string;
    /** 11-character YouTube video id. Click to load: nothing is requested from Google at page load. */
    youtubeId?: string;
    labels: DemoVideoLabels;
    /** Optional caption with markup; defaults to `labels.videoCaption`. */
    caption?: Snippet;
    class?: string;
  } = $props();

  const validYoutubeId = $derived(isYouTubeId(youtubeId) ? youtubeId : undefined);
</script>

{#if src}
  <figure class="w-full {className}">
    <video
      class="block aspect-video w-full border border-ink bg-ink object-contain"
      controls
      preload="metadata"
      playsinline
      {poster}
      aria-label={labels.title}
    >
      <source {src} />
      {#if captionsSrc}
        <track kind="captions" src={captionsSrc} srclang={captionsLang} label={captionsLang} default />
      {/if}
      {labels.unsupported}
    </video>
    <figcaption class="mt-3 text-[0.875rem] text-ink-soft">
      {#if caption}{@render caption()}{:else}{labels.videoCaption}{/if}
    </figcaption>
  </figure>
{:else if validYoutubeId}
  <figure class="w-full {className}">
    <YouTubeEmbed id={validYoutubeId} title={labels.title} playLabel={labels.playLabel} privacyNote={labels.privacyNote} />
    <figcaption class="mt-3 text-[0.875rem] text-ink-soft">
      {#if caption}{@render caption()}{:else}{labels.videoCaption}{/if}
    </figcaption>
  </figure>
{/if}
