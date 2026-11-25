<script lang="ts">
  import type { Snippet } from 'svelte';

  /**
   * One reading column: 66 characters wide, 18px type, 1.65 leading. Paragraphs are separated by space,
   * not by indents. MarginNote floats into the free space on the right from the xl breakpoint.
   */
  let { class: className = '', children }: { class?: string; children: Snippet } = $props();
</script>

<div
  class="max-w-[66ch] text-[1.0625rem] leading-[1.65] text-ink-soft sm:text-[1.125rem] [&>p:not(:first-child)]:mt-5 {className}"
>
  {@render children()}
</div>
