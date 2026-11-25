<script lang="ts">
  import { untrack } from 'svelte';
  import { api, describeError } from '../../lib/api';
  import Button from '../../lib/components/Button.svelte';
  import ClassChip from '../../lib/components/ClassChip.svelte';
  import EmptyState from '../../lib/components/EmptyState.svelte';
  import Notice from '../../lib/components/Notice.svelte';
  import SegmentedControl from '../../lib/components/SegmentedControl.svelte';
  import StackedBars, { type StackedColumn } from '../../lib/components/charts/StackedBars.svelte';
  import { formatPercent } from '../../lib/format';
  import type { SessionDetection, SessionTimelineResponse } from '../../lib/types';
  import {
    REPLAY_SPEEDS,
    advancePosition,
    bucketCount,
    bucketIndexAt,
    chooseBucketSeconds,
    clampPosition,
    detectionsInWindow,
    formatClock,
    type ReplaySpeed,
  } from './replay-logic';

  interface Props {
    sessionId: string;
    durationSeconds: number;
  }

  let { sessionId, durationSeconds }: Props = $props();

  /** Detections are read in pages. The replay stops reading at this many rows and says so. */
  const DETECTION_PAGE = 500;
  const DETECTION_CAP = 5000;
  /** The list under the chart shows this many rows for the current bucket. */
  const LIST_CAP = 60;

  let timeline = $state<SessionTimelineResponse | null>(null);
  let detections = $state<SessionDetection[]>([]);
  let detectionsTotal = $state(0);
  let loading = $state(true);
  let error = $state<string | null>(null);
  let position = $state(0);
  let playing = $state(false);
  let speed = $state<ReplaySpeed>(1);

  const duration = $derived(Math.max(0, durationSeconds));
  const bucket = $derived(chooseBucketSeconds(duration));
  const count = $derived(bucketCount(duration, bucket));
  const current = $derived(bucketIndexAt(position, bucket, count));
  const windowStart = $derived(current * bucket);
  const windowEnd = $derived(windowStart + bucket);
  const inWindow = $derived(detectionsInWindow(detections, windowStart, windowEnd));
  const truncated = $derived(detectionsTotal > detections.length);
  const columns = $derived<StackedColumn[]>(
    (timeline?.buckets ?? []).map((item) => ({ label: formatClock(item.start_offset), counts: item.class_counts })),
  );
  const speedOptions = REPLAY_SPEEDS.map((value) => ({ value: String(value), label: `${value}x` }));

  async function load(id: string, seconds: number) {
    loading = true;
    error = null;
    try {
      const size = chooseBucketSeconds(seconds);
      const [timelineResponse, first] = await Promise.all([
        api.v1.getSessionTimeline(id, size),
        api.v1.getSessionDetections(id, { limit: DETECTION_PAGE, offset: 0 }),
      ]);
      timeline = timelineResponse;
      detectionsTotal = first.total;
      const rows = [...first.detections];
      while (rows.length < first.total && rows.length < DETECTION_CAP) {
        const page = await api.v1.getSessionDetections(id, { limit: DETECTION_PAGE, offset: rows.length });
        if (page.detections.length === 0) break;
        rows.push(...page.detections);
      }
      detections = rows.sort((a, b) => a.offset_seconds - b.offset_seconds);
    } catch (failure) {
      error = describeError(failure, 'The replay could not be loaded.');
    } finally {
      loading = false;
    }
  }

  $effect(() => {
    const id = sessionId;
    const seconds = durationSeconds;
    untrack(() => {
      position = 0;
      playing = false;
    });
    void load(id, seconds);
  });

  // Playback: the position moves with wall-clock time times the speed. It stops at the end, when the
  // page is hidden, and when the replay is unmounted. Reads of `position` inside the interval do not
  // re-run this effect, so it only restarts when play, pause or speed change.
  $effect(() => {
    if (!playing) return;
    const multiplier = speed;
    let last = performance.now();
    const timer = setInterval(() => {
      const now = performance.now();
      const step = advancePosition(position, (now - last) / 1000, multiplier, duration);
      last = now;
      position = step.position;
      if (step.ended) playing = false;
    }, 100);
    const onVisibility = () => {
      if (document.visibilityState === 'hidden') playing = false;
    };
    document.addEventListener('visibilitychange', onVisibility);
    return () => {
      clearInterval(timer);
      document.removeEventListener('visibilitychange', onVisibility);
    };
  });

  function togglePlay() {
    if (playing) {
      playing = false;
      return;
    }
    // At the end, play starts again from the top.
    if (duration > 0 && position >= duration) position = 0;
    playing = duration > 0;
  }

  function seek(value: number) {
    position = clampPosition(value, duration);
  }

  function onScrub(event: Event) {
    seek(Number((event.currentTarget as HTMLInputElement).value));
  }

  function onSpeed(value: string) {
    speed = Number(value) as ReplaySpeed;
  }

  function pick(index: number) {
    const item = timeline?.buckets[index];
    if (item) seek(item.start_offset);
  }
