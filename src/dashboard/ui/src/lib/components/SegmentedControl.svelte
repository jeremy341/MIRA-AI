<script lang="ts" module>
  export interface SegmentOption<V extends string> {
    value: V;
    label: string;
    disabled?: boolean;
  }
</script>

<script lang="ts" generics="V extends string">
  interface Props {
    label: string;
    value: V;
    options: ReadonlyArray<SegmentOption<V>>;
    disabled?: boolean;
    onchange?: (value: V) => void;
  }

  let { label, value, options, disabled = false, onchange }: Props = $props();

  function select(next: V) {
    if (disabled || next === value) return;
    onchange?.(next);
  }

  /** Arrow keys move the selection, as they do in a native radio group. */
  function onKey(event: KeyboardEvent, index: number) {
    const enabled = options.filter((o) => !o.disabled);
    if (enabled.length === 0) return;
    const current = enabled.findIndex((o) => o.value === options[index].value);
    let next = -1;
    if (event.key === 'ArrowRight' || event.key === 'ArrowDown') next = (current + 1) % enabled.length;
    if (event.key === 'ArrowLeft' || event.key === 'ArrowUp') next = (current - 1 + enabled.length) % enabled.length;
    if (next < 0) return;
    event.preventDefault();
    select(enabled[next].value);
    const button = (event.currentTarget as HTMLElement).parentElement?.querySelector<HTMLElement>(
      `[data-value="${enabled[next].value}"]`,
    );
    button?.focus();
  }
</script>

<div class="segmented" role="radiogroup" aria-label={label}>
  {#each options as option, index (option.value)}
    {@const selected = option.value === value}
    <button
      type="button"
      role="radio"
      class="segment"
      class:selected
      aria-checked={selected ? 'true' : 'false'}
      data-value={option.value}
      tabindex={selected ? 0 : -1}
      disabled={disabled || option.disabled}
      onclick={() => select(option.value)}
      onkeydown={(event) => onKey(event, index)}
    >
      {option.label}
    </button>
  {/each}
</div>

<style>
  .segmented {
    display: inline-flex;
    flex-wrap: wrap;
    gap: 0.25rem;
    padding: 0.25rem;
    border-radius: var(--radius-button);
    background: var(--sunken);
  }
  .segment {
    min-height: 2.25rem;
    padding: 0 0.9rem;
    border: 0;
    border-radius: var(--radius-control);
    background: transparent;
    color: var(--ink-soft);
    font-size: var(--text-small);
    font-weight: var(--font-weight-medium);
    cursor: pointer;
    transition:
      background-color var(--dur-fast) ease-out,
      color var(--dur-fast) ease-out;
  }
  .segment:hover:not(:disabled):not(.selected) {
    color: var(--ink);
  }
  .selected {
    background: var(--raised);
    color: var(--ink);
    box-shadow: var(--shadow-raised);
  }
  .segment:focus-visible {
    outline: 2px solid var(--accent);
    outline-offset: 1px;
  }
  .segment:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }
</style>
