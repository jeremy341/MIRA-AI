<script lang="ts">
  import Button from '../../lib/components/Button.svelte';
  import Card from '../../lib/components/Card.svelte';
  import PageHeader from '../../lib/components/PageHeader.svelte';
  import SegmentedControl from '../../lib/components/SegmentedControl.svelte';
  import Slider from '../../lib/components/Slider.svelte';
  import Notice from '../../lib/components/Notice.svelte';
  import { formatMs } from '../../lib/format';
  import { router } from '../../lib/stores/router.svelte';
  import { detect, type DetectSource } from '../../lib/stores/detect.svelte';
  import { live } from '../../lib/stores/live.svelte';
  import { settings } from '../../lib/stores/settings.svelte';
  import { system } from '../../lib/stores/system.svelte';
  import type { StepAction } from './detect-logic';
  import { confidenceLabel, readinessSteps } from './detect-logic';
  import { connectCamera, loadSavedModel, modelToLoad, startStream, stopStream } from './detect-actions';
  import DetectionList from './DetectionList.svelte';
  import ImagePanel from './ImagePanel.svelte';
  import LivePreview from './LivePreview.svelte';
  import SessionControls from './SessionControls.svelte';

  const SOURCES = [
    { value: 'camera', label: 'Connected camera' },
    { value: 'image', label: 'Image file' },
  ] as const;

  const plannedModel = $derived(modelToLoad()?.name ?? null);

  const steps = $derived(
    readinessSteps({
      source: detect.source,
      cameraReady: system.cameraReady,
      modelLoaded: system.modelLoaded,
      streaming: system.streaming,
      savedModel: plannedModel,
      loadedModelName: settings.saved.model.name || plannedModel,
    }),
  );

  /** One next step at a time: the first step that still needs doing, or "Stop stream" while it runs. */
  const nextStep = $derived(
    steps.find((step) => step.action && step.state !== 'done') ?? steps.find((step) => step.action === 'stop') ?? null,
  );
  const waitingHint = $derived(steps.find((step) => step.state === 'waiting' && !step.action)?.detail ?? null);

  const busy = $derived({
    connect: detect.connectBusy,
    load: detect.loadBusy,
    start: detect.streamAction === 'starting',
    stop: detect.streamAction === 'stopping',
    settings: false,
  } satisfies Partial<Record<StepAction, boolean>>);

  const livePeople = $derived(live.state.frame ? live.state.frame.detections.filter((d) => d.confidence >= detect.minConfidence).length : 0);
  const fpsValue = $derived(
    system.streaming ? (live.state.metrics?.fps ?? live.fps).toFixed(1) : '-',
  );

  function onStep(action: StepAction) {
    switch (action) {
      case 'connect':
        void connectCamera();
        break;
      case 'load':
        void loadSavedModel();
        break;
      case 'start':
        void startStream();
        break;
      case 'stop':
        void stopStream();
        break;
      case 'settings':
        router.navigate('settings');
        break;
    }
  }

  function setSource(value: DetectSource) {
    detect.source = value;
  }
</script>

<PageHeader title="Detect">
  {#snippet actions()}
    <SegmentedControl
      label="Detection source"
      value={detect.source}
      options={SOURCES}
      onchange={setSource}
    />
  {/snippet}
</PageHeader>

<div class="layout">
  <div class="main">
    <Card>
      <div class="toolbar">
        {#if nextStep && nextStep.action && nextStep.actionLabel}
          {@const action = nextStep.action}
          <Button
            variant={action === 'stop' ? 'secondary' : 'primary'}
            busy={busy[action] ?? false}
            onclick={() => onStep(action)}
          >
            {nextStep.actionLabel}
          </Button>
          {#if action !== 'stop'}<span class="hint">{nextStep.detail}</span>{/if}
        {:else if waitingHint}
          <span class="hint">{waitingHint}</span>
        {/if}

        <div class="threshold">
          <label class="threshold-label" for="min-confidence">Min. confidence</label>
          <Slider
            id="min-confidence"
            value={detect.minConfidence}
            min={0.05}
            max={1}
            step={0.05}
            format={confidenceLabel}
            oninput={(value) => (detect.minConfidence = value)}
          />
        </div>
      </div>

      {#if detect.streamError}
        <div class="error"><Notice tone="warning">{detect.streamError}</Notice></div>
      {/if}

      {#if detect.source === 'camera'}
        <LivePreview minConfidence={detect.minConfidence} />
      {:else}
        <ImagePanel minConfidence={detect.minConfidence} />
      {/if}

      {#if detect.source === 'camera'}
        <p class="metrics" aria-label="Stream metrics">
          <span><b>{fpsValue}</b> FPS</span>
          <span><b>{system.streaming && live.state.metrics ? formatMs(live.state.metrics.latencyMs) : '-'}</b> per frame</span>
          <span><b>{live.state.frame ? livePeople : '-'}</b> {live.state.frame ? (livePeople === 1 ? 'object' : 'objects') : 'objects'}</span>
        </p>
      {/if}
    </Card>
  </div>

  <aside class="side">
    <SessionControls />
    <Card title="Detections">
      <DetectionList
        detections={detect.source === 'camera' ? (live.state.frame?.detections ?? []) : (detect.imageResult?.detections ?? [])}
        minConfidence={detect.minConfidence}
        idleText={detect.source === 'camera' ? 'They appear here while the stream runs.' : 'Check an image to see them here.'}
      />
    </Card>
  </aside>
</div>

<style>
  .layout {
    display: grid;
    grid-template-columns: minmax(0, 1fr) minmax(15rem, 18rem);
    gap: var(--space-4);
    align-items: start;
    min-width: 0;
  }
  .main,
  .side {
    display: grid;
    gap: var(--space-4);
    min-width: 0;
  }
  .toolbar {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    gap: var(--space-3) var(--space-4);
    margin-bottom: var(--space-3);
  }
  .hint {
    flex: 1;
    min-width: 0;
    font-size: var(--text-small);
    color: var(--ink-soft);
  }
  .threshold {
    display: flex;
    align-items: center;
    gap: var(--space-3);
    margin-left: auto;
    width: 22rem;
    max-width: 100%;
  }
  .threshold :global(.slider) {
    flex: 1;
    min-width: 0;
    grid-template-columns: minmax(0, 1fr) 2.5rem;
  }
  .threshold-label {
    flex-shrink: 0;
    font-size: var(--text-small);
    color: var(--ink-soft);
  }
  .error {
    margin-bottom: var(--space-3);
  }
  .metrics {
    display: flex;
    flex-wrap: wrap;
    gap: var(--space-1) var(--space-5);
    margin: var(--space-3) 0 0;
    font-size: var(--text-small);
    color: var(--ink-soft);
  }
  .metrics b {
    font-family: var(--font-mono);
    font-weight: var(--font-weight-medium);
    color: var(--ink);
  }
  @media (max-width: 1099px) {
    .layout {
      grid-template-columns: minmax(0, 1fr);
    }
  }
  @media (max-width: 599px) {
    .threshold {
      margin-left: 0;
      width: 100%;
    }
  }
</style>
