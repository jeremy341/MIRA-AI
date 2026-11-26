<script lang="ts">
  import type { Dictionary } from '$i18n';
  import type { Locale } from '$i18n/config';
  import Rich from '../Rich.svelte';
  import HomeSection from './HomeSection.svelte';
  import ResultStrip from './ResultStrip.svelte';

  /** "What is MIRA?": how a detection works in three steps, then the headline numbers. */
  let { lang, dict }: { lang: Locale; dict: Dictionary } = $props();

  const t = $derived(dict.home.what);
</script>

<HomeSection id="what" title={t.title} lede={t.lede}>
  <ol aria-label={t.stepsLabel} class="grid grid-cols-[minmax(0,1fr)] gap-4 md:grid-cols-3">
    {#each t.steps as step, index (step.title)}
      <li class="rounded-2xl bg-tint p-6 sm:p-8">
        <span
          aria-hidden="true"
          class="flex size-10 items-center justify-center rounded-lg bg-brand font-mono text-[1rem] text-white"
        >
          {index + 1}
        </span>
        <h3 class="mt-5 text-[1.25rem] font-semibold text-brand-ink">{step.title}</h3>
        <p class="mt-2 text-[0.9375rem] leading-[1.6] text-ink-soft"><Rich text={step.text} /></p>
      </li>
    {/each}
  </ol>

  <ResultStrip {lang} {dict} />
</HomeSection>
