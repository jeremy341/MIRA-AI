<script lang="ts">
  import { onDestroy, onMount } from 'svelte';
  import { api, describeError } from '../../lib/api';
  import Badge from '../../lib/components/Badge.svelte';
  import Button from '../../lib/components/Button.svelte';
  import Card from '../../lib/components/Card.svelte';
  import ClassChip from '../../lib/components/ClassChip.svelte';
  import Dialog from '../../lib/components/Dialog.svelte';
  import EmptyState from '../../lib/components/EmptyState.svelte';
  import Field from '../../lib/components/Field.svelte';
  import Notice from '../../lib/components/Notice.svelte';
  import Slider from '../../lib/components/Slider.svelte';
  import { formatDateTime, formatMs, formatPercent } from '../../lib/format';
  import { system } from '../../lib/stores/system.svelte';
  import { toasts } from '../../lib/stores/toasts.svelte';
  import { CLASS_NAMES, type ClassCounts, type CompareRecord, type CompareWinnerHint } from '../../lib/types';
  import { COMPARE_MAX_MODELS, canSelectMore, hasModelsErrors, toggleModel, validateCompare, winnerLines, type ModelsErrors } from './models-logic';

  /** One model's card. Reopened comparisons have no image, because the server keeps none. */
  interface ShownModel {
    name: string;
    latency_ms: number;
    objects: number;
    class_counts: ClassCounts;
    avg_confidence: number | null;
    annotated_image: string | null;
  }

  interface Shown {
    id: string;
    input_name: string;
    created_at: string | null;
    models: ShownModel[];
    winner_hint: CompareWinnerHint;
    reopened: boolean;
  }

  let selected = $state<string[]>([]);
  let file = $state<File | null>(null);
  let previewUrl = $state<string | null>(null);
  let confidence = $state(0.25);
  let errors = $state<ModelsErrors>({});
  let running = $state(false);
  let dragOver = $state(false);
  let shown = $state<Shown | null>(null);

  let history = $state<CompareRecord[]>([]);
  let historyTotal = $state(0);
  let historyError = $state<string | null>(null);
  let opening = $state<string | null>(null);
  let deleteTarget = $state<CompareRecord | null>(null);
  let deleteOpen = $state(false);
  let deleting = $state(false);

  const labelFor = (name: string) => system.models?.find((model) => model.name === name)?.label ?? name;

  async function loadHistory() {
    try {
      const page = await api.v1.listComparisons(20);
      history = page.comparisons;
      historyTotal = page.total;
      historyError = null;
    } catch (failure) {
      historyError = describeError(failure, 'Past comparisons could not be loaded.');
    }
  }

  onMount(() => {
    if (!system.models) void system.refreshModels();
    void loadHistory();
  });

  function setFile(next: File | null) {
    if (previewUrl) URL.revokeObjectURL(previewUrl);
    file = next;
    previewUrl = next ? URL.createObjectURL(next) : null;
    errors = { ...errors, file: undefined };
  }

  onDestroy(() => {
    if (previewUrl) URL.revokeObjectURL(previewUrl);
  });

  function onPick(event: Event) {
    setFile((event.currentTarget as HTMLInputElement).files?.[0] ?? null);
  }

  function onDrop(event: DragEvent) {
    event.preventDefault();
    dragOver = false;
    const dropped = event.dataTransfer?.files?.[0] ?? null;
    if (dropped) setFile(dropped);
  }

  function toggle(name: string) {
    selected = toggleModel(selected, name, COMPARE_MAX_MODELS);
    errors = { ...errors, models: undefined };
  }

  async function run(event: SubmitEvent) {
    event.preventDefault();
    errors = validateCompare({ models: selected, file, confidence });
    if (hasModelsErrors(errors) || !file) return;
    running = true;
    try {
      const form = new FormData();
      form.append('image', file, file.name);
      form.append('models', selected.join(','));
      form.append('confidence', String(confidence));
      const response = await api.v1.runCompare(form);
      shown = {
        id: response.id,
        input_name: response.input_name,
        created_at: null,
        models: response.models.map((model) => ({ ...model, annotated_image: model.annotated_image })),
        winner_hint: response.winner_hint,
        reopened: false,
      };
      toasts.success('Comparison saved. It is listed below.');
      void loadHistory();
    } catch (failure) {
      toasts.error(describeError(failure, 'The comparison could not run.'));
    } finally {
      running = false;
    }
  }

  async function open(id: string) {
    opening = id;
    try {
      const record = await api.v1.getComparison(id);
      shown = {
        id: record.id,
        input_name: record.input_name,
        created_at: record.created_at,
        models: record.models.map((model) => ({ ...model, annotated_image: null })),
        winner_hint: record.winner_hint,
        reopened: true,
      };
    } catch (failure) {
      toasts.error(describeError(failure, 'That comparison could not be opened.'));
    } finally {
      opening = null;
    }
  }

  async function remove() {
    if (!deleteTarget) return;
    deleting = true;
    try {
      await api.v1.deleteComparison(deleteTarget.id);
      if (shown?.id === deleteTarget.id) shown = null;
      history = history.filter((item) => item.id !== deleteTarget?.id);
      historyTotal = Math.max(0, historyTotal - 1);
      deleteOpen = false;
      toasts.success('Comparison deleted.');
    } catch (failure) {
      toasts.error(describeError(failure, 'The comparison could not be deleted.'));
    } finally {
      deleting = false;
    }
  }
