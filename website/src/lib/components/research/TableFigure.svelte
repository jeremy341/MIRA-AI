<script lang="ts">
  import type { Snippet } from 'svelte';

  /**
   * A numbered table the way a paper sets it: the caption sits ABOVE the table (figures keep theirs below).
   * Local variant of Figure, which puts the caption below.
   */
  let {
    id,
    n,
    label,
    caption,
    class: className = '',
    children
  }: {
    id?: string;
    n: number;
    /** Localised word: "Table" or "Tabelle". */
    label: string;
    caption: Snippet | string;
    class?: string;
    children: Snippet;
  } = $props();
</script>

<figure {id} class="min-w-0 {className}">
  <figcaption class="mb-3 flex max-w-[72ch] gap-3 text-[0.875rem] leading-[1.5] text-ink-soft">
    <span class="shrink-0 font-sans font-semibold text-ink">{label}&nbsp;{n}</span>
    <span>{#if typeof caption === 'string'}{caption}{:else}{@render caption()}{/if}</span>
  </figcaption>
  {@render children()}
</figure>
