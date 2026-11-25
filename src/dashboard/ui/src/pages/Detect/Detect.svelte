<script lang="ts">
  import Button from '../../lib/components/Button.svelte';
  import Card from '../../lib/components/Card.svelte';
  import PageHeader from '../../lib/components/PageHeader.svelte';
  import SegmentedControl from '../../lib/components/SegmentedControl.svelte';
  import Slider from '../../lib/components/Slider.svelte';
  import StatTile from '../../lib/components/StatTile.svelte';
  import Field from '../../lib/components/Field.svelte';
  import { formatMs } from '../../lib/format';
  import { router } from '../../lib/stores/router.svelte';
  import { detect, type DetectSource } from '../../lib/stores/detect.svelte';
  import { live } from '../../lib/stores/live.svelte';
  import { settings } from '../../lib/stores/settings.svelte';
  import { system } from '../../lib/stores/system.svelte';
  import type { StepAction } from './detect-logic';
  import { confidenceLabel, objectCountLabel, readinessSteps } from './detect-logic';
  import { connectCamera, loadSavedModel, startStream, stopStream } from './detect-actions';
  import DetectionList from './DetectionList.svelte';
  import ImagePanel from './ImagePanel.svelte';
  import ReadinessSteps from './ReadinessSteps.svelte';
  import LivePreview from './LivePreview.svelte';
  import RecentDetections from './RecentDetections.svelte';
  import SessionControls from './SessionControls.svelte';
  import StatisticsPanel from './StatisticsPanel.svelte';

  const SOURCES = [
    { value: 'camera', label: 'Connected camera' },
    { value: 'image', label: 'Image file' },
  ] as const;

  const steps = $derived(
    readinessSteps({
      source: detect.source,
      cameraReady: system.cameraReady,
      modelLoaded: system.modelLoaded,
      streaming: system.streaming,
      savedModel: settings.saved.model.name || null,
      loadedModelName: settings.saved.model.name || null,
    }),
  );

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

<PageHeader
  title="Detect"
  description="Live detection from the connected camera, or one image file checked with the saved model."
>
  {#snippet actions()}
    <SegmentedControl
      label="Detection source"
      value={detect.source}
      options={SOURCES}
      onchange={setSource}
    />
  {/snippet}
</PageHeader>

<div class="stack">
  <Card title="Readiness" description="Work through the steps in order. Each step tells you what is needed next.">
    <ReadinessSteps {steps} {busy} streamError={detect.streamError} onaction={onStep} />
  </Card>

  <div class="layout">
    <div class="main">
      <Card title={detect.source === 'camera' ? 'Live preview' : 'Image check'}>
        {#snippet actions()}
          {#if detect.source === 'camera'}
            <div class="stream-buttons">
              <Button
                variant="primary"
                busy={detect.streamAction === 'starting'}
                disabled={system.streaming || !system.cameraReady || !system.modelLoaded || detect.streamAction !== 'idle'}
                onclick={startStream}
              >
                Start stream
              </Button>
              <Button
                variant="secondary"
                busy={detect.streamAction === 'stopping'}
                disabled={!system.streaming || detect.streamAction === 'stopping'}
                onclick={stopStream}
              >
                Stop stream
              </Button>
            </div>
          {/if}
        {/snippet}

        {#if detect.source === 'camera'}
          <LivePreview minConfidence={detect.minConfidence} />
        {:else}
          <ImagePanel minConfidence={detect.minConfidence} />
        {/if}

        <div class="threshold">
          <Field
            id="min-confidence"
            label={detect.source === 'camera' ? 'Minimum confidence' : 'Confidence for the next image'}
            hint={detect.source === 'camera'
              ? 'Hides boxes and list entries below this value. Model thresholds are in Settings.'
              : 'Applies the next time you check an image.'}
          >
            <Slider
              id="min-confidence"
              value={detect.minConfidence}
              min={0.05}
              max={1}
              step={0.05}
              format={confidenceLabel}
              oninput={(value) => (detect.minConfidence = value)}
            />
          </Field>
        </div>
      </Card>

      <div class="tiles">
        <StatTile label="Frame rate" value={fpsValue} unit="FPS" trend={live.fpsHistory} trendLabel="Frame rate over the last minute" hint={system.streaming ? 'Measured in the browser' : 'Stream stopped'} />
        <StatTile label="Inference" value={system.streaming && live.state.metrics ? formatMs(live.state.metrics.latencyMs) : '-'} hint={live.state.metrics ? `Average ${formatMs(live.state.metrics.avgLatencyMs)}` : 'Waiting for metrics'} />
        <StatTile label="Objects in view" value={live.state.frame ? livePeople : '-'} hint={live.state.frame ? objectCountLabel(livePeople) : 'No frame yet'} />
      </div>

      <Card title="Current detections" description="Highest confidence first.">
        <DetectionList
          detections={detect.source === 'camera' ? (live.state.frame?.detections ?? []) : (detect.imageResult?.detections ?? [])}
          minConfidence={detect.minConfidence}
          idleText={detect.source === 'camera' ? 'Detections appear here while the stream runs.' : 'Check an image to see its detections here.'}
        />
      </Card>
    </div>

    <aside class="side">
      <SessionControls />
      <StatisticsPanel />
      <RecentDetections />
    </aside>
  </div>
</div>

<style>
  .stack {
    display: grid;
    gap: var(--space-5);
    min-width: 0;
  }
  .layout {
    display: grid;
    grid-template-columns: minmax(0, 1fr) minmax(16rem, 20rem);
    gap: var(--space-5);
    align-items: start;
    min-width: 0;
  }
  .main,
  .side {
    display: grid;
    gap: var(--space-5);
    min-width: 0;
  }
  .stream-buttons {
    display: flex;
    flex-wrap: wrap;
    gap: var(--space-2);
  }
  .threshold {
    margin-top: var(--space-4);
    padding-top: var(--space-4);
    border-top: 1px solid var(--rule);
  }
  .tiles {
    display: grid;
    grid-template-columns: repeat(3, minmax(0, 1fr));
    gap: var(--space-3);
  }
  @media (max-width: 1099px) {
    .layout {
      grid-template-columns: minmax(0, 1fr);
    }
  }
  @media (max-width: 599px) {
    .tiles {
      grid-template-columns: minmax(0, 1fr);
    }
    .stream-buttons {
      width: 100%;
    }
  }
</style>
