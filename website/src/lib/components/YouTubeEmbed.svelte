<script lang="ts">
  import { tick } from 'svelte';
  import { youtubeEmbedUrl } from '$lib/demo-video';

  /**
   * Click to load. Until the visitor presses the button there is NO iframe, so no request goes to Google at page
   * load. The press is the consent: it creates the iframe (youtube-nocookie.com, autoplay) and moves focus into it.
   */
  let {
    id,
    title,
    playLabel,
    privacyNote,
    class: className = ''
  }: {
    id: string;
    /** Accessible title of the player. */
    title: string;
    /** Visible text of the play button, e.g. "Play video". */
    playLabel: string;
    /** Says that nothing is loaded from YouTube before the button is pressed. */
    privacyNote: string;
    class?: string;
  } = $props();

  let loaded = $state(false);
  let frame = $state<HTMLIFrameElement>();
  const noteId = $derived(`${id}-note`);

  async function load() {
    loaded = true;
    await tick();
    frame?.focus();
  }
</script>

<div class="aspect-video w-full overflow-hidden border border-ink bg-ink {className}">
  {#if loaded}
    <iframe
      bind:this={frame}
      class="size-full"
      src={youtubeEmbedUrl(id, true)}
      {title}
      allow="autoplay; encrypted-media; picture-in-picture"
      allowfullscreen
      referrerpolicy="strict-origin-when-cross-origin"
    ></iframe>
  {:else}
    <div class="flex size-full flex-col items-center justify-center gap-3 p-5 text-center">
      <button
        type="button"
        onclick={load}
        aria-label="{playLabel}: {title}"
        aria-describedby={noteId}
        class="inline-flex h-12 items-center justify-center rounded-lg border border-surface px-6 text-base font-medium text-surface transition-colors hover:bg-accent-soft hover:text-accent-strong"
      >
        {playLabel}
      </button>
      <p id={noteId} class="max-w-[34ch] text-[0.875rem] leading-snug text-surface/80">{privacyNote}</p>
    </div>
  {/if}
</div>
