<script lang="ts">
  import type { Dictionary } from '$i18n';
  import type { Locale } from '$i18n/config';
  import { HIGHLIGHT_IDS, landscapeRows } from '$lib/landscape-data';
  import ExperimentLandscape from './ExperimentLandscape.svelte';
  import Wave from '../Wave.svelte';
  import HomeSection from './HomeSection.svelte';

  /**
   * The 3D experiment landscape: all documented experiments as a bar chart. The chart falls back to flat bars when
   * WebGL is missing, the screen is narrow or the viewer prefers reduced motion, and the same numbers are always
   * available as a table.
   */
  let { lang, dict }: { lang: Locale; dict: Dictionary } = $props();

  const l = $derived(dict.home.landscape);
  const rows = $derived(landscapeRows(lang, l));
  const labels = $derived({
    chartLabel: l.chartLabel,
    stageA: l.stageA,
    stageB: l.stageB,
    metricA: l.metricA,
    metricB: l.metricB,
    noScore: l.noScore,
    noScoreShort: l.noScoreShort,
    axisTick: l.axisTick,
    highlighted: l.highlighted,
    hint: l.hint,
    hintFlat: l.hintFlat,
    resetView: l.resetView
  });
</script>

<!-- Waves lead into and out of the blue band. -->
<div class="bg-app">
  <Wave fill="var(--brand)" />
</div>

<HomeSection id="landscape" title={l.title} lede={l.lede} tone="brand" class="!pt-10">
  <p class="mx-auto mb-6 max-w-[68ch] rounded-xl border border-white/25 bg-brand-deep px-5 py-3.5 text-center text-[0.9375rem] leading-[1.55]">
    {l.note}
  </p>

  <figure class="card on-light !rounded-3xl p-4 sm:p-8">
    <ul aria-label={l.legendLabel} class="mb-4 flex flex-wrap gap-x-5 gap-y-2 text-[0.8125rem] text-ink-soft">
      <li class="flex items-center gap-2">
        <span class="size-3 rounded-sm bg-accent" aria-hidden="true"></span>{HIGHLIGHT_IDS.join(', ')}: {l.highlighted}
      </li>
      <li class="flex items-center gap-2">
        <span class="size-3 rounded-sm bg-(--mira-stage-a)" aria-hidden="true"></span>{l.stageA} ({l.metricA})
      </li>
      <li class="flex items-center gap-2">
        <span class="size-3 rounded-sm bg-(--mira-stage-b)" aria-hidden="true"></span>{l.stageB} ({l.metricB})
      </li>
      <li class="flex items-center gap-2">
        <span class="h-2 w-3 rounded-sm border border-rule-strong" aria-hidden="true"></span>{l.noScore}
      </li>
    </ul>

    {#key lang}
      <ExperimentLandscape {rows} {lang} {labels} />
    {/key}

    <figcaption class="mt-4 text-[0.875rem] leading-snug text-ink-soft">{l.caption}</figcaption>
  </figure>

  <details class="card on-light mt-4 px-5 py-3.5">
    <summary class="cursor-pointer text-[0.9375rem] font-medium text-ink">{l.tableSummary}</summary>
    <!-- svelte-ignore a11y_no_noninteractive_tabindex -->
    <div role="region" aria-label={l.tableCaption} tabindex="0" class="mt-3 overflow-x-auto">
      <table class="w-full min-w-[34rem] border-collapse text-left text-[0.875rem]">
        <caption class="sr-only">{l.tableCaption}</caption>
        <thead>
          <tr class="border-b border-rule bg-sunken/50 text-[0.8125rem] text-ink">
            <th scope="col" class="px-3 py-2 font-semibold">{l.columns.experiment}</th>
            <th scope="col" class="px-3 py-2 font-semibold">{l.columns.stage}</th>
            <th scope="col" class="px-3 py-2 font-semibold">{l.columns.metric}</th>
            <th scope="col" class="px-3 py-2 text-right font-semibold">{l.columns.value}</th>
            <th scope="col" class="px-3 py-2 font-semibold">{l.columns.split}</th>
          </tr>
        </thead>
        <tbody>
          {#each rows as row (row.id)}
            <tr class="border-b border-rule/70 align-top last:border-b-0">
              <th scope="row" class="px-3 py-2 text-left font-normal">
                <span class="font-mono text-ink">{row.id}</span>
                <span class="block text-[0.8125rem] text-ink-soft">{row.model}</span>
              </th>
              <td class="px-3 py-2 text-ink-soft">{l.stageNames[row.stage]}</td>
              <td class="px-3 py-2 text-ink-soft">{row.value === null ? l.noScore : row.metric}</td>
              <td class="px-3 py-2 text-right font-mono tabular text-ink">{row.value === null ? '' : row.valueText}</td>
              <td class="px-3 py-2 text-ink-soft">{row.split}</td>
            </tr>
          {/each}
        </tbody>
      </table>
    </div>
  </details>
</HomeSection>

<div class="on-brand">
  <Wave fill="var(--app)" />
</div>
