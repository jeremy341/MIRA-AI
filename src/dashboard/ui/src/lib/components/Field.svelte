<script lang="ts">
  import type { Snippet } from 'svelte';
  import { errorId, hintId } from './field-ids';

  interface Props {
    id: string;
    label: string;
    hint?: string;
    error?: string;
    /** Puts the label beside the control (for toggles and checkboxes). */
    inline?: boolean;
    children: Snippet;
  }

  let { id, label, hint, error, inline = false, children }: Props = $props();
</script>

<div class="field" class:inline class:invalid={Boolean(error)}>
  <label class="label" for={id}>{label}</label>
  <div class="control">
    {@render children()}
    {#if hint && !error}<p class="hint" id={hintId(id)}>{hint}</p>{/if}
    {#if error}<p class="error" id={errorId(id)}>{error}</p>{/if}
  </div>
</div>

<style>
  .field {
    display: grid;
    gap: var(--space-1-5, 0.375rem);
    min-width: 0;
  }
  .label {
    font-size: var(--text-small);
    font-weight: var(--font-weight-medium);
    color: var(--ink);
  }
  .control {
    min-width: 0;
  }
  .hint {
    margin-top: var(--space-1);
    font-size: var(--text-micro);
    color: var(--ink-soft);
    line-height: 1.45;
  }
  .error {
    margin-top: var(--space-1);
    font-size: var(--text-micro);
    color: var(--destructive);
    font-weight: var(--font-weight-medium);
    line-height: 1.45;
  }
  .inline {
    grid-template-columns: 1fr auto;
    align-items: center;
  }
  .inline .control {
    display: flex;
    justify-content: flex-end;
  }
</style>
