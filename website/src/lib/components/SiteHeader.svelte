<script lang="ts">
  import { page } from '$app/state';
  import { localePath, stripLocale, type Locale } from '$i18n/config';
  import type { Dictionary } from '$i18n';
  import { GITHUB_URL, NAV_ITEMS } from '$lib/site';
  import LanguageSwitch from './LanguageSwitch.svelte';
  import PillNav from './PillNav.svelte';

  /**
   * Top bar on the brand colour, so it runs straight into the blue band at the top of each page. It scrolls away with
   * the page and the floating pill takes over. Below md the links drop onto their own row, so nothing hides behind a
   * menu button.
   */
  let { lang, dict }: { lang: Locale; dict: Dictionary } = $props();

  const pathname = $derived(stripLocale(page.url.pathname));
  const navLinkClass =
    'inline-flex min-h-11 items-center rounded-lg px-3 text-[0.9375rem] font-medium transition-colors duration-(--dur-fast) hover:bg-white/12';
</script>

<header class="on-brand">
  <div class="shell !max-w-[90rem] flex flex-wrap items-center gap-x-4 py-3 md:py-4">
    <a
      href={localePath(lang, '/')}
      aria-label={dict.header.homeLabel}
      class="inline-flex min-h-11 items-center gap-2.5 rounded-lg text-[1.625rem] leading-none font-extrabold tracking-[-0.01em]"
    >
      <img src="/mira.svg" alt="" width="36" height="36" class="size-9" />
      <span>MIRA</span>
    </a>

    <nav
      aria-label={dict.nav.label}
      class="order-last -mx-3 flex w-[calc(100%+1.5rem)] flex-wrap items-center md:order-none md:mx-0 md:ml-8 md:w-auto md:gap-x-1"
    >
      {#each NAV_ITEMS as item (item.key)}
        {@const active = pathname === item.href || pathname.startsWith(`${item.href}/`)}
        <a
          href={localePath(lang, item.href)}
          aria-current={active ? 'page' : undefined}
          class="{navLinkClass} {active ? 'bg-white/16' : ''}"
        >
          {dict.nav[item.key]}
        </a>
      {/each}
      <a href={GITHUB_URL} target="_blank" rel="noopener noreferrer" class={navLinkClass}>
        {dict.nav.github}<span class="sr-only"> {dict.common.opensInNewTab}</span>
      </a>
    </nav>

    <div class="ml-auto flex items-center gap-3">
      <LanguageSwitch
        {lang}
        label={dict.common.languageLabel}
        names={dict.common.languageNames}
        switchTo={dict.common.switchTo}
      />
      <a href={localePath(lang, '/docs')} class="btn btn-light max-sm:hidden">{dict.home.hero.tryCta}</a>
    </div>
  </div>
</header>

<PillNav {lang} {dict} />
