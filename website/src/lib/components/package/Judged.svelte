<script lang="ts">
  import type { Dictionary } from '$i18n';
  import type { Locale } from '$i18n/config';
  import type { PackageCopy } from '$i18n/package';
  import Chapter from '../Chapter.svelte';
  import CopyCommand from '../CopyCommand.svelte';
  import Figure from '../Figure.svelte';
  import Prose from '../Prose.svelte';
  import Rich from '../Rich.svelte';
  import { formatDecimal } from './format';
  import { THRESHOLD_CONF, THRESHOLD_EXAMPLE_COMMAND, THRESHOLD_REJECT } from './package-data';

  /**
   * How `mira live` turns a confidence into what you see. Figure 1 is a bar from 0 to 1 cut by the two
   * thresholds; the list under it carries the same information as text, so the bar itself is decorative.
   */
  let { lang, dict, t }: { lang: Locale; dict: Dictionary; t: PackageCopy } = $props();

  const j = $derived(t.judged);
  const pct = (n: number) => `${(n * 100).toFixed(0)}%`;
  const num = (n: number) => formatDecimal(lang, n, 2);

  /** The three outcomes, in the order of the bar: how each one is drawn. */
  const SEGMENT = [
    'border border-ink bg-transparent',
    'border border-ink bg-rule',
    'border border-ink bg-ink'
  ] as const;
</script>

<Chapter id="judged" title={j.title}>
  <Prose>
    <p><Rich text={j.p1} {lang} /></p>
    <p><Rich text={j.p2} {lang} /></p>
  </Prose>
  <CopyCommand
    command={THRESHOLD_EXAMPLE_COMMAND}
    label={j.exampleCopyLabel}
    labels={dict.common.copy}
    class="mt-4 max-w-[46rem]"
  />

  <Figure id="fig-thresholds" n={1} label={dict.common.figure} class="mt-10 max-w-[46rem]">
    {#snippet caption()}<Rich text={j.figureCaption} {lang} />{/snippet}

    <div aria-hidden="true" class="select-none">
      <div class="relative h-6 font-mono text-micro text-muted-foreground">
        <span class="absolute left-0">0</span>
        <span class="absolute -translate-x-1/2" style:left={pct(THRESHOLD_CONF)}>{num(THRESHOLD_CONF)}</span>
        <span class="absolute -translate-x-1/2" style:left={pct(THRESHOLD_REJECT)}>{num(THRESHOLD_REJECT)}</span>
        <span class="absolute right-0">1</span>
      </div>
      <div class="flex h-12 font-mono text-micro">
        <div
          class="flex items-center justify-center text-muted-foreground {SEGMENT[0]}"
          style:width={pct(THRESHOLD_CONF)}
        >
          {j.scaleLabels.hidden}
        </div>
        <div
          class="-ml-px flex items-center justify-center text-ink {SEGMENT[1]}"
          style:width={pct(THRESHOLD_REJECT - THRESHOLD_CONF)}
        >
          {j.scaleLabels.uncertain}
        </div>
        <div class="-ml-px flex flex-1 items-center justify-center text-surface {SEGMENT[2]}">
          {j.scaleLabels.labelled}
        </div>
      </div>
    </div>

    <ol class="mt-6 border-t border-rule">
      {#each j.tiers as tier, index (tier.name)}
        <li
          class="grid grid-cols-[1rem_minmax(0,1fr)] gap-x-3 gap-y-0.5 border-b border-rule py-3 sm:grid-cols-[1rem_15rem_minmax(0,1fr)] sm:gap-x-4"
        >
          <span aria-hidden="true" class="mt-1.5 size-3 {SEGMENT[index]}"></span>
          <span class="text-[0.9375rem] leading-snug font-medium text-ink"><Rich text={tier.name} {lang} /></span>
          <span class="col-start-2 text-[0.9375rem] leading-snug text-ink-soft sm:col-start-3">{tier.text}</span>
        </li>
      {/each}
    </ol>
  </Figure>
</Chapter>
