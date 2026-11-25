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
  <dl class="items">
    <div class="item">
      <dt>Model</dt>
      <dd><StatusDot tone={model.tone} /><span class="text" title={model.text}>{model.text}</span></dd>
    </div>
    <div class="item">
      <dt>Connection</dt>
      <dd><StatusDot tone={connection.tone} pulse={connection.tone === 'warning'} /><span class="text">{connection.text}</span></dd>
    </div>
    <div class="item">
      <dt>Stream</dt>
      <dd><StatusDot tone={stream.tone} pulse={stream.text === 'Live'} /><span class="text">{stream.text}</span></dd>
    </div>
    <div class="item session">
      <dt>Session</dt>
      <dd><StatusDot tone={session.tone === 'accent' ? 'accent' : 'neutral'} /><span class="text" title={session.text}>{session.text}</span></dd>
    </div>
  </dl>
</header>

<style>
  .status-bar {
    position: sticky;
    top: 0;
    z-index: 30;
    background: color-mix(in srgb, var(--app) 92%, transparent);
    backdrop-filter: saturate(1.2) blur(6px);
    border-bottom: 1px solid var(--rule);
    padding: var(--space-2) var(--page-pad);
  }
  .items {
    display: flex;
    flex-wrap: wrap;
    gap: var(--space-2) var(--space-5);
    margin: 0 auto;
    max-width: var(--content-max);
  }
  .item {
    display: flex;
    align-items: center;
    gap: var(--space-2);
    min-width: 0;
    max-width: 100%;
  }
  dt {
    font-family: var(--font-mono);
    font-size: 0.6875rem;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    color: var(--ink-soft);
  }
  dd {
    display: flex;
    align-items: center;
    gap: var(--space-2);
    min-width: 0;
    margin: 0;
    font-size: var(--text-small);
    font-weight: var(--font-weight-medium);
    color: var(--ink);
  }
  .text {
    min-width: 0;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
    max-width: 16rem;
  }
  .item dt + dd {
    margin-left: 0;
  }
  @media (max-width: 899px) {
    .item {
      flex-direction: column;
      align-items: stretch;
      gap: 0;
    }
    dd {
      width: 100%;
    }
    .items {
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: var(--space-2) var(--space-3);
    }
    .text {
      max-width: 100%;
    }
  }
</style>
