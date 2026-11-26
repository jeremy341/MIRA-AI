<script lang="ts">
  import type { Locale } from '$i18n/config';
  import type { PackageCopy } from '$i18n/package';
  import Chapter from '../Chapter.svelte';
  import Heading from '../Heading.svelte';
  import Rich from '../Rich.svelte';
  import { EXTRAS } from './package-data';

  /** What you need to run it, and the optional extras. Plain ruled lists, no boxes. */
  let { lang, t }: { lang: Locale; t: PackageCopy } = $props();

  const ITEMS = ['python', 'camera', 'gpu', 'network'] as const;

  const r = $derived(t.requirements);
</script>

<Chapter id="requirements" title={r.title}>
  <div class="grid gap-12 md:grid-cols-2 md:gap-14">
    <div class="min-w-0">
      <Heading as="h3" size="title" class="text-ink">{r.requirementsTitle}</Heading>
      <dl class="mt-4 border-t border-rule-strong">
        {#each ITEMS as key (key)}
          <div class="grid gap-x-6 gap-y-0.5 border-b border-rule py-3 sm:grid-cols-[6rem_minmax(0,1fr)]">
            <dt class="text-[0.9375rem] font-medium text-ink">{r.items[key].label}</dt>
            <dd class="min-w-0 text-[0.9375rem] leading-snug text-ink-soft"><Rich text={r.items[key].text} {lang} /></dd>
          </div>
        {/each}
      </dl>
    </div>

    <div class="min-w-0">
      <Heading as="h3" size="title" class="text-ink">{r.extrasTitle}</Heading>
      <ul class="mt-4 border-t border-rule-strong">
        {#each EXTRAS as extra (extra.id)}
          <li class="border-b border-rule py-3">
            <code class="block font-mono text-[0.875rem] font-medium break-words text-ink">{extra.command}</code>
            <p class="mt-1 text-[0.9375rem] leading-snug text-ink-soft">{r.extras[extra.id]}</p>
          </li>
        {/each}
      </ul>
      <p class="mt-3 max-w-[46ch] text-micro text-muted-foreground">{r.extrasNote}</p>
    </div>
  </div>
</Chapter>
