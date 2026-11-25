<script lang="ts">
  import { onMount } from 'svelte';
  import { api, describeError } from '../../lib/api';
  import BarList from '../../lib/components/charts/BarList.svelte';
  import LineChart from '../../lib/components/charts/LineChart.svelte';
  import Card from '../../lib/components/Card.svelte';
  import EmptyState from '../../lib/components/EmptyState.svelte';
  import Notice from '../../lib/components/Notice.svelte';
  import Select from '../../lib/components/Select.svelte';
  import StatTile from '../../lib/components/StatTile.svelte';
  import { CLASS_COLORS, CLASS_LABELS } from '../../lib/classes';
  import { formatDuration, formatPercent } from '../../lib/format';
  import { formatTick } from '../../lib/charts/scale';
  import { CLASS_NAMES, type SessionDetail, type SessionSummary, type SessionTimelineResponse } from '../../lib/types';
  import { chooseBucketSeconds, formatClock } from '../Sessions/replay-logic';
  import { sortNewestFirst } from '../Sessions/session-list';

  let sessions = $state<SessionSummary[]>([]);
  let sessionId = $state('');
  let detail = $state<SessionDetail | null>(null);
  let timeline = $state<SessionTimelineResponse | null>(null);
  let loadingList = $state(true);
  let loading = $state(false);
  let error = $state<string | null>(null);

  const options = $derived(
    sessions.map((session) => ({ value: session.id, label: `${session.name} (${session.total_detections} detections)` })),
  );
  const classRows = $derived(
    detail
      ? CLASS_NAMES.map((cls) => ({ label: CLASS_LABELS[cls], value: detail?.class_counts[cls] ?? 0, color: CLASS_COLORS[cls] }))
      : [],
  );

  onMount(() => {
    void api.v1
      .listSessions({ limit: 50 })
      .then((page) => {
        sessions = sortNewestFirst(page.sessions);
        if (sessions.length) sessionId = sessions[0].id;
      })
      .catch((failure: unknown) => {
        error = describeError(failure, 'The sessions could not be listed.');
      })
      .finally(() => {
        loadingList = false;
      });
  });

  $effect(() => {
    const id = sessionId;
    if (!id) return;
    let stale = false;
    loading = true;
    error = null;
    void (async () => {
      try {
        const next = await api.v1.getSession(id);
        const size = chooseBucketSeconds(next.duration_seconds);
        const series = await api.v1.getSessionTimeline(id, size);
        if (stale) return;
        detail = next;
        timeline = series;
      } catch (failure) {
        if (!stale) error = describeError(failure, 'This session could not be loaded.');
      } finally {
        if (!stale) loading = false;
      }
    })();
    return () => {
      stale = true;
    };
  });

  const xs = $derived(timeline ? timeline.buckets.map((bucket) => bucket.start_offset) : []);
  const objectsSeries = $derived(timeline ? timeline.buckets.map((bucket) => bucket.objects) : []);
  const bucket = $derived(timeline?.bucket_seconds ?? 1);
</script>

<Card title="Session" description="Pick a session to see its class mix and how many objects it found over time.">
  {#if loadingList}
    <p class="note" role="status">Loading sessions</p>
  {:else if sessions.length === 0}
    <EmptyState compact icon="sessions" title="No sessions to analyse" description="Record a session on Detect or import a video. Its numbers appear here." />
  {:else}
    <div class="pick">
      <Select id="analytics-session" value={sessionId} {options} onchange={(value) => (sessionId = value)} />
    </div>

    {#if error}
      <Notice tone="danger"><p>{error}</p></Notice>
    {:else if loading || !detail || !timeline}
      <p class="note" role="status">Loading the session</p>
    {:else}
      <div class="tiles">
        <StatTile label="Detections" value={detail.total_detections.toLocaleString('en-US')} />
        <StatTile label="Average confidence" value={formatPercent(detail.avg_confidence)} />
        <StatTile label="Duration" value={formatDuration(detail.duration_seconds)} />
      </div>
      <div class="charts">
        <div class="chart-block">
          <LineChart
            title="Objects over time"
            description="Objects found in each {bucket}-second bucket of the session. Time runs from the start of the session."
            x={xs}
            series={[{ label: 'Objects', color: 'var(--accent)', values: objectsSeries }]}
            xFormat={formatClock}
            yFormat={formatTick}
            xHeading="Time"
            emptyText="This session has no detections to plot."
          />
        </div>
        <div class="chart-block">
          <h3 class="block-title">Class mix</h3>
          <BarList label="Detections per class" items={classRows} format={(value) => value.toLocaleString('en-US')} emptyText="No detections were recorded." />
        </div>
      </div>
    {/if}
  {/if}
</Card>

<style>
  .pick {
    margin-bottom: var(--space-4);
    max-width: 32rem;
  }
  .note {
    font-size: var(--text-small);
    color: var(--ink-soft);
  }
  .tiles {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(10rem, 1fr));
    gap: var(--space-3);
    margin-bottom: var(--space-5);
  }
  .charts {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(min(100%, 22rem), 1fr));
    gap: var(--space-6);
    align-items: start;
  }
  .block-title {
    font-size: var(--text-small);
    font-weight: var(--font-weight-semibold);
    margin-bottom: var(--space-3);
  }
</style>
