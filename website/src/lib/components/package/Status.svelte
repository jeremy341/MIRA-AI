<script lang="ts">
  import type { Locale } from '$i18n/config';
  import type { PackageCopy } from '$i18n/package';
  import Chapter from '../Chapter.svelte';
  import Prose from '../Prose.svelte';
  import Rich from '../Rich.svelte';
  import RuleList from '../RuleList.svelte';

  /** What works and what is not tested, said once, in two columns. */
  let { lang, t }: { lang: Locale; t: PackageCopy } = $props();

  const s = $derived(t.status);
</script>

<Chapter id="status" title={s.title}>
  <Prose>
    <p>{s.intro}</p>
  </Prose>
  <div class="mt-8 grid gap-10 md:grid-cols-2 md:gap-16">
    <div>
      <h3 class="font-serif text-title text-brand-ink">{s.worksTitle}</h3>
      <RuleList items={s.works} {lang} done />
    </div>
    <div>
      <h3 class="font-serif text-title text-brand-ink">{s.openTitle}</h3>
      <RuleList items={s.open} {lang} done={false} />
    </div>
  </div>
</Chapter>
