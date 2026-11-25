<script lang="ts">
  import type { Snippet } from 'svelte';
  import type { Locale } from '$i18n/config';
  import { fmt, formatConfidence } from '$i18n/format';
  import { classBorderVar, tagTextColor } from '$lib/class-colors';
  import type { DetectionFigureLabels } from '$lib/detection-labels';
  import type { FigureEntry } from '$lib/figures';
  import { CLASS_BY_ID } from '$lib/site';
  import FigureCaption from './FigureCaption.svelte';

  /**
   * A real photo with the model's real detections drawn on top as positioned HTML boxes (coordinates are
   * normalised 0..1, so they scale with the image). Each box carries a class-coloured tag with the class name
   * and confidence. The boxes are decorative for assistive technology: a visually hidden list repeats every
   * detection and is linked to the image with aria-describedby.
   */
  let {
    lang,
    entry,
    expectedFile,
    n,
    id,
    caption,
    labels,
    maxHeight = '34rem',
    toggle = true,
    priority = false,
    class: className = ''
  }: {
    lang: Locale;
    /** The photo and its detections. Null renders a labelled placeholder (the file is not in static/figures yet). */
    entry: FigureEntry | null;
    /** File name shown in the placeholder when `entry` is null. */
    expectedFile: string;
    n: number;
    id?: string;
    caption: Snippet | string;
    labels: DetectionFigureLabels;
    /** Limits the photo's height so a tall photo does not push the page down (CSS length). */
    maxHeight?: string;
    /** Show the "hide boxes" toggle. */
    toggle?: boolean;
    /** Load eagerly (for the photo that is on screen first). */
    priority?: boolean;
    class?: string;
  } = $props();

  const uid = $props.id();
  const listId = `${uid}-list`;

  let show = $state(true);

  const items = $derived(
    entry
      ? entry.detections.map((d) =>
          fmt(labels.altItem, { cls: labels.classes[d.cls], conf: formatConfidence(lang, d.confidence) })
        )
      : []
  );
  const alt = $derived(`${labels.altPrefix} ${items.length === 0 ? labels.altNone : ''}`.trim());
</script>

{#if !entry}
  <figure {id} class="min-w-0 {className}">
    <div
      role="img"
      aria-label="{labels.placeholderTitle}. {fmt(labels.placeholderHint, { file: expectedFile })}"
      class="flex aspect-[4/3] w-full max-w-[34rem] flex-col items-center justify-center gap-1 border border-dashed border-ink-soft bg-surface p-4 text-center"
    >
      <span class="font-serif text-lg text-ink">{labels.placeholderTitle}</span>
      <span class="font-mono text-xs text-muted-foreground">{fmt(labels.placeholderHint, { file: expectedFile })}</span>
    </div>
    <FigureCaption {n} label={labels.figure}>
      {#if typeof caption === 'string'}{caption}{:else}{@render caption()}{/if}
    </FigureCaption>
  </figure>
{:else}
  <figure {id} class="min-w-0 {className}" style:max-width="{entry.width}px">
    <div
      class="relative max-w-full overflow-hidden border border-rule bg-surface"
      style:width="min(100%, calc({maxHeight} * {entry.width / entry.height}))"
      style:aspect-ratio="{entry.width} / {entry.height}"
    >
      <img
        src="/figures/{entry.file}"
        width={entry.width}
        height={entry.height}
        {alt}
        aria-describedby={items.length > 0 ? listId : undefined}
        loading={priority ? 'eager' : 'lazy'}
        decoding="async"
        fetchpriority={priority ? 'high' : undefined}
        class="block h-full w-full object-cover"
      />
      {#if show}
        <div aria-hidden="true" class="absolute inset-0">
          {#each entry.detections as d, i}
            {@const color = CLASS_BY_ID[d.cls].cssVar}
            <div
              class="absolute {toggle ? 'detect-box' : ''}"
              style:left="{d.box[0] * 100}%"
              style:top="{d.box[1] * 100}%"
              style:width="{(d.box[2] - d.box[0]) * 100}%"
              style:height="{(d.box[3] - d.box[1]) * 100}%"
              style:border="2px solid {color}"
              style:box-shadow="0 0 0 1px rgb(255 255 255 / 0.85), inset 0 0 0 1px rgb(0 0 0 / 0.4)"
              style:animation-delay="{i * 60}ms"
            >
              <span
                class="absolute top-0 left-0 max-w-full overflow-hidden px-1.5 py-[3px] font-mono text-xs leading-none font-medium text-ellipsis whitespace-nowrap"
                style:background-color={color}
                style:color={tagTextColor(d.cls)}
                style:outline="1px solid {classBorderVar(d.cls)}"
              >
                {labels.classes[d.cls]} {formatConfidence(lang, d.confidence)}
              </span>
            </div>
          {/each}
        </div>
      {/if}
    </div>
    {#if items.length > 0}
      <ul id={listId} class="sr-only">
        <li>{labels.altListIntro}</li>
        {#each items as text}<li>{text}</li>{/each}
      </ul>
    {/if}
    <FigureCaption {n} label={labels.figure}>
      {#if typeof caption === 'string'}{caption}{:else}{@render caption()}{/if}
    </FigureCaption>
    {#if toggle && entry.detections.length > 0}
      <button
        type="button"
        aria-pressed={show}
        onclick={() => (show = !show)}
        class="nb-link mt-1 inline-flex min-h-11 items-center gap-1.5 text-[0.875rem] sm:min-h-8"
      >
        {labels.boxesToggle}
        <span aria-hidden="true" class="font-mono text-[0.8125rem] text-muted-foreground">
          {show ? labels.boxesOn : labels.boxesOff}
        </span>
      </button>
    {/if}
  </figure>
{/if}
