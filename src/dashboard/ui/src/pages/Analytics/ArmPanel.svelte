<script lang="ts">
  import { onMount } from 'svelte';
  import { api, describeError, isRouteMissing } from '../../lib/api';
  import Badge from '../../lib/components/Badge.svelte';
  import Button from '../../lib/components/Button.svelte';
  import Card from '../../lib/components/Card.svelte';
  import ClassChip from '../../lib/components/ClassChip.svelte';
  import EmptyState from '../../lib/components/EmptyState.svelte';
  import Notice from '../../lib/components/Notice.svelte';
  import Select from '../../lib/components/Select.svelte';
  import StatTile from '../../lib/components/StatTile.svelte';
  import { CLASS_LABELS } from '../../lib/classes';
  import { eventsFeed } from '../../lib/realtime/events-feed';
  import { startPolling } from '../../lib/poll';
  import { toasts } from '../../lib/stores/toasts.svelte';
  import { CLASS_NAMES, type ArmAccuracy, type ArmEvent, type ArmStatus, type BusEvent, type ClassName } from '../../lib/types';
  import { accuracyDetail, accuracySentence, canGiveFeedback, clockLabel, eventTitle, feedbackState, mergeEvents, timeMs } from './analytics-logic';

  let status = $state<ArmStatus | null>(null);
  let accuracy = $state<ArmAccuracy | null>(null);
  let events = $state<ArmEvent[]>([]);
  let testClass = $state<string>('glass');
  let sending = $state(false);
  let judging = $state<number | null>(null);
  let error = $state<string | null>(null);
  let unavailable = $state(false);

  const classOptions = CLASS_NAMES.map((cls) => ({ value: cls, label: CLASS_LABELS[cls] }));

  function handleFailure(failure: unknown, fallback: string) {
    if (isRouteMissing(failure)) {
      unavailable = true;
      return;
    }
    error = describeError(failure, fallback);
  }

  async function refreshStatus() {
    try {
      const [nextStatus, nextAccuracy] = await Promise.all([api.v1.getArmStatus(), api.v1.getArmAccuracy()]);
      status = nextStatus;
      accuracy = nextAccuracy;
      unavailable = false;
    } catch (failure) {
      handleFailure(failure, 'The arm status could not be loaded.');
    }
  }

  async function refreshEvents() {
    try {
      const page = await api.v1.listArmEvents(100);
      events = mergeEvents(events, page.events);
    } catch (failure) {
      handleFailure(failure, 'The event log could not be loaded.');
    }
  }

  onMount(() => {
    const stops = [
      startPolling(refreshStatus, { intervalMs: 5000 }),
      startPolling(refreshEvents, { intervalMs: 10_000 }),
      eventsFeed.subscribe(
        (bus: BusEvent) => {
          const incoming = bus.data as unknown as ArmEvent;
          events = mergeEvents(events, [incoming]);
          void refreshStatus();
        },
        ['arm_event'],
      ),
    ];
    return () => stops.forEach((stop) => stop());
  });

  async function sendTest() {
    sending = true;
    try {
      const event = await api.v1.sendArmCommand({ action: 'sort', class_name: testClass as ClassName });
      events = mergeEvents(events, [event]);
      toasts.info('Simulated sort sent. The result appears in the log.');
      void refreshStatus();
    } catch (failure) {
      toasts.error(describeError(failure, 'The simulated sort could not be sent.'));
    } finally {
      sending = false;
    }
  }

  async function judge(event: ArmEvent, correct: boolean) {
    judging = event.id;
    try {
      const updated = await api.v1.setArmFeedback(event.id, correct);
      events = mergeEvents(events.map((item) => (item.id === updated.id ? updated : item)), []);
      void refreshStatus();
    } catch (failure) {
      toasts.error(describeError(failure, 'The feedback could not be saved.'));
    } finally {
      judging = null;
    }
  }
</script>

