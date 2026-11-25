<script lang="ts">
  import { untrack } from 'svelte';
  import { ApiError, api, describeError, isRouteMissing, sessionExportUrl } from '../../lib/api';
  import Badge from '../../lib/components/Badge.svelte';
  import BarList from '../../lib/components/charts/BarList.svelte';
  import Button from '../../lib/components/Button.svelte';
  import Card from '../../lib/components/Card.svelte';
  import Dialog from '../../lib/components/Dialog.svelte';
  import EmptyState from '../../lib/components/EmptyState.svelte';
  import Field from '../../lib/components/Field.svelte';
  import Notice from '../../lib/components/Notice.svelte';
  import PageHeader from '../../lib/components/PageHeader.svelte';
  import StatTile from '../../lib/components/StatTile.svelte';
  import StatusDot from '../../lib/components/StatusDot.svelte';
  import TextInput from '../../lib/components/TextInput.svelte';
  import { CLASS_COLORS, CLASS_LABELS } from '../../lib/classes';
  import { formatDateTime, formatDuration, formatPercent } from '../../lib/format';
  import { formatClock } from './replay-logic';
  import { startPolling } from '../../lib/poll';
  import { router } from '../../lib/stores/router.svelte';
  import { toasts } from '../../lib/stores/toasts.svelte';
  import { CLASS_NAMES, type SessionDetail } from '../../lib/types';
  import SessionReplay from './SessionReplay.svelte';
  import { canDelete, deleteBlockedReason, isLive, sourceLabel, statusLabel } from './session-list';

  interface Props {
    id: string;
  }

  let { id }: Props = $props();

  let session = $state<SessionDetail | null>(null);
  let loading = $state(true);
  let missing = $state(false);
  let error = $state<string | null>(null);
  let nameDraft = $state('');
  let notesDraft = $state('');
  let saving = $state(false);
  let deleteOpen = $state(false);
  let deleting = $state(false);
  /** The id the drafts belong to. Refreshes do not overwrite what the user is typing. */
  let draftsFor = $state<string | null>(null);

  const name = $derived(nameDraft.trim());
  const nameValid = $derived(name.length > 0 && name.length <= 120);
  const dirty = $derived(
    session !== null && draftsFor === session.id && (name !== session.name || notesDraft !== (session.notes ?? '')),
  );
  /** Detections per minute of recording, to one decimal. A session with no duration has no rate. */
  function perMinute(row: SessionDetail): string {
    if (!(row.duration_seconds > 0)) return '-';
    return (Math.round((row.total_detections / row.duration_seconds) * 600) / 10).toLocaleString('en-US');
  }

  const nameError = $derived(name === '' ? 'Enter a name.' : name.length > 120 ? 'Keep the name under 120 characters.' : undefined);
  const sessionStatus = $derived(session?.status ?? null);
  const live = $derived(session ? isLive(session) : false);
  const blocked = $derived(session ? deleteBlockedReason(session) : null);
  const classRows = $derived(
    session
      ? CLASS_NAMES.map((cls) => ({ label: CLASS_LABELS[cls], value: session?.class_counts[cls] ?? 0, color: CLASS_COLORS[cls] }))
      : [],
  );

  async function load(sessionId: string) {
    try {
      const next = await api.v1.getSession(sessionId);
      if (sessionId !== id) return;
      session = next;
      error = null;
      missing = false;
      if (draftsFor !== sessionId) {
        nameDraft = next.name;
        notesDraft = next.notes ?? '';
        draftsFor = sessionId;
      }
    } catch (failure) {
      if (sessionId !== id) return;
      // A 404 for the session id means it is gone. A 404 for the route means the server lacks the API.
      if (failure instanceof ApiError && failure.status === 404 && !isRouteMissing(failure)) {
        missing = true;
        session = null;
      } else {
        error = describeError(failure, 'The session could not be loaded.');
      }
    } finally {
      if (sessionId === id) loading = false;
    }
  }

  $effect(() => {
    const current = id;
    untrack(() => {
      session = null;
      loading = true;
      missing = false;
      error = null;
      draftsFor = null;
    });
    void load(current);
  });

  // An import or a live session keeps changing, so the page re-reads the session every few seconds.
  $effect(() => {
    if (!session || session.status !== 'active') return;
    const current = session.id;
    return startPolling(() => load(current), { intervalMs: 3000, immediate: false });
  });

  async function save(event: SubmitEvent) {
    event.preventDefault();
    if (!session || !nameValid) return;
    saving = true;
    try {
      const updated = await api.v1.patchSession(session.id, { name, notes: notesDraft });
      if (updated && session.id === updated.id) session = updated;
      nameDraft = updated?.name ?? name;
      notesDraft = updated?.notes ?? notesDraft;
      toasts.success('Session saved.');
    } catch (failure) {
      toasts.error(describeError(failure, 'The session could not be saved.'));
    } finally {
      saving = false;
    }
  }

  async function remove() {
    if (!session) return;
    deleting = true;
    try {
      await api.v1.deleteSession(session.id);
      deleteOpen = false;
      toasts.success('Session deleted.');
      router.navigate('sessions');
    } catch (failure) {
      toasts.error(describeError(failure, 'The session could not be deleted.'));
    } finally {
      deleting = false;
    }
  }
