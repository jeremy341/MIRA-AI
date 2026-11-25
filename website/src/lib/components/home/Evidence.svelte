<script lang="ts">
  import type { Dictionary } from '$i18n';
  import type { Locale } from '$i18n/config';
  import { formatScoreLocale } from '$i18n/format';
  import { EXP018_019_CLASSES, EXP019_ALL, EXPERIMENTS } from '$lib/experiments';
  import { CLASSES } from '$lib/site';
  import Chapter from '../Chapter.svelte';
  import ClassChip from '../ClassChip.svelte';
  import Figure from '../Figure.svelte';
  import MarginNote from '../MarginNote.svelte';
  import Prose from '../Prose.svelte';
  import Rich from '../Rich.svelte';
  import Stat from '../Stat.svelte';
  import MapChart, { type MapChartRow } from './MapChart.svelte';

  let { lang, dict }: { lang: Locale; dict: Dictionary } = $props();

  const t = $derived(dict.home.evidence);
  const pct = (v: number) => formatScoreLocale(lang, v, true);

  function score(id: string): number {
    const run = EXPERIMENTS.find((e) => e.id === id);
    if (!run || run.result === null) throw new Error(`Missing score for ${id}`);
    return run.result.value;
  }

  /** The three runs of the README results table, taken from the experiment data (nothing retyped). */
  const chartRows = $derived.by<MapChartRow[]>(() => {
    const values = [score('EXP-014'), score('EXP-018'), score('EXP-019')];
    return t.chartRows.map((row, i) => ({
      id: row.id,
      note: row.note,
      value: values[i],
      outlined: row.id === 'EXP-014'
    }));
  });
</script>

<Chapter id="evidence" title={t.title}>
  <p class="max-w-[28ch] font-serif text-title text-ink-soft">{t.subtitle}</p>

  <Prose class="mt-6">
    <MarginNote><Rich text={t.mapNote} /></MarginNote>
    <p><Rich text={t.p1} /></p>
  </Prose>

  <div class="mt-10 grid gap-10 lg:grid-cols-[minmax(0,7fr)_minmax(0,4fr)] lg:gap-16">
    <Figure id="fig-2" n={2} label={dict.common.figure}>
      {#snippet caption()}<Rich text={t.chartCaption} />{/snippet}
      <MapChart rows={chartRows} {lang} ariaLabel={t.chartAria} />
    </Figure>
    <div class="lg:pt-2">
      <Stat>
        {#snippet value()}<Rich text={t.statValue} {lang} />{/snippet}
        {#snippet label()}<Rich text={t.statLabel} />{/snippet}
      </Stat>
    </div>
  </div>

  <div class="mt-14 grid gap-10 lg:grid-cols-[minmax(0,7fr)_minmax(0,5fr)] lg:gap-16">
    <Figure id="table-1" n={1} label={dict.common.table}>
      {#snippet caption()}<Rich text={t.tableCaption} />{/snippet}
      <div class="max-w-full overflow-x-auto">
        <table class="w-full min-w-[19rem] border-collapse text-left text-[0.9375rem]">
          <caption class="sr-only"><Rich text={t.tableCaption} /></caption>
          <thead>
            <tr class="border-b border-ink text-[0.8125rem] text-muted-foreground">
              <th scope="col" class="py-2 pr-3 font-medium">{t.tableColumns.cls}</th>
              {#each ['precision', 'recall', 'map50'] as const as key (key)}
                <th scope="col" class="px-2 py-2 text-right font-medium">{t.tableColumns[key]}</th>
              {/each}
            </tr>
          </thead>
          <tbody>
            {#each CLASSES as c (c.id)}
              {@const row = EXP018_019_CLASSES.find((r) => r.cls === c.id)}
              {#if row}
                <tr class="border-b border-rule">
                  <th scope="row" class="py-2.5 pr-3 text-left font-normal">
                    <ClassChip cls={c.id} label={dict.common.classes[c.id]} />
                  </th>
                  <td class="px-2 py-2.5 text-right font-mono tabular">{pct(row.precision)}</td>
                  <td class="px-2 py-2.5 text-right font-mono tabular {c.id === 'plastic' ? 'font-semibold text-ink' : ''}">{pct(row.recall)}</td>
                  <td class="px-2 py-2.5 text-right font-mono tabular">{pct(row.map50)}</td>
                </tr>
              {/if}
            {/each}
            <tr class="text-muted-foreground">
              <th scope="row" class="py-2.5 pr-3 text-left font-normal">{t.tableAll}</th>
              <td class="px-2 py-2.5 text-right font-mono tabular">{pct(EXP019_ALL.precision)}</td>
              <td class="px-2 py-2.5 text-right font-mono tabular">{pct(EXP019_ALL.recall)}</td>
              <td class="px-2 py-2.5 text-right font-mono tabular">{pct(EXP019_ALL.map50)}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </Figure>
    <div>
      <p class="font-serif text-title text-ink"><Rich text={t.plastic} {lang} /></p>
      <MarginNote inline class="mt-4"><Rich text={t.plasticNote} /></MarginNote>
    </div>
  </div>

  <div class="mt-14 border-t-2 border-ink pt-8">
    <h3 class="font-serif text-title text-ink">{t.caveatTitle}</h3>
    <Prose class="mt-3"><p><Rich text={t.caveat} /></p></Prose>
  </div>
</Chapter>
