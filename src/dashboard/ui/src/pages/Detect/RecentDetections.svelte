<script lang="ts">
  import { api, describeError } from '../../lib/api';
  import Button from '../../lib/components/Button.svelte';
  import Card from '../../lib/components/Card.svelte';
  import ClassChip from '../../lib/components/ClassChip.svelte';
  import Notice from '../../lib/components/Notice.svelte';
  import Table, { type Column } from '../../lib/components/Table.svelte';
  import { confidenceLabel } from './detect-logic';
  import { formatTime } from '../../lib/format';
  import type { Detection } from '../../lib/types';

  const RECENT_LIMIT = 20;

  let rows = $state.raw<Detection[] | null>(null);
  let busy = $state(false);
  let error = $state<string | null>(null);

  async function load() {
    busy = true;
    error = null;
    try {
      const response = await api.legacy.getRecentDetections(RECENT_LIMIT);
      rows = response.detections;
    } catch (err) {
      error = describeError(err, 'Recent detections are not available right now.');
    } finally {
      busy = false;
    }
  }

  const columns: Column<Detection>[] = [
    { key: 'time', label: 'Time', mono: true },
    { key: 'class', label: 'Class' },
    { key: 'confidence', label: 'Confidence', align: 'right', mono: true },
  ];

  const rowKey = (row: Detection) => `${row.timestamp}-${row.class_name}-${row.bbox.join(',')}`;
</script>

<Card title="Recent detections" description="The last 20 detections the server kept in memory.">
  {#snippet actions()}
    <Button variant="secondary" busy={busy} onclick={load}>{rows ? 'Refresh' : 'Load recent'}</Button>
  {/snippet}

  {#if error}
    <Notice tone="warning">{error}</Notice>
  {:else if rows && rows.length === 0}
    <p class="empty">No detections recorded yet.</p>
  {:else if rows}
    <Table caption="Recent detections" {columns} rows={rows} {rowKey}>
      {#snippet cell(row: Detection, column: Column<Detection>)}
        {#if column.key === 'time'}
          {formatTime(row.timestamp)}
        {:else if column.key === 'class'}
          <ClassChip className={row.class_name} />
        {:else}
          {confidenceLabel(row.confidence)}
        {/if}
      {/snippet}
    </Table>
  {:else}
    <p class="empty">Load the list to see the latest detections.</p>
  {/if}
</Card>

<style>
  .empty {
    font-size: var(--text-small);
    color: var(--ink-soft);
  }
</style>
