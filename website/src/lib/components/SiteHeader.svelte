<script lang="ts">
  import { page } from '$app/state';
  import { localePath, stripLocale, type Locale } from '$i18n/config';
  import type { Dictionary } from '$i18n';
  import { GITHUB_URL, NAV_ITEMS } from '$lib/site';
  import Canvas from './Canvas.svelte';
  import LanguageSwitch from './LanguageSwitch.svelte';

  /**
   * Top bar: wordmark, three page links, GitHub, language switch. It scrolls away with the page (no sticky bar
   * covering the figures). Below sm the links drop onto their own row so nothing is hidden behind a menu button.
   */
  let { lang, dict }: { lang: Locale; dict: Dictionary } = $props();

  const pathname = $derived(stripLocale(page.url.pathname));
  const navLinkClass =
    'inline-flex min-h-11 items-center px-0.5 text-[0.9375rem] text-ink-soft transition-colors duration-(--dur-fast) hover:bg-marker hover:text-ink sm:min-h-10';
  const wordmarkClass = 'inline-flex min-h-11 items-center gap-2.5 font-serif text-[1.75rem] leading-none font-semibold tracking-[0.04em] text-ink sm:text-[2rem]';
</script>

<header class="border-b border-rule">
  <Canvas class="flex flex-wrap items-center justify-between gap-x-8 gap-y-0 py-1.5 sm:py-3">
    <a
      href={localePath(lang, '/')}
      aria-label={dict.header.homeLabel}
      class={wordmarkClass}
    >
      <img src="/mira.svg" alt="" width="32" height="32" class="size-7 sm:size-8" />
      <span>MIRA</span>
    </a>

    <nav aria-label={dict.nav.label} class="order-last flex w-full flex-wrap items-center gap-x-6 sm:order-none sm:w-auto sm:flex-1 sm:gap-x-9">
      {#each NAV_ITEMS as item (item.key)}
        {@const active = pathname === item.href || pathname.startsWith(`${item.href}/`)}
        <a
          href={localePath(lang, item.href)}
          aria-current={active ? 'page' : undefined}
          class="{navLinkClass} {active ? 'font-semibold text-ink underline decoration-2 underline-offset-[6px]' : ''}"
        >
          {dict.nav[item.key]}
        </a>
      {/each}
      <a href={GITHUB_URL} target="_blank" rel="noopener noreferrer" class={navLinkClass}>
        {dict.nav.github}<span class="sr-only"> {dict.common.opensInNewTab}</span>
      </a>
    </nav>

    <LanguageSwitch
      {lang}
      label={dict.common.languageLabel}
      names={dict.common.languageNames}
      switchTo={dict.common.switchTo}
    />
  </Canvas>
</header>
