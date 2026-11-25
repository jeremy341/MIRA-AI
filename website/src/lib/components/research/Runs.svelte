<script lang="ts">
  import { fmt, formatInt, formatScoreLocale } from '$i18n/format';
  import { decimal } from '$i18n/research/vars';
  import { EXPERIMENTS, PLANNED_EXPERIMENT, scoredExperiments, type Experiment } from '$lib/experiments';
  import { EXPERIMENT_LOG_URL } from '$lib/site';
  import ExtLink from '../ExtLink.svelte';
  import Figure from '../Figure.svelte';
  import Prose from '../Prose.svelte';
  import Rich from '../Rich.svelte';
  import BarRows, { type BarRowData } from './BarRows.svelte';
  import { fill, type SectionProps } from './context';
  import ExperimentIndex, { type IndexRow } from './ExperimentIndex.svelte';
  import NumChapter from './NumChapter.svelte';
  import TableFigure from './TableFigure.svelte';

  /** Experiments whose bars are drawn dark: the clean-data runs. */
  const CLEAN_IDS = new Set(['EXP-018', 'EXP-019']);
  const BAR_COLS =
    'grid-cols-[7.5rem_minmax(0,1fr)_3.9rem] sm:grid-cols-[11rem_minmax(0,1fr)_4.5rem]';

  /** 4. All experiments: a figure of every score and an index of all of them. */
  let { lang, t, common, vars }: SectionProps = $props();

  const s = $derived(t.runs);
  const pct = (v: number) => formatScoreLocale(lang, v, true);

  const bars = (stage: 'A' | 'B'): BarRowData[] =>
    scoredExperiments(stage).map((e) => ({
      key: e.id,
      label: e.id,
      sub: t.experiments[e.id].title,
      value: e.result.value,
      display: pct(e.result.value),
      tone: CLEAN_IDS.has(e.id) ? 'ink' : 'soft'
    }));

  const toRow = (e: Experiment): IndexRow => {
    const copy = t.experiments[e.id];
    const split =
      e.evaluation.images === null
        ? copy.split
        : `${copy.split}, ${fmt(s.images, { n: formatInt(lang, e.evaluation.images) })}`;
    return {
      id: e.id,
      stage: e.stage,
      kind: e.kind === 'export' ? s.exportKind : null,
      title: copy.title,
      setup: copy.setup,
      score: e.result ? pct(e.result.value) : null,
      scoreKind: e.result ? (e.result.name === 'mAP50' ? s.scoreMap : s.scoreAcc) : null,
      scoreNote: e.result ? null : `${s.sizeOnly}, ${decimal(lang, e.modelSizeMb ?? 0, 2)} MB`,
      planned: false,
      scoredOn: e.result ? `${s.scoredOn}: ${split}` : split,
      note: copy.note,
      caveats: copy.caveat
    };
  };

  const rows = $derived<IndexRow[]>([
    ...EXPERIMENTS.map(toRow),
    {
      id: PLANNED_EXPERIMENT.id,
      stage: 'B',
      kind: null,
      title: t.limits.plannedTitle.replace(/^EXP-\d+: ?/, ''),
      setup: s.plannedSetup,
      score: null,
      scoreKind: null,
      scoreNote: s.planned,
      planned: true,
      scoredOn: s.plannedSplit,
      note: s.plannedNote,
      caveats: []
    }
  ]);
</script>

<NumChapter id="runs" n={4} title={s.title}>
  <Prose>
    <p><Rich text={fill(vars, s.p1)} {lang} /></p>
  </Prose>

  <Figure id="fig-3" n={3} label={common.figure} class="mt-10">
    {#snippet caption()}<Rich text={fill(vars, s.chartCaption)} {lang} />{/snippet}
    <div class="grid gap-x-14 gap-y-10 lg:grid-cols-[minmax(0,5fr)_minmax(0,7fr)]">
      <div>
        <h3 class="mb-2 border-b border-ink pb-1.5 font-sans text-[0.875rem] font-semibold text-ink">{s.panelA}</h3>
        <BarRows rows={bars('A')} ariaLabel={fill(vars, s.chartAriaA)} cols={BAR_COLS} />
      </div>
      <div>
        <h3 class="mb-2 border-b border-ink pb-1.5 font-sans text-[0.875rem] font-semibold text-ink">{s.panelB}</h3>
        <BarRows rows={bars('B')} ariaLabel={fill(vars, s.chartAriaB)} cols={BAR_COLS} />
      </div>
    </div>
  </Figure>

  <TableFigure id="table-4" n={4} label={common.table} caption={s.tableCaption} class="mt-14">
    <ExperimentIndex
      {rows}
      labels={{
        filterLabel: s.filterLabel,
        filters: s.filters,
        filterStatus: s.filterStatus,
        tableLabel: s.tableLabel,
        tableCaption: s.tableCaption,
        scrollHint: s.scrollHint,
        columns: s.columns,
        caveatLabel: s.caveatLabel
      }}
    />
  </TableFigure>

  <p class="mt-6 text-[0.9375rem]">
    <ExtLink href={EXPERIMENT_LOG_URL} hint={common.opensInNewTab}>{s.logLink}</ExtLink>
  </p>
</NumChapter>
