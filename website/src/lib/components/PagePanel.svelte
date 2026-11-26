<script lang="ts">
  import type { Snippet } from 'svelte';
  import Wave from './Wave.svelte';

  /**
   * The blue band for pages that sit beside a sidebar (docs and research front pages): a contained panel with the
   * wave along its bottom edge. Anything white inside it needs the `card on-light` classes.
   */
  let {
    titleId,
    title,
    eyebrow,
    class: className = '',
    children
  }: {
    titleId: string;
    title: string;
    eyebrow?: string;
    class?: string;
    children: Snippet;
  } = $props();
</script>

<header class="on-brand overflow-hidden rounded-t-3xl {className}">
  <div class="px-5 pt-8 pb-6 sm:px-10 sm:pt-12 sm:pb-8">
    {#if eyebrow}
      <p class="font-mono text-[0.8125rem] tracking-[0.08em] text-on-brand-soft uppercase">{eyebrow}</p>
    {/if}
    <h1 id={titleId} class="panel-title {eyebrow ? 'mt-3' : ''}">{title}</h1>
    {@render children()}
  </div>
  <Wave fill="var(--app)" />
</header>

<style>
  .panel-title {
    max-width: 18ch;
    font-size: clamp(2.25rem, 1.4rem + 2.8vw, 3.5rem);
    font-weight: 600;
    line-height: 1.1;
    letter-spacing: -0.028em;
    overflow-wrap: break-word;
    hyphens: auto;
  }
</style>
