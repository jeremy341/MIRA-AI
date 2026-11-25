<script lang="ts" module>
  export interface Column<T> {
    key: string;
    label: string;
    align?: 'left' | 'right';
    mono?: boolean;
    /** Value used when no cell snippet is given. */
    value?: (row: T) => string | number;
  }
</script>

<script lang="ts" generics="T">
  import type { Snippet } from 'svelte';

  interface Props {
    caption: string;
    columns: ReadonlyArray<Column<T>>;
    rows: readonly T[];
    rowKey: (row: T) => string;
    cell?: Snippet<[T, Column<T>]>;
  }

  let { caption, columns, rows, rowKey, cell }: Props = $props();
</script>

<div class="table-wrap">
  <table class="table">
    <caption class="visually-hidden">{caption}</caption>
    <thead>
      <tr>
        {#each columns as column (column.key)}
          <th scope="col" class:right={column.align === 'right'}>{column.label}</th>
        {/each}
      </tr>
    </thead>
    <tbody>
      {#each rows as row (rowKey(row))}
        <tr>
          {#each columns as column (column.key)}
            <td class:right={column.align === 'right'} class:mono={column.mono}>
              {#if cell}
                {@render cell(row, column)}
              {:else if column.value}
                {column.value(row)}
              {/if}
            </td>
          {/each}
        </tr>
      {/each}
    </tbody>
  </table>
</div>

<style>
  .table-wrap {
    width: 100%;
    overflow-x: auto;
  }
  .table {
    width: 100%;
    border-collapse: collapse;
    font-size: var(--text-small);
  }
  th,
  td {
    padding: var(--space-3) var(--space-3);
    border-bottom: 1px solid var(--rule);
    text-align: left;
    vertical-align: middle;
  }
  th {
    font-size: var(--text-micro);
    font-weight: var(--font-weight-medium);
    color: var(--ink-soft);
    white-space: nowrap;
  }
  td {
    color: var(--ink);
  }
  .right {
    text-align: right;
  }
  .mono {
    font-family: var(--font-mono);
    font-variant-numeric: tabular-nums;
    font-size: var(--text-micro);
  }
  tbody tr:hover {
    background: var(--app);
  }
</style>
