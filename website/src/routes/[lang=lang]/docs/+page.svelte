<script lang="ts">
  import { getDictionary } from '$i18n';
  import { localePath } from '$i18n/config';
  import CodeBlock from '$lib/components/docs/CodeBlock.svelte';
  import DocIcon from '$lib/components/docs/DocIcon.svelte';
  import Inline from '$lib/components/docs/Inline.svelte';
  import { codeLabelsFor, docIcon } from '$lib/components/docs/labels';
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
</script>

<Seo {lang} path="/docs" title={meta.title} description={meta.description} />

<div class="mx-auto w-full max-w-[76rem] px-5 pb-24 sm:px-8">
  <header class="mx-auto max-w-[62rem] pt-6 lg:pt-10">
    <Heading id="docs-title" as="h1" size="hero" class="text-ink">{ui.index.title}</Heading>
    <p class="mt-4 max-w-[52ch] text-[1.125rem] leading-[1.6] text-ink-soft"><Inline text={ui.index.lede} {lang} /></p>
    <div class="mt-7 flex flex-wrap items-center gap-3">
      <a href={localePath(lang, docPath('quickstart'))} class="btn btn-primary btn-lg">{ui.index.start}</a>
      <a href={localePath(lang, docPath('cli'))} class="btn btn-secondary btn-lg">{ui.index.cli}</a>
    </div>
    <div class="mt-6 max-w-[30rem]">
      <CodeBlock code={INSTALL_COMMAND} label={ui.index.installLabel} labels={codeLabels} />
    </div>
  </header>

  <section aria-label={ui.index.start} class="mx-auto mt-14 grid max-w-[62rem] gap-3 sm:grid-cols-2 xl:grid-cols-4">
    {#each ui.index.quick as card (card.slug)}
      <a
        href={localePath(lang, docPath(card.slug))}
        class="group rounded-2xl border border-rule bg-surface p-5 shadow-[var(--shadow-raised)] transition-colors duration-(--dur-fast) hover:border-accent"
      >
        <span class="mb-4 grid size-10 place-items-center rounded-lg bg-accent-soft text-accent-strong">
          <DocIcon name={docIcon(card.slug)} size={20} />
        </span>
        <span class="block text-[1.0625rem] font-semibold text-ink">{card.title}</span>
        <span class="mt-1 block text-[0.9375rem] leading-[1.5] text-ink-soft">{card.text}</span>
      </a>
    {/each}
  </section>

  <section aria-labelledby="browse-title" class="mx-auto mt-16 max-w-[62rem]">
    <Heading id="browse-title" as="h2" size="heading" class="text-ink">{ui.index.browse}</Heading>
    <div class="mt-5 grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
      {#each groups as entry (entry.group)}
        <section aria-labelledby="group-{entry.group}" class="rounded-2xl border border-rule bg-surface p-5 shadow-[var(--shadow-raised)]">
          <h3 id="group-{entry.group}" class="mb-3 text-[1.0625rem] font-semibold text-ink">{ui.groups[entry.group]}</h3>
          <ul class="space-y-0.5">
            {#each entry.pages as item (item.slug)}
              <li>
                <a
                  href={localePath(lang, docPath(item.slug))}
                  class="flex items-center gap-2.5 rounded-lg px-2 py-1.5 text-[0.9375rem] text-ink-soft transition-colors duration-(--dur-fast) hover:bg-hover/60 hover:text-ink"
                >
                  <DocIcon name={docIcon(item.slug)} size={17} />
                  {item.title}
                </a>
              </li>
            {/each}
          </ul>
        </section>
      {/each}
    </div>
  </section>

  <p class="mx-auto mt-12 max-w-[62rem] text-[0.875rem] leading-6 text-muted-foreground">
    {ui.index.issuesLead}
    <ExtLink href="{GITHUB_URL}/issues" hint={dict.common.opensInNewTab} class="text-ink">{ui.index.issuesLink}</ExtLink>{ui.index.issuesTail}
  </p>
</div>
