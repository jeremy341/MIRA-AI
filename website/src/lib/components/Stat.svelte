<script lang="ts">
  import type { Snippet } from 'svelte';

  /** A big figure with a label under it. `mono` switches the number to Geist Mono (for counts and commands). */
  let {
    value,
    label,
    mono = false,
    class: className = ''
  }: { value: Snippet | string; label: Snippet | string; mono?: boolean; class?: string } = $props();
</script>

<div class="min-w-0 {className}">
  <p class="text-stat tabular text-ink {mono ? 'font-mono' : 'font-serif'}">
    {#if typeof value === 'string'}{value}{:else}{@render value()}{/if}
  </p>
  <p class="mt-1.5 max-w-[34ch] text-[0.875rem] leading-snug text-ink-soft">
    {#if typeof label === 'string'}{label}{:else}{@render label()}{/if}
  </p>
</div>
