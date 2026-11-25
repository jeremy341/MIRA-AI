<script lang="ts">
  import { toasts } from '../stores/toasts.svelte';
  import Icon from './Icon.svelte';
  import IconButton from './IconButton.svelte';

  const icons = { success: 'check', error: 'alert', warning: 'alert', info: 'info' } as const;
</script>

<div class="region" aria-live="polite" aria-relevant="additions">
  {#each toasts.items as toast (toast.id)}
    <div class="toast {toast.kind}" role={toast.kind === 'error' ? 'alert' : 'status'}>
      <span class="icon" aria-hidden="true"><Icon name={icons[toast.kind]} size={18} /></span>
      <p class="message">{toast.message}</p>
      <IconButton icon="close" label="Dismiss notification" onclick={() => toasts.dismiss(toast.id)} />
    </div>
  {/each}
</div>

<style>
  /*
    Desktop: bottom right, the corner the page content rarely fills, so toasts do not cover the controls
    at the top of a page (the camera and image switch, for example). Newest at the bottom.
    Phone: just above the bottom tab bar. At most three are shown; each one dismisses itself.
  */
  .region {
    position: fixed;
    right: var(--space-4);
    bottom: var(--space-4);
    z-index: var(--z-toast);
    display: grid;
    gap: var(--space-2);
    width: min(24rem, calc(100vw - 2rem));
    pointer-events: none;
  }
  .toast {
    display: grid;
    grid-template-columns: auto 1fr auto;
    align-items: center;
    gap: var(--space-2);
    padding: var(--space-2) var(--space-2) var(--space-2) var(--space-3);
    border-radius: var(--radius-card);
    background: var(--raised);
    box-shadow: var(--shadow-floating);
    font-size: var(--text-small);
    pointer-events: auto;
    animation: enter var(--dur-base) var(--ease-out) both;
  }
  .toast.success .icon {
    color: var(--success-ink);
  }
  .toast.error .icon {
    color: var(--destructive);
  }
  .toast.warning .icon {
    color: var(--warning-ink);
  }
  .toast.info .icon {
    color: var(--accent-strong);
  }
  .icon {
    display: flex;
  }
  .message {
    min-width: 0;
    line-height: 1.45;
    overflow-wrap: anywhere;
  }
  @keyframes enter {
    from {
      opacity: 0;
      transform: translateY(6px);
    }
    to {
      opacity: 1;
      transform: translateY(0);
    }
  }
  @media (max-width: 899px) {
    .region {
      bottom: calc(var(--tabbar-height) + env(safe-area-inset-bottom, 0px) + var(--space-3));
      left: var(--space-4);
      right: var(--space-4);
      width: auto;
    }
  }
</style>
