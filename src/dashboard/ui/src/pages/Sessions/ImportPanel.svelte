<script lang="ts">
  import { onMount } from 'svelte';
  import { api, describeError } from '../../lib/api';
  import Button from '../../lib/components/Button.svelte';
  import Card from '../../lib/components/Card.svelte';
  import Field from '../../lib/components/Field.svelte';
  import Notice from '../../lib/components/Notice.svelte';
  import Select from '../../lib/components/Select.svelte';
  import SegmentedControl from '../../lib/components/SegmentedControl.svelte';
  import Slider from '../../lib/components/Slider.svelte';
  import TextInput from '../../lib/components/TextInput.svelte';
  import { isJobActive, jobStatusLabel, percentOf } from '../../lib/jobs/job-progress';
  import { startPolling } from '../../lib/poll';
  import { system } from '../../lib/stores/system.svelte';
  import { toasts } from '../../lib/stores/toasts.svelte';
  import type { Job } from '../../lib/types';
  import * as rules from './import-logic';

  interface Props {
    /** Called once an import has finished, so the list can show the new session. */
    onfinished?: () => void;
  }

  let { onfinished }: Props = $props();

  type Mode = 'video' | 'images' | 'folder';
  const modes = [
    { value: 'video', label: 'Video file' },
    { value: 'images', label: 'Image files' },
    { value: 'folder', label: 'Folder' },
  ] as const;

  let mode = $state<Mode>('video');
  let videoFile = $state<File | null>(null);
  let imageFiles = $state<File[]>([]);
  let folder = $state('');
  let modelName = $state('');
  let confidence = $state(0.25);
  let frameStride = $state(5);
  let name = $state('');
  let errors = $state<rules.ImportErrors>({});
  let submitting = $state(false);
  let formError = $state<string | null>(null);

  /** The import being tracked, and the session it writes to when it is known. */
  let job = $state<Job | null>(null);
  let sessionId = $state<string | null>(null);

  const activeId = $derived(job && isJobActive(job.status) ? job.id : null);
  const modelOptions = $derived((system.models ?? []).map((model) => ({ value: model.name, label: model.label })));

  // Pick a model once the list is loaded: the recommended one, or the first.
  $effect(() => {
    if (modelName || !system.models?.length) return;
    modelName = (system.models.find((model) => model.recommended) ?? system.models[0]).name;
  });

  // Poll the job every second while it runs. The effect only restarts when the job id changes.
  $effect(() => {
    const id = activeId;
    if (!id) return;
    return startPolling(
      async () => {
        const fresh = await api.v1.getJob(id);
        job = fresh;
        if (!isJobActive(fresh.status)) finish(fresh);
      },
      {
        intervalMs: 1000,
        immediate: false,
        onError: (error) => {
          formError = describeError(error, 'Lost contact with the job. It keeps running on the server.');
        },
      },
    );
  });

  function finish(done: Job) {
    if (done.status === 'completed') {
      toasts.success('Import finished. The session is in the list.');
      onfinished?.();
    } else if (done.status === 'failed') {
      toasts.error(done.error ?? 'The import failed.');
    } else if (done.status === 'cancelled') {
      toasts.info('The import was cancelled.');
      onfinished?.();
    }
  }

  onMount(() => {
    // Pick up an import that was started before this page was opened, if the server still has one.
    // Without a list the panel still works for new imports, so a failure here is not shown.
    void api.v1
      .listJobs(20)
      .then((payload) => {
        const running = payload.jobs.find((item) => item.kind.startsWith('batch') && isJobActive(item.status));
        if (running && !job) job = running;
      })
      .catch(() => undefined);
  });

  function setMode(next: string) {
    mode = next as Mode;
    errors = {};
    formError = null;
  }

  function onVideoPicked(event: Event) {
    videoFile = (event.currentTarget as HTMLInputElement).files?.[0] ?? null;
  }

  function onImagesPicked(event: Event) {
    imageFiles = Array.from((event.currentTarget as HTMLInputElement).files ?? []);
  }

  async function submit(event: SubmitEvent) {
    event.preventDefault();
    formError = null;
    const common = { modelName, confidence, name };
    errors =
      mode === 'video'
        ? rules.validateVideoImport({ ...common, file: videoFile, frameStride })
        : mode === 'images'
          ? rules.validateImageUpload({ ...common, files: imageFiles })
          : rules.validateFolderImport({ ...common, folder });
    if (rules.hasErrors(errors)) return;

    const title = name.trim() || undefined;
    submitting = true;
    try {
      let accepted: { job_id: string; session_id: string };
      if (mode === 'video' && videoFile) {
        accepted = await api.v1.uploadBatchVideo(videoFile, {
          model_name: modelName,
          confidence,
          frame_stride: frameStride,
          name: title,
        });
      } else if (mode === 'images') {
        accepted = await api.v1.uploadBatchImages(imageFiles, { model_name: modelName, confidence, name: title });
      } else {
        accepted = await api.v1.startBatchFromDirectory({
          directory: folder.trim(),
          recursive: false,
          model_name: modelName,
          confidence,
          name: title,
        });
      }
      sessionId = accepted.session_id;
      job = await api.v1.getJob(accepted.job_id).catch(() => ({
        id: accepted.job_id,
        kind: mode === 'video' ? 'batch_video' : 'batch_images',
        title: title ?? 'Import',
        status: 'running' as const,
        progress: 0,
        message: 'Starting',
        created_at: new Date().toISOString(),
        finished_at: null,
        result: null,
        error: null,
      }));
      toasts.info('Import started. Progress shows below.');
    } catch (error) {
      formError = describeError(error, 'The import could not start.');
      toasts.error(formError);
    } finally {
      submitting = false;
    }
  }

  async function cancel() {
    if (!job) return;
    try {
      job = await api.v1.cancelJob(job.id);
    } catch (error) {
      // 409 means the job finished a moment ago: fetch the final state instead.
      formError = describeError(error, 'The import could not be cancelled.');
      try {
        job = await api.v1.getJob(job.id);
      } catch {
        // Keep the last state we had.
      }
    }
  }

  function clearJob() {
    job = null;
    sessionId = null;
  }

  const percent = $derived(job ? percentOf(job.progress) : 0);
  const sessionHref = $derived(sessionId ? `#/sessions/${encodeURIComponent(sessionId)}` : '#/sessions');
