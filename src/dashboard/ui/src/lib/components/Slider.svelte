<script lang="ts">
  interface Props {
    id: string;
    value: number;
    min: number;
    max: number;
    step: number;
    /** Text for the value readout, for example a percentage. */
    format?: (value: number) => string;
    disabled?: boolean;
    describedby?: string;
    /** Names the slider for screen readers when the visible label is not enough. */
    ariaLabel?: string;
    oninput?: (value: number) => void;
  }

  let {
    id,
    value = $bindable(0),
    min,
    max,
    step,
    format = (v: number) => String(v),
    disabled = false,
    describedby,
    ariaLabel,
    oninput,
  }: Props = $props();

  const fill = $derived(max === min ? 0 : ((value - min) / (max - min)) * 100);

  function handle(event: Event) {
    const next = Number((event.currentTarget as HTMLInputElement).value);
    value = next;
    oninput?.(next);
  }
</script>

<div class="slider" style="--fill: {fill}%;">
  <input
    class="range"
    type="range"
    {id}
    {min}
    {max}
    {step}
    {value}
    {disabled}
    aria-describedby={describedby}
    aria-label={ariaLabel}
    aria-valuetext={format(value)}
    oninput={handle}
  />
  <output class="readout" for={id}>{format(value)}</output>
</div>

<style>
  .slider {
    display: grid;
    grid-template-columns: 1fr 4.5rem;
    align-items: center;
    gap: var(--space-3);
  }
  .range {
    width: 100%;
    min-height: var(--target);
    margin: 0;
    appearance: none;
    background: transparent;
    cursor: pointer;
  }
  .range::-webkit-slider-runnable-track {
    height: 0.375rem;
    border-radius: var(--radius-pill);
    background: linear-gradient(to right, var(--accent) var(--fill), var(--sunken) var(--fill));
  }
  .range::-moz-range-track {
    height: 0.375rem;
    border-radius: var(--radius-pill);
    background: var(--sunken);
  }
  .range::-moz-range-progress {
    height: 0.375rem;
    border-radius: var(--radius-pill);
    background: var(--accent);
  }
  .range::-webkit-slider-thumb {
    -webkit-appearance: none;
    width: 1.25rem;
    height: 1.25rem;
    margin-top: -0.4375rem;
    border-radius: 50%;
    background: var(--raised);
    border: 2px solid var(--accent-strong);
    box-shadow: var(--shadow-raised);
  }
  .range::-moz-range-thumb {
    width: 1.1rem;
    height: 1.1rem;
    border-radius: 50%;
    background: var(--raised);
    border: 2px solid var(--accent-strong);
  }
  .range:focus-visible {
    outline: 2px solid var(--accent);
    outline-offset: 4px;
    border-radius: var(--radius-pill);
  }
  .range:disabled {
    cursor: not-allowed;
    opacity: 0.5;
  }
  .readout {
    font-family: var(--font-mono);
    font-size: var(--text-micro);
    font-variant-numeric: tabular-nums;
    text-align: right;
    color: var(--ink);
  }
</style>
