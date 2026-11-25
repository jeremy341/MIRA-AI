<script lang="ts">
  import { getDictionary } from '$i18n';
  import { getResearchDictionary } from '$i18n/research';
  import { researchVars } from '$i18n/research/vars';
  import Seo from '$lib/components/Seo.svelte';
  import ResearchOverview from '$lib/components/research/ResearchOverview.svelte';

  let { data } = $props();

  const lang = $derived(data.lang);
  const dict = $derived(getDictionary(lang));
  const t = $derived(getResearchDictionary(lang));
  const section = $derived({
    lang,
    t,
    common: dict.common,
    figures: dict.figures,
    vars: researchVars(lang)
  });
</script>

<Seo {lang} path="/research" title={t.meta.title} description={t.meta.description} />

<div class="mx-auto w-full max-w-[58rem] px-5 pb-24 sm:px-8">
  <ResearchOverview {...section} />
</div>
