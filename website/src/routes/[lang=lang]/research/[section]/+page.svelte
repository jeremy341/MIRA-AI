<script lang="ts">
  import { setContext } from 'svelte';
  import { getDictionary } from '$i18n';
  import { localePath } from '$i18n/config';
  import { DOCS_UI } from '$i18n/docs/ui';
  import { getResearchDictionary } from '$i18n/research';
  import { researchVars } from '$i18n/research/vars';
  import PageNav from '$lib/components/docs/PageNav.svelte';
  import DataNote from '$lib/components/research/DataNote.svelte';
  import Edge from '$lib/components/research/Edge.svelte';
  import Limits from '$lib/components/research/Limits.svelte';
  import Photos from '$lib/components/research/Photos.svelte';
  import Question from '$lib/components/research/Question.svelte';
  import Results from '$lib/components/research/Results.svelte';
  import Runs from '$lib/components/research/Runs.svelte';
  import Tried from '$lib/components/research/Tried.svelte';
  import Seo from '$lib/components/Seo.svelte';
  import { researchPath } from '$lib/research-sections';
  import type { PageData } from './$types';

  let { data }: { data: PageData } = $props();

  // Each section component renders its chapter as the page (an h1, no rule above it).
  setContext('research-standalone', true);

  const COMPONENTS = {
    question: Question,
    tried: Tried,
    results: Results,
    runs: Runs,
    photos: Photos,
    edge: Edge,
    limits: Limits,
    data: DataNote
  } as const;

  const lang = $derived(data.lang);
  const ui = $derived(DOCS_UI[lang]);
  const dict = $derived(getDictionary(lang));
  const t = $derived(getResearchDictionary(lang));
  const sectionProps = $derived({
    lang,
    t,
    common: dict.common,
    figures: dict.figures,
    vars: researchVars(lang)
  });
  const Section = $derived(COMPONENTS[data.section]);
  const label = $derived(t.head.contents[data.section]);
  const title = (id: keyof typeof t.head.contents | null) => (id ? { slug: id, title: t.head.contents[id] } : undefined);
</script>

<Seo
  {lang}
  path={researchPath(data.section)}
  title="{label} | {t.meta.title}"
  description={t.overview.cards[data.section]}
/>

<div class="research-page mx-auto w-full max-w-[52rem] px-5 pb-24 sm:px-8">
  <nav aria-label={ui.breadcrumbLabel} class="pt-4 text-[0.875rem] text-ink-soft lg:pt-6">
    <ol class="flex flex-wrap items-center gap-x-2">
      <li><a href={localePath(lang, '/research')} class="hover:text-ink">{dict.nav.research}</a></li>
      <li aria-hidden="true">/</li>
      <li aria-current="page" class="font-medium text-ink">{label}</li>
    </ol>
  </nav>

  <div class="mt-4">
    <Section {...sectionProps} />
  </div>

  <PageNav {lang} {ui} base="/research" prev={title(data.prev)} next={title(data.next)} />
</div>

<style>
  /* The side notes sit in the margin in the old layout. Here the page is one centred column, so they stay in the flow. */
  .research-page :global([role='note']) {
    float: none !important;
    clear: none !important;
    width: auto !important;
    margin: 1.25rem 0 !important;
    border-top: 0 !important;
    border-left: 2px solid var(--ink) !important;
    padding: 0 0 0 0.75rem !important;
  }
</style>
