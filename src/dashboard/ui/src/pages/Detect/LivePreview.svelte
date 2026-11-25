<script lang="ts">
  import { onMount } from 'svelte';
  import Badge from '../../lib/components/Badge.svelte';
  import Button from '../../lib/components/Button.svelte';
  import DetectionCanvas from '../../lib/components/DetectionCanvas.svelte';
  import EmptyState from '../../lib/components/EmptyState.svelte';
  import Notice from '../../lib/components/Notice.svelte';
  import { live } from '../../lib/stores/live.svelte';
  import { system } from '../../lib/stores/system.svelte';
  import { objectCountLabel, previewMessage } from './detect-logic';
  import { reconnectLive } from './detect-actions';

  interface Props {
    /** Boxes below this confidence are hidden. */
    minConfidence: number;
  }

  let { minConfidence }: Props = $props();

  /** Frames older than this during a running stream count as "no frames". */
  const STALE_MS = 4000;

  // A clock that ticks once a second, so the "no frames" wording appears without a new frame arriving.
  let now = $state(Date.now());
  onMount(() => {
    const timer = setInterval(() => {
      now = Date.now();
    }, 1000);
    return () => clearInterval(timer);
  });

  const frame = $derived(live.state.frame);
  const stale = $derived(live.state.lastFrameAt === null || now - live.state.lastFrameAt > STALE_MS);
  const visibleCount = $derived(frame ? frame.detections.filter((d) => d.confidence >= minConfidence).length : 0);
  const hint = $derived(
    previewMessage({
      cameraReady: system.cameraReady,
      modelLoaded: system.modelLoaded,
      streaming: system.streaming,
      hasFrame: frame !== null,
      stale: system.streaming && stale,
    }),
  );
  const linkLost = $derived(live.link === 'reconnecting' || live.link === 'unavailable' || live.link === 'closed');
</script>

<div class="preview">
  {#if linkLost}
    <Notice tone={live.link === 'unavailable' ? 'danger' : 'warning'} title="Live link lost">
      {#if live.link === 'unavailable'}
        The server does not offer the live video socket. Check that the dashboard server is running the latest version.
      {:else if live.link === 'reconnecting' && live.linkInfo.retryInMs !== null}
        Reconnecting in {Math.ceil(live.linkInfo.retryInMs / 1000)} s. Frames resume once the link is back.
      {:else}
        Frames are paused until the link is back.
      {/if}
      {#snippet actions()}
        <Button variant="secondary" onclick={reconnectLive}>Reconnect now</Button>
      {/snippet}
    </Notice>
  {/if}

  {#if live.state.notice}
    <div class="note">
      <Notice tone="info">{live.state.notice}</Notice>
    </div>
  {/if}

  {#if frame}
    <div class="frame">
      <DetectionCanvas
        src={frame.src}
        detections={frame.detections}
        {minConfidence}
        label="Live preview: {objectCountLabel(visibleCount)} above {Math.round(minConfidence * 100)}%"
      />
      <span class="badge">
        <Badge tone={system.streaming ? 'success' : 'neutral'}>{system.streaming ? 'Live' : 'Last frame'}</Badge>
      </span>
    </div>
  {:else}
    <div class="placeholder">
      <EmptyState icon="camera" title={hint.title} description={hint.description} compact />
    </div>
  {/if}

</div>

<style>
  .preview {
    display: grid;
    gap: var(--space-3);
    min-width: 0;
  }
  .frame {
    position: relative;
    border-radius: var(--radius-control);
    overflow: hidden;
    background: #161616;
  }
  .badge {
    position: absolute;
    top: var(--space-2);
    left: var(--space-2);
  }
  .placeholder {
    display: grid;
    place-items: center;
    min-height: 16rem;
    border-radius: var(--radius-control);
    background: var(--app);
    border: 1px dashed var(--rule-strong);
  }
</style>
