<script lang="ts">
  import type { Dictionary } from '$i18n';
  import type { Locale } from '$i18n/config';
  import { formatScoreLocale } from '$i18n/format';
  import type { PackageCopy } from '$i18n/package';
  import Chapter from '../Chapter.svelte';
  import FigureCaption from '../FigureCaption.svelte';
  import MarginNote from '../MarginNote.svelte';
  import Prose from '../Prose.svelte';
  import Rich from '../Rich.svelte';
  import { formatDecimal } from './format';
  import { MODEL_ROWS, type ModelRow } from './package-data';
  import ScrollRegion from './ScrollRegion.svelte';

  /**
   * The detector files: three in the wheel, the rest optional from Hugging Face. Scores are validation numbers
   * from the experiment log, never real-world accuracy. The table scrolls inside its own labelled region on a phone.
   */
  let { lang, dict, t }: { lang: Locale; dict: Dictionary; t: PackageCopy } = $props();

  const GROUPS = ['bundled', 'separate'] as const;

  const m = $derived(t.models);
  const rowsFor = (where: ModelRow['where']) => MODEL_ROWS.filter((row) => row.where === where);
</script>

{#snippet score(value: number | null)}
  {#if value === null}
    <span class="font-sans text-[0.8125rem] text-muted-foreground">{m.notRecorded}</span>
  {:else}
    {formatScoreLocale(lang, value, true)}
  {/if}
{/snippet}

<Chapter id="models" title={m.title}>
  <div class="flow-root max-w-[66ch]">
    <MarginNote class="mt-0">{m.splitNote}</MarginNote>
    <Prose>
      <p><Rich text={m.p1} {lang} /></p>
    </Prose>
  </div>

  <figure class="mt-8 min-w-0">
    <ScrollRegion label={m.tableLabel}>
      <table class="w-full min-w-[42rem] border-collapse text-left text-[0.9375rem]">
        <caption class="sr-only">{m.caption}</caption>
        <thead>
          <tr class="border-b border-rule-strong text-[0.8125rem] font-semibold text-ink">
            <th scope="col" class="py-2 pr-4 font-semibold">{m.columns.file}</th>
            <th scope="col" class="px-4 py-2 font-semibold">{m.columns.format}</th>
            <th scope="col" class="px-4 py-2 text-right font-semibold">{m.columns.size}</th>
            <th scope="col" class="px-4 py-2 text-right font-semibold">{m.columns.map50}</th>
            <th scope="col" class="py-2 pl-4 text-right font-semibold">{m.columns.map5095}</th>
          </tr>
        </thead>
        {#each GROUPS as group (group)}
          <tbody>
            <tr>
              <th scope="rowgroup" colspan="5" class="pt-7 pb-2 text-left font-serif text-title font-medium text-ink">
                {m.groups[group]}
              </th>
            </tr>
            {#each rowsFor(group) as row (row.file)}
              <tr class="border-t border-rule align-top">
                <th scope="row" class="py-3 pr-4 text-left font-normal">
                  <span class="block font-mono text-[0.8125rem] font-medium whitespace-nowrap text-ink">{row.file}</span>
                  {#if row.note}
                    <span class="mt-1 block max-w-[34ch] text-micro leading-snug text-muted-foreground">
                      {m.notes[row.note]}
                    </span>
                  {/if}
                </th>
                <td class="px-4 py-3 whitespace-nowrap text-ink-soft">{row.format}</td>
                <td class="tabular px-4 py-3 text-right font-mono text-[0.875rem] whitespace-nowrap">
                  {formatDecimal(lang, row.sizeMb, 2)} MB
                </td>
                <td class="tabular px-4 py-3 text-right font-mono text-[0.875rem] whitespace-nowrap">
                  {@render score(row.map50)}
                </td>
                <td class="tabular py-3 pl-4 text-right font-mono text-[0.875rem] whitespace-nowrap">
                  {@render score(row.map5095)}
                </td>
              </tr>
            {/each}
          </tbody>
        {/each}
      </table>
    </ScrollRegion>
    <FigureCaption n={1} label={dict.common.table}>{m.caption}</FigureCaption>
  </figure>
</Chapter>
