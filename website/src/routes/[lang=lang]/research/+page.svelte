<script lang="ts">
  import { getDictionary } from '$i18n';
  import { getResearchDictionary } from '$i18n/research';
  import { researchVars } from '$i18n/research/vars';
  import Seo from '$lib/components/Seo.svelte';
  import DataNote from '$lib/components/research/DataNote.svelte';
  import Edge from '$lib/components/research/Edge.svelte';
  import Head from '$lib/components/research/Head.svelte';
  import Limits from '$lib/components/research/Limits.svelte';
  import Photos from '$lib/components/research/Photos.svelte';
  import Question from '$lib/components/research/Question.svelte';
  import ResearchShell from '$lib/components/research/ResearchShell.svelte';
  import Results from '$lib/components/research/Results.svelte';
  import Runs from '$lib/components/research/Runs.svelte';
  import Tried from '$lib/components/research/Tried.svelte';

  let { data } = $props();

  const lang = $derived(data.lang);
  const dict = $derived(getDictionary(lang));
  const t = $derived(getResearchDictionary(lang));

  /**
   * Research: a short paper written by a student. Title and abstract, eight numbered sections with numbered
   * figures and tables. All copy is in src/i18n/research, all numbers come from src/lib/experiments.ts.
   */
  const section = $derived({
    lang,
    t,
    common: dict.common,
    figures: dict.figures,
    vars: researchVars(lang)
  });

  const SECTION_IDS = ['question', 'tried', 'results', 'runs', 'photos', 'edge', 'limits', 'data'] as const;
  const sections = $derived(SECTION_IDS.map((id) => ({ id, label: t.head.contents[id] })));
</script>

<Seo {lang} path="/research" title={t.meta.title} description={t.meta.description} />

<ResearchShell {lang} {sections} label={t.head.contentsLabel}>
  <Head {...section} />
  <Question {...section} />
  <Tried {...section} />
  <Results {...section} />
  <Runs {...section} />
  <Photos {...section} />
  <Edge {...section} />
  <Limits {...section} />
  <DataNote {...section} />
</ResearchShell>
