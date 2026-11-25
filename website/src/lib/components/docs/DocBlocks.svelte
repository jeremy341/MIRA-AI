<script lang="ts">
  import type { Locale } from '$i18n/config';
  import { getDictionary } from '$i18n';
  import type { DocsUi } from '$i18n/docs/ui';
  import { fmt } from '$i18n/format';
  import { stripInline, type DocSection } from '$lib/docs-content';
  import { CLASSES } from '$lib/site';
  import ClassChip from '../ClassChip.svelte';
  import Heading from '../Heading.svelte';
  import CodeBlock from './CodeBlock.svelte';
  import Inline from './Inline.svelte';
  import { codeLabelsFor } from './labels';

  /** One documentation section: a rule, the serif h2 with its anchor, then the blocks. */
  let { section, lang, ui }: { section: DocSection; lang: Locale; ui: DocsUi } = $props();

  const codeLabels = $derived(codeLabelsFor(lang, ui));
  const classNames = $derived(getDictionary(lang).common.classes);

  /** Anchors clear the sticky mobile bar (3.5rem). From lg there is no sticky bar. */
  const ANCHOR_OFFSET = 'scroll-mt-20 lg:scroll-mt-8';
  const BODY = 'max-w-[66ch] text-[1rem] leading-[1.7] text-ink-soft sm:text-[1.0625rem]';
</script>

