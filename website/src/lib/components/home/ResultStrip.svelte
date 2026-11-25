<script lang="ts">
  import type { Dictionary } from '$i18n';
  import { localePath, type Locale } from '$i18n/config';
  import { fmt, formatInt, formatScoreLocale } from '$i18n/format';
  import { EXPERIMENTS } from '$lib/experiments';
  import { CLASSES, FACTS } from '$lib/site';
  import Canvas from '../Canvas.svelte';

  let { lang, dict }: { lang: Locale; dict: Dictionary } = $props();

  const t = $derived(dict.home.hero);
  const s = $derived(dict.home.stats);
</script>

<!-- The headline result with its honesty line, as three cards. The "See the results" button of the hero scrolls here. -->
<section id="results" aria-label={t.resultsCta} class="scroll-mt-20 pb-4">
  <Canvas>
    <div class="mx-auto grid max-w-[68rem] grid-cols-[minmax(0,1fr)] gap-3 md:grid-cols-[minmax(0,2fr)_minmax(0,1fr)_minmax(0,1fr)]">
      <div class="rounded-2xl border border-rule bg-surface p-6 shadow-[var(--shadow-raised)] sm:p-7">
        <p class="font-mono text-[2.25rem] leading-none font-medium tabular text-ink sm:text-[2.75rem]">
          {formatScoreLocale(lang, FACTS.exp019Map50, true)}
        </p>
        <p class="mt-2 text-[0.9375rem] font-semibold text-ink">mAP50</p>
        <p class="mt-3 max-w-[44ch] text-[0.9375rem] leading-[1.55] text-ink-soft">
          {fmt(t.benchmark, { count: formatInt(lang, FACTS.validationImages) })}
        </p>
        <a class="nb-link mt-3 inline-block text-[0.9375rem]" href={localePath(lang, '/research')}>{t.benchmarkLink}</a>
      </div>
      <div class="rounded-2xl border border-rule bg-surface p-6 shadow-[var(--shadow-raised)] sm:p-7">
        <p class="font-mono text-[2.25rem] leading-none font-medium tabular text-ink sm:text-[2.75rem]">{EXPERIMENTS.length}</p>
        <p class="mt-3 text-[0.9375rem] leading-[1.5] text-ink-soft">{s.experiments}</p>
      </div>
      <div class="rounded-2xl border border-rule bg-surface p-6 shadow-[var(--shadow-raised)] sm:p-7">
        <p class="font-mono text-[2.25rem] leading-none font-medium tabular text-ink sm:text-[2.75rem]">{CLASSES.length}</p>
        <p class="mt-3 text-[0.9375rem] leading-[1.5] text-ink-soft">{s.classes}</p>
      </div>
    </div>
  </Canvas>
</section>
