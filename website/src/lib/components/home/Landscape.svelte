<script lang="ts">
  import type { Dictionary } from '$i18n';
  import type { Locale } from '$i18n/config';
  import { HIGHLIGHT_IDS, landscapeRows } from '$lib/landscape-data';
  import ExperimentLandscape from './ExperimentLandscape.svelte';
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

<HomeSection id="landscape" title={l.title} lede={l.lede}>
  <p class="mb-5 max-w-[68ch] rounded-xl border border-accent/25 bg-accent-soft px-4 py-3 text-[0.9375rem] leading-[1.55] text-ink/85">
    {l.note}
  </p>

  <figure class="rounded-2xl border border-rule bg-surface p-4 shadow-[var(--shadow-raised)] sm:p-6">
    <ul aria-label={l.legendLabel} class="mb-4 flex flex-wrap gap-x-5 gap-y-2 text-[0.8125rem] text-ink-soft">
      <li class="flex items-center gap-2">
        <span class="size-3 rounded-sm bg-accent" aria-hidden="true"></span>{HIGHLIGHT_IDS.join(', ')}: {l.highlighted}
      </li>
      <li class="flex items-center gap-2">
        <span class="size-3 rounded-sm bg-[#8a8a8a]" aria-hidden="true"></span>{l.stageA} ({l.metricA})
      </li>
      <li class="flex items-center gap-2">
        <span class="size-3 rounded-sm bg-[#4d4d4d]" aria-hidden="true"></span>{l.stageB} ({l.metricB})
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

  <details class="mt-4 rounded-xl border border-rule bg-surface px-4 py-3 shadow-[var(--shadow-raised)]">
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
