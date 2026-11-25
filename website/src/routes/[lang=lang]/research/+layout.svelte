<script lang="ts">
  import { getDictionary } from '$i18n';
  import { DOCS_UI } from '$i18n/docs/ui';
  import { getResearchDictionary } from '$i18n/research';
  import DocsShell from '$lib/components/docs/DocsShell.svelte';
  import { RESEARCH_SECTION_IDS } from '$lib/research-sections';

  /** The research report uses the same chrome as the documentation: sidebar with one entry per section, top bar. */
  let { data, children } = $props();

  const lang = $derived(data.lang);
  const dict = $derived(getDictionary(lang));
  const t = $derived(getResearchDictionary(lang));
  const nav = $derived([
    {
      id: 'report',
      label: t.head.contentsLabel,
      pages: RESEARCH_SECTION_IDS.map((id) => ({ slug: id, title: t.head.contents[id] }))
    }
  ]);
</script>

<DocsShell {lang} ui={DOCS_UI[lang]} {nav} base="/research" badge={dict.nav.research} search={false} {children} />
