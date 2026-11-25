<script lang="ts">
  import type { Snippet } from 'svelte';
  import Canvas from '../Canvas.svelte';
  import Heading from '../Heading.svelte';

  /**
   * Chapter with the section number in front of the title, in mono, so "section 7" in the text can be found.
   * Local variant of Chapter (whose title is a plain string).
   */
  let {
    id,
    n,
    title,
    class: className = '',
    children
  }: { id: string; n: number; title: string; class?: string; children: Snippet } = $props();
</script>

<section {id} aria-labelledby="{id}-title" class="border-t border-rule pb-12 pt-12 sm:pb-16 sm:pt-16 {className}">
  <Canvas>
    <Heading as="h2" size="heading" id="{id}-title" class="max-w-[30ch] text-ink">
      <span class="mr-3 font-mono text-[0.55em] font-normal text-muted-foreground sm:mr-4">{n}</span>{title}
    </Heading>
    <div class="mt-6 sm:mt-8">
      {@render children()}
    </div>
  </Canvas>
</section>
