<script lang="ts">
  import DocBlocks from '$lib/components/docs/DocBlocks.svelte';
  import DocsToc from '$lib/components/docs/DocsToc.svelte';
  import Inline from '$lib/components/docs/Inline.svelte';
  import { tocItemsFor } from '$lib/components/docs/labels';
  import PageNav from '$lib/components/docs/PageNav.svelte';
  import Heading from '$lib/components/Heading.svelte';
  import Seo from '$lib/components/Seo.svelte';
  import { docPath } from '$lib/docs-content';

  let { data } = $props();

  const lang = $derived(data.lang);
  const ui = $derived(data.ui);
  const doc = $derived(data.doc);
  const tocItems = $derived(tocItemsFor(doc));
</script>

<Seo {lang} path={docPath(doc.slug)} title="{doc.title} | {ui.metaSuffix}" description={doc.summary} />

<article aria-labelledby="doc-title" class="min-w-0 pt-10 pb-20 lg:col-start-2 lg:row-start-1 lg:pt-12">
  <p class="text-[0.75rem] leading-5 font-semibold tracking-[0.08em] text-muted-foreground uppercase">
    {ui.groups[doc.group]}
  </p>
  <Heading id="doc-title" as="h1" size="display" class="mt-2 text-ink">{doc.title}</Heading>
  {#if doc.lead}
    <p class="mt-5 max-w-[60ch] font-serif text-lede text-ink-soft"><Inline text={doc.lead} {lang} /></p>
  {/if}
  <div class="mt-10 sm:mt-12">
    {#each doc.sections as section (section.id)}
      <DocBlocks {section} {lang} {ui} />
    {/each}
  </div>
  <PageNav {lang} {ui} prev={data.prev} next={data.next} />
</article>
<DocsToc items={tocItems} label={ui.onThisPage} />
