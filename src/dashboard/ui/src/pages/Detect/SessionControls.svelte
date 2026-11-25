<script lang="ts">
  import Button from '../../lib/components/Button.svelte';
  import Card from '../../lib/components/Card.svelte';
  import Field from '../../lib/components/Field.svelte';
  import Notice from '../../lib/components/Notice.svelte';
  import TextInput from '../../lib/components/TextInput.svelte';
  import { describedBy } from '../../lib/components/field-ids';
  import { defaultSessionName, formatTime } from '../../lib/format';
  import { detect } from '../../lib/stores/detect.svelte';
  import { system } from '../../lib/stores/system.svelte';
  import { startSession, stopSession } from './detect-actions';

  const unavailable = $derived(system.sessions === 'unavailable');
  const active = $derived(system.activeSession);
  const placeholder = defaultSessionName();
</script>

<Card title="Session" description="Detections are saved to a session while the stream runs.">
  {#if unavailable}
    <Notice tone="info" title="Not available yet">
      Sessions are not available on this server yet. Detection still works without them.
    </Notice>
    <Field id="session-name-off" label="Session name" hint="Available once sessions are enabled on the server.">
      <TextInput id="session-name-off" value="" placeholder={placeholder} disabled />
    </Field>
    <div class="actions">
      <Button disabled>Start session</Button>
    </div>
  {:else if active}
    <dl class="active">
      <div>
        <dt>Name</dt>
        <dd>{active.name}</dd>
      </div>
      <div>
        <dt>Started</dt>
        <dd>{formatTime(active.started_at)}</dd>
      </div>
      <div>
        <dt>Detections</dt>
        <dd class="mono">{active.total_detections}</dd>
      </div>
    </dl>
    <div class="actions">
      <Button variant="secondary" busy={detect.sessionBusy} onclick={() => stopSession(active.id)}>Stop session</Button>
    </div>
  {:else}
    <Field id="session-name" label="Session name" hint="Leave empty to use the date and time.">
      <TextInput
        id="session-name"
        bind:value={detect.sessionName}
        placeholder={placeholder}
        maxlength={80}
        describedby={describedBy('session-name', { hint: 'Leave empty to use the date and time.' })}
      />
    </Field>
    <div class="actions">
      <Button busy={detect.sessionBusy} disabled={detect.sessionBusy} onclick={startSession}>Start session</Button>
    </div>
  {/if}

  {#if detect.sessionError}
    <div class="error">
      <Notice tone="danger">{detect.sessionError}</Notice>
    </div>
  {/if}
</Card>

<style>
  .active {
    display: grid;
    gap: var(--space-3);
    margin: 0;
  }
  .active div {
    display: flex;
    justify-content: space-between;
    gap: var(--space-3);
    font-size: var(--text-small);
  }
  dt {
    color: var(--ink-soft);
  }
  dd {
    margin: 0;
    font-weight: var(--font-weight-medium);
    text-align: right;
    overflow-wrap: anywhere;
  }
  .mono {
    font-family: var(--font-mono);
  }
  .actions {
    margin-top: var(--space-4);
  }
  .error {
    margin-top: var(--space-3);
  }
</style>
