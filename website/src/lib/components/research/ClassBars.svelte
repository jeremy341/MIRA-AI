<script lang="ts" module>
  import type { ClassId } from '$lib/site';

  export type ClassBarRow = {
    cls: ClassId;
    /** Percent, EXP-014. */
    before: number;
    /** Percent, EXP-018. */
    after: number;
    beforeDisplay: string;
    afterDisplay: string;
  };
</script>

<script lang="ts">
  import { classBorderVar } from '$lib/class-colors';
  import { CLASS_BY_ID, CLASSES } from '$lib/site';
  import ClassChip from '../ClassChip.svelte';
  import { TICKS } from './chart';

  /**
   * Per-class mAP50 of two runs. Each class gets its own colour (the same as in the detection frames), and
   * the two runs are told apart by TEXTURE, not by colour: hatched is the earlier run, solid the later one.
   * Class names and values are printed, so colour is never the only signal.
   */
  let {
    rows,
    classNames,
    beforeLabel,
    afterLabel,
    ariaLabel
  }: {
    rows: readonly ClassBarRow[];
    classNames: Record<ClassId, string>;
    beforeLabel: string;
    afterLabel: string;
    ariaLabel: string;
  } = $props();

  const ordered = $derived(CLASSES.map((c) => rows.find((r) => r.cls === c.id)).filter((r): r is ClassBarRow => !!r));

  function barStyle(cls: ClassId, hatched: boolean, value: number): string {
    const fill = CLASS_BY_ID[cls].cssVar;
    const edge = classBorderVar(cls);
    const base = `width:${value}%;border:1.5px solid ${edge};`;
    return hatched
      ? `${base}background-color:var(--surface);background-image:repeating-linear-gradient(135deg, ${edge} 0 1.5px, transparent 1.5px 5px);`
      : `${base}background-color:${fill};`;
  }
</script>

{#snippet gridlines()}
  <div aria-hidden="true" class="pointer-events-none absolute inset-0">
    {#each TICKS as t (t)}
      <span class="absolute inset-y-0 border-l border-rule" style:left="{t}%"></span>
    {/each}
  </div>
{/snippet}

<div>
  <p class="mb-3 flex flex-wrap gap-x-6 gap-y-1 text-[0.8125rem] text-ink-soft">
    <span class="inline-flex items-center gap-2">
      <span
        aria-hidden="true"
        class="inline-block h-3 w-6 border-[1.5px] border-ink-soft bg-surface"
        style="background-image: repeating-linear-gradient(135deg, var(--ink-soft) 0 1.5px, transparent 1.5px 5px)"
      ></span>
      {beforeLabel}
    </span>
    <span class="inline-flex items-center gap-2">
      <span aria-hidden="true" class="inline-block h-3 w-6 border-[1.5px] border-ink-soft bg-ink-soft"></span>
      {afterLabel}
    </span>
  </p>
  <div
    role="group"
    aria-label={ariaLabel}
    class="grid grid-cols-[5.75rem_minmax(0,1fr)_3.9rem] gap-x-3 sm:grid-cols-[8rem_minmax(0,1fr)_4.5rem]"
  >
    {#each ordered as r (r.cls)}
      <div class="contents">
        <div class="row-span-2 flex items-center border-t border-rule py-3 text-[0.9375rem]">
          <ClassChip cls={r.cls} label={classNames[r.cls]} />
        </div>
        <div class="relative flex items-center border-t border-rule pt-3 pb-[0.1875rem]">
          {@render gridlines()}
          <div aria-hidden="true" class="relative h-[1rem]" style={barStyle(r.cls, true, r.before)}></div>
        </div>
        <div
          class="flex items-center justify-end border-t border-rule pt-3 pb-[0.1875rem] font-mono text-[0.8125rem] tabular text-ink"
        >
          <span class="sr-only">{beforeLabel}: </span>
          {r.beforeDisplay}
        </div>
        <div class="relative flex items-center pt-[0.1875rem] pb-3">
          {@render gridlines()}
          <div aria-hidden="true" class="relative h-[1rem]" style={barStyle(r.cls, false, r.after)}></div>
        </div>
        <div class="flex items-center justify-end pt-[0.1875rem] pb-3 font-mono text-[0.8125rem] tabular text-ink">
          <span class="sr-only">{afterLabel}: </span>
          {r.afterDisplay}
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
    <div></div>
  </div>
</div>