</script>

<Card title="Import a video or images" description="Runs the detector over a recording, a set of images or a folder on this computer. The result is saved as a session.">
  {#if job}
    <section class="progress" aria-labelledby="import-progress-title">
      <div class="progress-head">
        <h3 id="import-progress-title" class="progress-title">{job.title}</h3>
        <span class="status">{jobStatusLabel(job)}</span>
      </div>
      <div
        class="bar"
        role="progressbar"
        aria-label="Import progress"
        aria-valuemin="0"
        aria-valuemax="100"
        aria-valuenow={percent}
        aria-valuetext="{percent}%"
      >
        <span class="fill" style="width: {percent}%"></span>
      </div>
      <p class="message" aria-live="polite">{job.message || 'Working'}</p>

      {#if job.status === 'queued' || job.status === 'running'}
        <div class="actions">
          <Button variant="secondary" onclick={cancel}>Cancel import</Button>
        </div>
      {:else if job.status === 'completed'}
        <Notice tone="success" title="Import finished">
          <p>The session holds the detections from this import.</p>
          {#snippet actions()}
            <Button variant="secondary" href={sessionHref}>Open the session</Button>
            <Button variant="ghost" onclick={clearJob}>Start another</Button>
          {/snippet}
        </Notice>
      {:else if job.status === 'failed'}
        <Notice tone="danger" title="Import failed">
          <p>{job.error ?? 'The job stopped before it finished.'}</p>
          {#snippet actions()}
            <Button variant="ghost" onclick={clearJob}>Dismiss</Button>
          {/snippet}
        </Notice>
      {:else}
        <Notice tone="warning" title="Import cancelled">
          <p>Detections recorded before the cancel stay in the session.</p>
          {#snippet actions()}
            <Button variant="secondary" href={sessionHref}>Open the session</Button>
            <Button variant="ghost" onclick={clearJob}>Dismiss</Button>
          {/snippet}
        </Notice>
      {/if}
    </section>
  {:else}
    <form class="form" onsubmit={submit} novalidate>
      <div class="mode">
        <SegmentedControl label="Source" value={mode} options={modes} onchange={setMode} disabled={submitting} />
      </div>

      {#if mode === 'video'}
        <Field id="import-video" label="Video" hint="MP4, AVI, MOV or MKV. Up to 500 MB." error={errors.file}>
          <input id="import-video" class="file" type="file" accept=".mp4,.avi,.mov,.mkv,video/mp4,video/x-msvideo,video/quicktime,video/x-matroska" onchange={onVideoPicked} disabled={submitting} />
        </Field>
        <Field id="import-stride" label="Frame stride" hint="Run the model on every Nth frame. 5 means one frame in five." error={errors.stride}>
          <TextInput id="import-stride" type="number" bind:value={frameStride} min={1} max={120} step={1} inputmode="numeric" invalid={Boolean(errors.stride)} disabled={submitting} />
        </Field>
      {:else if mode === 'images'}
        <Field id="import-images" label="Images" hint="JPEG or PNG. Up to 200 files at once." error={errors.files}>
          <input id="import-images" class="file" type="file" multiple accept=".jpg,.jpeg,.png,image/jpeg,image/png" onchange={onImagesPicked} disabled={submitting} />
        </Field>
        {#if imageFiles.length}<p class="note">{imageFiles.length} {imageFiles.length === 1 ? 'image' : 'images'} chosen.</p>{/if}
      {:else}
        <Field id="import-folder" label="Folder path" hint="A folder on this computer. Only JPEG and PNG files are read. Subfolders are not searched." error={errors.folder}>
          <TextInput id="import-folder" value={folder} placeholder="C:\bins\samples" invalid={Boolean(errors.folder)} disabled={submitting} />
        </Field>
      {/if}

      <div class="grid">
        <Field id="import-model" label="Model" error={errors.model}>
          {#if system.modelsError && modelOptions.length === 0}
            <p class="note">{system.modelsError}</p>
          {:else}
            <Select id="import-model" value={modelName} options={modelOptions} invalid={Boolean(errors.model)} disabled={submitting} onchange={(value) => (modelName = value)} />
          {/if}
        </Field>
        <Field id="import-confidence" label="Confidence" hint="Detections below this score are dropped." error={errors.confidence}>
          <Slider id="import-confidence" bind:value={confidence} min={0.05} max={1} step={0.05} format={(v) => v.toFixed(2)} disabled={submitting} />
        </Field>
        <Field id="import-name" label="Name" hint="Optional. A dated name is used when this is empty.">
          <TextInput id="import-name" bind:value={name} placeholder="Bin B2, stride 5" maxlength={120} disabled={submitting} />
        </Field>
      </div>

      {#if formError}<Notice tone="danger">{formError}</Notice>{/if}

      <div class="submit">
        <Button type="submit" busy={submitting} disabled={submitting}>
          {submitting ? 'Sending' : 'Start import'}
        </Button>
        {#if mode === 'video'}
          <p class="note">A large video can take a minute to upload before the progress bar starts.</p>
        {/if}
      </div>
    </form>
  {/if}
</Card>

<style>
  .form {
    display: grid;
    gap: var(--space-4);
    min-width: 0;
  }
  .mode {
    min-width: 0;
  }
  .grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(14rem, 1fr));
    gap: var(--space-4);
    min-width: 0;
  }
  .file {
    display: block;
    width: 100%;
    min-height: var(--target);
    font-size: var(--text-small);
    color: var(--ink-soft);
  }
  .file::file-selector-button {
    min-height: var(--target);
    margin-right: var(--space-3);
    padding: 0 var(--space-3);
    border: 1px solid var(--control-edge);
    border-radius: var(--radius-control);
    background: var(--raised);
    color: var(--ink);
    font: inherit;
    cursor: pointer;
  }
  .note {
    font-size: var(--text-micro);
    color: var(--ink-soft);
  }
  .submit {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    gap: var(--space-3);
  }
  .progress {
    display: grid;
    gap: var(--space-3);
    min-width: 0;
  }
  .progress-head {
    display: flex;
    flex-wrap: wrap;
    justify-content: space-between;
    align-items: baseline;
    gap: var(--space-2);
  }
  .progress-title {
    font-size: var(--text-small);
    font-weight: var(--font-weight-semibold);
    overflow-wrap: anywhere;
  }
  .status {
    font-family: var(--font-mono);
    font-size: var(--text-micro);
    font-variant-numeric: tabular-nums;
    color: var(--ink-soft);
  }
  .bar {
    height: 0.75rem;
    border-radius: var(--radius-pill);
    background: var(--sunken);
    overflow: hidden;
  }
  .fill {
    display: block;
    height: 100%;
    border-radius: var(--radius-pill);
    background: var(--accent);
    transition: width var(--dur-base) var(--ease-out);
  }
  .message {
    font-size: var(--text-small);
    color: var(--ink-soft);
  }
  .actions {
    display: flex;
    flex-wrap: wrap;
    gap: var(--space-2);
  }
  @media (prefers-reduced-motion: reduce) {
    .fill {
      transition: none;
    }
  }
</style>
