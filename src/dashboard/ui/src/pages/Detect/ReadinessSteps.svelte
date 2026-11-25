<script lang="ts">
  import Button from '../../lib/components/Button.svelte';
  import Icon from '../../lib/components/Icon.svelte';
  import Notice from '../../lib/components/Notice.svelte';
  import type { ReadinessStep, StepAction } from './detect-logic';

  interface Props {
    steps: ReadinessStep[];
    busy: Partial<Record<StepAction, boolean>>;
    streamError: string | null;
    onaction: (action: StepAction) => void;
  }

  let { steps, busy, streamError, onaction }: Props = $props();

  const stateLabel = { done: 'Done', next: 'Next', waiting: 'Waiting', optional: 'Not needed' } as const;
</script>

<section class="steps" aria-label="Readiness">
  <ol class="list">
    {#each steps as step, index (step.key)}
      <li class="step {step.state}">
        <span class="badge" aria-hidden="true">
          {#if step.state === 'done'}<Icon name="check" size={16} />{:else}{index + 1}{/if}
        </span>
        <div class="text">
          <p class="title">
            {step.title}
            <span class="state">{stateLabel[step.state]}</span>
          </p>
          <p class="detail">{step.detail}</p>
        </div>
        {#if step.action && step.actionLabel}
          <div class="action">
            <Button
              variant={step.action === 'stop' ? 'secondary' : 'primary'}
              busy={busy[step.action] ?? false}
              onclick={() => step.action && onaction(step.action)}
            >
              {step.actionLabel}
            </Button>
          </div>
        {/if}
      </li>
    {/each}
  </ol>
  {#if streamError}
    <div class="notice">
      <Notice tone="warning">{streamError}</Notice>
    </div>
  {/if}
</section>

<style>
  .list {
    display: grid;
    grid-template-columns: repeat(3, minmax(0, 1fr));
    gap: var(--space-3);
    margin: 0;
    padding: 0;
    list-style: none;
  }
  .step {
    display: grid;
    grid-template-columns: auto 1fr;
    grid-template-areas:
      'badge text'
      'action action';
    gap: var(--space-3);
    align-items: start;
    min-width: 0;
    padding: var(--space-4);
    border-radius: var(--radius-card);
    background: var(--app);
  }
  .step.next {
    background: var(--accent-subtle);
  }
  .badge {
    grid-area: badge;
    display: grid;
    place-items: center;
    width: 1.75rem;
    height: 1.75rem;
    border-radius: 50%;
    background: var(--surface);
    color: var(--ink-soft);
    font-family: var(--font-mono);
    font-size: var(--text-micro);
    font-weight: var(--font-weight-bold);
    box-shadow: var(--shadow-raised);
  }
  .done .badge {
    background: var(--success-ink);
    color: var(--surface);
    box-shadow: none;
  }
  .next .badge {
    background: var(--accent-strong);
    color: var(--on-accent);
    box-shadow: none;
  }
  .text {
    grid-area: text;
    min-width: 0;
  }
  .title {
    font-size: var(--text-small);
    font-weight: var(--font-weight-semibold);
    color: var(--ink);
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    gap: var(--space-2);
  }
  .state {
    font-family: var(--font-mono);
    font-size: 0.6875rem;
    font-weight: 400;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    color: var(--ink-soft);
  }
  .detail {
    margin-top: 0.125rem;
    font-size: var(--text-micro);
    color: var(--ink-soft);
    line-height: 1.45;
  }
  .action {
    grid-area: action;
  }
  .notice {
    margin-top: var(--space-3);
  }
  @media (max-width: 899px) {
    .list {
      grid-template-columns: minmax(0, 1fr);
    }
    .step {
      grid-template-columns: auto 1fr;
    }
  }
</style>
