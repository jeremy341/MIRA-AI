<script lang="ts">
  import { localePath, type Locale } from '$i18n/config';
  import type { DocsUi } from '$i18n/docs/ui';
  import { docPath } from '$lib/docs-content';

  /** Previous and next page, in reading order, under a heavy rule like the end of a chapter. */
  let {
    lang,
    ui,
    prev,
    next
  }: {
    lang: Locale;
    ui: DocsUi;
    prev?: { slug: string; title: string };
    next?: { slug: string; title: string };
  } = $props();

  const item = 'group block min-w-0 py-5 sm:py-6';
  const title =
    'mt-1 inline font-serif text-[1.25rem] leading-snug font-medium text-ink group-hover:bg-marker group-focus-visible:bg-marker';
</script>

{#if prev || next}
  <nav aria-label={ui.prevNextLabel} class="mt-20 grid gap-x-8 border-t border-ink sm:grid-cols-2">
    {#if prev}
      <a href={localePath(lang, docPath(prev.slug))} rel="prev" class={item}>
        <span class="block text-[0.8125rem] text-muted-foreground"><span aria-hidden="true">&larr; </span>{ui.previous}</span>
        <span class={title}>{prev.title}</span>
      </a>
    {:else}
      <span class="hidden sm:block"></span>
    {/if}
    {#if next}
      <a href={localePath(lang, docPath(next.slug))} rel="next" class="{item} sm:text-right">
        <span class="block text-[0.8125rem] text-muted-foreground">{ui.next}<span aria-hidden="true"> &rarr;</span></span>
        <span class={title}>{next.title}</span>
      </a>
    {/if}
  </nav>
{/if}
