<script lang="ts">
  import type { Snippet } from 'svelte';
  import FigureCaption from './FigureCaption.svelte';

  /** A numbered figure: the content (photo, chart, table), then a caption that starts with its number. */
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
    /** Localised word: "Figure" or "Abbildung" (or "Table"). */
    label: string;
    caption: Snippet | string;
    class?: string;
    children: Snippet;
  } = $props();
</script>

<figure {id} class="min-w-0 {className}">
  {@render children()}
  <FigureCaption {n} {label}>
    {#if typeof caption === 'string'}{caption}{:else}{@render caption()}{/if}
  </FigureCaption>
</figure>
