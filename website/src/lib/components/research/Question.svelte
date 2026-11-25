<script lang="ts">
  import { CLASSES } from '$lib/site';
  import ClassChip from '../ClassChip.svelte';
  import MarginNote from '../MarginNote.svelte';
  import Prose from '../Prose.svelte';
  import Rich from '../Rich.svelte';
  import { fill, type SectionProps } from './context';
  import NumChapter from './NumChapter.svelte';

  /** 1. Question and setup. */
  let { lang, t, common, vars }: SectionProps = $props();

  const q = $derived(t.question);
</script>

<NumChapter id="question" n={1} title={q.title}>
  <Prose>
    <p><Rich text={fill(vars, q.p1)} {lang} /></p>
    <p aria-label={q.classesLabel} class="flex flex-wrap items-center gap-x-6 gap-y-2 text-[0.9375rem] text-ink">
      <span class="text-[0.8125rem] font-semibold">{q.classesLabel}</span>
      {#each CLASSES as c (c.id)}
        <ClassChip cls={c.id} label={common.classes[c.id]} />
      {/each}
    </p>
    <p><Rich text={fill(vars, q.p2)} {lang} /></p>
    <MarginNote><Rich text={fill(vars, q.note)} {lang} /></MarginNote>
    <p><Rich text={fill(vars, q.p3)} {lang} /></p>
  </Prose>
</NumChapter>
