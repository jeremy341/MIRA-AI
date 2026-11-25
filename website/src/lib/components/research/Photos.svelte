<script lang="ts" module>
  /** The two photos of this section: a missed plastic bottle and a cardboard box that is called paper. */
  export const MISSED_FILE = 'detect-07.jpg';
  export const OUT_OF_SCOPE_FILE = 'detect-08.jpg';
</script>

<script lang="ts">
  import { fmt, formatConfidence } from '$i18n/format';
  import type { DetectionFigureLabels } from '$lib/detection-labels';
  import { loadFigures, topDetection, type FigureEntry } from '$lib/figures';
  import DetectionFigure from '../DetectionFigure.svelte';
  import MarginNote from '../MarginNote.svelte';
  import Prose from '../Prose.svelte';
  import Rich from '../Rich.svelte';
  import { fill, type SectionProps } from './context';
  import NumChapter from './NumChapter.svelte';

  /** 5. Real photos and failures (Figures 4 and 5), drawn from static/figures/detections.json. */
  let { lang, t, common, figures, vars }: SectionProps = $props();

  const s = $derived(t.photos);
  const entries = loadFigures();
  const find = (file: string): FigureEntry | null => entries.find((e) => e.file === file) ?? null;
  const missed = find(MISSED_FILE);
  const outOfScope = find(OUT_OF_SCOPE_FILE);

  const labels = $derived<DetectionFigureLabels>({
    figure: common.figure,
    boxesToggle: figures.boxesToggle,
    boxesOn: figures.boxesOn,
    boxesOff: figures.boxesOff,
    altPrefix: figures.altPrefix,
    altNone: figures.altNone,
    altListIntro: figures.altListIntro,
    altItem: figures.altItem,
    placeholderTitle: figures.placeholderTitle,
    placeholderHint: figures.placeholderHint,
    classes: common.classes
  });

  const missedCaption = $derived.by(() => {
    if (!missed) return s.unavailable;
    const top = topDetection(missed);
    return top
      ? fmt(s.wrong, {
          trueClass: common.classes[missed.trueClass === 'cardboard' ? 'paper' : missed.trueClass],
          predicted: common.classes[top.cls],
          conf: formatConfidence(lang, top.confidence)
        })
      : fmt(s.missed, { conf: formatConfidence(lang, missed.conf) });
  });

  const outCaption = $derived.by(() => {
    const top = outOfScope ? topDetection(outOfScope) : null;
    return outOfScope && top
      ? fmt(s.outOfScope, { predicted: common.classes[top.cls], conf: formatConfidence(lang, top.confidence) })
      : s.unavailable;
  });
</script>

<NumChapter id="photos" n={5} title={s.title}>
  <Prose>
    <p><Rich text={fill(vars, s.p1)} {lang} /></p>
    <MarginNote><Rich text={fill(vars, s.note)} {lang} /></MarginNote>
    <p><Rich text={fill(vars, s.p2)} {lang} /></p>
  </Prose>

  <div class="mt-10 grid gap-x-10 gap-y-10 sm:grid-cols-2 lg:max-w-[48rem]">
    <DetectionFigure
      {lang}
      entry={missed}
      expectedFile={MISSED_FILE}
      n={4}
      id="fig-4"
      caption={missedCaption}
      {labels}
      maxHeight="22rem"
    />
    <DetectionFigure
      {lang}
      entry={outOfScope}
      expectedFile={OUT_OF_SCOPE_FILE}
      n={5}
      id="fig-5"
      caption={outCaption}
      {labels}
      maxHeight="22rem"
    />
  </div>
</NumChapter>
