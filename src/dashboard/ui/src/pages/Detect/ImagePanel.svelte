<script lang="ts">
  import Button from '../../lib/components/Button.svelte';
  import DetectionCanvas from '../../lib/components/DetectionCanvas.svelte';
  import Icon from '../../lib/components/Icon.svelte';
  import Notice from '../../lib/components/Notice.svelte';
  import Spinner from '../../lib/components/Spinner.svelte';
  import { detect } from '../../lib/stores/detect.svelte';
  import { system } from '../../lib/stores/system.svelte';
  import { confidenceLabel, IMAGE_ACCEPT, objectCountLabel } from './detect-logic';
  import { detectImage } from './detect-actions';

  interface Props {
    minConfidence: number;
  }

  let { minConfidence }: Props = $props();

  let input: HTMLInputElement | undefined = $state();
  let dragOver = $state(false);
  let slow = $state(false);

  const blockedReason = $derived.by(() => {
    if (system.streaming) return 'Stop the stream to check an image.';
    if (!system.modelLoaded) return 'Load a model first.';
    return null;
  });
  const stale = $derived(detect.imageResult !== null && detect.imageResult.threshold !== minConfidence);

  // After eight seconds, tell the person the server is still working and that large images take longer.
  $effect(() => {
    if (!detect.imageBusy) {
      slow = false;
      return;
    }
    const timer = setTimeout(() => {
      slow = true;
    }, 8000);
    return () => clearTimeout(timer);
  });

  function pick(files: FileList | null | undefined) {
    const file = files?.[0];
    if (file) void detectImage(file);
    if (input) input.value = '';
  }

  function onDrop(event: DragEvent) {
    event.preventDefault();
    dragOver = false;
    if (blockedReason) return;
    pick(event.dataTransfer?.files);
  }

  function onDragOver(event: DragEvent) {
    event.preventDefault();
    if (!blockedReason) dragOver = true;
  }
</script>

<div class="image-panel">
  {#if detect.imageResult}
    <DetectionCanvas
      src={detect.imageResult.src}
      detections={detect.imageResult.detections}
      {minConfidence}
      label="Image result: {objectCountLabel(detect.imageResult.detections.filter((d) => d.confidence >= minConfidence).length)} in {detect.imageResult.fileName}"
    />
    <div class="result-row">
      <p class="summary">
        {objectCountLabel(detect.imageResult.detections.filter((d) => d.confidence >= minConfidence).length)}
        at {confidenceLabel(detect.imageResult.threshold)} threshold.
        <span class="file">{detect.imageResult.fileName}</span>
      </p>
      <div class="actions">
        {#if stale}
          <Button
            variant="secondary"
            busy={detect.imageBusy}
            disabled={blockedReason !== null || detect.imageFile === null}
            onclick={() => detect.imageFile && void detectImage(detect.imageFile)}>Run again</Button
          >
        {/if}
        <Button variant="ghost" disabled={blockedReason !== null || detect.imageBusy} onclick={() => input?.click()}>
          Choose another image
        </Button>
      </div>
    </div>
    {#if stale}
      <p class="note">The threshold changed. Run the image again to apply it.</p>
    {/if}
    {#if blockedReason}<p class="blocked">{blockedReason}</p>{/if}
  {:else}
    <div
      class="dropzone"
      class:over={dragOver}
      class:blocked={blockedReason !== null}
      role="group"
      aria-label="Image drop area"
      ondragover={onDragOver}
      ondragleave={() => (dragOver = false)}
      ondrop={onDrop}
    >
      <span class="mark" aria-hidden="true"><Icon name="upload" size={24} /></span>
      <p class="title">Drop a JPEG or PNG here</p>
      <p class="hint">Up to 8 MB. The image is checked on the server with the saved model.</p>
      <Button disabled={blockedReason !== null || detect.imageBusy} onclick={() => input?.click()}>
        Choose image
      </Button>
      {#if blockedReason}<p class="blocked">{blockedReason}</p>{/if}
    </div>
  {/if}

  <input
    bind:this={input}
    class="file-input"
    type="file"
    accept={IMAGE_ACCEPT}
    aria-label="Choose a JPEG or PNG image"
    disabled={blockedReason !== null}
    onchange={(event) => pick((event.currentTarget as HTMLInputElement).files)}
  />

  {#if detect.imageBusy}
    <div class="busy" role="status">
      <Spinner size="sm" label="" />
      <span>{slow ? 'Still working. Large images take longer.' : 'Checking the image…'}</span>
    </div>
  {/if}

  {#if detect.imageError}
    <div class="error">
      <Notice tone="danger">{detect.imageError}</Notice>
    </div>
  {/if}
</div>

<style>
  .image-panel {
    display: grid;
    gap: var(--space-3);
    min-width: 0;
  }
  .dropzone {
    display: grid;
    justify-items: center;
    align-content: center;
    gap: var(--space-2);
    min-height: 16rem;
    padding: var(--space-6);
    border-radius: var(--radius-control);
    border: 1.5px dashed var(--rule-strong);
    background: var(--app);
    text-align: center;
    transition: border-color var(--dur-fast) ease-out, background-color var(--dur-fast) ease-out;
  }
  .over {
    border-color: var(--accent);
    background: var(--accent-subtle);
  }
  .mark {
    display: grid;
    place-items: center;
    width: 3rem;
    height: 3rem;
    border-radius: var(--radius-card);
    background: var(--surface);
    color: var(--accent-strong);
    box-shadow: var(--shadow-raised);
  }
  .title {
    font-weight: var(--font-weight-semibold);
  }
  .hint {
    font-size: var(--text-micro);
    color: var(--ink-soft);
  }
  .blocked {
    font-size: var(--text-small);
    color: var(--warning-ink);
    font-weight: var(--font-weight-medium);
  }
  .result-row {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    justify-content: space-between;
    gap: var(--space-3);
  }
  .summary {
    font-size: var(--text-small);
    color: var(--ink);
  }
  .file {
    display: block;
    font-size: var(--text-micro);
    color: var(--ink-soft);
    overflow-wrap: anywhere;
  }
  .actions {
    display: flex;
    flex-wrap: wrap;
    gap: var(--space-2);
  }
  .note {
    font-size: var(--text-micro);
    color: var(--warning-ink);
  }
  .busy {
    display: flex;
    align-items: center;
    gap: var(--space-2);
    font-size: var(--text-small);
    color: var(--ink-soft);
  }
  .file-input {
    position: absolute;
    width: 1px;
    height: 1px;
    opacity: 0;
    pointer-events: none;
  }
</style>
