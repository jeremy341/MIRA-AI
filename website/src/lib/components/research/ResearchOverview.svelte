<script lang="ts">
  import { localePath } from '$i18n/config';
  import { formatScoreLocale } from '$i18n/format';
  import { getExperiment } from '$lib/experiments';
  import { RESEARCH_SECTION_IDS, researchPath } from '$lib/research-sections';
  import DocIcon from '../docs/DocIcon.svelte';
  import { docIcon } from '../docs/labels';
  import Figure from '../Figure.svelte';
  import Heading from '../Heading.svelte';
  import PagePanel from '../PagePanel.svelte';
  import Rich from '../Rich.svelte';
  import Stat from '../Stat.svelte';
  import BarRows, { type BarRowData } from './BarRows.svelte';
  import { fill, type SectionProps } from './context';

  /**
   * The front page of the report: title, the result in one figure, the abstract, and a card for every section.
   * The numbers are the ones the results section uses (src/lib/experiments.ts), never retyped.
   */
  let { lang, t, common, vars }: SectionProps = $props();

  const head = $derived(t.head);
  const o = $derived(t.overview);
  const r = $derived(t.results);
  const pct = (v: number) => formatScoreLocale(lang, v, true);

  function scoreOf(id: string): number {
    const run = getExperiment(id);
    if (!run.result) throw new Error(`No score for ${id}`);
    return run.result.value;
  }

  const headline = $derived<BarRowData[]>(
    r.chartRows.map((row) => ({
      key: row.id,
      label: row.id,
      sub: row.note,
      value: scoreOf(row.id),
      display: pct(scoreOf(row.id)),
      // The baseline was scored on another split, so its bar is only outlined.
      tone: row.id === 'EXP-014' ? 'outline' : 'ink'
    }))
  );
</script>

<div class="pt-2 lg:pt-4">
  <PagePanel titleId="research-title" title={head.title} eyebrow={head.eyebrow}>
    <p class="mt-4 max-w-[44ch] text-[1.1875rem] leading-[1.55] text-on-brand-soft">{head.subtitle}</p>
    <p class="mt-3 max-w-[56ch] text-[0.875rem] leading-snug text-on-brand-soft">{head.byline}</p>
    <a href="#report" class="btn btn-light btn-lg mt-6">{o.cardsTitle}</a>
  </PagePanel>
</div>

<section aria-labelledby="result-title" class="card mt-8 p-5 sm:p-8">
  <h2 id="result-title" class="text-[0.8125rem] font-semibold tracking-[0.08em] text-brand-ink uppercase">{o.resultTitle}</h2>
  <div class="mt-5 grid gap-8 lg:grid-cols-[minmax(0,7fr)_minmax(0,4fr)] lg:gap-12">
    <Figure id="fig-1" n={1} label={common.figure}>
      {#snippet caption()}<Rich text={fill(vars, r.chartCaption)} {lang} />{/snippet}
      <BarRows rows={headline} ariaLabel={fill(vars, r.chartAria)} />
    </Figure>
    <div class="lg:pt-2">
      <Stat>
        {#snippet value()}<Rich text={fill(vars, r.statValue)} {lang} />{/snippet}
        {#snippet label()}<Rich text={fill(vars, r.statLabel)} {lang} />{/snippet}
      </Stat>
      <p class="mt-4 max-w-[34ch] text-[0.875rem] leading-snug text-ink-faint">{o.resultNote}</p>
    </div>
  </div>
</section>

<section aria-labelledby="abstract-title" class="mt-4 rounded-2xl bg-tint p-5 sm:p-8">
  <h2 id="abstract-title" class="text-[0.8125rem] font-semibold tracking-[0.08em] text-brand-ink uppercase">
    {head.abstractLabel}
  </h2>
  <p class="mt-3 text-[1.0625rem] leading-[1.7] text-ink-soft">
    <Rich text={fill(vars, head.abstract)} {lang} />
  </p>
</section>

<section id="report" aria-labelledby="cards-title" class="mt-14 scroll-mt-20">
  <Heading id="cards-title" as="h2" size="heading" class="text-ink">{o.cardsTitle}</Heading>
  <ol class="mt-5 grid gap-4 sm:grid-cols-2">
    {#each RESEARCH_SECTION_IDS as id, index (id)}
      <li>
        <a
          href={localePath(lang, researchPath(id))}
          class="group flex h-full gap-4 rounded-2xl bg-tint p-5 transition-colors duration-(--dur-fast) hover:bg-tint-strong"
        >
          <span class="grid size-10 shrink-0 place-items-center rounded-lg bg-brand text-white">
            <DocIcon name={docIcon(id)} size={20} />
          </span>
          <span class="min-w-0">
            <span class="block text-[0.75rem] text-muted-foreground tabular">{index + 1}</span>
            <span class="block text-[1.0625rem] font-semibold text-ink group-hover:text-accent-strong">{head.contents[id]}</span>
            <span class="mt-1 block text-[0.9375rem] leading-[1.5] text-ink-soft">{o.cards[id]}</span>
          </span>
        </a>
      </li>
    {/each}
  </ol>
</section>
