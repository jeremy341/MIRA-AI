<script lang="ts">
  import { onMount } from 'svelte';
  import type { Dictionary } from '$i18n';
  import type { Locale } from '$i18n/config';
  import { formatConfidence } from '$i18n/format';
  import { tagTextColor } from '$lib/class-colors';
  import { getFigure } from '$lib/figures';
  import { CLASS_BY_ID } from '$lib/site';
  import ClassChip from '../ClassChip.svelte';
  import Rich from '../Rich.svelte';
  import HomeSection from './HomeSection.svelte';
  import ResultStrip from './ResultStrip.svelte';

  /**
   * "What is MIRA?": three steps on the left, one real photo on the right. On first sight the steps advance once and
   * rest on the box. Any click, hover or focus stops that, and it never runs with reduced motion.
   */
  let { lang, dict }: { lang: Locale; dict: Dictionary } = $props();

  const STEP_MS = 3200;
  /** The step the automatic run rests on: the photo with its box. */
  const REST = 1;
  const t = $derived(dict.home.what);
  const entry = getFigure('detect-06.jpg');
  const detection = entry?.detections[0];

  let active = $state(REST);
  let running = $state(false);
  let root: HTMLDivElement | undefined = $state();
  let timers: ReturnType<typeof setTimeout>[] = [];

  function stop() {
    running = false;
    for (const timer of timers) clearTimeout(timer);
    timers = [];
  }

  function choose(index: number) {
    stop();
    active = index;
  }

  function play() {
    running = true;
    active = 0;
    timers = [
      setTimeout(() => (active = 2), STEP_MS),
      setTimeout(() => {
        active = REST;
        running = false;
      }, STEP_MS * 2)
    ];
  }

  onMount(() => {
    if (!root || matchMedia('(prefers-reduced-motion: reduce)').matches) return;
    const seen = new IntersectionObserver(
      (entries) => {
        if (!entries.some((item) => item.isIntersecting)) return;
        seen.disconnect();
        play();
      },
      { threshold: 0.4 }
    );
    seen.observe(root);
    return () => {
      seen.disconnect();
      stop();
    };
  });

  const boxText = $derived(detection ? detection.box.map((v) => formatConfidence(lang, v)).join(' · ') : '');
</script>

<HomeSection id="what" title={t.title} lede={t.lede}>
  {#if entry && detection}
    <div
      bind:this={root}
      role="group"
      aria-label={t.stepsLabel}
      class="grid grid-cols-[minmax(0,1fr)] items-center gap-8 lg:grid-cols-[minmax(0,5fr)_minmax(0,7fr)] lg:gap-12"
      onpointerenter={() => running && choose(active)}
      onfocusin={() => running && choose(active)}
    >
      <ol class="space-y-2">
        {#each t.steps as step, index (step.title)}
          <li>
            <button
              type="button"
              aria-pressed={active === index}
              onclick={() => choose(index)}
              class="w-full rounded-2xl p-5 text-left transition-[background-color,box-shadow] duration-(--dur-base) {active === index
                ? 'bg-tint'
                : 'hover:bg-sunken'}"
            >
              <span class="flex items-baseline gap-3 text-[1.1875rem] font-semibold text-brand-ink">
                <span class="font-mono text-[0.875rem] text-accent-strong">{index + 1}</span>{step.title}
              </span>
              <span class="mt-1.5 block pl-6 text-[0.9375rem] leading-[1.55] text-ink-soft"><Rich text={step.text} /></span>
              <span aria-hidden="true" class="mt-3 ml-6 block h-1 overflow-hidden rounded-full bg-tint-strong">
                {#if active === index}
                  <span class="progress block h-full rounded-full bg-brand" class:running={running && index === 0} style:--ms="{STEP_MS}ms"></span>
                {/if}
              </span>
            </button>
          </li>
        {/each}
      </ol>

      <figure class="min-w-0">
        <div class="rounded-3xl bg-tint p-4 sm:p-8">
          <div class="card relative mx-auto max-w-[36rem] overflow-hidden" style:aspect-ratio="{entry.width} / {entry.height}">
            <img
              src="/figures/{entry.file}"
              width={entry.width}
              height={entry.height}
              alt={t.photoAlt}
              loading="lazy"
              decoding="async"
              class="block h-full w-full object-cover"
            />
            {#if active > 0}
              <div
                aria-hidden="true"
                class="detect-box absolute"
                style:left="{detection.box[0] * 100}%"
                style:top="{detection.box[1] * 100}%"
                style:width="{(detection.box[2] - detection.box[0]) * 100}%"
                style:height="{(detection.box[3] - detection.box[1]) * 100}%"
                style:border="3px solid {CLASS_BY_ID[detection.cls].cssVar}"
                style:box-shadow="0 0 0 1px rgb(255 255 255 / 0.9), inset 0 0 0 1px rgb(255 255 255 / 0.55)"
              >
                <span
                  class="absolute top-0 left-0 px-2 py-1 font-mono text-[0.8125rem] leading-none whitespace-nowrap"
                  style:background-color={CLASS_BY_ID[detection.cls].cssVar}
                  style:color={tagTextColor(detection.cls)}
                >
                  {dict.common.classes[detection.cls]} {formatConfidence(lang, detection.confidence)}
                </span>
              </div>
            {/if}
            {#if active === 2}
              <div class="detect-box card absolute right-3 bottom-3 left-3 p-4 sm:left-auto sm:w-[17rem]">
                <p class="text-[0.9375rem] font-bold">{t.resultTitle}</p>
                <dl class="mt-2 space-y-1.5 text-[0.8125rem]">
                  <div class="flex justify-between gap-4">
                    <dt class="text-ink-soft">{t.resultCls}</dt>
                    <dd><ClassChip cls={detection.cls} label={dict.common.classes[detection.cls]} /></dd>
                  </div>
                  <div class="flex justify-between gap-4">
                    <dt class="text-ink-soft">{t.resultConf}</dt>
                    <dd class="font-mono">{formatConfidence(lang, detection.confidence)}</dd>
                  </div>
                  <div class="border-t border-rule pt-1.5">
                    <dt class="text-ink-soft">{t.resultBox}</dt>
                    <dd class="mt-0.5 font-mono">{boxText}</dd>
                  </div>
                </dl>
              </div>
            {/if}
          </div>
        </div>
        <figcaption class="mt-3 text-[0.875rem] leading-snug text-ink-soft"><Rich text={t.example} /></figcaption>
      </figure>
    </div>
  {/if}

  <ResultStrip {lang} {dict} />
</HomeSection>

<style>
  .progress {
    width: 100%;
  }
  .progress.running {
    animation: fill var(--ms) linear both;
  }
  @keyframes fill {
    from {
      width: 0;
    }
  }
</style>
