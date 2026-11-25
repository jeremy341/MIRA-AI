<script lang="ts">
  import type { Snippet } from 'svelte';

  interface Props {
    tone?: 'neutral' | 'accent' | 'success' | 'warning' | 'danger';
    /** Outline badges sit on a surface without a fill (for "Recommended", for example). */
    outline?: boolean;
    children: Snippet;
  }

  let { tone = 'neutral', outline = false, children }: Props = $props();
</script>

<span class="badge {tone}" class:outline>{@render children()}</span>

<style>
  .badge {
    display: inline-flex;
    align-items: center;
    gap: 0.3rem;
    min-height: 1.5rem;
    padding: 0.125rem 0.625rem;
    border-radius: var(--radius-pill);
    font-size: var(--text-micro);
    font-weight: var(--font-weight-medium);
    line-height: 1.2;
    white-space: nowrap;
    background: var(--sunken);
    color: var(--ink-soft);
  }
  .accent {
    background: var(--accent-subtle);
    color: var(--accent-strong);
  }
  .success {
    background: var(--success-subtle);
    color: var(--success-ink);
  }
  .warning {
    background: var(--warning-subtle);
    color: var(--warning-ink);
  }
  .danger {
    background: var(--destructive-subtle);
    color: var(--destructive);
  }
  .outline {
    background: var(--raised);
    box-shadow: inset 0 0 0 1px var(--rule-strong);
  }
</style>
