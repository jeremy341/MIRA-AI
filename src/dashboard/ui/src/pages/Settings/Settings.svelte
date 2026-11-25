<script lang="ts">
  import { onMount } from 'svelte';
  import { api, describeError } from '../../lib/api';
  import Badge from '../../lib/components/Badge.svelte';
  import Button from '../../lib/components/Button.svelte';
  import Card from '../../lib/components/Card.svelte';
  import Field from '../../lib/components/Field.svelte';
  import Notice from '../../lib/components/Notice.svelte';
  import PageHeader from '../../lib/components/PageHeader.svelte';
  import Select, { type SelectOption } from '../../lib/components/Select.svelte';
  import Slider from '../../lib/components/Slider.svelte';
  import TextInput from '../../lib/components/TextInput.svelte';
  import Toggle from '../../lib/components/Toggle.svelte';
  import { describedBy } from '../../lib/components/field-ids';
  import { formatMegabytes } from '../../lib/format';
  import { router } from '../../lib/stores/router.svelte';
  import { settings } from '../../lib/stores/settings.svelte';
  import { system } from '../../lib/stores/system.svelte';
  import { toasts } from '../../lib/stores/toasts.svelte';
  import { stopStream } from '../Detect/detect-actions';
  import {
    hasErrors,
    payloadsOf,
    RESOLUTION_PRESETS,
    SETTING_LIMITS,
    validateSettings,
    type SettingsFieldKey,
  } from '../../lib/settings-model';
  import { confidenceLabel } from '../Detect/detect-logic';

  const modelNames = $derived((system.models ?? []).map((m) => m.name));
  const errors = $derived(validateSettings(settings.draft, modelNames));
  const locked = $derived(system.streaming);
  const selectedModel = $derived((system.models ?? []).find((m) => m.name === settings.draft.model.name) ?? null);

  let applying = $state(false);

  const modelOptions = $derived<SelectOption[]>(
    modelNames.length === 0
      ? [{ value: '', label: 'No models found', disabled: true }]
      : (system.models ?? []).map((m) => ({
          value: m.name,
          label: `${m.label}, ${formatMegabytes(m.size_mb)}${m.recommended ? ', recommended' : ''}`,
        })),
  );

  const resolutionOptions: SelectOption[] = RESOLUTION_PRESETS.map((p) => ({
    value: `${p.width}x${p.height}`,
    label: p.label,
  }));
  const resolutionKey = $derived(`${settings.draft.camera.width}x${settings.draft.camera.height}`);

  function setResolution(key: string) {
    const preset = RESOLUTION_PRESETS.find((p) => `${p.width}x${p.height}` === key);
    if (!preset) return;
    settings.draft.camera.width = preset.width;
    settings.draft.camera.height = preset.height;
  }

  function fieldError(key: SettingsFieldKey): string | undefined {
    return errors[key];
  }

  // Pick a sensible model once the list arrives: the recommended one, or the first one.
  $effect(() => {
    if (settings.draft.model.name || modelNames.length === 0) return;
    const recommended = (system.models ?? []).find((m) => m.recommended);
    settings.draft.model.name = (recommended ?? system.models?.[0])?.name ?? '';
  });

  onMount(() => {
    if (!system.models) void system.refreshModels();
  });

  async function apply() {
    if (locked) {
      toasts.warning('Stop the stream on the Detect page before changing settings.');
      return;
    }
    if (hasErrors(errors)) {
      toasts.error('Fix the highlighted fields before applying.');
      return;
    }
    applying = true;
    const draft = $state.snapshot(settings.draft);
    const payload = payloadsOf(draft);
    const failures: string[] = [];
    try {
      await api.legacy.initializeCamera(payload.camera);
    } catch (error) {
      failures.push(`Camera: ${describeError(error, 'the camera could not be set up.')}`);
    }
    try {
      await api.legacy.loadModel(payload.model);
    } catch (error) {
      failures.push(`Model: ${describeError(error, 'the model could not be loaded.')}`);
    }
    applying = false;
    if (failures.length === 0) {
      settings.markApplied(draft);
      toasts.success('Settings applied. The camera and model are ready.');
    } else {
      toasts.error(failures.join(' '));
    }
    await system.refreshStatus();
  }

  function restoreDefaults() {
    settings.resetDraft();
    toasts.info('Defaults restored. Press Apply to use them.');
  }
</script>

