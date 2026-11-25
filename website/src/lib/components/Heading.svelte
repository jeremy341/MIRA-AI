<script lang="ts">
  import type { Snippet } from 'svelte';

  const SIZE_CLASS = {
    hero: 'text-hero',
    display: 'text-display',
    heading: 'text-heading',
    title: 'text-title'
  } as const;

  /**
   * Heading in the serif. Pick the semantic level with `as` and the look with `size`.
   * hero: Home headline. display: page title. heading: section title. title: sub-section or row title.
   */
  let {
    as = 'h2',
    size = 'heading',
    id,
    class: className = '',
    children
  }: {
    as?: 'h1' | 'h2' | 'h3' | 'h4';
    size?: keyof typeof SIZE_CLASS;
    id?: string;
    class?: string;
    children: Snippet;
  } = $props();
</script>

<svelte:element this={as} {id} class="font-serif {SIZE_CLASS[size]} {className}">
  {@render children()}
</svelte:element>
