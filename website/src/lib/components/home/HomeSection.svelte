<script lang="ts">
  import type { Snippet } from 'svelte';
  import Canvas from '../Canvas.svelte';
  import Heading from '../Heading.svelte';

  /**
   * A homepage section in the docs style: a heading (always an h2, it names the landmark), an optional lede, then
   * the content as cards. No rules across the page; the space between sections does the separating.
   */
  let {
    id,
    title,
    lede,
    class: className = '',
    children
  }: { id: string; title: string; lede?: string; class?: string; children: Snippet } = $props();
</script>

<section {id} aria-labelledby="{id}-title" class="scroll-mt-20 py-12 sm:py-16 {className}">
  <Canvas>
    <div class="mx-auto max-w-[68rem]">
      <Heading as="h2" size="heading" id="{id}-title" class="max-w-[28ch] text-ink">{title}</Heading>
      {#if lede}<p class="mt-3 max-w-[56ch] text-[1.0625rem] leading-[1.6] text-ink-soft">{lede}</p>{/if}
      <div class="mt-8">
        {@render children()}
      </div>
    </div>
  </Canvas>
</section>
