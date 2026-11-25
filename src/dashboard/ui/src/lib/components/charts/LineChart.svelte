<script lang="ts" module>
  let counter = 0;
  export function nextChartId(): string {
    counter += 1;
    return `chart-${counter}`;
  }

  export interface LineSeries {
    label: string;
    /** A CSS colour: a token such as var(--accent), or a hex value. */
    color: string;
    values: ReadonlyArray<number | null>;
  }
</script>

<script lang="ts">
  import { extent, formatTick, linearScale, linePath, niceTicks, type Domain } from '../../charts/scale';

  interface Props {
    title: string;
    /** The text alternative: what the chart shows and how to read it. */
    description: string;
    /** Position of each sample along x, in the unit `xFormat` expects. Each series has one value per position. */
    x: readonly number[];
    series: readonly LineSeries[];
    xFormat?: (value: number) => string;
    yFormat?: (value: number) => string;
    /** A fixed y range. By default the axis starts at zero, or at the lowest value when that is below zero. */
    yDomain?: Domain;
    emptyText?: string;
    height?: number;
    /** Column heading for the data table, for the x values. */
    xHeading?: string;
  }

  let {
    title,
    description,
    x,
    series,
    xFormat = formatTick,
    yFormat = formatTick,
    yDomain,
    emptyText = 'No samples yet.',
    height = 220,
    xHeading = 'Position',
  }: Props = $props();

  const id = nextChartId();
  let width = $state(0);
  let showTable = $state(false);

  const left = 46;
  const right = 10;
  const top = 10;
  const bottom = 28;
  const plotWidth = $derived(Math.max(120, (width || 640) - left - right));
  const plotHeight = $derived(height - top - bottom);

  const hasData = $derived(series.some((s) => extent(s.values) !== null));
  const xDomain = $derived<Domain>(extent(x) ?? [0, 1]);
  const yExtent = $derived(extent(series.flatMap((s) => [...s.values])));
  const yBounds = $derived<Domain>(
    yDomain ?? (yExtent ? [Math.min(0, yExtent[0]), yExtent[1]] : [0, 1]),
  );
  const ticks = $derived(niceTicks(yBounds[0], yBounds[1], 4));
  const yScale = $derived(linearScale([ticks[0], ticks[ticks.length - 1]], [top + plotHeight, top]));
  const xScale = $derived(linearScale(xDomain, [left, left + plotWidth]));
  const paths = $derived(series.map((s) => linePath(x, s.values, xScale, yScale)));
  /** First, middle and last positions get a label. Fewer samples get fewer labels. */
  const labelled = $derived(
    x.length === 0 ? [] : [...new Set([0, Math.floor((x.length - 1) / 2), x.length - 1])],
  );
  const anchorFor = (index: number) => (index === 0 ? 'start' : index === x.length - 1 ? 'end' : 'middle');
</script>

<figure class="chart" bind:clientWidth={width}>
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
            <th scope="col">{xHeading}</th>
            {#each series as s}<th scope="col">{s.label}</th>{/each}
          </tr>
        </thead>
        <tbody>
          {#each x as value, index}
            <tr>
              <th scope="row">{xFormat(value)}</th>
              {#each series as s}
                <td>{typeof s.values[index] === 'number' ? yFormat(s.values[index] as number) : '-'}</td>
              {/each}
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
          <text class="tick" x={left - 8} y={yScale(tick) + 4} text-anchor="end">{yFormat(tick)}</text>
        {/each}
        {#each labelled as index (index)}
          <text class="tick" x={xScale(x[index])} y={height - 8} text-anchor={anchorFor(index)}>{xFormat(x[index])}</text>
        {/each}
        {#each series as s, i (s.label)}
          <path d={paths[i]} fill="none" class="line" style="stroke: {s.color}" />
        {/each}
      </svg>
    </div>
    <ul class="legend">
      {#each series as s (s.label)}
        <li><span class="swatch" style="background: {s.color}" aria-hidden="true"></span>{s.label}</li>
      {/each}
    </ul>
  {/if}
</figure>

<style>
  .chart {
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
  .plot {
    min-width: 0;
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
  .line {
    stroke-width: 2;
    stroke-linejoin: round;
    stroke-linecap: round;
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
    gap: var(--space-1-5, 0.375rem);
  }
  .swatch {
    width: 0.75rem;
    height: 0.75rem;
    border-radius: 3px;
  }
  .table-wrap {
    overflow-x: auto;
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
  th[scope='col']:first-child,
  th[scope='row'] {
    text-align: left;
  }
  .empty {
    display: grid;
    place-items: center;
    min-height: 8rem;
    padding: var(--space-4);
    border-radius: var(--radius-control);
    background: var(--app);
    color: var(--ink-soft);
    font-size: var(--text-small);
    text-align: center;
  }
</style>