</script>

<div class="compare">
  <Card title="Compare on one image" description="Run two to four models on the same picture and see where they differ.">
    <form class="form" onsubmit={run} novalidate>
      <fieldset class="models" aria-describedby={errors.models ? 'compare-models-error' : undefined}>
        <legend>Models <span class="legend-note">{selected.length} of {COMPARE_MAX_MODELS} chosen, at least 2</span></legend>
        {#if !system.models}
          <p class="note" role="status">Loading the models</p>
        {:else if system.models.length === 0}
          <p class="note">No models are installed. Add one to the models folder, then reload.</p>
        {:else}
          <ul class="choices">
            {#each system.models as model (model.name)}
              {@const checked = selected.includes(model.name)}
              {@const disabled = !checked && !canSelectMore(selected, COMPARE_MAX_MODELS)}
              <li>
                <label class="choice" class:checked class:disabled>
                  <input type="checkbox" {checked} {disabled} onchange={() => toggle(model.name)} />
                  <span class="choice-text">
                    <span class="choice-name">{model.label}</span>
                    <span class="choice-file">{model.name}</span>
                    {#if model.recommended}<span><Badge tone="accent" outline>Recommended</Badge></span>{/if}
                  </span>
                </label>
              </li>
            {/each}
          </ul>
        {/if}
        {#if errors.models}<p id="compare-models-error" class="error">{errors.models}</p>{/if}
      </fieldset>

      <Field id="compare-image" label="Image" hint="JPEG or PNG, up to 8 MB. Drop a file here or choose one." error={errors.file}>
        <label
          class="drop"
          class:over={dragOver}
          ondragover={(event) => {
            event.preventDefault();
            dragOver = true;
          }}
          ondragleave={() => (dragOver = false)}
          ondrop={onDrop}
        >
          <input id="compare-image" class="visually-hidden-input" type="file" accept="image/jpeg,image/png" onchange={onPick} disabled={running} />
          {#if previewUrl}
            <img class="preview" src={previewUrl} alt="Preview of the selected file" />
            <span class="drop-text">{file?.name} ({Math.round((file?.size ?? 0) / 1024)} KB). Choose another to replace it.</span>
          {:else}
            <span class="drop-text">Drop a JPEG or PNG here, or <span class="link">choose a file</span></span>
          {/if}
        </label>
      </Field>

      <Field id="compare-confidence" label="Confidence" hint="Detections below this score are dropped in every model." error={errors.confidence}>
        <Slider id="compare-confidence" bind:value={confidence} min={0.05} max={1} step={0.05} format={(v) => v.toFixed(2)} disabled={running} />
      </Field>

      <div class="submit">
        <Button type="submit" busy={running} disabled={running}>Compare models</Button>
      </div>
    </form>
  </Card>

  <section class="results" aria-labelledby="compare-results-title">
    <h2 id="compare-results-title" class="visually-hidden">Comparison results</h2>
    {#if shown}
      <div class="result-head">
        <p class="result-name">{shown.input_name}</p>
        {#if shown.reopened && shown.created_at}
          <p class="note">Saved {formatDateTime(shown.created_at)}. Images are not kept for saved comparisons, so only the numbers are shown.</p>
        {/if}
      </div>

      <Notice tone="info" title="What the run shows">
        <ul class="winner">
          {#each winnerLines(shown.winner_hint) as line (line)}<li>{line}</li>{/each}
        </ul>
        <p class="winner-note">{shown.winner_hint.note}</p>
      </Notice>

      <div class="cards">
        {#each shown.models as model (model.name)}
          <article class="model-card" aria-labelledby="model-{model.name.replace(/[^a-z0-9]/gi, '-')}">
            <header class="model-head">
              <h3 id="model-{model.name.replace(/[^a-z0-9]/gi, '-')}" class="model-name">{labelFor(model.name)}</h3>
              <span class="model-file">{model.name}</span>
            </header>
            {#if model.annotated_image}
              <img class="annotated" src={model.annotated_image} alt="{labelFor(model.name)} found {model.objects} {model.objects === 1 ? 'object' : 'objects'}, boxed on the picture" />
            {:else}
              <div class="no-image">No image kept for this comparison</div>
            {/if}
            <dl class="numbers">
              <div><dt>Latency</dt><dd>{formatMs(model.latency_ms)}</dd></div>
              <div><dt>Objects</dt><dd>{model.objects}</dd></div>
              <div><dt>Average confidence</dt><dd>{formatPercent(model.avg_confidence)}</dd></div>
            </dl>
            <ul class="classes" aria-label="Objects per class">
              {#each CLASS_NAMES as cls}
                <li><ClassChip className={cls} value={String(model.class_counts[cls])} /></li>
              {/each}
            </ul>
          </article>
        {/each}
      </div>
    {:else}
      <EmptyState
        icon="models"
        title="No comparison yet"
        description="Choose two to four models and an image, then run the comparison. Every model sees the same picture."
      />
    {/if}
  </section>

  <Card title="Past comparisons" description={historyTotal ? `${historyTotal} saved. The list keeps the latest 20.` : 'Saved comparisons appear here.'}>
    {#if historyError}
      <Notice tone="danger"><p>{historyError}</p></Notice>
    {:else if history.length === 0}
      <p class="note">Nothing saved yet.</p>
    {:else}
      <ul class="history">
        {#each history as item (item.id)}
          <li>
            <div class="history-text">
              <span class="history-name">{item.input_name}</span>
              <span class="note">{formatDateTime(item.created_at)} · {item.models.map((model) => labelFor(model.name)).join(', ')}</span>
            </div>
            <div class="history-actions">
              <Button variant="secondary" size="md" busy={opening === item.id} onclick={() => open(item.id)}>Open</Button>
              <Button variant="ghost" onclick={() => { deleteTarget = item; deleteOpen = true; }}>Delete</Button>
            </div>
          </li>
        {/each}
      </ul>
    {/if}
  </Card>

  <Dialog bind:open={deleteOpen} title="Delete this comparison?">
    <p>The saved numbers for "{deleteTarget?.input_name}" are removed. The model files are not affected.</p>
    {#snippet actions()}
      <Button variant="ghost" disabled={deleting} onclick={() => (deleteOpen = false)}>Keep it</Button>
      <Button variant="danger" busy={deleting} onclick={remove}>Delete comparison</Button>
    {/snippet}
  </Dialog>
</div>

<style>
  .compare {
    display: grid;
    gap: var(--space-6);
    min-width: 0;
  }
  .form {
    display: grid;
    gap: var(--space-5);
    min-width: 0;
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
    grid-template-columns: repeat(auto-fill, minmax(17rem, 1fr));
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
  .drop {
    display: grid;
    place-items: center;
    gap: var(--space-3);
    min-height: 9rem;
    padding: var(--space-4);
    border: 1.5px dashed var(--control-edge);
    border-radius: var(--radius-card);
    background: var(--raised);
    text-align: center;
    cursor: pointer;
  }
  .drop.over {
    border-color: var(--accent);
    background: var(--accent-subtle);
  }
  .drop:focus-within {
    outline: 2px solid var(--accent);
    outline-offset: 2px;
  }
  .visually-hidden-input {
    position: absolute;
    width: 1px;
    height: 1px;
    opacity: 0;
    overflow: hidden;
  }
  .preview {
    max-height: 9rem;
    width: auto;
    border-radius: var(--radius-control);
  }
  .drop-text {
    font-size: var(--text-small);
    color: var(--ink-soft);
    overflow-wrap: anywhere;
  }
  .link {
    color: var(--accent-strong);
    font-weight: var(--font-weight-medium);
    text-decoration: underline;
  }
  .submit {
    display: flex;
    flex-wrap: wrap;
    gap: var(--space-3);
  }
  .error {
    font-size: var(--text-micro);
    color: var(--destructive);
    font-weight: var(--font-weight-medium);
  }
  .note {
    font-size: var(--text-micro);
    color: var(--ink-soft);
  }
  .results {
    display: grid;
    gap: var(--space-4);
    min-width: 0;
  }
  .result-head {
    display: grid;
    gap: var(--space-1);
  }
  .result-name {
    font-size: var(--text-title);
    font-weight: var(--font-weight-semibold);
    overflow-wrap: anywhere;
  }
  .winner {
    margin: 0;
    padding-left: 1.125rem;
  }
  .winner-note {
    margin-top: var(--space-2);
    color: var(--ink-soft);
    font-size: var(--text-micro);
  }
  .cards {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(min(100%, 17rem), 1fr));
    gap: var(--space-4);
  }
  .model-card {
    display: grid;
    gap: var(--space-3);
    align-content: start;
    padding: var(--space-4);
    border-radius: var(--radius-card);
    background: var(--surface);
    box-shadow: var(--shadow-raised);
    min-width: 0;
  }
  .model-head {
    display: grid;
    gap: 0.125rem;
  }
  .model-name {
    font-size: var(--text-small);
    font-weight: var(--font-weight-semibold);
    overflow-wrap: anywhere;
  }
  .model-file {
    font-family: var(--font-mono);
    font-size: var(--text-micro);
    color: var(--ink-soft);
    overflow-wrap: anywhere;
  }
  .annotated {
    width: 100%;
    height: auto;
    border-radius: var(--radius-control);
    background: var(--sunken);
  }
  .no-image {
    display: grid;
    place-items: center;
    min-height: 8rem;
    border-radius: var(--radius-control);
    background: var(--app);
    color: var(--ink-soft);
    font-size: var(--text-micro);
    text-align: center;
    padding: var(--space-3);
  }
  .numbers {
    display: grid;
    grid-template-columns: repeat(3, minmax(0, 1fr));
    gap: var(--space-2);
    margin: 0;
  }
  .numbers div {
    display: grid;
    gap: 0.125rem;
    min-width: 0;
  }
  .numbers dt {
    font-size: var(--text-micro);
    color: var(--ink-soft);
  }
  .numbers dd {
    margin: 0;
    font-family: var(--font-mono);
    font-variant-numeric: tabular-nums;
    font-size: var(--text-small);
    font-weight: var(--font-weight-semibold);
  }
  .classes {
    display: flex;
    flex-wrap: wrap;
    gap: var(--space-1);
    list-style: none;
    margin: 0;
    padding: 0;
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
    padding: var(--space-2) 0;
    border-bottom: 1px solid var(--rule);
  }
  .history-text {
    display: grid;
    min-width: 0;
  }
  .history-name {
    font-size: var(--text-small);
    font-weight: var(--font-weight-medium);
    overflow-wrap: anywhere;
  }
  .history-actions {
    display: flex;
    gap: var(--space-1);
  }
</style>
