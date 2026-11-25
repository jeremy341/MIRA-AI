<script lang="ts">
  import Sparkline from './Sparkline.svelte';

  interface Props {
    label: string;
    value: string | number;
    unit?: string;
    hint?: string;
    /** Optional recent values, drawn as a small line. */
    trend?: number[];
    trendLabel?: string;
  }

  let { label, value, unit, hint, trend, trendLabel }: Props = $props();
</script>

<div class="tile">
  <p class="label">{label}</p>
  <p class="value">
    <span class="number">{value}</span>
    {#if unit}<span class="unit">{unit}</span>{/if}
  </p>
  {#if trend && trend.length > 1}
    <div class="trend">
      <Sparkline values={trend} label={trendLabel ?? `${label} over time`} />
    </div>
  {/if}
  {#if hint}<p class="hint">{hint}</p>{/if}
</div>

<style>
  .tile {
    display: grid;
    gap: var(--space-1);
    min-width: 0;
    padding: var(--space-4);
    border-radius: var(--radius-card);
    background: var(--surface);
    box-shadow: var(--shadow-raised);
  }
  .label {
    font-size: var(--text-micro);
    color: var(--ink-soft);
    font-weight: var(--font-weight-medium);
  }
  .value {
    display: flex;
    align-items: baseline;
    gap: var(--space-1);
    min-width: 0;
    line-height: 1.1;
  }
  .number {
    font-family: var(--font-mono);
    font-size: var(--text-stat);
    font-weight: var(--font-weight-bold);
    font-variant-numeric: tabular-nums;
    letter-spacing: -0.02em;
    overflow-wrap: anywhere;
  }
  .unit {
    font-family: var(--font-mono);
    font-size: var(--text-micro);
    color: var(--ink-soft);
  }
  .trend {
    margin-top: var(--space-1);
  }
  .hint {
    font-size: var(--text-micro);
    color: var(--ink-soft);
  }
</style>
