<script lang="ts">
  import type { Dictionary } from '$i18n';
  import { localePath, type Locale } from '$i18n/config';
  import { fmt, formatInt, formatScoreLocale } from '$i18n/format';
  import { EXPERIMENTS } from '$lib/experiments';
  import { CLASSES, FACTS } from '$lib/site';

  let { lang, dict }: { lang: Locale; dict: Dictionary } = $props();

  const t = $derived(dict.home.hero);
  const s = $derived(dict.home.stats);
  const figure = 'text-[clamp(2.5rem,2rem+2vw,3.5rem)] leading-none font-semibold tracking-[-0.03em] tabular text-brand-ink';
</script>

<!-- The headline result with its honesty line. The "See the results" button of the hero scrolls here. -->
<div
  id="results"
  role="group"
  aria-label={t.resultsCta}
  class="mt-16 grid scroll-mt-24 grid-cols-[minmax(0,1fr)] border-y border-rule sm:mt-20 md:grid-cols-[minmax(0,2fr)_minmax(0,1fr)_minmax(0,1fr)]"
>
  <div class="py-8 md:pr-8">
    <p class={figure}>{formatScoreLocale(lang, FACTS.exp019Map50, true)} <span class="text-[1.25rem] tracking-normal">mAP50</span></p>
    <p class="mt-3 max-w-[46ch] text-[0.9375rem] leading-[1.55] text-ink-soft">
      {fmt(t.benchmark, { count: formatInt(lang, FACTS.validationImages) })}
    </p>
    <a class="nb-link mt-2 inline-block text-[0.9375rem] font-medium" href={localePath(lang, '/research')}>{t.benchmarkLink}</a>
  </div>
  <div class="border-t border-rule py-8 md:border-t-0 md:border-l md:px-8">
    <p class={figure}>{EXPERIMENTS.length}</p>
    <p class="mt-3 text-[0.9375rem] leading-[1.5] text-ink-soft">{s.experiments}</p>
  </div>
  <div class="border-t border-rule py-8 md:border-t-0 md:border-l md:pl-8">
    <p class={figure}>{CLASSES.length}</p>
    <p class="mt-3 text-[0.9375rem] leading-[1.5] text-ink-soft">{s.classes}</p>
  </div>
</div>
