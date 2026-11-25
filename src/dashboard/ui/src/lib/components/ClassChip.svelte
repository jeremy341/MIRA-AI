<script lang="ts">
  import { CLASS_COLORS, CLASS_INK, CLASS_LABELS } from '../classes';
  import type { ClassName } from '../types';

  interface Props {
    className: ClassName;
    /** Shows a number after the name, such as a count or a confidence. */
    value?: string;
  }

  let { className, value }: Props = $props();
</script>

<span class="chip" style="--chip-fill: {CLASS_COLORS[className]}; --chip-ink: {CLASS_INK[className]};">
  <span class="swatch" aria-hidden="true"></span>
  <span class="name">{CLASS_LABELS[className]}</span>
  {#if value !== undefined}<span class="value">{value}</span>{/if}
</span>

<style>
  .chip {
    display: inline-flex;
    align-items: center;
    gap: 0.4rem;
    min-height: 1.5rem;
    padding: 0.125rem 0.6rem 0.125rem 0.45rem;
    border-radius: var(--radius-pill);
    background: var(--sunken);
    color: var(--ink);
    font-size: var(--text-micro);
    font-weight: var(--font-weight-medium);
    white-space: nowrap;
  }
  .swatch {
    width: 0.65rem;
    height: 0.65rem;
    border-radius: 3px;
    background: var(--chip-fill);
    box-shadow: inset 0 0 0 1px rgb(0 0 0 / 12%);
  }
  .value {
    font-family: var(--font-mono);
    font-variant-numeric: tabular-nums;
    color: var(--ink-soft);
  }
</style>
