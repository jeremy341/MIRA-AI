<script lang="ts">
  import type { Locale } from '$i18n/config';
  import Rich from './Rich.svelte';

  /** A ruled list of short statements. A filled dot marks what works, a ring marks what is still open. */
  let { items, done, lang }: { items: readonly string[]; done: boolean; lang?: Locale } = $props();
</script>

<ul class="mt-4 divide-y divide-rule border-y border-rule">
  {#each items as item (item)}
    <li class="flex gap-3.5 py-3.5 text-[0.9375rem] leading-[1.55] text-ink-soft">
      <span
        aria-hidden="true"
        class="mt-[0.3rem] size-3 shrink-0 rounded-full {done ? 'bg-brand' : 'border-2 border-rule-strong'}"
      ></span>
      <span class="min-w-0"><Rich text={item} {lang} /></span>
    </li>
  {/each}
</ul>
