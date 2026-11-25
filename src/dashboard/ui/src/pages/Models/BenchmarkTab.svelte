<script lang="ts">
  import { onMount } from 'svelte';
  import { api, describeError } from '../../lib/api';
  import Badge from '../../lib/components/Badge.svelte';
  import Button from '../../lib/components/Button.svelte';
  import Card from '../../lib/components/Card.svelte';
  import Dialog from '../../lib/components/Dialog.svelte';
  import EmptyState from '../../lib/components/EmptyState.svelte';
  import Field from '../../lib/components/Field.svelte';
  import Notice from '../../lib/components/Notice.svelte';
  import Slider from '../../lib/components/Slider.svelte';
  import Table, { type Column } from '../../lib/components/Table.svelte';
  import TextInput from '../../lib/components/TextInput.svelte';
  import { CLASS_LABELS } from '../../lib/classes';
  import { formatDateTime, formatMs } from '../../lib/format';
  import { isJobActive, jobStatusLabel, percentOf } from '../../lib/jobs/job-progress';
  import { startPolling } from '../../lib/poll';
  import { system } from '../../lib/stores/system.svelte';
  import { toasts } from '../../lib/stores/toasts.svelte';
  import { CLASS_NAMES, type BenchmarkModelResult, type BenchmarkRun, type Job } from '../../lib/types';
  import {
    BENCHMARK_MAX_MODELS,
    DEFAULT_MAX_IMAGES,
    benchmarkStatusLabel,
    canSelectMore,
    formatMetric,
    hasModelsErrors,
    isBenchmarkDeletable,
    toggleModel,
    validateBenchmark,
    type ModelsErrors,
  } from './models-logic';

  let selected = $state<string[]>([]);
  let dataset = $state('');
  let confidence = $state(0.25);
  let maxImagesText = $state(String(DEFAULT_MAX_IMAGES));
  /** The text field as a whole number, or null while it is not one. */
  const maxImages = $derived(/^d+$/.test(maxImagesText.trim()) ? Number(maxImagesText.trim()) : null);
  let errors = $state<ModelsErrors>({});
  let starting = $state(false);
  let formError = $state<string | null>(null);

  let runs = $state<BenchmarkRun[]>([]);
  let runsTotal = $state(0);
  let runsError = $state<string | null>(null);
  let selectedRunId = $state<string | null>(null);
  let selectedRun = $state<BenchmarkRun | null>(null);
  let activeJob = $state<Job | null>(null);
  let deleteTarget = $state<BenchmarkRun | null>(null);
  let deleteOpen = $state(false);
  let deleting = $state(false);

  const activeId = $derived(activeJob && isJobActive(activeJob.status) ? activeJob.id : null);
  const modelLabel = (name: string) => system.models?.find((model) => model.name === name)?.label ?? name;

  const columns: Column<BenchmarkModelResult>[] = [
    { key: 'model', label: 'Model' },
    { key: 'map50', label: 'mAP50', align: 'right', mono: true, value: (row) => formatMetric(row.map50) },
    { key: 'map50_95', label: 'mAP50-95', align: 'right', mono: true, value: (row) => formatMetric(row.map50_95) },
    { key: 'precision', label: 'Precision', align: 'right', mono: true, value: (row) => formatMetric(row.precision) },
    { key: 'recall', label: 'Recall', align: 'right', mono: true, value: (row) => formatMetric(row.recall) },
    { key: 'f1', label: 'F1', align: 'right', mono: true, value: (row) => formatMetric(row.f1) },
    { key: 'latency', label: 'Latency', align: 'right', mono: true, value: (row) => formatMs(row.avg_latency_ms) },
    { key: 'fps', label: 'FPS', align: 'right', mono: true, value: (row) => formatMetric(row.fps, 1) },
  ];

  async function loadRuns() {
    try {
      const page = await api.v1.listBenchmarkRuns(20);
      runs = page.runs;
      runsTotal = page.total;
      runsError = null;
      if (!selectedRunId && runs.length) selectRun(runs.find((run) => run.status === 'completed')?.id ?? runs[0].id);
    } catch (failure) {
      runsError = describeError(failure, 'Past runs could not be loaded.');
    }
  }

  async function selectRun(id: string) {
    selectedRunId = id;
    try {
      selectedRun = await api.v1.getBenchmarkRun(id);
    } catch (failure) {
      toasts.error(describeError(failure, 'That run could not be opened.'));
    }
  }

  onMount(() => {
    if (!system.models) void system.refreshModels();
    void loadRuns();
  });

  // While a benchmark job runs, poll it every second and refresh the run it writes to.
  $effect(() => {
    const id = activeId;
    if (!id) return;
    return startPolling(
      async () => {
        const fresh = await api.v1.getJob(id);
        activeJob = fresh;
        if (selectedRunId) await selectRun(selectedRunId);
        if (!isJobActive(fresh.status)) {
          if (fresh.status === 'completed') toasts.success('Benchmark finished.');
          else if (fresh.status === 'failed') toasts.error(fresh.error ?? 'The benchmark failed.');
          else toasts.info('The benchmark was cancelled. Partial results are kept.');
          void loadRuns();
        }
      },
      { intervalMs: 1000, immediate: false },
    );
  });

  async function start(event: SubmitEvent) {
    event.preventDefault();
    formError = null;
    errors = validateBenchmark({ models: selected, dataset, confidence, maxImages });
    if (hasModelsErrors(errors)) return;
    starting = true;
    try {
      const accepted = await api.v1.createBenchmarkRun({
        models: selected,
        dataset: dataset.trim() || undefined,
        confidence,
        max_images: maxImages ?? undefined,
      });
      selectedRunId = accepted.run_id;
      activeJob = await api.v1.getJob(accepted.job_id).catch(() => null);
      if (!activeJob) activeJob = { id: accepted.job_id, kind: 'benchmark', title: 'Benchmark', status: 'running', progress: 0, message: 'Starting', created_at: new Date().toISOString(), finished_at: null, result: null, error: null };
      void loadRuns();
    } catch (failure) {
      formError = describeError(failure, 'The benchmark could not start.');
      toasts.error(formError);
    } finally {
      starting = false;
    }
  }

  async function cancel() {
    if (!activeJob) return;
    try {
      activeJob = await api.v1.cancelJob(activeJob.id);
    } catch (failure) {
      toasts.error(describeError(failure, 'The benchmark could not be cancelled.'));
    }
  }

  async function remove() {
    if (!deleteTarget) return;
    deleting = true;
    try {
      await api.v1.deleteBenchmarkRun(deleteTarget.id);
      if (selectedRunId === deleteTarget.id) {
        selectedRunId = null;
        selectedRun = null;
      }
      deleteOpen = false;
      toasts.success('Run deleted.');
      await loadRuns();
    } catch (failure) {
      toasts.error(describeError(failure, 'The run could not be deleted.'));
    } finally {
      deleting = false;
    }
  }

  const percent = $derived(activeJob ? percentOf(activeJob.progress) : 0);
  const errorsByModel = $derived((selectedRun?.results ?? []).filter((result) => result.errors.length > 0));
