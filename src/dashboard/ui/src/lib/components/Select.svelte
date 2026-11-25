<script lang="ts" module>
  export interface SelectOption {
    value: string;
    label: string;
    disabled?: boolean;
  }
</script>

<script lang="ts">
  interface Props {
    id: string;
    value: string;
    options: readonly SelectOption[];
    disabled?: boolean;
    invalid?: boolean;
    describedby?: string;
    onchange?: (value: string) => void;
  }

  let { id, value, options, disabled = false, invalid = false, describedby, onchange }: Props = $props();

  function handle(event: Event) {
    onchange?.((event.currentTarget as HTMLSelectElement).value);
  }
</script>

<div class="wrap" class:invalid>
  <select
    class="select"
    {id}
    {disabled}
    aria-invalid={invalid ? 'true' : undefined}
    aria-describedby={describedby}
    onchange={handle}
  >
    {#each options as option (option.value)}
      <option value={option.value} selected={option.value === value} disabled={option.disabled}>{option.label}</option>
    {/each}
  </select>
  <span class="chevron" aria-hidden="true"></span>
</div>

<style>
  .wrap {
    position: relative;
    width: 100%;
  }
  .select {
    width: 100%;
    min-height: 2.5rem;
    padding: 0 2.25rem 0 var(--space-3);
    border: 1px solid var(--control-edge);
    border-radius: var(--radius-control);
    background: var(--raised);
    color: var(--ink);
    font-size: var(--text-small);
    appearance: none;
    cursor: pointer;
  }
  .select:hover:not(:disabled) {
    border-color: var(--ink-soft);
  }
  .select:focus-visible {
    outline: 2px solid var(--accent);
    outline-offset: 1px;
    border-color: var(--accent);
  }
  .select:disabled {
    background: var(--sunken);
    color: var(--ink-soft);
    cursor: not-allowed;
  }
  .chevron {
    position: absolute;
    right: 0.9rem;
    top: 50%;
    width: 0.45rem;
    height: 0.45rem;
    margin-top: -0.35rem;
    border-right: 2px solid var(--ink-soft);
    border-bottom: 2px solid var(--ink-soft);
    transform: rotate(45deg);
    pointer-events: none;
  }
  .invalid .select {
    border-color: var(--destructive);
    box-shadow: inset 0 0 0 1px var(--destructive);
  }
</style>
