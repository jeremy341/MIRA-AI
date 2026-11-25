<script lang="ts">
  import Icon, { type IconName } from './Icon.svelte';

  interface Props {
    icon: IconName;
    /** Required: an icon alone is not a name for screen readers. */
    label: string;
    variant?: 'ghost' | 'secondary';
    disabled?: boolean;
    title?: string;
    onclick?: (event: MouseEvent) => void;
  }

  let { icon, label, variant = 'ghost', disabled = false, title, onclick }: Props = $props();
</script>

<button
  class="icon-btn {variant}"
  type="button"
  aria-label={label}
  title={title ?? label}
  {disabled}
  {onclick}
>
  <Icon name={icon} size={18} />
</button>

<style>
  .icon-btn {
    display: inline-grid;
    place-items: center;
    width: var(--target);
    height: var(--target);
    flex-shrink: 0;
    border: 0;
    border-radius: var(--radius-control);
    cursor: pointer;
    transition:
      background-color var(--dur-fast) ease-out,
      transform var(--dur-fast) var(--ease-out);
  }
  .icon-btn:active:not(:disabled) {
    transform: scale(0.94);
  }
  .icon-btn:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }
  .ghost {
    background: transparent;
    color: var(--ink-soft);
  }
  .ghost:hover:not(:disabled) {
    background: var(--hover);
    color: var(--ink);
  }
  .secondary {
    background: var(--accent-subtle);
    color: var(--accent-strong);
  }
  .secondary:hover:not(:disabled) {
    background: var(--accent-subtle-hover);
  }
</style>
