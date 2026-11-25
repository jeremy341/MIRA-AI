<script lang="ts">
  import type { Snippet } from 'svelte';

  interface Props {
    id: string;
    checked: boolean;
    disabled?: boolean;
    describedby?: string;
    onchange?: (checked: boolean) => void;
    children: Snippet;
  }

  let { id, checked = $bindable(false), disabled = false, describedby, onchange, children }: Props = $props();

  function toggle() {
    if (disabled) return;
    checked = !checked;
    onchange?.(checked);
  }
</script>

<button
  class="toggle"
  type="button"
  role="switch"
  {id}
  aria-checked={checked ? 'true' : 'false'}
  aria-describedby={describedby}
  {disabled}
  onclick={toggle}
>
  <span class="text">{@render children()}</span>
  <span class="track" class:on={checked} aria-hidden="true"><span class="knob"></span></span>
</button>

<style>
  .toggle {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: var(--space-3);
    width: 100%;
    min-height: 2.5rem;
    padding: 0;
    border: 0;
    background: transparent;
    color: var(--ink);
    font-size: var(--text-small);
    text-align: left;
    cursor: pointer;
  }
  .toggle:disabled {
    cursor: not-allowed;
    opacity: 0.55;
  }
  .toggle:focus-visible {
    outline: 2px solid var(--accent);
    outline-offset: 3px;
    border-radius: var(--radius-control);
  }
  .track {
    position: relative;
    flex-shrink: 0;
    width: 2.75rem;
    height: 1.625rem;
    border-radius: var(--radius-pill);
    background: var(--rule-strong);
    transition: background-color var(--dur-base) var(--ease-out);
  }
  .track.on {
    background: var(--accent);
  }
  .knob {
    position: absolute;
    top: 0.1875rem;
    left: 0.1875rem;
    width: 1.25rem;
    height: 1.25rem;
    border-radius: 50%;
    background: var(--raised);
    box-shadow: 0 1px 2px rgb(0 0 0 / 20%);
    transition: transform var(--dur-base) var(--ease-out);
  }
  .on .knob {
    transform: translateX(1.125rem);
  }
  @media (prefers-reduced-motion: reduce) {
    .track,
    .knob {
      transition: none;
    }
  }
</style>
