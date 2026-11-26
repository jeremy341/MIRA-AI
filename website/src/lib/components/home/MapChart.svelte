<script lang="ts" module>
  export type MapChartRow = {
    id: string;
    note: string;
    /** Percent, 0 to 100. */
    value: number;
    /** An outlined bar marks the earlier baseline that was scored on a different split. */
    outlined?: boolean;
  };
</script>

<script lang="ts">
  import type { Locale } from '$i18n/config';
  import { formatScoreLocale } from '$i18n/format';

  const TICKS = [0, 25, 50, 75, 100];

  /**
   * One series, three bars: mAP50 per run. HTML and CSS only, no chart library: bars are 22px thick with square
   * ends, values sit inside the bar end in mono, the axis has hairline gridlines at 0, 25, 50, 75 and 100.
   * The numbers are visible text, so the chart is never the only source. Single series, so no legend and ink
   * only (class colours are reserved for charts split by class).
   */
  let { rows, lang, ariaLabel }: { rows: readonly MapChartRow[]; lang: Locale; ariaLabel: string } = $props();
</script>

<div
  role="group"
  aria-label={ariaLabel}
  class="grid grid-cols-[5.25rem_minmax(0,1fr)] gap-x-3 sm:grid-cols-[7.5rem_minmax(0,1fr)] sm:gap-x-4"
>
  {#each rows as row (row.id)}
    <div class="contents">
      <div class="flex flex-col justify-center py-2.5">
        <span class="font-mono text-[0.8125rem] font-medium text-ink sm:text-[0.875rem]">{row.id}</span>
        <span class="text-[0.75rem] leading-tight hyphens-auto [overflow-wrap:anywhere] text-muted-foreground sm:text-[0.8125rem]">{row.note}</span>
      </div>
      <div class="relative flex items-center py-2.5">
        <div aria-hidden="true" class="pointer-events-none absolute inset-x-0 inset-y-0">
          {#each TICKS as t (t)}
            <span class="absolute inset-y-0 border-l border-rule" style:left="{t}%"></span>
          {/each}
        </div>
        <div
          class="relative flex h-[1.375rem] items-center justify-end pr-2 font-mono text-[0.8125rem] font-medium tabular {row.outlined
            ? 'border-[1.5px] border-brand bg-surface text-brand-ink'
            : 'bg-brand text-white'} rounded-r-md"
          style:width="{row.value}%"
        >
          {formatScoreLocale(lang, row.value, true)}
        </div>
      </div>
    </div>
  {/each}
  <div></div>
  <div aria-hidden="true" class="relative mt-1 h-5 border-t border-rule-strong font-mono text-[0.75rem] text-muted-foreground">
    {#each TICKS as t (t)}
      <span
        class="absolute top-1 {t === 0 ? 'left-0' : t === 100 ? 'right-0' : '-translate-x-1/2'}"
        style:left={t === 0 || t === 100 ? undefined : `${t}%`}
      >
        {t}
      </span>
    {/each}
  </div>
</div>
