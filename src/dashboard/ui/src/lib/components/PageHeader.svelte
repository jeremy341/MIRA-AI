<script lang="ts">
  import type { Snippet } from 'svelte';

  interface Props {
    title: string;
    description?: string;
    eyebrow?: string;
    actions?: Snippet;
  }

  let { title, description, eyebrow, actions }: Props = $props();
</script>

<header class="page-header">
  <div class="text">
    {#if eyebrow}<p class="eyebrow">{eyebrow}</p>{/if}
    <h1 class="title">{title}</h1>
    {#if description}<p class="description">{description}</p>{/if}
  </div>
  {#if actions}<div class="actions">{@render actions()}</div>{/if}
</header>

<style>
  .page-header {
    display: flex;
    flex-wrap: wrap;
    align-items: flex-end;
    justify-content: space-between;
    gap: var(--space-4);
    margin-bottom: var(--space-6);
  }
  .text {
    min-width: 0;
    max-width: var(--measure);
  }
  .eyebrow {
    font-family: var(--font-mono);
    font-size: var(--text-micro);
    color: var(--ink-soft);
    text-transform: uppercase;
    letter-spacing: 0.06em;
    margin-bottom: var(--space-1);
  }
  .title {
    font-size: var(--text-display);
    font-weight: var(--font-weight-semibold);
    letter-spacing: -0.02em;
    line-height: var(--text-display--line-height, 1.15);
  }
  .description {
    margin-top: var(--space-2);
    color: var(--ink-soft);
    font-size: var(--text-lede);
    line-height: 1.5;
  }
  .actions {
    display: flex;
    flex-wrap: wrap;
    gap: var(--space-2);
    align-items: center;
  }
</style>