</script>

<nav class="back" aria-label="Breadcrumb">
  <a href="#/sessions">Sessions</a>
  <span aria-hidden="true">/</span>
  <span class="here">{session?.name ?? 'Session'}</span>
</nav>

{#if loading}
  <p class="note" role="status">Loading the session</p>
{:else if missing}
  <EmptyState
    icon="sessions"
    title="This session does not exist"
    description="It may have been deleted. The list has the sessions that are left."
  >
    {#snippet actions()}
      <Button variant="secondary" href="#/sessions">Back to sessions</Button>
    {/snippet}
  </EmptyState>
{:else if error && !session}
  <Notice tone="danger" title="The session could not load">
    <p>{error}</p>
    {#snippet actions()}
      <Button variant="secondary" onclick={() => load(id)}>Try again</Button>
    {/snippet}
  </Notice>
{:else if session}
  <PageHeader
    title={session.name}
    eyebrow="{sourceLabel(session.source)} session"
    description="Started {formatDateTime(session.started_at)}. {statusLabel(session.status)}."
  >
    {#snippet actions()}
      {#if live}
        <Badge tone="danger"><StatusDot tone="danger" pulse />Live</Badge>
      {:else if sessionStatus === 'active'}
        <Badge tone="accent">Running</Badge>
      {:else if sessionStatus === 'failed'}
        <Badge tone="danger">Failed</Badge>
      {/if}
    {/snippet}
  </PageHeader>

  <div class="stats" aria-label="Session totals">
    <StatTile label="Detections" value={session.total_detections.toLocaleString('en-US')} />
    <StatTile label="Duration" value={formatClock(session.duration_seconds)} hint={formatDuration(session.duration_seconds)} />
    <StatTile label="Average confidence" value={formatPercent(session.avg_confidence)} />
    <StatTile label="Per minute" value={perMinute(session)} hint="Detections per minute of recording" />
  </div>

  <div class="columns">
    <Card title="Classes" description="Detections per class in this session.">
      <BarList label="Detections per class" items={classRows} format={(value) => value.toLocaleString('en-US')} emptyText="No detections were recorded." />
    </Card>

    <Card title="Export" description="Download the data, or open a report to print or save as a PDF.">
      <div class="exports">
        <Button variant="secondary" href={sessionExportUrl(session.id, 'csv')} download={true}>Export CSV</Button>
        <Button variant="secondary" href={sessionExportUrl(session.id, 'json')} download={true}>Export JSON</Button>
        <Button variant="secondary" href={sessionExportUrl(session.id, 'report')} target="_blank" rel="noopener">HTML report</Button>
      </div>
      <p class="hint">The report opens in a new tab. Print the report to save a PDF.</p>
      {#if live || session.status === 'active'}
        <p class="hint">This session is still running, so the files hold what has been recorded so far.</p>
      {/if}
    </Card>
  </div>

  <Card title="Replay" description="Scrub through the session, or play it back at the pace it was recorded.">
    {#if session.status === 'active'}
      <Notice tone="info">
        <p>The replay is available once the session has finished. Until then the totals above update as it runs.</p>
      </Notice>
    {:else}
      <SessionReplay sessionId={session.id} durationSeconds={session.duration_seconds} />
    {/if}
  </Card>

  <div class="columns">
    <Card title="Details" description="Rename the session or add a note for later.">
      <form class="details" onsubmit={save} novalidate>
        <Field id="session-name" label="Name" error={nameError}>
          <TextInput id="session-name" bind:value={nameDraft} maxlength={160} invalid={!nameValid} disabled={saving} />
        </Field>
        <Field id="session-notes" label="Notes" hint="Optional. What the run was for, lighting, belt speed, anything you will want to remember.">
          <textarea id="session-notes" class="area" rows="4" maxlength="2000" bind:value={notesDraft} disabled={saving}></textarea>
        </Field>
        <dl class="facts">
          <dt>Model</dt><dd>{session.model_name ?? 'None recorded'}</dd>
          <dt>Ended</dt><dd>{session.ended_at ? formatDateTime(session.ended_at) : 'Still running'}</dd>
        </dl>
        <div class="row">
          <Button type="submit" busy={saving} disabled={!dirty || !nameValid || saving}>Save changes</Button>
        </div>
      </form>
    </Card>

    <Card title="Delete" description="Removes the session with its detections and metrics.">
      {#if blocked}
        <Notice tone="warning"><p>{blocked}</p></Notice>
      {/if}
      <div class="row">
        <Button variant="danger" disabled={!canDelete(session)} onclick={() => (deleteOpen = true)}>Delete session</Button>
      </div>
    </Card>
  </div>

  <Dialog bind:open={deleteOpen} title="Delete this session?">
    <p>
      "{session.name}" and its {session.total_detections.toLocaleString('en-US')} detections are removed. This cannot be undone.
      Export first if you need the data.
    </p>
    {#snippet actions()}
      <Button variant="ghost" onclick={() => (deleteOpen = false)} disabled={deleting}>Keep session</Button>
      <Button variant="danger" busy={deleting} onclick={remove}>Delete session</Button>
    {/snippet}
  </Dialog>
{/if}

<style>
  .back {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    gap: var(--space-2);
    min-height: 2.75rem;
    font-size: var(--text-small);
    color: var(--ink-soft);
    margin-bottom: var(--space-2);
  }
  .back a {
    display: inline-flex;
    align-items: center;
    min-height: var(--target);
    color: var(--accent-strong);
    font-weight: var(--font-weight-medium);
    text-decoration: none;
  }
  .back a:hover {
    text-decoration: underline;
  }
  .here {
    overflow-wrap: anywhere;
  }
  .note {
    color: var(--ink-soft);
    font-size: var(--text-small);
  }
  .stats {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(10.5rem, 1fr));
    gap: var(--space-3);
    margin-bottom: var(--space-5);
  }
  .columns {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(min(100%, 22rem), 1fr));
    gap: var(--space-5);
    margin: var(--space-5) 0;
    align-items: start;
  }
  .exports {
    display: flex;
    flex-wrap: wrap;
    gap: var(--space-2);
  }
  .hint {
    margin-top: var(--space-3);
    font-size: var(--text-micro);
    color: var(--ink-soft);
  }
  .details {
    display: grid;
    gap: var(--space-4);
    min-width: 0;
  }
  .area {
    width: 100%;
    min-height: 6rem;
    padding: var(--space-2) var(--space-3);
    border: 1px solid var(--control-edge);
    border-radius: var(--radius-control);
    background: var(--raised);
    color: var(--ink);
    font: inherit;
    font-size: var(--text-small);
    line-height: 1.5;
    resize: vertical;
  }
  .facts {
    display: grid;
    grid-template-columns: auto minmax(0, 1fr);
    gap: var(--space-1) var(--space-4);
    font-size: var(--text-micro);
    margin: 0;
  }
  .facts dt {
    color: var(--ink-soft);
  }
  .facts dd {
    margin: 0;
    overflow-wrap: anywhere;
  }
  .row {
    display: flex;
    flex-wrap: wrap;
    gap: var(--space-2);
  }
</style>
