<script lang="ts">
  import type { Snippet } from 'svelte';
  import Icon, { type IconName } from './Icon.svelte';

  interface Props {
    tone?: 'info' | 'success' | 'warning' | 'danger';
    title?: string;
    children: Snippet;
    actions?: Snippet;
  }

  let { tone = 'info', title, children, actions }: Props = $props();

  const icons: Record<typeof tone, IconName> = {
    info: 'info',
    success: 'check',
    warning: 'alert',
    danger: 'alert',
  };
</script>

<!-- Danger and warning are announced at once; informational notes wait for the screen reader. -->
<div class="notice {tone}" role={tone === 'danger' ? 'alert' : 'status'}>
  <span class="icon" aria-hidden="true"><Icon name={icons[tone]} size={18} /></span>
  <div class="body">
    {#if title}<p class="title">{title}</p>{/if}
    <div class="text">{@render children()}</div>
    {#if actions}<div class="actions">{@render actions()}</div>{/if}
  </div>
</div>

<style>
  .notice {
    display: flex;
    gap: var(--space-3);
    align-items: flex-start;
    padding: var(--space-3) var(--space-4);
    border-radius: var(--radius-control);
    font-size: var(--text-small);
    line-height: 1.5;
    background: var(--info-subtle);
    color: var(--ink);
  }
  .success {
    background: var(--success-subtle);
  }
  .warning {
    background: var(--warning-subtle);
  }
  .danger {
    background: var(--destructive-subtle);
  }
  .icon {
    display: flex;
    margin-top: 0.125rem;
    color: var(--info-ink);
  }
  .success .icon {
    color: var(--success-ink);
  }
  .warning .icon {
    color: var(--warning-ink);
  }
  .danger .icon {
    color: var(--destructive);
  }
  .body {
    min-width: 0;
    flex: 1;
  }
  .title {
    font-weight: var(--font-weight-semibold);
    margin-bottom: var(--space-1);
  }
  .text :global(p + p) {
    margin-top: var(--space-1);
  }
  .actions {
    display: flex;
    flex-wrap: wrap;
    gap: var(--space-2);
    margin-top: var(--space-2);
  }
</style>
