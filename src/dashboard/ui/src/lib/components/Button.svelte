<script lang="ts">
  import type { Snippet } from 'svelte';
  import Spinner from './Spinner.svelte';

  interface Props {
    variant?: 'primary' | 'secondary' | 'danger' | 'ghost';
    size?: 'md' | 'lg';
    type?: 'button' | 'submit';
    /** Renders a link styled as a button. */
    href?: string;
    disabled?: boolean;
    /** Shows a spinner and blocks clicks. The label stays, so the width does not jump. */
    busy?: boolean;
    block?: boolean;
    title?: string;
    onclick?: (event: MouseEvent) => void;
    children: Snippet;
  }

  let {
    variant = 'primary',
    size = 'md',
    type = 'button',
    href,
    disabled = false,
    busy = false,
    block = false,
    title,
    onclick,
    children,
  }: Props = $props();

  const inactive = $derived(disabled || busy);
</script>

{#if href}
  <a
    class="btn {variant} {size}"
    class:block
    class:inactive
    {href}
    {title}
    aria-disabled={inactive ? 'true' : undefined}
    tabindex={inactive ? -1 : undefined}
  >
    {@render children()}
  </a>
{:else}
  <button
    class="btn {variant} {size}"
    class:block
    {type}
    {title}
    disabled={inactive}
    aria-busy={busy ? 'true' : undefined}
    {onclick}
  >
    {#if busy}<Spinner size="sm" />{/if}
    {@render children()}
  </button>
{/if}

<style>
  .btn {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    gap: var(--space-2);
    min-height: var(--target);
    padding: 0 1.125rem;
    border: 1px solid transparent;
    border-radius: var(--radius-button);
    font-family: var(--font-sans);
    font-size: var(--text-small);
    font-weight: var(--font-weight-medium);
    line-height: 1;
    white-space: nowrap;
    text-decoration: none;
    cursor: pointer;
    user-select: none;
    transition:
      background-color var(--dur-fast) ease-out,
      border-color var(--dur-fast) ease-out,
      transform var(--dur-fast) var(--ease-out);
  }

  .btn:active:not(.inactive) {
    transform: scale(0.97);
  }

  .lg {
    min-height: 3rem;
    padding: 0 1.5rem;
    font-size: 1rem;
  }

  .block {
    display: flex;
    width: 100%;
  }

  .primary {
    background: var(--ink);
    color: var(--surface);
  }
  .primary:hover:not(.inactive) {
    background: #000;
  }

  .secondary {
    background: var(--accent-subtle);
    color: var(--accent-strong);
  }
  .secondary:hover:not(.inactive) {
    background: var(--accent-subtle-hover);
  }

  .danger {
    background: var(--destructive);
    color: var(--on-accent);
  }
  .danger:hover:not(.inactive) {
    background: #951f21;
  }

  .ghost {
    background: transparent;
    color: var(--ink-soft);
  }
  .ghost:hover:not(.inactive) {
    background: var(--hover);
    color: var(--ink);
  }

  .inactive {
    opacity: 0.5;
    cursor: not-allowed;
  }
</style>
