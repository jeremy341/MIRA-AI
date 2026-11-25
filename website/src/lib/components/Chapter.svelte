<script lang="ts">
  import type { Snippet } from 'svelte';
  import Canvas from './Canvas.svelte';
  import Heading from './Heading.svelte';

  /**
   * A page section: a thin rule across the page, then a serif heading and the content on the canvas.
   * The heading is always an h2 and names the landmark.
   */
  let {
    id,
    title,
    class: className = '',
    children
  }: { id: string; title: string; class?: string; children: Snippet } = $props();
</script>

<section {id} aria-labelledby="{id}-title" class="border-t border-rule pb-12 pt-12 sm:pb-16 sm:pt-16 {className}">
  <Canvas>
    <Heading as="h2" size="heading" id="{id}-title" class="max-w-[30ch] text-ink">{title}</Heading>
    <div class="mt-6 sm:mt-8">
      {@render children()}
    </div>
  </Canvas>
</section>
