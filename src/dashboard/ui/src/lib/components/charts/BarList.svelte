<script lang="ts" module>
  export interface BarItem {
    label: string;
    value: number;
    /** A CSS colour for the bar. Defaults to the accent. */
    color?: string;
    /** A short line under the label, such as the average confidence. */
    detail?: string;
  }
</script>

<script lang="ts">
  import { formatPercent } from '../../format';

  interface Props {
    /** Names the list for screen readers. */
    label: string;
    items: readonly BarItem[];
    /** Formats the value. The share of the total is shown after it. */
    format?: (value: number) => string;
    emptyText?: string;
  }

  let { label, items, format = (value: number) => value.toLocaleString('en-US'), emptyText = 'Nothing to show yet.' }: Props =
    $props();

  const total = $derived(items.reduce((sum, item) => sum + Math.max(0, item.value), 0));
  const largest = $derived(Math.max(0, ...items.map((item) => item.value)));
</script>

{#if items.length === 0 || total === 0}
  <p class="empty" role="status">{emptyText}</p>
{:else}
  <ul class="bars" aria-label={label}>
    {#each items as item (item.label)}
      {@const share = total > 0 ? item.value / total : 0}
      <li class="row">
        <div class="line">
          <span class="name">{item.label}</span>
          <span class="value">{format(item.value)} <span class="share">({formatPercent(share)})</span></span>
        </div>
        <div class="track" aria-hidden="true">
          <div class="fill" style="width: {largest > 0 ? (item.value / largest) * 100 : 0}%; background: {item.color ?? 'var(--accent)'}"></div>
        </div>
        {#if item.detail}<p class="detail">{item.detail}</p>{/if}
      </li>
    {/each}
  </ul>
{/if}

<style>
  .bars {
    display: grid;
    gap: var(--space-3);
    list-style: none;
    margin: 0;
    padding: 0;
    min-width: 0;
  }
  .row {
    display: grid;
    gap: 0.375rem;
    min-width: 0;
  }
  .line {
    display: flex;
    flex-wrap: wrap;
    justify-content: space-between;
    align-items: baseline;
    gap: var(--space-1) var(--space-3);
    font-size: var(--text-small);
  }
  .name {
    font-weight: var(--font-weight-medium);
    min-width: 0;
    overflow-wrap: anywhere;
  }
  .value {
    font-family: var(--font-mono);
    font-size: var(--text-micro);
    font-variant-numeric: tabular-nums;
    white-space: nowrap;
  }
  .share {
    color: var(--ink-soft);
  }
  .track {
    height: 0.625rem;
    border-radius: var(--radius-pill);
    background: var(--sunken);
    overflow: hidden;
  }
  .fill {
    height: 100%;
    border-radius: var(--radius-pill);
    transition: width var(--dur-base) var(--ease-out);
  }
  .detail {
    font-size: var(--text-micro);
    color: var(--ink-soft);
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
  @media (prefers-reduced-motion: reduce) {
    .fill {
      transition: none;
    }
  }
</style>
