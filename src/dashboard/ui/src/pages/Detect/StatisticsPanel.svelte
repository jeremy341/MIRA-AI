<script lang="ts">
  import { onMount } from 'svelte';
  import { api, describeError } from '../../lib/api';
  import Card from '../../lib/components/Card.svelte';
  import ClassChip from '../../lib/components/ClassChip.svelte';
  import Notice from '../../lib/components/Notice.svelte';
  import Spinner from '../../lib/components/Spinner.svelte';
  import StatTile from '../../lib/components/StatTile.svelte';
  import { CLASS_COLORS } from '../../lib/classes';
  import { CLASS_NAMES } from '../../lib/types';
  import type { StatisticsSnapshot } from '../../lib/types';
  import { confidenceLabel } from './detect-logic';

  const REFRESH_MS = 5000;
  const PERIOD_SECONDS = 60;

  let snapshot = $state.raw<StatisticsSnapshot | null>(null);
  let error = $state<string | null>(null);
  let loading = $state(true);

  async function refresh() {
    // Polling pauses while the tab is hidden, so an idle page does not keep the server busy.
    if (document.hidden) return;
    try {
      const response = await api.legacy.getStatistics(PERIOD_SECONDS);
      snapshot = response.statistics;
      error = null;
    } catch (err) {
      error = describeError(err, 'Statistics are not available right now.');
    } finally {
      loading = false;
    }
  }

  onMount(() => {
    void refresh();
    const timer = setInterval(() => void refresh(), REFRESH_MS);
    return () => clearInterval(timer);
  });

  const maxCount = $derived(
    Math.max(1, ...CLASS_NAMES.map((cls) => snapshot?.class_counts[cls] ?? 0)),
  );
</script>

<Card title="Last minute" description="Detections from the server over the last 60 seconds.">
  {#if loading}
    <div class="loading"><Spinner label="Loading statistics" /></div>
  {:else if error}
    <Notice tone="warning">{error}</Notice>
  {:else if snapshot}
    <div class="tiles">
      <StatTile label="Detections" value={snapshot.total_detections} hint="in 60 s" />
      <StatTile
        label="Avg confidence"
        value={snapshot.average_confidence === null ? '-' : confidenceLabel(snapshot.average_confidence)}
        hint={snapshot.average_confidence === null ? 'No detections yet' : 'across all classes'}
      />
    </div>
    <ul class="bars" aria-label="Detections per class">
      {#each CLASS_NAMES as cls (cls)}
        {@const count = snapshot.class_counts[cls] ?? 0}
        <li class="bar-row">
          <ClassChip className={cls} />
          <span class="track" aria-hidden="true"><span class="fill" style="width: {(count / maxCount) * 100}%; background: {CLASS_COLORS[cls]};"></span></span>
          <span class="count">{count}</span>
        </li>
      {/each}
    </ul>
  {/if}
</Card>

<style>
  .loading {
    display: grid;
    place-items: center;
    min-height: 6rem;
    color: var(--ink-soft);
  }
  .tiles {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: var(--space-3);
    margin-bottom: var(--space-4);
  }
  .bars {
    display: grid;
    gap: var(--space-2);
    margin: 0;
    padding: 0;
    list-style: none;
  }
  .bar-row {
    display: grid;
    grid-template-columns: 6.5rem 1fr 2rem;
    align-items: center;
    gap: var(--space-2);
  }
  .track {
    display: block;
    height: 0.5rem;
    border-radius: var(--radius-pill);
    background: var(--sunken);
    overflow: hidden;
  }
  .fill {
    display: block;
    height: 100%;
    border-radius: inherit;
    background: var(--ink-soft);
    transition: width var(--dur-base) var(--ease-out);
  }
  .count {
    font-family: var(--font-mono);
    font-size: var(--text-micro);
    text-align: right;
    font-variant-numeric: tabular-nums;
  }
  @media (prefers-reduced-motion: reduce) {
    .fill {
      transition: none;
    }
  }
</style>
