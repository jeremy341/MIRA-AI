<script lang="ts">
  import type { Snippet } from 'svelte';

  /**
   * A small side note. On screens from xl up it sits in the right margin next to the text it follows;
   * on smaller screens it is a short indented block in the flow. Put it BEFORE the paragraph it annotates.
   * Use it for caveats and asides, one or two per section at most. A `div role="note"` and not an `aside`, so
   * the page does not collect a pile of complementary landmarks.
   */
  let {
    inline = false,
    class: className = '',
    children
  }: {
    /** Never move into the margin (use inside narrow columns). */
    inline?: boolean;
    class?: string;
    children: Snippet;
  } = $props();
</script>

<div
  role="note"
  class="my-5 border-l-2 border-brand pl-3 text-[0.8125rem] leading-[1.45] text-muted-foreground {inline
    ? ''
    : 'xl:float-right xl:clear-right xl:-mr-[17rem] xl:ml-6 xl:mb-4 xl:mt-1 xl:w-[14.5rem] xl:border-l-0 xl:border-t xl:pl-0 xl:pt-2'} {className}"
>
  {@render children()}
</div>
