<script lang="ts" module>
  import type { ClassCounts } from '../../types';

  export interface StackedColumn {
    label: string;
    counts: ClassCounts;
  }
</script>

<script lang="ts">
  import { CLASS_COLORS, CLASS_LABELS } from '../../classes';
  import { CLASS_NAMES } from '../../types';
  import { linearScale, niceTicks } from '../../charts/scale';
  import { nextChartId } from './LineChart.svelte';

  interface Props {
    title: string;
    description: string;
    /** One column per time bucket. Each column stacks the class counts, bottom to top, in class order. */
    columns: readonly StackedColumn[];
    /** The column to mark, for example the replay position. */
    activeIndex?: number | null;
    /** Called when a column is clicked. Clicks are a pointer shortcut; the scrubber is the keyboard control. */
    onpick?: (index: number) => void;
    emptyText?: string;
    height?: number;
  }

  let { title, description, columns, activeIndex = null, onpick, emptyText = 'No detections in this session.', height = 200 }: Props =
    $props();

  const id = nextChartId();
  let width = $state(0);
  let showTable = $state(false);

  const left = 34;
  const right = 6;
  const top = 8;
  const bottom = 6;
  const plotWidth = $derived(Math.max(120, (width || 640) - left - right));
  const plotHeight = $derived(height - top - bottom);

  const totals = $derived(columns.map((c) => CLASS_NAMES.reduce((sum, cls) => sum + c.counts[cls], 0)));
  const peak = $derived(Math.max(0, ...totals));
  const ticks = $derived(niceTicks(0, Math.max(1, peak), 3));
  const yScale = $derived(linearScale([0, ticks[ticks.length - 1]], [top + plotHeight, top]));
  const band = $derived(columns.length ? plotWidth / columns.length : 0);
  const barWidth = $derived(Math.max(1, band * 0.78));
  const hasData = $derived(peak > 0);

  /** Segments for each column, bottom to top, as rectangles. */
  const segments = $derived(
    columns.map((column, index) => {
      const cx = left + band * index + band / 2;
      let base = 0;
      return CLASS_NAMES.map((cls) => {
        const value = column.counts[cls];
        const top0 = yScale(base + value);
        const bottom0 = yScale(base);
        base += value;
        return { cls, x: cx - barWidth / 2, y: top0, height: Math.max(0, bottom0 - top0) };
      });
    }),
  );
  const activeX = $derived(activeIndex !== null && columns.length ? left + band * activeIndex + band / 2 : null);
</script>