<PageHeader
  title="Settings"
  description="Camera and model settings. Press Apply to send them to the server. They are locked while the stream runs."
/>

<div class="stack">
  {#if locked}
    <Notice tone="warning" title="Settings are locked while the stream runs">
      Stop the stream to change the camera or the model.
      {#snippet actions()}
        <Button variant="secondary" onclick={() => stopStream()}>Stop stream</Button>
        <Button variant="ghost" onclick={() => router.navigate('detect')}>Back to Detect</Button>
      {/snippet}
    </Notice>
  {/if}

  {#if system.modelsError}
    <Notice tone="warning">{system.modelsError}</Notice>
  {/if}

  <div class="grid">
    <fieldset class="group" disabled={locked || applying}>
      <legend class="visually-hidden">Camera settings</legend>
      <Card title="Camera" description="Used by Connect camera on the Detect page.">
        <div class="fields">
          <Field
            id="camera-index"
            label="Camera index"
            hint="0 is usually the first camera connected."
            error={fieldError('camera.index')}
          >
            <TextInput
              id="camera-index"
              type="number"
              inputmode="numeric"
              min={SETTING_LIMITS.index.min}
              max={SETTING_LIMITS.index.max}
              step={1}
              bind:value={settings.draft.camera.index}
              invalid={Boolean(fieldError('camera.index'))}
              describedby={describedBy('camera-index', { hint: 'hint', error: fieldError('camera.index') })}
            />
          </Field>

          <Field
            id="camera-resolution"
            label="Resolution"
            hint="Larger frames look sharper and run slower on a Raspberry Pi."
            error={fieldError('camera.resolution')}
          >
            <Select
              id="camera-resolution"
              value={resolutionKey}
              options={resolutionOptions}
              invalid={Boolean(fieldError('camera.resolution'))}
              describedby={describedBy('camera-resolution', { hint: 'hint', error: fieldError('camera.resolution') })}
              onchange={setResolution}
            />
          </Field>

          <Field
            id="camera-fps"
            label="Frame rate"
            hint="Frames per second to ask the camera for (1 to 60)."
            error={fieldError('camera.fps')}
          >
            <TextInput
              id="camera-fps"
              type="number"
              inputmode="numeric"
              min={SETTING_LIMITS.fps.min}
              max={SETTING_LIMITS.fps.max}
              step={1}
              bind:value={settings.draft.camera.fps}
              invalid={Boolean(fieldError('camera.fps'))}
              describedby={describedBy('camera-fps', { hint: 'hint', error: fieldError('camera.fps') })}
            />
          </Field>

          <div class="toggles">
            <Toggle id="camera-autofocus" bind:checked={settings.draft.camera.autofocus}>Autofocus</Toggle>
            <Toggle id="camera-exposure" bind:checked={settings.draft.camera.auto_exposure}>Auto exposure</Toggle>
          </div>
        </div>
      </Card>
    </fieldset>

    <fieldset class="group" disabled={locked || applying}>
      <legend class="visually-hidden">Model settings</legend>
      <Card title="Model and thresholds" description="Thresholds apply to the loaded model.">
        <div class="fields">
          <Field id="model-name" label="Model" error={fieldError('model.name')}>
            <Select
              id="model-name"
              value={settings.draft.model.name}
              options={modelOptions}
              disabled={modelNames.length === 0}
              invalid={Boolean(fieldError('model.name'))}
              describedby={describedBy('model-name', { error: fieldError('model.name') })}
              onchange={(value) => (settings.draft.model.name = value)}
            />
          </Field>

          {#if selectedModel}
            <div class="model-card">
              <div class="model-head">
                <span class="model-name">{selectedModel.name}</span>
                {#if selectedModel.recommended}<Badge tone="accent">Recommended</Badge>{/if}
              </div>
              <p class="model-meta">
                {formatMegabytes(selectedModel.size_mb)}, input {selectedModel.input_size} px,
                {selectedModel.model_type === 'yolo_tflite' ? 'TFLite' : 'PyTorch'}{selectedModel.is_tflite_int8 ? ', INT8' : ''}
              </p>
            </div>
          {:else if modelNames.length === 0 && system.modelsError === null && system.models !== null}
            <Notice tone="info">No models were found. Add a model file to the detection models folder, then reload.</Notice>
          {/if}

          <Field
            id="model-confidence"
            label="Confidence threshold"
            hint="Detections below this score are dropped."
            error={fieldError('model.conf_threshold')}
          >
            <Slider
              id="model-confidence"
              bind:value={settings.draft.model.conf_threshold}
              min={0.05}
              max={1}
              step={0.05}
              format={confidenceLabel}
              describedby={describedBy('model-confidence', { hint: 'hint', error: fieldError('model.conf_threshold') })}
            />
          </Field>

          <Field id="model-reject" label="Reject threshold" hint="Scores below this value are rejected." error={fieldError('model.reject_threshold')}>
            <Slider
              id="model-reject"
              bind:value={settings.draft.model.reject_threshold}
              min={0}
              max={1}
              step={0.05}
              format={confidenceLabel}
              describedby={describedBy('model-reject', { hint: 'hint', error: fieldError('model.reject_threshold') })}
            />
          </Field>

          <Field id="model-iou" label="IoU threshold" hint="Overlapping boxes above this overlap are merged." error={fieldError('model.iou_threshold')}>
            <Slider
              id="model-iou"
              bind:value={settings.draft.model.iou_threshold}
              min={0}
              max={1}
              step={0.05}
              format={confidenceLabel}
              describedby={describedBy('model-iou', { hint: 'hint', error: fieldError('model.iou_threshold') })}
            />
          </Field>

          <Field
            id="model-latency"
            label="Target latency (ms)"
            hint="Time budget per frame, from {SETTING_LIMITS.latency.min} to {SETTING_LIMITS.latency.max} ms."
            error={fieldError('model.target_latency_ms')}
          >
            <TextInput
              id="model-latency"
              type="number"
              inputmode="numeric"
              min={SETTING_LIMITS.latency.min}
              max={SETTING_LIMITS.latency.max}
              step={1}
              bind:value={settings.draft.model.target_latency_ms}
              invalid={Boolean(fieldError('model.target_latency_ms'))}
              describedby={describedBy('model-latency', { hint: 'hint', error: fieldError('model.target_latency_ms') })}
            />
          </Field>

          <div class="toggles">
            <Toggle id="model-tracking" bind:checked={settings.draft.model.enable_tracking}>Object tracking</Toggle>
          </div>
        </div>
      </Card>
    </fieldset>
  </div>

  <div class="actions-bar">
    <p class="state" aria-live="polite">
      {#if settings.dirty}Unsaved changes.{:else}All changes are applied.{/if}
    </p>
    <div class="buttons">
      <Button variant="ghost" onclick={restoreDefaults} disabled={applying || locked}>Reset defaults</Button>
      <Button variant="ghost" onclick={() => settings.revertDraft()} disabled={!settings.dirty || applying || locked}>Discard changes</Button>
      <Button busy={applying} disabled={locked || hasErrors(errors) || applying} onclick={apply}>Apply settings</Button>
    </div>
  </div>
</div>

<style>
  .stack {
    display: grid;
    gap: var(--space-5);
    min-width: 0;
  }
  .grid {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: var(--space-5);
    align-items: start;
  }
  .group {
    min-width: 0;
    margin: 0;
    padding: 0;
    border: 0;
  }
  .group:disabled {
    opacity: 0.6;
  }
  .fields {
    display: grid;
    gap: var(--space-5);
  }
  .toggles {
    display: grid;
    gap: var(--space-2);
  }
  .model-card {
    display: grid;
    gap: var(--space-1);
    padding: var(--space-3) var(--space-4);
    border-radius: var(--radius-control);
    background: var(--app);
  }
  .model-head {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    gap: var(--space-2);
  }
  .model-name {
    font-family: var(--font-mono);
    font-size: var(--text-small);
    overflow-wrap: anywhere;
  }
  .model-meta {
    font-size: var(--text-micro);
    color: var(--ink-soft);
  }
  .actions-bar {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    justify-content: space-between;
    gap: var(--space-3);
    padding: var(--space-4) var(--space-5);
    border-radius: var(--radius-card);
    background: var(--surface);
    box-shadow: var(--shadow-raised);
    position: sticky;
    bottom: 1rem;
  }
  .state {
    font-size: var(--text-small);
    color: var(--ink-soft);
  }
  .buttons {
    display: flex;
    flex-wrap: wrap;
    gap: var(--space-2);
    justify-content: flex-end;
  }
  @media (max-width: 899px) {
    .grid {
      grid-template-columns: minmax(0, 1fr);
    }
    /* On a phone the bar scrolls with the form; a sticky bar would cover the fields. */
    .actions-bar {
      position: static;
    }
  }
</style>