</script>

<div class="benchmark">
  <Card title="Start a benchmark" description="Runs each model on a labelled dataset and reports mAP, precision, recall and latency. A run can take a while.">
    {#if activeJob}
      <section class="progress" aria-labelledby="benchmark-progress-title">
        <div class="progress-head">
          <h3 id="benchmark-progress-title" class="progress-title">{activeJob.title}</h3>
          <span class="status">{jobStatusLabel(activeJob)}</span>
        </div>
        <div class="bar" role="progressbar" aria-label="Benchmark progress" aria-valuemin="0" aria-valuemax="100" aria-valuenow={percent} aria-valuetext="{percent}%">
          <span class="fill" style="width: {percent}%"></span>
        </div>
        <p class="note" aria-live="polite">{activeJob.message || 'Working'}</p>
        {#if isJobActive(activeJob.status)}
          <div><Button variant="secondary" onclick={cancel}>Cancel benchmark</Button></div>
        {:else}
          <div><Button variant="ghost" onclick={() => (activeJob = null)}>Start another</Button></div>
        {/if}
      </section>
    {:else}
      <form class="form" onsubmit={start} novalidate>
        <fieldset class="models" aria-describedby={errors.models ? 'benchmark-models-error' : undefined}>
          <legend>Models <span class="legend-note">{selected.length} of {BENCHMARK_MAX_MODELS} chosen, at least 1</span></legend>
          {#if !system.models}
            <p class="note" role="status">Loading the models</p>
          {:else if system.models.length === 0}
            <p class="note">No models are installed. Add one to the models folder, then reload.</p>
          {:else}
            <ul class="choices">
              {#each system.models as model (model.name)}
                {@const checked = selected.includes(model.name)}
                {@const disabled = !checked && !canSelectMore(selected, BENCHMARK_MAX_MODELS)}
                <li>
                  <label class="choice" class:checked class:disabled>
                    <input type="checkbox" {checked} {disabled} onchange={() => { selected = toggleModel(selected, model.name, BENCHMARK_MAX_MODELS); errors = { ...errors, models: undefined }; }} />
                    <span class="choice-text">
                      <span class="choice-name">{model.label}</span>
                      <span class="choice-file">{model.name}</span>
                    </span>
                  </label>
                </li>
              {/each}
            </ul>
          {/if}
          {#if errors.models}<p id="benchmark-models-error" class="error">{errors.models}</p>{/if}
        </fieldset>

        <div class="grid">
          <Field id="benchmark-dataset" label="Dataset" hint="Optional. A dataset.yaml or a folder on this computer. Empty uses the project default." error={errors.dataset}>
            <TextInput id="benchmark-dataset" bind:value={dataset} placeholder="Project default" invalid={Boolean(errors.dataset)} disabled={starting} />
          </Field>
          <Field id="benchmark-max" label="Images" hint="How many images to score. Whole number from 1 to 5000." error={errors.maxImages}>
            <TextInput id="benchmark-max" type="number" bind:value={maxImagesText} min={1} max={5000} step={1} inputmode="numeric" invalid={Boolean(errors.maxImages)} disabled={starting} />
          </Field>
        </div>
        <Field id="benchmark-confidence" label="Confidence" hint="Detections below this score are not counted." error={errors.confidence}>
          <Slider id="benchmark-confidence" bind:value={confidence} min={0.05} max={1} step={0.05} format={(v) => v.toFixed(2)} disabled={starting} />
        </Field>

        {#if formError}<Notice tone="danger">{formError}</Notice>{/if}
        <div><Button type="submit" busy={starting} disabled={starting}>Start benchmark</Button></div>
      </form>
    {/if}
  </Card>

  <section class="results" aria-labelledby="benchmark-results-title">
    <h2 id="benchmark-results-title" class="section-title">Results</h2>
    {#if !selectedRun}
      <EmptyState icon="models" title="No results yet" description="Start a benchmark, or open a past run below. Numbers appear here as each model finishes." />
    {:else}
      <div class="run-meta">
        <Badge tone={selectedRun.status === 'completed' ? 'success' : selectedRun.status === 'failed' ? 'danger' : 'neutral'}>{benchmarkStatusLabel(selectedRun.status)}</Badge>
        <span class="note">Started {formatDateTime(selectedRun.created_at)} · {selectedRun.config.models.length} {selectedRun.config.models.length === 1 ? 'model' : 'models'} · confidence {selectedRun.config.confidence.toFixed(2)} · up to {selectedRun.config.max_images ?? 'all'} images</span>
        <span class="note path">Dataset: {selectedRun.config.dataset}</span>
      </div>

      {#if errorsByModel.length}
        <Notice tone="warning" title="Some images or labels were not scored">
          <ul class="errors">
            {#each errorsByModel as result (result.model)}
              {#each result.errors as message (message)}<li><strong>{modelLabel(result.model)}:</strong> {message}</li>{/each}
            {/each}
          </ul>
        </Notice>
      {/if}

      {#if selectedRun.results && selectedRun.results.length}
        <Table caption="Benchmark results per model" columns={columns} rows={selectedRun.results} rowKey={(row) => row.model}>
          {#snippet cell(row, column)}
            {#if column.key === 'model'}
              <span class="model-cell">{modelLabel(row.model)}</span>
            {:else if column.value}
              {column.value(row)}
            {/if}
          {/snippet}
        </Table>
        <div class="details">
          {#each selectedRun.results as result (result.model)}
            <details>
              <summary>Per-class details for {modelLabel(result.model)}</summary>
              <div class="class-table">
                <table>
                  <caption class="visually-hidden">Per-class results for {modelLabel(result.model)}</caption>
                  <thead><tr><th scope="col">Class</th><th scope="col">Precision</th><th scope="col">Recall</th><th scope="col">F1</th><th scope="col">True pos.</th><th scope="col">False pos.</th><th scope="col">False neg.</th></tr></thead>
                  <tbody>
                    {#each Object.entries(result.per_class) as [name, metrics] (name)}
                      <tr>
                        <th scope="row">{CLASS_NAMES.includes(name as (typeof CLASS_NAMES)[number]) ? CLASS_LABELS[name as (typeof CLASS_NAMES)[number]] : name}</th>
                        <td>{formatMetric(metrics.precision)}</td>
                        <td>{formatMetric(metrics.recall)}</td>
                        <td>{formatMetric(metrics.f1)}</td>
                        <td>{metrics.tp}</td>
                        <td>{metrics.fp}</td>
                        <td>{metrics.fn}</td>
                      </tr>
                    {:else}
                      <tr><td colspan="7">No per-class numbers for this model.</td></tr>
                    {/each}
                  </tbody>
                </table>
              </div>
            </details>
          {/each}
        </div>
      {:else if selectedRun.status === 'queued' || selectedRun.status === 'running'}
        <p class="note" role="status">No model has finished yet.</p>
      {:else}
        <p class="note">This run has no results.</p>
      {/if}
    {/if}
  </section>

  <Card title="Past runs" description={runsTotal ? `${runsTotal} saved. The list keeps the latest 20.` : 'Finished and cancelled runs appear here.'}>
    {#if runsError}
      <Notice tone="danger"><p>{runsError}</p></Notice>
    {:else if runs.length === 0}
      <p class="note">No runs yet.</p>
    {:else}
      <ul class="history">
        {#each runs as run (run.id)}
          <li class:current={run.id === selectedRunId}>
            <div class="history-text">
              <span class="history-name">{run.config.models.map(modelLabel).join(', ')}</span>
              <span class="note">{formatDateTime(run.created_at)} · <Badge>{benchmarkStatusLabel(run.status)}</Badge></span>
            </div>
            <div class="history-actions">
              <Button variant="secondary" onclick={() => selectRun(run.id)}>Open</Button>
              <Button variant="ghost" disabled={!isBenchmarkDeletable(run.status)} title={isBenchmarkDeletable(run.status) ? undefined : 'A running benchmark cannot be deleted. Cancel it first.'} onclick={() => { deleteTarget = run; deleteOpen = true; }}>Delete</Button>
            </div>
          </li>
        {/each}
      </ul>
    {/if}
  </Card>

  <Dialog bind:open={deleteOpen} title="Delete this run?">
    <p>The results of this benchmark run are removed. The dataset and the model files are not changed.</p>
    {#snippet actions()}
      <Button variant="ghost" disabled={deleting} onclick={() => (deleteOpen = false)}>Keep it</Button>
      <Button variant="danger" busy={deleting} onclick={remove}>Delete run</Button>
    {/snippet}
  </Dialog>
</div>

<style>
  .benchmark {
    display: grid;
    gap: var(--space-6);
    min-width: 0;
  }
  .form {
    display: grid;
    gap: var(--space-5);
    min-width: 0;
  }
  .grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(14rem, 1fr));
    gap: var(--space-4);
  }
  .models {
    display: grid;
    gap: var(--space-2);
    min-width: 0;
    margin: 0;
    padding: 0;
    border: 0;
  }
  legend {
    font-size: var(--text-small);
    font-weight: var(--font-weight-medium);
    margin-bottom: var(--space-2);
    padding: 0;
  }
  .legend-note {
    font-weight: normal;
    color: var(--ink-soft);
    font-size: var(--text-micro);
    margin-left: var(--space-2);
  }
  .choices {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(15rem, 1fr));
    gap: var(--space-2);
    list-style: none;
    margin: 0;
    padding: 0;
  }
  .choice {
    display: flex;
    align-items: center;
    gap: var(--space-3);
    min-height: var(--target);
    padding: var(--space-2) var(--space-3);
    border: 1px solid var(--rule-strong);
    border-radius: var(--radius-control);
    background: var(--raised);
    cursor: pointer;
  }
  .choice.checked {
    border-color: var(--accent);
    background: var(--accent-subtle);
  }
  .choice.disabled {
    opacity: 0.55;
    cursor: not-allowed;
  }
  .choice input {
    width: 1.125rem;
    height: 1.125rem;
    accent-color: var(--accent);
    flex-shrink: 0;
  }
  .choice-text {
    display: grid;
    min-width: 0;
    flex: 1;
  }
  .choice-name {
    font-size: var(--text-small);
    font-weight: var(--font-weight-medium);
    overflow-wrap: anywhere;
  }
  .choice-file {
    font-family: var(--font-mono);
    font-size: var(--text-micro);
    color: var(--ink-soft);
    overflow-wrap: anywhere;
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
  .results {
    display: grid;
    gap: var(--space-4);
    min-width: 0;
  }
  .section-title {
    font-size: var(--text-title);
    font-weight: var(--font-weight-semibold);
  }
  .run-meta {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    gap: var(--space-2) var(--space-3);
  }
  .note {
    font-size: var(--text-micro);
    color: var(--ink-soft);
  }
  .path {
    font-family: var(--font-mono);
    overflow-wrap: anywhere;
  }
  .error {
    font-size: var(--text-micro);
    color: var(--destructive);
    font-weight: var(--font-weight-medium);
  }
  .errors {
    margin: 0;
    padding-left: 1.125rem;
    display: grid;
    gap: var(--space-1);
  }
  .model-cell {
    font-weight: var(--font-weight-medium);
    overflow-wrap: anywhere;
  }
  .details {
    display: grid;
    gap: var(--space-2);
  }
  details {
    border-radius: var(--radius-control);
    background: var(--surface);
    box-shadow: var(--shadow-raised);
    padding: 0 var(--space-4);
  }
  summary {
    min-height: var(--target);
    display: flex;
    align-items: center;
    font-size: var(--text-small);
    font-weight: var(--font-weight-medium);
    color: var(--accent-strong);
    cursor: pointer;
  }
  .class-table {
    overflow-x: auto;
    padding-bottom: var(--space-3);
  }
  .class-table table {
    width: 100%;
    border-collapse: collapse;
    font-size: var(--text-micro);
    font-variant-numeric: tabular-nums;
  }
  .class-table th,
  .class-table td {
    padding: var(--space-2);
    border-bottom: 1px solid var(--rule);
    text-align: right;
    white-space: nowrap;
  }
  .class-table th[scope='row'] {
    text-align: left;
  }
  .history {
    display: grid;
    list-style: none;
    margin: 0;
    padding: 0;
  }
  .history li {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    justify-content: space-between;
    gap: var(--space-3);
    min-height: 3.25rem;
    padding: var(--space-2) var(--space-2);
    border-bottom: 1px solid var(--rule);
  }
  .history li.current {
    background: var(--accent-subtle);
  }
  .history-text {
    display: grid;
    gap: 0.125rem;
    min-width: 0;
  }
  .history-name {
    font-size: var(--text-small);
    font-weight: var(--font-weight-medium);
    overflow-wrap: anywhere;
  }
  .history-actions {
    display: flex;
    flex-wrap: wrap;
    gap: var(--space-1);
  }
  @media (prefers-reduced-motion: reduce) {
    .fill {
      transition: none;
    }
  }
</style>
