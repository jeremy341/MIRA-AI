<script lang="ts" module>
  export type Filter = 'all' | 'A' | 'B';

  /** One table row, fully formatted by the parent so this component carries no copy of its own. */
  export type IndexRow = {
    id: string;
    stage: 'A' | 'B';
    /** Short label for export runs, else null. */
    kind: string | null;
    title: string;
    setup: string;
    /** Formatted score such as "90,58 %", or null when there is none. */
    score: string | null;
    /** "mAP50" or "accuracy" next to the score. */
    scoreKind: string | null;
    /** Shown instead of a score: "size only" or "planned, not run". */
    scoreNote: string | null;
    planned: boolean;
    /** The "Scored on: ..." line, already combined with the image count. */
    scoredOn: string;
    note: string;
    caveats: string[];
  };

  export type IndexLabels = {
    filterLabel: string;
    filters: Record<Filter, string>;
    /** Contains {shown} and {total}. */
    filterStatus: string;
    tableLabel: string;
    /** Accessible name of the table (visually hidden `<caption>`); the same text as the visible figure caption. */
    tableCaption: string;
    /** Visible only on small screens. */
    scrollHint: string;
    columns: { run: string; what: string; score: string; note: string };
    caveatLabel: string;
  };
</script>

<script lang="ts">
  import { fmt } from '$i18n/format';
  import ScrollRegion from './ScrollRegion.svelte';
  import { NUM_LEFT, TABLE, TBODY, TD, TD_LAST, TH, THEAD } from './table-styles';

  const FILTERS: readonly Filter[] = ['all', 'A', 'B'];

  /**
   * Index of every experiment. A stage switch (real buttons, Tab and Enter or Space) narrows the rows.
   * Without JavaScript all rows are in the HTML. The scroll region keeps a wide table off the page edge.
   */
  let { rows, labels }: { rows: readonly IndexRow[]; labels: IndexLabels } = $props();

  const uid = $props.id();
  let filter = $state<Filter>('all');

  const matches = (row: IndexRow, f: Filter) => f === 'all' || row.stage === f;
  const shown = $derived(rows.filter((r) => matches(r, filter)));
  const status = $derived(fmt(labels.filterStatus, { shown: shown.length, total: rows.length }));
</script>

<div>
  <div class="flex flex-wrap items-center gap-x-1 gap-y-1 border-b border-rule pb-1 text-[0.9375rem]">
    <span class="mr-3 text-muted-foreground" id="{uid}-filter-label">{labels.filterLabel}</span>
    <div role="group" aria-labelledby="{uid}-filter-label" class="flex flex-wrap gap-x-5">
      {#each FILTERS as f (f)}
        <button
          type="button"
          aria-pressed={filter === f}
          onclick={() => (filter = f)}
          class="-mb-px inline-flex min-h-11 items-center gap-2 border-b-2 px-0.5 sm:min-h-10 {filter === f
            ? 'border-ink font-semibold text-ink'
            : 'border-transparent text-ink-soft hover:border-rule hover:text-ink'}"
        >
          {labels.filters[f]}
          <span class="font-mono text-[0.8125rem] tabular text-muted-foreground"
            >{rows.filter((r) => matches(r, f)).length}</span
          >
        </button>
      {/each}
    </div>
  </div>
  <p role="status" class="mt-2 text-[0.8125rem] text-muted-foreground">{status}</p>

  <p class="mt-1 text-[0.8125rem] text-muted-foreground sm:hidden">{labels.scrollHint}</p>

  <ScrollRegion label={labels.tableLabel} class="mt-3">
    <table class="{TABLE} min-w-[46rem]">
      <caption class="sr-only">{labels.tableCaption}</caption>
      <thead class={THEAD}>
        <tr>
          <th scope="col" class={TH}>{labels.columns.run}</th>
          <th scope="col" class="{TH} w-[30%]">{labels.columns.what}</th>
          <th scope="col" class={TH}>{labels.columns.score}</th>
          <th scope="col" class="{TH} w-[34%]">{labels.columns.note}</th>
        </tr>
      </thead>
      <tbody class={TBODY}>
        {#each shown as r (r.id)}
          <tr class={r.planned ? 'text-ink-soft' : undefined}>
            <th scope="row" class="{TD} font-mono text-[0.875rem] font-medium whitespace-nowrap text-ink">
              {r.id}
              {#if r.kind}
                <span class="mt-0.5 block font-sans text-[0.75rem] font-normal text-muted-foreground">{r.kind}</span>
              {/if}
            </th>
            <td class={TD}>
              <span class="block font-medium text-ink">{r.title}</span>
              <span class="mt-0.5 block text-[0.8125rem] leading-snug text-muted-foreground">{r.setup}</span>
            </td>
            <td class={NUM_LEFT}>
              {#if r.score}
                <span class="text-ink">{r.score}</span>
                <span class="ml-1.5 font-sans text-[0.75rem] text-muted-foreground">{r.scoreKind}</span>
              {:else}
                <span
                  class="inline-block font-sans text-[0.8125rem] {r.planned
                    ? 'border border-dashed border-ink px-1.5 py-0.5 text-ink'
                    : 'text-muted-foreground'}">{r.scoreNote}</span
                >
              {/if}
              <span class="mt-1 block font-sans text-[0.75rem] leading-snug whitespace-normal text-muted-foreground"
                >{r.scoredOn}</span
              >
            </td>
            <td class={TD_LAST}>
              <span class="block">{r.note}</span>
              {#each r.caveats as c (c)}
                <span class="mt-1.5 block text-[0.8125rem] leading-snug text-muted-foreground">
                  <span class="font-medium text-ink-soft">{labels.caveatLabel}:</span>
                  {c}
                </span>
              {/each}
            </td>
          </tr>
        {/each}
      </tbody>
    </table>
  </ScrollRegion>
</div>
