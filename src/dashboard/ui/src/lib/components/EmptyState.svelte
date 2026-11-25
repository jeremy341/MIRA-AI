<script lang="ts">
  import type { Snippet } from 'svelte';
  import Icon, { type IconName } from './Icon.svelte';

  interface Props {
    icon?: IconName;
    title: string;
    description?: string;
    /** Compact variant for use inside a card or a preview area. */
    compact?: boolean;
    actions?: Snippet;
  }

  let { icon = 'dot', title, description, compact = false, actions }: Props = $props();
</script>

<div class="empty" class:compact>
  <span class="mark" aria-hidden="true"><Icon name={icon} size={compact ? 20 : 24} /></span>
  <h2 class="title">{title}</h2>
  {#if description}<p class="description">{description}</p>{/if}
  {#if actions}<div class="actions">{@render actions()}</div>{/if}
</div>

<style>
  .empty {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    text-align: center;
    gap: var(--space-2);
    padding: var(--space-10) var(--space-5);
    color: var(--ink-soft);
    max-width: 34rem;
    margin: 0 auto;
  }
  .compact {
    padding: var(--space-6) var(--space-4);
  }
  .mark {
    display: grid;
    place-items: center;
    width: 3rem;
    height: 3rem;
    border-radius: var(--radius-card);
    background: var(--accent-subtle);
    color: var(--accent-strong);
    margin-bottom: var(--space-2);
  }
  .compact .mark {
    width: 2.5rem;
    height: 2.5rem;
  }
  .title {
    font-size: var(--text-title);
    font-weight: var(--font-weight-semibold);
    color: var(--ink);
  }
  .description {
    font-size: var(--text-small);
    line-height: 1.55;
    max-width: 30rem;
  }
  .actions {
    display: flex;
    flex-wrap: wrap;
    justify-content: center;
    gap: var(--space-2);
    margin-top: var(--space-2);
  }
</style>
