<script lang="ts">
  import { localePath, type Locale } from '$i18n/config';
  import type { Dictionary } from '$i18n';
  import { GITHUB_URL, HF_URL, NAV_ITEMS, PYPI_URL } from '$lib/site';
  import Canvas from './Canvas.svelte';
  import ExtLink from './ExtLink.svelte';

  let { lang, dict }: { lang: Locale; dict: Dictionary } = $props();
  const hint = $derived(dict.common.opensInNewTab);
</script>

<footer class="mt-16 border-t border-ink">
  <Canvas class="flex flex-col gap-8 py-10 sm:flex-row sm:justify-between">
    <div class="max-w-[34ch]">
      <p class="flex items-center gap-2 font-serif text-xl font-semibold tracking-[0.04em] text-ink">
        <img src="/mira.svg" alt="" width="24" height="24" class="size-6" />MIRA
      </p>
      <p class="mt-2 text-[0.875rem] leading-snug text-ink-soft">{dict.footer.blurb}</p>
      <p class="mt-2 text-[0.875rem] text-muted-foreground">{dict.footer.licence}</p>
    </div>
    <div class="flex gap-12 text-[0.9375rem]">
      <nav aria-label={dict.footer.pagesTitle}>
        <p class="font-sans text-[0.8125rem] font-semibold text-ink">{dict.footer.pagesTitle}</p>
        <ul class="mt-2 space-y-0.5">
          <li>
            <a href={localePath(lang, '/')} class="nb-link inline-block py-1">{dict.nav.home}</a>
          </li>
          {#each NAV_ITEMS as item (item.key)}
            <li>
              <a href={localePath(lang, item.href)} class="nb-link inline-block py-1">{dict.nav[item.key]}</a>
            </li>
          {/each}
        </ul>
      </nav>
      <nav aria-label={dict.footer.projectTitle}>
        <p class="font-sans text-[0.8125rem] font-semibold text-ink">{dict.footer.projectTitle}</p>
        <ul class="mt-2 space-y-0.5">
          <li><ExtLink href={GITHUB_URL} {hint} class="inline-block py-1">{dict.footer.github}</ExtLink></li>
          <li><ExtLink href={PYPI_URL} {hint} class="inline-block py-1">{dict.footer.pypi}</ExtLink></li>
          <li><ExtLink href={HF_URL} {hint} class="inline-block py-1">{dict.footer.huggingface}</ExtLink></li>
        </ul>
      </nav>
    </div>
  </Canvas>
</footer>