</script>

<div class="replay">
  {#if loading}
    <p class="note" role="status">Loading the timeline</p>
  {:else if error}
    <Notice tone="danger" title="The replay could not load">
      <p>{error}</p>
      {#snippet actions()}
        <Button variant="secondary" onclick={() => load(sessionId, durationSeconds)}>Try again</Button>
      {/snippet}
    </Notice>
  {:else if !timeline || duration === 0 || detectionsTotal === 0}
    <EmptyState compact icon="analytics" title="Nothing to replay" description="This session has no detections. Replay needs at least one." />
  {:else}
    <div class="controls">
      <Button variant="secondary" onclick={togglePlay}>
        {playing ? 'Pause' : 'Play'}
      </Button>
      <SegmentedControl label="Replay speed" value={String(speed)} options={speedOptions} onchange={onSpeed} />
      <p class="clock" aria-live="off">
        <span class="now">{formatClock(position)}</span>
        <span class="of">of {formatClock(duration)}</span>
      </p>
    </div>

    <label class="scrub">
      <span class="visually-hidden">Replay position</span>
      <input
        type="range"
        min="0"
        max={duration}
        step="0.1"
        value={position}
        oninput={onScrub}
        aria-valuetext="{formatClock(position)} of {formatClock(duration)}"
      />
    </label>

    <StackedBars
      title="Detections over the session"
      description="One column per {bucket} second{bucket === 1 ? '' : 's'}, stacked by class. Select a column to move the replay there."
      {columns}
      activeIndex={current}
      onpick={pick}
      height={180}
    />

    <section class="here" aria-labelledby="replay-here-title">
      <div class="here-head">
        <h3 id="replay-here-title" class="here-title">
          Detections from {formatClock(windowStart)} to {formatClock(Math.min(windowEnd, duration))}
        </h3>
        <p class="note">{inWindow.length} {inWindow.length === 1 ? 'detection' : 'detections'}</p>
      </div>
      {#if inWindow.length === 0}
        <p class="note">Nothing was detected in this part of the session.</p>
      {:else}
        <ul class="list">
          {#each inWindow.slice(0, LIST_CAP) as row, index (index + ':' + row.offset_seconds + ':' + row.class_name)}
            <li>
              <span class="time">{formatClock(row.offset_seconds)}</span>
              <ClassChip className={row.class_name} />
              <span class="conf">{formatPercent(row.confidence)}</span>
              <span class="track">{row.track_id === null ? 'no track' : `track ${row.track_id}`}</span>
            </li>
          {/each}
        </ul>
        {#if inWindow.length > LIST_CAP}
          <p class="note">Showing the first {LIST_CAP}. Scrub to a shorter span to see the rest.</p>
        {/if}
      {/if}
    </section>

    {#if truncated}
      <Notice tone="info">
        <p>Only the first {detections.length.toLocaleString('en-US')} of {detectionsTotal.toLocaleString('en-US')} detections are loaded for the replay. The export has every row.</p>
      </Notice>
    {/if}
  {/if}
</div>

<style>
  .replay {
    display: grid;
    gap: var(--space-4);
    min-width: 0;
  }
  .controls {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    gap: var(--space-3);
  }
  .clock {
    margin-left: auto;
    font-family: var(--font-mono);
    font-variant-numeric: tabular-nums;
    font-size: var(--text-small);
  }
  .now {
    font-weight: var(--font-weight-bold);
  }
  .of {
    color: var(--ink-soft);
  }
  .scrub input {
    width: 100%;
    min-height: var(--target);
    accent-color: var(--accent);
    cursor: pointer;
  }
  .here {
    display: grid;
    gap: var(--space-2);
    min-width: 0;
  }
  .here-head {
    display: flex;
    flex-wrap: wrap;
    justify-content: space-between;
    align-items: baseline;
    gap: var(--space-2);
  }
  .here-title {
    font-size: var(--text-small);
    font-weight: var(--font-weight-semibold);
  }
  .note {
    font-size: var(--text-micro);
    color: var(--ink-soft);
  }
  .list {
    display: grid;
    list-style: none;
    margin: 0;
    padding: 0;
    max-height: 18rem;
    overflow-y: auto;
  }
  .list li {
    display: grid;
    grid-template-columns: 4.5rem auto 4rem minmax(0, 1fr);
    align-items: center;
    gap: var(--space-3);
    min-height: 2.5rem;
    padding: var(--space-1) 0;
    border-bottom: 1px solid var(--rule);
    font-size: var(--text-micro);
    font-variant-numeric: tabular-nums;
  }
  .time,
  .conf {
    font-family: var(--font-mono);
  }
  .track {
    color: var(--ink-soft);
    text-align: right;
  }
  @media (max-width: 420px) {
    .list li {
      grid-template-columns: 4rem auto minmax(0, 1fr);
    }
    .conf {
      display: none;
    }
  }
</style>
