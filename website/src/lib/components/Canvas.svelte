<script lang="ts">
  import type { Snippet } from 'svelte';

  /** The wide canvas: nearly edge to edge, with Orchard's page gutter (20px, 58px from md). Reading text uses Prose. */
  let {
    as = 'div',
    class: className = '',
    children,
    ...rest
  }: { as?: string; class?: string; children?: Snippet; [key: string]: unknown } = $props();
</script>

<svelte:element this={as} class="mx-auto w-full max-w-[112rem] px-5 md:px-[3.625rem] {className}" {...rest}>
  {@render children?.()}
</svelte:element>
