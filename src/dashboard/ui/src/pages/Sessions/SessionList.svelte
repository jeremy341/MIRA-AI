<script lang="ts">
  import { onMount } from 'svelte';
  import { api, describeError, isRouteMissing } from '../../lib/api';
  import Badge from '../../lib/components/Badge.svelte';
  import Button from '../../lib/components/Button.svelte';
  import EmptyState from '../../lib/components/EmptyState.svelte';
  import Notice from '../../lib/components/Notice.svelte';
  import StatusDot from '../../lib/components/StatusDot.svelte';
  import { formatDateTime, formatDuration } from '../../lib/format';
  import { startPolling } from '../../lib/poll';
  import type { SessionSummary } from '../../lib/types';
  import { PAGE_SIZE, hasMore, isLive, mergeSessionPages, sortNewestFirst, sourceLabel, statusLabel } from './session-list';

  let sessions = $state<SessionSummary[]>([]);
  let total = $state(0);
  let loading = $state(true);
  let loadingMore = $state(false);
  let error = $state<string | null>(null);
  let unavailable = $state(false);

  async function loadFirst(limit: number) {
    try {
      const page = await api.v1.listSessions({ limit, offset: 0 });
      sessions = sortNewestFirst(page.sessions);
      total = page.total;
      error = null;
      unavailable = false;
    } catch (failure) {
      if (isRouteMissing(failure)) {
        unavailable = true;
        sessions = [];
        total = 0;
      } else {
        error = describeError(failure, 'The sessions could not be loaded.');
      }
    } finally {
      loading = false;
    }
  }

  async function loadMore() {
    loadingMore = true;
    try {
      const page = await api.v1.listSessions({ limit: PAGE_SIZE, offset: sessions.length });
      sessions = mergeSessionPages(sessions, page.sessions);
      total = page.total;
    } catch (failure) {
      error = describeError(failure, 'More sessions could not be loaded.');
    } finally {
      loadingMore = false;
    }
  }

  onMount(() => {
    // Keep what the list shows fresh while the page is open, without shrinking a list the user has paged through.
    const stop = startPolling(() => loadFirst(Math.max(PAGE_SIZE, sessions.length)), { intervalMs: 5000, immediate: false });
    void loadFirst(PAGE_SIZE);
    return stop;
  });
</script>

<section class="list" aria-labelledby="sessions-list-title">
  <div class="list-head">
    <h2 id="sessions-list-title" class="heading">Recent sessions</h2>
    {#if !loading && !unavailable}
      <p class="count" aria-live="polite">{total} {total === 1 ? 'session' : 'sessions'}</p>
    {/if}
  </div>

  {#if loading}
    <p class="note" role="status">Loading sessions</p>
  {:else if unavailable}
    <EmptyState icon="sessions" title="Sessions are not available yet" description="This server does not have the sessions API. The list appears once it is running." />
  {:else if error}
    <Notice tone="danger" title="The list could not load">
      <p>{error}</p>
      {#snippet actions()}
        <Button variant="secondary" onclick={() => loadFirst(PAGE_SIZE)}>Try again</Button>
      {/snippet}
    </Notice>
  {:else if sessions.length === 0}
    <EmptyState
      icon="sessions"
      title="No sessions yet"
      description="Start a session on Detect with the camera, or import a video or a set of images below."
    >
      {#snippet actions()}
        <Button variant="secondary" href="#/detect">Go to Detect</Button>
      {/snippet}
    </EmptyState>
  {:else}
    <ul class="rows">
      {#each sessions as session (session.id)}
        {@const live = isLive(session)}
        <li>
          <a class="row" href="#/sessions/{encodeURIComponent(session.id)}" aria-label="{session.name}, {statusLabel(session.status)}, {session.total_detections} detections">
            <span class="main">
              <span class="name-line">
                <span class="name">{session.name}</span>
                {#if live}
                  <Badge tone="danger"><StatusDot tone="danger" pulse />Live</Badge>
                {:else if session.status === 'active'}
                  <Badge tone="accent">Running</Badge>
                {:else if session.status === 'failed'}
                  <Badge tone="danger">Failed</Badge>
                {/if}
              </span>
              <span class="meta">
                <Badge outline>{sourceLabel(session.source)}</Badge>
                <span>{session.model_name ?? 'No model recorded'}</span>
                <span aria-hidden="true">·</span>
                <span>{formatDateTime(session.started_at)}</span>
                <span aria-hidden="true">·</span>
                <span>{formatDuration(session.duration_seconds)}</span>
              </span>
            </span>
            <span class="numbers">
              <span class="total">{session.total_detections.toLocaleString('en-US')}</span>
              <span class="unit">detections</span>
            </span>
          </a>
        </li>
      {/each}
    </ul>
    {#if hasMore(sessions.length, total)}
      <div class="more">
        <Button variant="secondary" busy={loadingMore} onclick={loadMore}>Load more</Button>
      </div>
    {/if}
  {/if}
</section>

<style>
  .list {
    display: grid;
    gap: var(--space-3);
    min-width: 0;
  }
  .list-head {
    display: flex;
    flex-wrap: wrap;
    align-items: baseline;
    justify-content: space-between;
    gap: var(--space-2);
  }
  .heading {
    font-size: var(--text-title);
    font-weight: var(--font-weight-semibold);
  }
  .count {
    font-size: var(--text-micro);
    color: var(--ink-soft);
    font-family: var(--font-mono);
  }
  .note {
    color: var(--ink-soft);
    font-size: var(--text-small);
  }
  .rows {
    display: grid;
    gap: var(--space-2);
    list-style: none;
    margin: 0;
    padding: 0;
  }
  .row {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: var(--space-4);
    min-height: 4rem;
    padding: var(--space-3) var(--space-4);
    border-radius: var(--radius-card);
    background: var(--surface);
    box-shadow: var(--shadow-raised);
    color: var(--ink);
    text-decoration: none;
    min-width: 0;
    transition: background-color var(--dur-fast) ease-out;
  }
  .row:hover {
    background: var(--raised);
    box-shadow:
      0 0 0 1px var(--rule-strong),
      0 1px 2px rgb(0 0 0 / 4%);
  }
  .row:focus-visible {
    outline: 2px solid var(--accent);
    outline-offset: 2px;
  }
  .main {
    display: grid;
    gap: var(--space-1);
    min-width: 0;
  }
  .name-line {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    gap: var(--space-2);
    min-width: 0;
  }
  .name {
    font-weight: var(--font-weight-semibold);
    overflow-wrap: anywhere;
  }
  .meta {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    gap: var(--space-1) var(--space-2);
    font-size: var(--text-micro);
    color: var(--ink-soft);
  }
  .numbers {
    display: grid;
    justify-items: end;
    flex-shrink: 0;
    text-align: right;
  }
  .total {
    font-family: var(--font-mono);
    font-size: var(--text-title);
    font-weight: var(--font-weight-bold);
    font-variant-numeric: tabular-nums;
  }
  .unit {
    font-size: var(--text-micro);
    color: var(--ink-soft);
  }
  .more {
    display: flex;
    justify-content: center;
    padding-top: var(--space-2);
  }
</style>
