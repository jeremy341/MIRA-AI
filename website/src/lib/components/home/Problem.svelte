<script lang="ts">
  import type { Dictionary } from '$i18n';
  import Rich from '../Rich.svelte';
  import HomeSection from './HomeSection.svelte';

  let { dict }: { dict: Dictionary } = $props();
  const t = $derived(dict.home.problem);
</script>

<HomeSection id="problem" title={t.title} align="start">
  <div class="grid grid-cols-[minmax(0,1fr)] gap-10 lg:grid-cols-2 lg:gap-16">
    <div class="min-w-0">
      <p class="max-w-[56ch] text-[1.125rem] leading-[1.65] text-ink-soft"><Rich text={t.p1} /></p>
      <ol aria-label={t.triedLabel} class="mt-8">
        {#each t.tried as step, index (step.name)}
          <li class="relative border-l-2 py-3 pl-5 {index === t.tried.length - 1 ? 'border-brand' : 'border-rule'}">
            <p class="text-[1.1875rem] font-semibold text-brand-ink">
              <span class="mr-2 font-mono text-[0.875rem] text-accent-strong">{index + 1}</span>{step.name}
            </p>
            <p class="mt-1 text-[0.9375rem] leading-[1.55] text-ink-soft"><Rich text={step.text} /></p>
          </li>
        {/each}
      </ol>
    </div>

    <div class="flex min-w-0 flex-col justify-center gap-4 rounded-3xl bg-tint p-4 sm:p-8">
      <div class="card p-6 sm:p-7">
        <p class="text-[1rem] leading-[1.65] text-ink-soft"><Rich text={t.p2} /></p>
        <p class="mt-4 border-l-2 border-brand pl-3 text-[0.875rem] leading-[1.55] text-ink-soft"><Rich text={t.note} /></p>
      </div>
      <div class="card p-6 sm:p-7">
        <p class="text-[1rem] leading-[1.65] text-ink-soft"><Rich text={t.p3} /></p>
      </div>
    </div>
  </div>
</HomeSection>