{#snippet anchor(id: string, title: string)}
  <a
    href="#{id}"
    aria-label={fmt(ui.anchorLabel, { title })}
    class="ml-1 inline-flex size-9 items-center justify-center align-middle font-sans text-[1rem] font-normal text-muted-foreground opacity-0 transition-opacity duration-(--dur-fast) ease-out group-hover/heading:opacity-100 hover:bg-marker hover:text-ink focus-visible:opacity-100 [@media(hover:none)]:opacity-60"
  >
    <span aria-hidden="true">#</span>
  </a>
{/snippet}

<section
  aria-labelledby={section.id}
  class="mt-14 border-t border-rule pt-7 first:mt-0 first:border-t-0 first:pt-0"
>
  <div class="group/heading flex items-center">
    <Heading as="h2" size="title" id={section.id} class="text-ink {ANCHOR_OFFSET}">{section.title}</Heading>
    {@render anchor(section.id, section.title)}
  </div>

  {#each section.blocks as block}
    {#if block.type === 'p'}
      <p class="my-4 {BODY}"><Inline text={block.text} {lang} /></p>
    {:else if block.type === 'h3'}
      <div class="group/heading mt-10 mb-2 flex items-center">
        <h3
          id={block.id}
          class="font-serif text-[1.1875rem] leading-snug font-medium text-ink sm:text-[1.3125rem] {ANCHOR_OFFSET}"
        >
          {block.text}
        </h3>
        {@render anchor(block.id, block.text)}
      </div>
    {:else if block.type === 'code'}
      <CodeBlock code={block.code} label={block.label} output={block.output} labels={codeLabels} />
    {:else if block.type === 'list'}
      <svelte:element
        this={block.ordered ? 'ol' : 'ul'}
        class="my-4 space-y-2 pl-6 marker:text-muted-foreground {BODY} {block.ordered ? 'list-decimal marker:font-medium' : 'list-disc'}"
      >
        {#each block.items as item}
          <li class="pl-1"><Inline text={item} {lang} /></li>
        {/each}
      </svelte:element>
    {:else if block.type === 'callout'}
      <!-- A thin-rule note in the article column. The article column has no free margin (the contents list sits there), so it stays inline, like MarginNote `inline`, with a label and a serif title. -->
      <div role="note" class="my-7 max-w-[66ch] border-l-2 pl-4 {block.tone === 'warning' ? 'border-ink' : 'border-rule'}">
        <p class="text-[0.75rem] leading-5 font-semibold tracking-[0.08em] text-muted-foreground uppercase">
          {block.tone === 'warning' ? ui.warning : ui.note}
        </p>
        <p class="mt-0.5 font-serif text-[1.125rem] leading-snug font-medium text-ink">{block.title}</p>
        <p class="mt-1.5 text-[0.9375rem] leading-[1.65] text-ink-soft"><Inline text={block.text} {lang} /></p>
      </div>
    {:else if block.type === 'table'}
      <figure class="my-7 max-w-full min-w-0">
        <!-- The visible caption is hidden from assistive tech because the table's own (visually hidden) caption says the same. -->
        <figcaption aria-hidden="true" class="mb-2 text-[0.8125rem] leading-snug text-muted-foreground">
          {block.caption}
        </figcaption>
        <!-- A scrollable region must be reachable by keyboard so its overflow can be scrolled. -->
        <!-- svelte-ignore a11y_no_noninteractive_tabindex -->
        <div
          role="region"
          aria-label="{block.caption}. {ui.tableScrollLabel}"
          tabindex="0"
          class="overflow-x-auto border-t border-b border-rule border-t-ink"
        >
          <table class="w-full min-w-[32rem] border-collapse text-left text-[0.9375rem]">
            <caption class="sr-only">{block.caption}</caption>
            <thead>
              <tr class="border-b border-rule">
                {#each block.head as cell}
                  <th scope="col" class="px-3 py-2.5 text-[0.8125rem] font-semibold whitespace-nowrap text-ink first:pl-0 last:pr-0">
                    {cell}
                  </th>
                {/each}
              </tr>
            </thead>
            <tbody>
              {#each block.rows as row}
                <tr class="border-t border-rule/70 align-top first:border-t-0">
                  {#each row as cell, columnIndex}
                    {#if columnIndex === 0}
                      <!-- A single identifier such as conf_threshold never breaks in the middle. -->
                      <th
                        scope="row"
                        class="py-3 pr-3 pl-0 text-left leading-6 font-normal text-ink {/\s/.test(stripInline(cell))
                          ? ''
                          : 'whitespace-nowrap [&_code]:[overflow-wrap:normal]'}"
                      >
                        <Inline text={cell} {lang} />
                      </th>
                    {:else}
                      <td class="px-3 py-3 leading-6 text-ink-soft last:pr-0"><Inline text={cell} {lang} /></td>
                    {/if}
                  {/each}
                </tr>
              {/each}
            </tbody>
          </table>
        </div>
      </figure>
    {:else if block.type === 'endpoints'}
      <ul aria-label={ui.endpointsLabel} class="my-7 border-t border-ink">
        {#each block.items as item (`${item.method}-${item.path}`)}
          <li
            class="grid grid-cols-[3.25rem_minmax(0,1fr)] gap-x-3 gap-y-0.5 border-b border-rule py-3 sm:grid-cols-[3.25rem_minmax(0,17rem)_minmax(0,1fr)]"
          >
            <span class="font-mono text-[0.8125rem] leading-6 font-semibold text-ink">{item.method}</span>
            <code class="min-w-0 font-mono text-[0.875rem] leading-6 text-ink [overflow-wrap:anywhere]">{item.path}</code>
            <span class="col-start-2 text-[0.9375rem] leading-6 text-ink-soft sm:col-start-3">{item.text}</span>
          </li>
        {/each}
      </ul>
    {:else if block.type === 'flow'}
      <ol aria-label={block.label} class="my-8 grid gap-x-6 gap-y-5 sm:grid-cols-2 lg:grid-cols-4">
        {#each block.steps as step, stepIndex (step.title)}
          <li class="min-w-0 border-t-2 border-ink pt-2.5">
            <p class="tabular text-[0.8125rem] text-muted-foreground">
              {String(stepIndex + 1).padStart(2, '0')}{#if stepIndex < block.steps.length - 1}<span aria-hidden="true" class="ml-2">&rarr;</span>{/if}
            </p>
            <p class="mt-1 font-serif text-[1.125rem] leading-snug font-medium text-ink">{step.title}</p>
            <p class="mt-1 text-[0.875rem] leading-[1.55] text-ink-soft">{step.detail}</p>
          </li>
        {/each}
      </ol>
    {:else if block.type === 'classes'}
      <ul aria-label={ui.classesLabel} class="my-5 flex flex-wrap gap-x-7 gap-y-2.5">
        {#each CLASSES as cls (cls.id)}
          <li class="flex items-baseline gap-2">
            <span class="tabular text-[0.8125rem] text-muted-foreground">{cls.index}</span>
            <ClassChip cls={cls.id} label={classNames[cls.id]} />
            {#if classNames[cls.id] !== cls.id}
              <code class="font-mono text-[0.8125rem] text-muted-foreground">{cls.id}</code>
            {/if}
          </li>
        {/each}
      </ul>
    {/if}
  {/each}
</section>
