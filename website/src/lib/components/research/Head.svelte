<script lang="ts">
  import Heading from '../Heading.svelte';
  import Rich from '../Rich.svelte';
  import { fill, type SectionProps } from './context';

  /** The top of the paper: title, subtitle, byline and the abstract. The page's only h1 lives here. */
  let { lang, t, vars }: SectionProps = $props();

  const head = $derived(t.head);
</script>

<header class="pt-6 pb-10 sm:pt-8 sm:pb-14">
  <p class="font-mono text-[0.8125rem] tracking-[0.08em] text-ink-faint uppercase">{head.eyebrow}</p>
  <Heading as="h1" size="display" class="mt-4 max-w-[19ch] text-ink">{head.title}</Heading>
  <p class="mt-5 max-w-[36ch] text-lede text-ink-soft">{head.subtitle}</p>
  <p class="mt-5 max-w-[52ch] text-[0.875rem] leading-snug text-ink-faint">{head.byline}</p>

  <section
    aria-labelledby="abstract-title"
    class="mt-10 rounded-xl border border-rule bg-surface p-5 shadow-[var(--shadow-raised)] sm:mt-12 sm:p-6"
  >
    <h2 id="abstract-title" class="text-[0.8125rem] font-semibold tracking-[0.08em] text-ink uppercase">
      {head.abstractLabel}
    </h2>
    <p class="mt-3 text-[1.0625rem] leading-[1.65] text-ink-soft sm:text-[1.125rem]">
      <Rich text={fill(vars, head.abstract)} {lang} />
    </p>
  </section>
</header>
