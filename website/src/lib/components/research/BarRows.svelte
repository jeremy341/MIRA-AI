<script lang="ts" module>
  export type BarTone = 'ink' | 'soft' | 'outline';

  export type BarRowData = {
    key: string;
    /** Main label, usually the experiment id. */
    label: string;
    /** Second line under the label. */
    sub?: string;
    /** Percent, 0 to 100. */
    value: number;
    /** The printed value, already formatted for the language. */
    display: string;
    tone: BarTone;
  };
</script>

<script lang="ts">
  import Rich from '../Rich.svelte';
  import { TICKS } from './chart';

  const TONE: Record<BarTone, string> = {
    ink: 'bg-brand',
    soft: 'bg-muted-foreground',
    outline: 'border-[1.5px] border-brand bg-surface'
  };

  /**
   * One series of horizontal bars, HTML and CSS only. Every bar prints its value in its own column, so the
   * numbers are text a reader (or a screen reader) can use and the chart is never the only source.
   * Ink bars, thin hairline axis, no animation, no tooltip.
   */
  let {
    rows,
    ariaLabel,
    cols = 'grid-cols-[6rem_minmax(0,1fr)_3.9rem] sm:grid-cols-[9rem_minmax(0,1fr)_4.5rem]'
  }: {
    rows: readonly BarRowData[];
    ariaLabel: string;
    /** Tailwind grid-cols classes for label, track and value (must be literal strings). */
    cols?: string;
  } = $props();
</script>

<div role="group" aria-label={ariaLabel} class="grid gap-x-3 {cols}">
  {#each rows as row (row.key)}
    <div class="contents">
      <div class="flex min-w-0 flex-col justify-center py-1.5">
        <span class="font-mono text-[0.8125rem] leading-tight font-medium text-ink">{row.label}</span>
        {#if row.sub}
          <span class="mt-0.5 text-[0.75rem] leading-tight hyphens-auto [overflow-wrap:anywhere] text-muted-foreground"><Rich text={row.sub} /></span>
        {/if}
      </div>
      <div class="relative flex items-center py-1.5">
        <div aria-hidden="true" class="pointer-events-none absolute inset-0">
          {#each TICKS as t (t)}
            <span class="absolute inset-y-0 border-l border-rule" style:left="{t}%"></span>
          {/each}
        </div>
        <div aria-hidden="true" class="relative h-[1.125rem] {TONE[row.tone]}" style:width="{row.value}%"></div>
      </div>
      <div class="flex items-center justify-end py-1.5 font-mono text-[0.8125rem] tabular text-ink">{row.display}</div>
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
  <div></div>
</div>
