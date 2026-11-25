<script lang="ts">
  import type { Dictionary } from '$i18n';
  import { localePath, type Locale } from '$i18n/config';
  import { fmt, formatInt, formatScoreLocale } from '$i18n/format';
  import { FACTS } from '$lib/site';
  import Canvas from '../Canvas.svelte';

  let { lang, dict }: { lang: Locale; dict: Dictionary } = $props();

  const t = $derived(dict.home.hero);
</script>

<!-- The headline result with its honesty line. The "See the results" button of the hero scrolls here. -->
<div id="results" class="scroll-mt-24">
  <Canvas>
    <div class="mt-10 border-y border-rule py-5 sm:flex sm:items-center sm:gap-6">
      <p class="shrink-0 font-mono text-xl font-medium tabular text-ink">
        {formatScoreLocale(lang, FACTS.exp019Map50, true)} mAP50
      </p>
      <div class="mt-1 text-sm text-ink-soft sm:mt-0">
        <p>{fmt(t.benchmark, { count: formatInt(lang, FACTS.validationImages) })}</p>
        <a class="nb-link mt-1 inline-block" href={localePath(lang, '/research')}>{t.benchmarkLink}</a>
      </div>
    </div>
  </Canvas>
</div>
