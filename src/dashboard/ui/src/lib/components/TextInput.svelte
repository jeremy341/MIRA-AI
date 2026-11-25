<script lang="ts">
  interface Props {
    id: string;
    value: string | number;
    type?: 'text' | 'number' | 'search';
    min?: number;
    max?: number;
    step?: number;
    placeholder?: string;
    disabled?: boolean;
    invalid?: boolean;
    describedby?: string;
    name?: string;
    maxlength?: number;
    inputmode?: 'numeric' | 'decimal' | 'text';
  }

  let {
    id,
    value = $bindable(''),
    type = 'text',
    min,
    max,
    step,
    placeholder,
    disabled = false,
    invalid = false,
    describedby,
    name,
    maxlength,
    inputmode,
  }: Props = $props();
</script>

<input
  class="input"
  class:invalid
  {id}
  {name}
  {type}
  bind:value
  {min}
  {max}
  {step}
  {placeholder}
  {disabled}
  {maxlength}
  {inputmode}
  aria-invalid={invalid ? 'true' : undefined}
  aria-describedby={describedby}
/>

<style>
  .input {
    width: 100%;
    min-height: 2.5rem;
    padding: 0 var(--space-3);
    border: 1px solid var(--control-edge);
    border-radius: var(--radius-control);
    background: var(--raised);
    color: var(--ink);
    font-size: var(--text-small);
    font-variant-numeric: tabular-nums;
    transition: border-color var(--dur-fast) ease-out;
  }
  .input::placeholder {
    color: var(--ink-soft);
    opacity: 0.85;
  }
  .input:hover:not(:disabled) {
    border-color: var(--ink-soft);
  }
  .input:focus-visible {
    outline: 2px solid var(--accent);
    outline-offset: 1px;
    border-color: var(--accent);
  }
  .input:disabled {
    background: var(--sunken);
    color: var(--ink-soft);
    cursor: not-allowed;
  }
  .invalid {
    border-color: var(--destructive);
    box-shadow: inset 0 0 0 1px var(--destructive);
  }
</style>
