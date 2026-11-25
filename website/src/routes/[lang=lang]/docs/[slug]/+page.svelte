<script lang="ts">
  import { localePath } from '$i18n/config';
  import DocBlocks from '$lib/components/docs/DocBlocks.svelte';
  import DocsToc from '$lib/components/docs/DocsToc.svelte';
  import Inline from '$lib/components/docs/Inline.svelte';
  import { tocItemsFor } from '$lib/components/docs/labels';
  import PageActions from '$lib/components/docs/PageActions.svelte';
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

<div class="mx-auto grid w-full max-w-[76rem] grid-cols-[minmax(0,1fr)] justify-center gap-x-14 px-5 pb-24 sm:px-8 xl:grid-cols-[minmax(0,44rem)_14rem]">
  <article aria-labelledby="doc-title" class="min-w-0 pt-4 lg:pt-6">
    <nav aria-label={ui.breadcrumbLabel} class="text-[0.875rem] text-ink-soft">
      <ol class="flex flex-wrap items-center gap-x-2">
        <li><a href={localePath(lang, '/docs')} class="hover:text-ink">{ui.breadcrumbHome}</a></li>
        <li aria-hidden="true">/</li>
        <li>{ui.groups[doc.group]}</li>
        <li aria-hidden="true">/</li>
        <li aria-current="page" class="font-medium text-ink">{doc.title}</li>
      </ol>
    </nav>
    <Heading id="doc-title" as="h1" size="hero" class="mt-4 text-ink">{doc.title}</Heading>
    <PageActions {doc} {ui} {lang} />
    {#if doc.lead}
      <p class="mt-6 text-[1.0625rem] leading-[1.65] text-ink-soft"><Inline text={doc.lead} {lang} /></p>
    {/if}
    <div class="mt-10">
      {#each doc.sections as section (section.id)}
        <DocBlocks {section} {lang} {ui} />
      {/each}
    </div>
    <PageNav {lang} {ui} prev={data.prev} next={data.next} />
  </article>
  <DocsToc items={tocItems} label={ui.onThisPage} />
</div>
