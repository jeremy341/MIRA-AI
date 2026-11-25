<script lang="ts">
  import { getDictionary } from '$i18n';
  import { localePath } from '$i18n/config';
  import CodeBlock from '$lib/components/docs/CodeBlock.svelte';
  import Inline from '$lib/components/docs/Inline.svelte';
  import { codeLabelsFor } from '$lib/components/docs/labels';
  import ExtLink from '$lib/components/ExtLink.svelte';
  import Heading from '$lib/components/Heading.svelte';
  import Seo from '$lib/components/Seo.svelte';
  import { docPath } from '$lib/docs-content';
  import { GITHUB_URL, INSTALL_COMMAND } from '$lib/site';

  let { data } = $props();

  const lang = $derived(data.lang);
  const ui = $derived(data.ui);
  const dict = $derived(getDictionary(lang));
  const meta = $derived(dict.meta.pages.docs);
  const groups = $derived(data.groups);
  const codeLabels = $derived(codeLabelsFor(lang, ui));

  /** Running page number across groups, so the index reads 01 to 12. */
  const offsets = $derived(
    groups.map((_, position) => groups.slice(0, position).reduce((sum, entry) => sum + entry.pages.length, 0))
  );
</script>

<Seo {lang} path="/docs" title={meta.title} description={meta.description} />

<article aria-labelledby="docs-title" class="min-w-0 pt-10 pb-20 lg:col-start-2 lg:row-start-1 lg:pt-12 xl:col-span-2">
  <Heading id="docs-title" as="h1" size="display" class="text-ink">{ui.index.title}</Heading>
  <p class="mt-5 max-w-[56ch] font-serif text-lede text-ink-soft"><Inline text={ui.index.lede} {lang} /></p>

  <div class="mt-8 max-w-[34rem]">
    <CodeBlock code={INSTALL_COMMAND} label={ui.index.installLabel} labels={codeLabels} />
    <div class="mt-6 flex flex-wrap items-center gap-x-6 gap-y-3">
      <a href={localePath(lang, docPath('quickstart'))} class="btn btn-primary btn-lg">{ui.index.start}</a>
      <a href={localePath(lang, docPath('cli'))} class="btn btn-secondary btn-lg px-1">{ui.index.cli}</a>
    </div>
    <p class="mt-5 text-[0.875rem] text-muted-foreground [@media(hover:none)]:hidden">
      {ui.index.pressKey}
      <kbd class="border border-rule px-1.5 py-0.5 font-mono text-[0.75rem] text-ink">Alt</kbd> +
      <kbd class="border border-rule px-1.5 py-0.5 font-mono text-[0.75rem] text-ink">/</kbd>
      {ui.index.toSearch}
    </p>
  </div>

  <div class="mt-16 border-t border-ink">
    {#each groups as entry, groupIndex (entry.group)}
      <section
        aria-labelledby="group-{entry.group}"
        class="grid gap-x-10 border-b border-rule py-8 md:grid-cols-[11rem_minmax(0,1fr)]"
      >
        <Heading id="group-{entry.group}" as="h2" size="title" class="text-ink">{ui.groups[entry.group]}</Heading>
        <ol class="mt-4 md:mt-0">
          {#each entry.pages as item, pageIndex (item.slug)}
            <li class="grid grid-cols-[2rem_minmax(0,1fr)] {pageIndex > 0 ? 'border-t border-rule/70' : ''}">
              <span aria-hidden="true" class="tabular pt-[1.0625rem] text-[0.8125rem] text-muted-foreground">
                {String(offsets[groupIndex] + pageIndex + 1).padStart(2, '0')}
              </span>
              <a href={localePath(lang, docPath(item.slug))} class="group block py-3.5">
                <span
                  class="font-serif text-[1.1875rem] leading-snug font-medium text-ink group-hover:bg-marker group-focus-visible:bg-marker"
                >
                  {item.title}
                </span>
                <span class="mt-1 block max-w-[52ch] text-[0.9375rem] leading-[1.55] text-ink-soft">{item.summary}</span>
              </a>
            </li>
          {/each}
        </ol>
      </section>
    {/each}
  </div>

  <p class="mt-10 max-w-[62ch] text-[0.875rem] leading-6 text-muted-foreground">
    {ui.index.issuesLead}
    <ExtLink href="{GITHUB_URL}/issues" hint={dict.common.opensInNewTab} class="text-ink">{ui.index.issuesLink}</ExtLink>{ui.index.issuesTail}
  </p>
</article>
