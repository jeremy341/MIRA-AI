<script lang="ts" module>
  let counter = 0;
  function nextId(): string {
    counter += 1;
    return `card-title-${counter}`;
  }
</script>

<script lang="ts">
  import type { Snippet } from 'svelte';

  interface Props {
    title?: string;
    description?: string;
    /** `card` is a standard surface, `panel` is the larger rounded variant for page-level groups. */
    variant?: 'card' | 'panel';
    /** Heading level for the title. Pages use h1; cards default to h2. */
    headingLevel?: 1 | 2 | 3;
    actions?: Snippet;
    footer?: Snippet;
    children: Snippet;
    id?: string;
  }

  let { title, description, variant = 'card', headingLevel = 2, actions, footer, children, id }: Props = $props();

  const titleId = nextId();
</script>

<section class="surface {variant}" aria-labelledby={title ? titleId : undefined} {id}>
  {#if title || actions}
    <header class="head">
      <div class="heading">
        {#if title}
          <svelte:element this={`h${headingLevel}`} id={titleId} class="title">{title}</svelte:element>
        {/if}
        {#if description}<p class="description">{description}</p>{/if}
      </div>
      {#if actions}<div class="actions">{@render actions()}</div>{/if}
    </header>
  {/if}
  <div class="body">
    {@render children()}
  </div>
  {#if footer}
    <footer class="foot">{@render footer()}</footer>
  {/if}
</section>

<style>
  .surface {
    background: var(--surface);
    border-radius: var(--radius-card);
    box-shadow: var(--shadow-raised);
    padding: var(--space-5);
    min-width: 0;
  }
  .panel {
    border-radius: var(--radius-panel);
    padding: var(--space-6);
  }
  .head {
    display: flex;
    flex-wrap: wrap;
    align-items: flex-start;
    justify-content: space-between;
    gap: var(--space-3);
    margin-bottom: var(--space-4);
  }
  .heading {
    min-width: 0;
  }
  .title {
    font-size: var(--text-title);
    font-weight: var(--font-weight-semibold);
    line-height: var(--text-title--line-height, 1.35);
  }
  .description {
    margin-top: var(--space-1);
    color: var(--ink-soft);
    font-size: var(--text-small);
  }
  .actions {
    display: flex;
    flex-wrap: wrap;
    gap: var(--space-2);
    align-items: center;
  }
  .body {
    min-width: 0;
  }
  .foot {
    margin-top: var(--space-4);
    padding-top: var(--space-4);
    border-top: 1px solid var(--rule);
  }
</style>
