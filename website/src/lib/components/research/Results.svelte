<script lang="ts">
  import { formatScoreLocale } from '$i18n/format';
  import { EXP014_CLASSES, EXP018_019_CLASSES, EXP019_ALL, getExperiment } from '$lib/experiments';
  import { CLASSES } from '$lib/site';
  import ClassChip from '../ClassChip.svelte';
  import Figure from '../Figure.svelte';
  import MarginNote from '../MarginNote.svelte';
  import Prose from '../Prose.svelte';
  import Rich from '../Rich.svelte';
  import Stat from '../Stat.svelte';
  import BarRows, { type BarRowData } from './BarRows.svelte';
  import ClassBars, { type ClassBarRow } from './ClassBars.svelte';
  import { fill, type SectionProps } from './context';
  import NumChapter from './NumChapter.svelte';
  import ScrollRegion from './ScrollRegion.svelte';
  import TableFigure from './TableFigure.svelte';
  import { NUM, TABLE, TBODY, TD, TH, TH_NUM, THEAD } from './table-styles';

  /** 3. Results: the headline figure, the per-class table and the per-class chart. */
  let { lang, t, common, vars }: SectionProps = $props();

  const r = $derived(t.results);
  const pct = (v: number) => formatScoreLocale(lang, v, true);

  function scoreOf(id: string): number {
    const run = getExperiment(id);
    if (!run.result) throw new Error(`No score for ${id}`);
    return run.result.value;
  }

  const headline = $derived<BarRowData[]>(
    r.chartRows.map((row) => ({
      key: row.id,
      label: row.id,
      sub: row.note,
      value: scoreOf(row.id),
      display: pct(scoreOf(row.id)),
      // The baseline was scored on another split, so its bar is only outlined.
      tone: row.id === 'EXP-014' ? 'outline' : 'ink'
    }))
  );

  /** EXP-014 (hatched) against EXP-018 (solid), per class. */
  const classRows = $derived<ClassBarRow[]>(
    EXP014_CLASSES.map((before) => {
      const after = EXP018_019_CLASSES.find((x) => x.cls === before.cls);
      if (!after) throw new Error(`Missing EXP-018 row for ${before.cls}`);
      return {
        cls: before.cls,
        before: before.map50,
        after: after.map50,
        beforeDisplay: pct(before.map50),
        afterDisplay: pct(after.map50)
      };
    })
  );
</script>

<NumChapter id="results" n={3} title={r.title}>
  <Prose>
    <p><Rich text={fill(vars, r.p1)} {lang} /></p>
  </Prose>

  <div class="mt-10 grid gap-10 lg:grid-cols-[minmax(0,7fr)_minmax(0,4fr)] lg:gap-16">
    <Figure id="fig-1" n={1} label={common.figure}>
      {#snippet caption()}<Rich text={fill(vars, r.chartCaption)} {lang} />{/snippet}
      <BarRows rows={headline} ariaLabel={fill(vars, r.chartAria)} />
    </Figure>
    <div class="lg:pt-2">
      <Stat>
        {#snippet value()}<Rich text={fill(vars, r.statValue)} {lang} />{/snippet}
        {#snippet label()}<Rich text={fill(vars, r.statLabel)} {lang} />{/snippet}
      </Stat>
    </div>
  </div>

  <Prose class="mt-14">
    <MarginNote><Rich text={fill(vars, r.marginRecall)} {lang} /></MarginNote>
    <p><Rich text={fill(vars, r.p2)} {lang} /></p>
  </Prose>

  <TableFigure id="table-3" n={3} label={common.table} class="mt-8 max-w-[44rem]">
    {#snippet caption()}<Rich text={fill(vars, r.classTableCaption)} {lang} />{/snippet}
    <ScrollRegion label={r.classTableLabel}>
      <table class="{TABLE} sm:min-w-[24rem]">
        <caption class="sr-only"><Rich text={fill(vars, r.classTableCaption)} {lang} /></caption>
        <thead class={THEAD}>
          <tr>
            <th scope="col" class={TH}>{r.classColumns.cls}</th>
            {#each ['precision', 'recall', 'map50'] as const as key (key)}
              <th scope="col" class="{TH_NUM} {key === 'precision' ? 'hidden sm:table-cell' : ''}">
                {r.classColumns[key]}
              </th>
            {/each}
          </tr>
        </thead>
        <tbody class={TBODY}>
          {#each CLASSES as c (c.id)}
            {@const row = EXP018_019_CLASSES.find((x) => x.cls === c.id)}
            {#if row}
              <tr>
                <th scope="row" class="{TD} font-normal">
                  <ClassChip cls={c.id} label={common.classes[c.id]} />
                </th>
                <td class="{NUM} hidden sm:table-cell">{pct(row.precision)}</td>
                <td class={NUM}>
                  {#if c.id === 'plastic'}
                    <span
                      class="mr-2 border border-ink px-1 py-px align-middle font-sans text-[0.6875rem] font-medium tracking-[0.04em] uppercase"
                      >{r.classWeakMark}</span
                    >
                    <span class="font-semibold text-ink">{pct(row.recall)}</span>
                  {:else}
                    {pct(row.recall)}
                  {/if}
                </td>
                <td class={NUM}>{pct(row.map50)}</td>
              </tr>
            {/if}
          {/each}
          <tr class="text-ink-soft">
            <th scope="row" class="{TD} font-normal">{r.classAll}</th>
            <td class="{NUM} hidden sm:table-cell">{pct(EXP019_ALL.precision)}</td>
            <td class={NUM}>{pct(EXP019_ALL.recall)}</td>
            <td class={NUM}>{pct(EXP019_ALL.map50)}</td>
          </tr>
        </tbody>
      </table>
    </ScrollRegion>
  </TableFigure>

  <Prose class="mt-14">
    <p><Rich text={fill(vars, r.p3)} {lang} /></p>
  </Prose>

  <Figure id="fig-2" n={2} label={common.figure} class="mt-8 max-w-[48rem]">
    {#snippet caption()}<Rich text={fill(vars, r.classChartCaption)} {lang} />{/snippet}
    <ClassBars
      rows={classRows}
      classNames={common.classes}
      beforeLabel={r.classChartBefore}
      afterLabel={r.classChartAfter}
      ariaLabel={fill(vars, r.classChartAria)}
    />
  </Figure>
</NumChapter>