<figure class="stacked" bind:clientWidth={width}>
  <div class="head">
    <h3 class="title" id="{id}-title">{title}</h3>
    {#if hasData}
      <button
        type="button"
        class="toggle"
        aria-expanded={showTable}
        aria-controls="{id}-body"
        onclick={() => (showTable = !showTable)}
      >
        {showTable ? 'Show chart' : 'Show data table'}
      </button>
    {/if}
  </div>

  {#if !hasData}
    <p class="empty" role="status">{emptyText}</p>
  {:else if showTable}
    <div class="table-wrap" id="{id}-body">
      <table>
        <caption class="visually-hidden">{title}</caption>
        <thead>
          <tr>
            <th scope="col">Time</th>
            {#each CLASS_NAMES as cls}<th scope="col">{CLASS_LABELS[cls]}</th>{/each}
            <th scope="col">Total</th>
          </tr>
        </thead>
        <tbody>
          {#each columns as column, index}
            <tr class:current={index === activeIndex}>
              <th scope="row">{column.label}</th>
              {#each CLASS_NAMES as cls}<td>{column.counts[cls]}</td>{/each}
              <td>{totals[index]}</td>
            </tr>
          {/each}
        </tbody>
      </table>
    </div>
  {:else}
    <div class="plot" id="{id}-body">
      <svg viewBox="0 0 {width || 640} {height}" role="img" aria-labelledby="{id}-svg-title {id}-desc" class="svg">
        <title id="{id}-svg-title">{title}</title>
        <desc id="{id}-desc">{description}</desc>
        {#each ticks as tick (tick)}
          <line class="grid" x1={left} x2={left + plotWidth} y1={yScale(tick)} y2={yScale(tick)} />
          <text class="tick" x={left - 6} y={yScale(tick) + 4} text-anchor="end">{tick}</text>
        {/each}
        {#each segments as stack, index (index)}
          {#each stack as part (part.cls)}
            {#if part.height > 0}
              <rect x={part.x} y={part.y} width={barWidth} height={part.height} style="fill: {CLASS_COLORS[part.cls]}" />
            {/if}
          {/each}
        {/each}
        {#if onpick}
          {#each columns as _column, index (index)}
            <rect
              class="hit"
              aria-hidden="true"
              x={left + band * index}
              y={top}
              width={band}
              height={plotHeight}
              onclick={() => onpick?.(index)}
            />
          {/each}
        {/if}
        {#if activeX !== null}
          <line class="cursor" x1={activeX} x2={activeX} y1={top} y2={top + plotHeight} />
        {/if}
      </svg>
    </div>
    <ul class="legend" aria-label="Colours">
      {#each CLASS_NAMES as cls}
        <li><span class="swatch" style="background: {CLASS_COLORS[cls]}" aria-hidden="true"></span>{CLASS_LABELS[cls]}</li>
      {/each}
    </ul>
  {/if}
</figure>

<style>
  .stacked {
    display: grid;
    gap: var(--space-3);
    margin: 0;
    min-width: 0;
  }
  .head {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    justify-content: space-between;
    gap: var(--space-2);
  }
  .title {
    font-size: var(--text-small);
    font-weight: var(--font-weight-semibold);
  }
  .toggle {
    min-height: var(--target);
    padding: 0 var(--space-3);
    border: 1px solid var(--control-edge);
    border-radius: var(--radius-control);
    background: var(--raised);
    color: var(--ink);
    font-size: var(--text-micro);
    font-weight: var(--font-weight-medium);
    cursor: pointer;
  }
  .toggle:hover {
    background: var(--hover);
  }
  .svg {
    width: 100%;
    height: auto;
    overflow: visible;
  }
  .grid {
    stroke: var(--rule);
    stroke-width: 1;
  }
  .tick {
    fill: var(--ink-soft);
    font-family: var(--font-mono);
    font-size: 11px;
    font-variant-numeric: tabular-nums;
  }
  .hit {
    fill: transparent;
    cursor: pointer;
  }
  .cursor {
    stroke: var(--ink);
    stroke-width: 2;
  }
  .legend {
    display: flex;
    flex-wrap: wrap;
    gap: var(--space-2) var(--space-4);
    list-style: none;
    margin: 0;
    padding: 0;
    font-size: var(--text-micro);
    color: var(--ink-soft);
  }
  .legend li {
    display: inline-flex;
    align-items: center;
    gap: 0.375rem;
  }
  .swatch {
    width: 0.75rem;
    height: 0.75rem;
    border-radius: 3px;
  }
  .table-wrap {
    overflow-x: auto;
    max-height: 18rem;
  }
  table {
    width: 100%;
    border-collapse: collapse;
    font-size: var(--text-micro);
    font-variant-numeric: tabular-nums;
  }
  th,
  td {
    padding: var(--space-2);
    border-bottom: 1px solid var(--rule);
    text-align: right;
    white-space: nowrap;
  }
  th {
    color: var(--ink-soft);
    font-weight: var(--font-weight-medium);
  }
  th[scope='row'] {
    text-align: left;
  }
  .current {
    background: var(--accent-subtle);
  }
  .empty {
    display: grid;
    place-items: center;
    min-height: 6rem;
    padding: var(--space-4);
    border-radius: var(--radius-control);
    background: var(--app);
    color: var(--ink-soft);
    font-size: var(--text-small);
    text-align: center;
  }
</style>
