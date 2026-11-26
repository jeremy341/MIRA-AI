<script lang="ts">
  import { onMount } from 'svelte';
  import { page } from '$app/state';
  import { localePath, stripLocale, type Locale } from '$i18n/config';
  import type { Dictionary } from '$i18n';
  import { NAV_ITEMS } from '$lib/site';

  /**
   * The floating pill that slides in once the top bar has scrolled away. While it is hidden it is `inert`, so it
   * takes no focus and screen readers do not meet the navigation twice.
   */
  let { lang, dict }: { lang: Locale; dict: Dictionary } = $props();

  const SHOW_AFTER = 360;
  const pathname = $derived(stripLocale(page.url.pathname));
  let shown = $state(false);
  /** The package page has its own sticky menu bar below lg, which the pill would cover. */
  const hasLocalBar = $derived(pathname === '/package');

  onMount(() => {
    const update = () => (shown = window.scrollY > SHOW_AFTER);
    update();
    window.addEventListener('scroll', update, { passive: true });
    return () => window.removeEventListener('scroll', update);
  });

  const linkClass =
    'inline-flex min-h-10 items-center rounded-lg px-2.5 text-[0.9375rem] font-medium transition-colors duration-(--dur-fast) hover:bg-white/14 sm:px-3';
</script>

<div class="pill-wrap {hasLocalBar ? 'max-lg:!hidden' : ''}" class:shown inert={!shown}>
  <nav aria-label={dict.nav.label} class="on-brand pill">
    <a
      href={localePath(lang, '/')}
      aria-label={dict.header.homeLabel}
      class="inline-flex size-10 items-center justify-center rounded-lg"
    >
      <img src="/mira.svg" alt="" width="30" height="30" class="size-[1.875rem]" />
    </a>
    <span aria-hidden="true" class="mx-1 h-6 w-px bg-white/30"></span>
    {#each NAV_ITEMS as item (item.key)}
      {@const active = pathname === item.href || pathname.startsWith(`${item.href}/`)}
      <a
        href={localePath(lang, item.href)}
        aria-current={active ? 'page' : undefined}
        class="{linkClass} {active ? 'bg-white/16' : ''}"
      >
        {dict.nav[item.key]}
      </a>
    {/each}
    <a href={localePath(lang, '/docs')} class="btn btn-light !min-h-10 ml-2 max-sm:hidden">{dict.home.hero.tryCta}</a>
  </nav>
</div>

<style>
  .pill-wrap {
    position: fixed;
    z-index: 60;
    top: 0.75rem;
    inset-inline: 0;
    display: flex;
    justify-content: center;
    padding-inline: 0.75rem;
    pointer-events: none;
    opacity: 0;
    transform: translateY(-140%);
    visibility: hidden;
    transition:
      transform var(--dur-base) var(--ease-out),
      opacity var(--dur-base) ease-out,
      visibility 0s var(--dur-base);
  }
  .pill-wrap.shown {
    opacity: 1;
    transform: translateY(0);
    visibility: visible;
    transition:
      transform var(--dur-base) var(--ease-out),
      opacity var(--dur-base) ease-out,
      visibility 0s;
  }
  .pill {
    display: flex;
    align-items: center;
    gap: 0.125rem;
    padding: 0.375rem;
    border-radius: 0.875rem;
    box-shadow: var(--shadow-floating);
    pointer-events: auto;
  }
</style>
