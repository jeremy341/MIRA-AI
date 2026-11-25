<script lang="ts">
  import { decimal } from '$i18n/research/vars';
  import { EXP019_EXPORTS } from '$lib/experiments';
  import MarginNote from '../MarginNote.svelte';
  import Prose from '../Prose.svelte';
  import Rich from '../Rich.svelte';
  import { fill, type SectionProps } from './context';
  import NumChapter from './NumChapter.svelte';
  import ScrollRegion from './ScrollRegion.svelte';
  import TableFigure from './TableFigure.svelte';
  import { NUM, TABLE, TBODY, TD, TH, TH_NUM, THEAD } from './table-styles';

  /** 6. Edge export: file sizes (Table 5), the cost of quantizing, and what has not been measured. */
  let { lang, t, common, vars }: SectionProps = $props();

  const s = $derived(t.edge);
  const formatName = (file: string, fallback: string) => s.formats[file as keyof typeof s.formats] ?? fallback;
</script>

<NumChapter id="edge" n={6} title={s.title}>
  <Prose>
    <p><Rich text={fill(vars, s.p1)} {lang} /></p>
  </Prose>

  <TableFigure id="table-5" n={5} label={common.table} caption={s.tableCaption} class="mt-8 max-w-[44rem]">
    <ScrollRegion label={s.tableLabel}>
      <table class="{TABLE} min-w-[30rem]">
        <caption class="sr-only">{s.tableCaption}</caption>
        <thead class={THEAD}>
          <tr>
            <th scope="col" class={TH}>{s.columns.format}</th>
            <th scope="col" class={TH}>{s.columns.file}</th>
            <th scope="col" class={TH_NUM}>{s.columns.size}</th>
          </tr>
        </thead>
        <tbody class={TBODY}>
          {#each EXP019_EXPORTS as f (f.file)}
            <tr>
              <th scope="row" class="{TD} font-normal text-ink">{formatName(f.file, f.format)}</th>
              <td class="{TD} font-mono text-[0.8125rem] text-ink-soft">{f.file}</td>
              <td class={NUM}>{decimal(lang, f.bytes / 1_000_000, 2)} {s.sizeUnit}</td>
            </tr>
          {/each}
        </tbody>
      </table>
    </ScrollRegion>
  </TableFigure>

  <Prose class="mt-10">
    <MarginNote><Rich text={fill(vars, s.marginSize)} {lang} /></MarginNote>
    <p><Rich text={fill(vars, s.p2)} {lang} /></p>
    <p><Rich text={fill(vars, s.p3)} {lang} /></p>
    <p><Rich text={fill(vars, s.p4)} {lang} /></p>
  </Prose>
</NumChapter>
