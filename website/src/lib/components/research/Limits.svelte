<script lang="ts">
  import { formatInt } from '$i18n/format';
  import { PLANNED_EXPERIMENT as P } from '$lib/experiments';
  import { GITHUB_URL } from '$lib/site';
  import ExtLink from '../ExtLink.svelte';
  import Heading from '../Heading.svelte';
  import Prose from '../Prose.svelte';
  import Rich from '../Rich.svelte';
  import { fill, type SectionProps } from './context';
  import NumChapter from './NumChapter.svelte';
  import ScrollRegion from './ScrollRegion.svelte';
  import TableFigure from './TableFigure.svelte';
  import { TABLE, TBODY, TD, TD_LAST } from './table-styles';

  /** 7. Limits and next steps, the inconsistencies I found in my own log, and EXP-020 (planned, not run). */
  let { lang, t, common, vars }: SectionProps = $props();

  const s = $derived(t.limits);
  const configUrl = `${GITHUB_URL}/blob/main/${P.configFile}`;
  const ROW_KEYS = ['model', 'mix', 'images', 'settings', 'validation', 'camera', 'result', 'config'] as const;
</script>

{#snippet numbered(items: readonly string[])}
  <ol class="max-w-[66ch] space-y-3.5 text-[1.0625rem] leading-[1.6] text-ink-soft sm:text-[1.125rem]">
    {#each items as item, i (i)}
      <li class="grid grid-cols-[1.75rem_minmax(0,1fr)] gap-x-1">
        <span class="pt-[0.2em] font-mono text-[0.8125rem] text-muted-foreground">{i + 1}</span>
        <span><Rich text={fill(vars, item)} {lang} /></span>
      </li>
    {/each}
  </ol>
{/snippet}

<NumChapter id="limits" n={7} title={s.title}>
  <Heading as="h3" size="title" class="text-ink">{s.limitsTitle}</Heading>
  <div class="mt-4">{@render numbered(s.limits)}</div>

  <Heading as="h3" size="title" class="mt-12 text-ink">{s.logTitle}</Heading>
  <p class="mt-2 max-w-[66ch] text-[0.9375rem] text-muted-foreground"><Rich text={fill(vars, s.logIntro)} {lang} /></p>
  <div class="mt-4">
    <ul
      class="max-w-[66ch] list-outside list-disc space-y-2.5 pl-5 text-[1rem] leading-[1.6] text-ink-soft marker:text-muted-foreground sm:text-[1.0625rem]"
    >
      {#each s.log as item, i (i)}
        <li><Rich text={fill(vars, item)} {lang} /></li>
      {/each}
    </ul>
  </div>

  <Heading as="h3" size="title" class="mt-12 text-ink">{s.nextTitle}</Heading>
  <div class="mt-4">{@render numbered(s.next)}</div>

  <Heading as="h3" size="title" class="mt-12 text-ink">{s.plannedTitle}</Heading>
  <Prose class="mt-3">
    <p><Rich text={fill(vars, s.plannedIntro)} {lang} /></p>
  </Prose>
  <TableFigure id="table-6" n={6} label={common.table} caption={s.plannedCaption} class="mt-6 max-w-[44rem]">
    <ScrollRegion label={s.plannedLabel}>
      <table class="{TABLE} min-w-[26rem]">
        <caption class="sr-only">{s.plannedCaption}</caption>
        <thead class="sr-only">
          <tr>
            <th scope="col">{s.plannedRows.model}</th>
            <th scope="col">{s.plannedRows.result}</th>
          </tr>
        </thead>
        <tbody class="{TBODY} border-t-2 border-rule-strong">
          {#each ROW_KEYS as key (key)}
            <tr>
              <th scope="row" class="{TD} w-[10rem] font-normal text-muted-foreground">{s.plannedRows[key]}</th>
              <td class="{TD_LAST} text-ink">
                {#if key === 'model'}
                  {P.model}
                {:else if key === 'mix'}
                  {s.plannedMix}
                {:else if key === 'images'}
                  <span class="font-mono tabular">{formatInt(lang, P.trainImages)}</span>
                {:else if key === 'settings'}
                  <span class="font-mono text-[0.8125rem]">{fill(vars, s.plannedSettings)}</span>
                {:else if key === 'validation'}
                  {s.plannedValidation}
                {:else if key === 'camera'}
                  {s.plannedCamera}
                {:else if key === 'result'}
                  <strong class="font-semibold text-ink">{s.plannedResult}</strong>
                {:else}
                  <ExtLink href={configUrl} hint={common.opensInNewTab} class="break-all">
                    <code class="text-[0.8125rem]">{P.configFile}</code>
                  </ExtLink>
                {/if}
              </td>
            </tr>
          {/each}
        </tbody>
      </table>
    </ScrollRegion>
  </TableFigure>
</NumChapter>
