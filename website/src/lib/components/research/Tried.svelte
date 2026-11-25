<script lang="ts">
  import Prose from '../Prose.svelte';
  import Rich from '../Rich.svelte';
  import { fill, type SectionProps } from './context';
  import NumChapter from './NumChapter.svelte';
  import ScrollRegion from './ScrollRegion.svelte';
  import TableFigure from './TableFigure.svelte';
  import { TABLE, TBODY, TD, TD_LAST, TH, TH_LAST, THEAD } from './table-styles';

  /** 2. What I tried: the four models (Table 1) and the data sources (Table 2). */
  let { lang, t, common, vars }: SectionProps = $props();

  const s = $derived(t.tried);
</script>

<NumChapter id="tried" n={2} title={s.title}>
  <Prose>
    <p><Rich text={fill(vars, s.p1)} {lang} /></p>
  </Prose>

  <TableFigure id="table-1" n={1} label={common.table} caption={s.modelsCaption} class="mt-10 max-w-[52rem]">
    <ScrollRegion label={s.modelsLabel}>
      <table class="{TABLE} min-w-[38rem]">
        <caption class="sr-only">{s.modelsCaption}</caption>
        <thead class={THEAD}>
          <tr>
            <th scope="col" class={TH}>{s.modelsColumns.model}</th>
            <th scope="col" class={TH}>{s.modelsColumns.task}</th>
            <th scope="col" class={TH}>{s.modelsColumns.runs}</th>
            <th scope="col" class={TH_LAST}>{s.modelsColumns.lesson}</th>
          </tr>
        </thead>
        <tbody class={TBODY}>
          {#each s.models as m (m.name)}
            <tr>
              <th scope="row" class="{TD} font-medium whitespace-nowrap text-ink">{m.name}</th>
              <td class="{TD} text-ink-soft">{m.task}</td>
              <td class="{TD} text-ink-soft"><Rich text={fill(vars, m.runs)} {lang} /></td>
              <td class={TD_LAST}>{m.lesson}</td>
            </tr>
          {/each}
        </tbody>
      </table>
    </ScrollRegion>
  </TableFigure>

  <Prose class="mt-12">
    <p><Rich text={fill(vars, s.p2)} {lang} /></p>
  </Prose>

  <TableFigure id="table-2" n={2} label={common.table} caption={s.datasetsCaption} class="mt-10 max-w-[52rem]">
    <ScrollRegion label={s.datasetsLabel}>
      <table class="{TABLE} min-w-[36rem]">
        <caption class="sr-only">{s.datasetsCaption}</caption>
        <thead class={THEAD}>
          <tr>
            <th scope="col" class={TH}>{s.datasetsColumns.source}</th>
            <th scope="col" class={TH}>{s.datasetsColumns.what}</th>
            <th scope="col" class={TH_LAST}>{s.datasetsColumns.status}</th>
          </tr>
        </thead>
        <tbody class={TBODY}>
          {#each s.datasets as d, i (d.name)}
            {@const dropped = i === s.datasets.length - 1}
            <tr class={dropped ? 'text-ink-soft' : undefined}>
              <th scope="row" class="{TD} font-medium whitespace-nowrap text-ink">{d.name}</th>
              <td class={TD}>{d.what}</td>
              <td class="{TD_LAST} {dropped ? 'font-medium text-ink' : 'text-ink-soft'}">{d.status}</td>
            </tr>
          {/each}
        </tbody>
      </table>
    </ScrollRegion>
  </TableFigure>

  <Prose class="mt-12">
    <p><Rich text={fill(vars, s.p3)} {lang} /></p>
    <p class="text-[0.9375rem] text-muted-foreground sm:text-[1rem]"><Rich text={fill(vars, s.splitNote)} {lang} /></p>
  </Prose>
</NumChapter>
