<script lang="ts">
  import type { Dictionary } from '$i18n';
  import Rich from '../Rich.svelte';
  import HomeSection from './HomeSection.svelte';

  let { dict }: { dict: Dictionary } = $props();
  const t = $derived(dict.home.problem);
</script>

<HomeSection id="problem" title={t.title}>
  <p class="max-w-[62ch] text-[1.125rem] leading-[1.65] text-ink-soft"><Rich text={t.p1} /></p>

  <ol aria-label={t.triedLabel} class="mt-8 grid grid-cols-[minmax(0,1fr)] gap-3 sm:grid-cols-2 lg:grid-cols-4">
    {#each t.tried as step, index (step.name)}
      <li class="rounded-2xl border border-rule bg-surface p-5 shadow-[var(--shadow-raised)]">
        <p class="font-mono text-[0.8125rem] text-muted-foreground tabular">{index + 1}</p>
        <p class="mt-1 text-[1.0625rem] font-semibold text-ink">{step.name}</p>
        <p class="mt-1.5 text-[0.9375rem] leading-[1.5] text-ink-soft"><Rich text={step.text} /></p>
      </li>
    {/each}
  </ol>

  <div class="mt-8 grid grid-cols-[minmax(0,1fr)] gap-3 md:grid-cols-2">
    <div class="rounded-2xl border border-rule bg-surface p-6 shadow-[var(--shadow-raised)]">
      <p class="text-[1rem] leading-[1.65] text-ink-soft"><Rich text={t.p2} /></p>
      <p class="mt-4 border-l-2 border-accent pl-3 text-[0.875rem] leading-[1.5] text-ink-soft"><Rich text={t.note} /></p>
    </div>
    <div class="rounded-2xl border border-rule bg-surface p-6 shadow-[var(--shadow-raised)]">
      <p class="text-[1rem] leading-[1.65] text-ink-soft"><Rich text={t.p3} /></p>
    </div>
  </div>
</HomeSection>
