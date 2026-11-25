<script lang="ts">
  import type { Snippet } from 'svelte';

  /**
   * Horizontal scroll container for wide tables. It is a labelled, focusable region, so keyboard users can
   * scroll it with the arrow keys and the page itself never scrolls sideways.
   */
  let { label, class: className = '', children }: { label: string; class?: string; children: Snippet } = $props();
</script>

<!-- svelte-ignore a11y_no_noninteractive_tabindex: a scrollable region must be focusable so keyboard users can scroll it -->
<div role="region" aria-label={label} tabindex="0" class="relative max-w-full overflow-x-auto overscroll-x-contain {className}">
  {@render children()}
</div>
