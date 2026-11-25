<script lang="ts">
  import { localePath, type Locale } from '$i18n/config';
  import type { DocsUi } from '$i18n/docs/ui';

  /** Previous and next page as two cards at the end of the article. */
  let {
    lang,
    ui,
    prev,
    next,
    base = '/docs'
  }: {
    lang: Locale;
    ui: DocsUi;
    base?: string;
    prev?: { slug: string; title: string };
    next?: { slug: string; title: string };
  } = $props();

  const card =
    'group block min-w-0 rounded-xl border border-rule bg-surface px-5 py-4 shadow-[var(--shadow-raised)] transition-colors duration-(--dur-fast) hover:border-accent';
</script>

{#if prev || next}
  <nav aria-label={ui.prevNextLabel} class="mt-16 grid gap-3 sm:grid-cols-2">
    {#if prev}
      <a href={localePath(lang, `${base}/${prev.slug}`)} rel="prev" class={card}>
        <span class="block text-[0.8125rem] text-muted-foreground"><span aria-hidden="true">&larr; </span>{ui.previous}</span>
        <span class="mt-1 block text-[1.0625rem] font-semibold text-ink group-hover:text-accent-strong">{prev.title}</span>
      </a>
    {:else}
      <span class="hidden sm:block"></span>
    {/if}
    {#if next}
      <a href={localePath(lang, `${base}/${next.slug}`)} rel="next" class="{card} sm:text-right">
        <span class="block text-[0.8125rem] text-muted-foreground">{ui.next}<span aria-hidden="true"> &rarr;</span></span>
        <span class="mt-1 block text-[1.0625rem] font-semibold text-ink group-hover:text-accent-strong">{next.title}</span>
      </a>
    {/if}
  </nav>
{/if}