<Card title="Sorting arm" description="A placeholder for the sorting arm. Nothing here moves hardware yet.">
  {#if unavailable}
    <EmptyState compact icon="settings" title="The arm API is not available yet" description="This server does not have the sorting arm endpoints." />
  {:else}
    {#if status && !status.connected}
      <Notice tone="warning">
        <p>No robot connected. Commands are simulated.</p>
      </Notice>
    {/if}

    {#if error}
      <Notice tone="danger"><p>{error}</p></Notice>
    {/if}

    <div class="tiles">
      <StatTile label="State" value={status ? (status.state === 'busy' ? 'Busy' : 'Idle') : '-'} hint={status ? `Mode: ${status.mode}` : undefined} />
      <StatTile label="Accuracy" value={status ? accuracySentence(status) : '-'} hint={accuracy ? accuracyDetail(accuracy) : undefined} />
    </div>

    <div class="grid">
      <section class="test" aria-labelledby="arm-test-title">
        <h3 id="arm-test-title" class="block-title">Test a sort</h3>
        <p class="note">Sends a simulated sort for one class. The log records the request and the result.</p>
        <div class="test-row">
          <Select id="arm-test-class" value={testClass} options={classOptions} onchange={(value) => (testClass = value)} disabled={sending} />
          <Button busy={sending} disabled={sending} onclick={sendTest}>Send simulated sort</Button>
        </div>
      </section>

      <section class="log" aria-labelledby="arm-log-title">
        <h3 id="arm-log-title" class="block-title">Event log</h3>
        {#if events.length === 0}
          <p class="note" role="status">No arm events yet. Send a test sort to fill the log.</p>
        {:else}
          <ol class="events">
            {#each events as event (event.id)}
              <li class="event">
                <div class="event-main">
                  <span class="time">{clockLabel(timeMs(event.ts))}</span>
                  <span class="title">{eventTitle(event)}</span>
                  {#if event.payload.message}<span class="message">{event.payload.message}</span>{/if}
                  {#if event.class_name}<ClassChip className={event.class_name} />{/if}
                </div>
                {#if canGiveFeedback(event)}
                  {@const judged = feedbackState(event)}
                  <div class="judge" role="group" aria-label="Was this sort correct?">
                    <Button variant={judged === 'correct' ? 'primary' : 'secondary'} size="md" busy={judging === event.id} onclick={() => judge(event, true)}>
                      {judged === 'correct' ? 'Marked correct' : 'Correct'}
                    </Button>
                    <Button variant={judged === 'incorrect' ? 'danger' : 'ghost'} size="md" disabled={judging === event.id} onclick={() => judge(event, false)}>
                      {judged === 'incorrect' ? 'Marked incorrect' : 'Incorrect'}
                    </Button>
                  </div>
                {:else}
                  <Badge>{event.kind.replace('_', ' ')}</Badge>
                {/if}
              </li>
            {/each}
          </ol>
        {/if}
      </section>
    </div>
  {/if}
</Card>

<style>
  .tiles {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(12rem, 1fr));
    gap: var(--space-3);
    margin: var(--space-4) 0 var(--space-5);
  }
  .grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(min(100%, 20rem), 1fr));
    gap: var(--space-6);
    align-items: start;
  }
  .block-title {
    font-size: var(--text-small);
    font-weight: var(--font-weight-semibold);
    margin-bottom: var(--space-2);
  }
  .note {
    font-size: var(--text-micro);
    color: var(--ink-soft);
  }
  .test {
    display: grid;
    gap: var(--space-3);
    min-width: 0;
  }
  .test-row {
    display: grid;
    grid-template-columns: minmax(0, 1fr) auto;
    gap: var(--space-3);
    align-items: center;
  }
  .events {
    display: grid;
    gap: var(--space-2);
    list-style: none;
    margin: 0;
    padding: 0;
    max-height: 26rem;
    overflow-y: auto;
  }
  .event {
    display: grid;
    gap: var(--space-2);
    padding: var(--space-3);
    border-radius: var(--radius-control);
    background: var(--app);
    min-width: 0;
  }
  .event-main {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    gap: var(--space-1) var(--space-3);
    font-size: var(--text-small);
    min-width: 0;
  }
  .time {
    font-family: var(--font-mono);
    font-size: var(--text-micro);
    color: var(--ink-soft);
  }
  .title {
    font-weight: var(--font-weight-medium);
    overflow-wrap: anywhere;
  }
  .message {
    font-size: var(--text-micro);
    color: var(--ink-soft);
    overflow-wrap: anywhere;
  }
  .judge {
    display: flex;
    flex-wrap: wrap;
    gap: var(--space-2);
  }
</style>
