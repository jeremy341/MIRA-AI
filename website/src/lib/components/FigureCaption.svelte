<script lang="ts">
  import type { Snippet } from 'svelte';

  let { n, label, children }: { n: number; label: string; children: Snippet } = $props();
</script>

<!-- svelte-ignore a11y_figcaption_parent: always rendered as the direct child of the <figure> in Figure.svelte / DetectionFigure.svelte -->
<figcaption class="mt-3 flex max-w-[72ch] gap-3 text-[0.875rem] leading-[1.5] text-ink-soft">
  <span class="shrink-0 font-sans font-semibold text-ink">{label}&nbsp;{n}</span>
  <span>{@render children()}</span>
</figcaption>
