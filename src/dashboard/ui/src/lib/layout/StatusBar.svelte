<script lang="ts">
  import StatusDot from '../components/StatusDot.svelte';
  import { live } from '../stores/live.svelte';
  import { system } from '../stores/system.svelte';
  import { settings } from '../stores/settings.svelte';
  import { describeConnection, describeModel, describeSession, describeStream } from '../status-summary';

  const model = $derived(describeModel(system.status, settings.saved.model.name || null, system.statusError));
  const connection = $derived(describeConnection(live.link, live.linkInfo, system.statusError));
  // "Live" means a frame arrived in the last few seconds, so slow streams (well under 1 fps) still read as live.
  const stream = $derived(describeStream(system.status, live.fresh));
  const session = $derived(describeSession(system.activeSession, system.sessions));
</script>

<header class="status-bar" aria-label="System status">
  <ul class="items">
    <li class="item" title={model.text}>
      <StatusDot tone={model.tone} /><span class="visually-hidden">Model: </span><span class="text">{model.text}</span>
    </li>
    <li class="item">
      <StatusDot tone={stream.tone} pulse={stream.text === 'Live'} /><span class="visually-hidden">Stream: </span><span class="text">{stream.text}</span>
    </li>
    {#if session.tone === 'accent'}
      <li class="item" title={session.text}>
        <StatusDot tone="accent" /><span class="visually-hidden">Session: </span><span class="text">Recording {session.text}</span>
      </li>
    {/if}
    {#if connection.tone !== 'success'}
      <li class="item">
        <StatusDot tone={connection.tone} pulse={connection.tone === 'warning'} /><span class="visually-hidden">Connection: </span><span class="text">{connection.text}</span>
      </li>
    {/if}
  </ul>
</header>

<style>
  .status-bar {
    position: sticky;
    top: 0;
    z-index: 30;
    background: color-mix(in srgb, var(--app) 92%, transparent);
    backdrop-filter: saturate(1.2) blur(6px);
    border-bottom: 1px solid var(--rule);
    padding: 0 var(--page-pad);
  }
  .items {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    gap: 0 var(--space-5);
    min-height: 2.5rem;
    margin: 0 auto;
    padding: 0;
    list-style: none;
    max-width: var(--content-max);
  }
  .item {
    display: flex;
    align-items: center;
    gap: var(--space-2);
    min-width: 0;
    font-size: var(--text-small);
    color: var(--ink-soft);
  }
  .text {
    min-width: 0;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
    max-width: 16rem;
  }
</style>
