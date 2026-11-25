<script lang="ts">
  import type { Snippet } from 'svelte';

  /** Link to another site: new tab, noopener, and a screen reader hint (pass the localised hint). */
  let {
    href,
    hint,
    class: className = '',
    children
  }: { href: string; hint: string; class?: string; children: Snippet } = $props();
</script>

<a {href} target="_blank" rel="noopener noreferrer" class="nb-link {className}">{@render children()}<span class="sr-only"> {hint}</span></a>
