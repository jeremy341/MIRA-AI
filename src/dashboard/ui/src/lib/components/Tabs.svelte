<script lang="ts" module>
  export interface TabItem<V extends string> {
    value: V;
    label: string;
    count?: number;
  }
</script>

<script lang="ts" generics="V extends string">
  interface Props {
    label: string;
    value: V;
    items: ReadonlyArray<TabItem<V>>;
    onchange?: (value: V) => void;
    /** Element id prefix so each tab can be linked to its panel with aria-controls. */
    idPrefix?: string;
  }

  let { label, value, items, onchange, idPrefix = 'tab' }: Props = $props();

  function onKey(event: KeyboardEvent, index: number) {
    let next = -1;
    if (event.key === 'ArrowRight') next = (index + 1) % items.length;
    if (event.key === 'ArrowLeft') next = (index - 1 + items.length) % items.length;
    if (event.key === 'Home') next = 0;
    if (event.key === 'End') next = items.length - 1;
    if (next < 0) return;
    event.preventDefault();
    onchange?.(items[next].value);
    (event.currentTarget as HTMLElement).parentElement?.querySelector<HTMLElement>(`#${idPrefix}-${items[next].value}`)?.focus();
  }
</script>

<div class="tabs" role="tablist" aria-label={label}>
  {#each items as item, index (item.value)}
    {@const selected = item.value === value}
    <button
      type="button"
      role="tab"
      id="{idPrefix}-{item.value}"
      class="tab"
      class:selected
      aria-selected={selected ? 'true' : 'false'}
      aria-controls="{idPrefix}-panel"
      tabindex={selected ? 0 : -1}
      onclick={() => onchange?.(item.value)}
      onkeydown={(event) => onKey(event, index)}
    >
      <span>{item.label}</span>
      {#if item.count !== undefined}<span class="count">{item.count}</span>{/if}
    </button>
  {/each}
</div>

<style>
  .tabs {
    display: flex;
    gap: var(--space-1);
    overflow-x: auto;
    border-bottom: 1px solid var(--rule);
    scrollbar-width: none;
  }
  .tab {
    display: inline-flex;
    align-items: center;
    gap: var(--space-2);
    min-height: 2.75rem;
    padding: 0 var(--space-3);
    margin-bottom: -1px;
    border: 0;
    border-bottom: 2px solid transparent;
    background: transparent;
    color: var(--ink-soft);
    font-size: var(--text-small);
    font-weight: var(--font-weight-medium);
    white-space: nowrap;
    cursor: pointer;
  }
  .tab:hover {
    color: var(--ink);
  }
  .selected {
    color: var(--accent-strong);
    border-bottom-color: var(--accent-strong);
  }
  .tab:focus-visible {
    outline: 2px solid var(--accent);
    outline-offset: -2px;
    border-radius: var(--radius-control) var(--radius-control) 0 0;
  }
  .count {
    font-family: var(--font-mono);
    font-size: var(--text-micro);
    padding: 0 0.4rem;
    border-radius: var(--radius-pill);
    background: var(--sunken);
    color: var(--ink-soft);
  }
</style>
