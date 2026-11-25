<script lang="ts">
  import ClassChip from '../../lib/components/ClassChip.svelte';
  import EmptyState from '../../lib/components/EmptyState.svelte';
  import { confidenceLabel } from './detect-logic';
  import type { LiveDetection } from '../../lib/realtime/video-state';

  interface Props {
    detections: readonly LiveDetection[];
    minConfidence: number;
    /** Shown when nothing is in the list at all (before the first frame or image). */
    idleText: string;
  }

  let { detections, minConfidence, idleText }: Props = $props();

  const visible = $derived(detections.filter((d) => d.confidence >= minConfidence));
  const sorted = $derived([...visible].sort((a, b) => b.confidence - a.confidence));
</script>

{#if sorted.length === 0}
  <EmptyState
    icon="detect"
    compact
    title={detections.length === 0 ? 'Nothing detected yet' : 'Nothing above this confidence'}
    description={detections.length === 0 ? idleText : `${detections.length} hidden by the minimum confidence.`}
  />
{:else}
  <ul class="list" aria-label="Detections">
    {#each sorted as detection, index (index)}
      <li class="row">
        <ClassChip className={detection.className} />
        <span class="conf">{confidenceLabel(detection.confidence)}</span>
        <span class="track">{detection.trackId !== null ? `track ${detection.trackId}` : 'no track'}</span>
      </li>
    {/each}
  </ul>
{/if}

<style>
  .list {
    display: grid;
    margin: 0;
    padding: 0;
    list-style: none;
  }
  .row {
    display: grid;
    grid-template-columns: auto auto 1fr;
    align-items: center;
    gap: var(--space-3);
    min-height: 2.5rem;
    border-bottom: 1px solid var(--rule);
  }
  .row:last-child {
    border-bottom: 0;
  }
  .conf {
    font-family: var(--font-mono);
    font-size: var(--text-small);
    font-variant-numeric: tabular-nums;
    text-align: right;
  }
  .track {
    font-size: var(--text-micro);
    color: var(--ink-soft);
    text-align: right;
  }
</style>
