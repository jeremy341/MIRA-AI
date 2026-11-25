<script lang="ts">
  import type { Locale } from '$i18n/config';
  import type { PackageCopy } from '$i18n/package';
  import Chapter from '../Chapter.svelte';
  import Prose from '../Prose.svelte';
  import Rich from '../Rich.svelte';

  /** What works and what is not tested, said once, in two columns. */
  let { lang, t }: { lang: Locale; t: PackageCopy } = $props();

  const s = $derived(t.status);
</script>

{#snippet bullets(items: readonly string[])}
  <ul class="space-y-2.5 text-[1.0625rem] leading-snug text-ink-soft marker:text-ink">
    {#each items as item (item)}
      <li class="ml-5 list-disc pl-1"><Rich text={item} {lang} /></li>
    {/each}
  </ul>
{/snippet}

<Chapter id="status" title={s.title}>
  <Prose>
    <p>{s.intro}</p>
  </Prose>
  <div class="mt-8 grid gap-10 md:grid-cols-2 md:gap-16">
    <div>
      <h3 class="font-serif text-title text-ink">{s.worksTitle}</h3>
      <div class="mt-4">{@render bullets(s.works)}</div>
    </div>
    <div>
      <h3 class="font-serif text-title text-ink">{s.openTitle}</h3>
      <div class="mt-4">{@render bullets(s.open)}</div>
    </div>
  </div>
</Chapter>
