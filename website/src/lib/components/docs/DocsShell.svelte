<script lang="ts">
  import { onMount, type Snippet } from 'svelte';
  import { page } from '$app/state';
  import { getDictionary } from '$i18n';
  import { localePath, type Locale } from '$i18n/config';
  import type { DocsUi } from '$i18n/docs/ui';
  import { GITHUB_URL } from '$lib/site';
  import LanguageSwitch from '../LanguageSwitch.svelte';
  import DocsNav from './DocsNav.svelte';
  import DocsSearch from './DocsSearch.svelte';
  import type { NavGroup } from './types';

  /**
   * Docs chrome in the layout of Orchard's docs: a full-height sidebar panel on the left (logo, filter, grouped
   * pages), a slim top bar with search and links, and the page centred in the space that is left. Below lg the
   * sidebar is a modal drawer (a native <dialog>: focus is trapped, Escape closes it, focus returns to the button).
   */
  let {
    lang,
    ui,
    nav,
    base = '/docs',
    badge,
    search = true,
    children
  }: {
    lang: Locale;
    ui: DocsUi;
    nav: NavGroup[];
    /** '/docs' or '/research'. */
    base?: string;
    /** The small label next to the logo. */
    badge?: string;
    /** The docs search covers the docs only, so the research report hides it. */
    search?: boolean;
    children: Snippet;
  } = $props();

  const dict = $derived(getDictionary(lang));

  let dialog = $state<HTMLDialogElement>();
  let menuOpen = $state(false);

  function openMenu() {
    if (dialog && !dialog.open) {
      dialog.showModal();
      menuOpen = true;
    }
  }
  const closeMenu = () => dialog?.close();
  // aria-expanded follows the dialog itself, whichever way it closed (button, backdrop, Escape, link, resize).
  const syncMenuOpen = () => (menuOpen = dialog?.open ?? false);

  // Close the drawer after navigating.
  $effect(() => {
    void page.url.pathname;
    dialog?.close();
  });

  // Close it if the viewport grows to the sidebar layout.
  onMount(() => {
    const query = window.matchMedia('(min-width: 1024px)');
    const onChange = (event: MediaQueryListEvent) => {
      if (event.matches) dialog?.close();
    };
    query.addEventListener('change', onChange);
    return () => query.removeEventListener('change', onChange);
  });

  const topLink =
    'hidden rounded-lg px-2.5 py-1.5 text-[0.9375rem] text-ink-soft transition-colors duration-(--dur-fast) hover:bg-hover/60 hover:text-ink xl:inline-block';
</script>

{#snippet brand()}
  <a href={localePath(lang, '/')} class="flex items-center gap-2.5" aria-label={dict.header.homeLabel}>
    <img src="/mira.svg" alt="" width="30" height="30" class="size-[1.875rem]" />
    <span class="text-[1.25rem] leading-none font-extrabold tracking-[0.04em] text-ink">MIRA</span>
  </a>
  <span class="rounded-md bg-sunken px-2 py-0.5 text-[0.75rem] font-medium text-ink-soft">{badge ?? ui.metaSuffix}</span>
{/snippet}

<div class="min-h-dvh bg-app">
  <!-- Sidebar: the full height of the window, like Orchard's. -->
  <aside aria-label={ui.sectionName} class="fixed inset-y-0 left-0 z-20 hidden w-[18rem] p-2.5 lg:block">
    <div class="flex h-full flex-col overflow-hidden rounded-2xl border border-rule bg-surface shadow-[var(--shadow-raised)]">
      <div class="flex items-center gap-2.5 px-4 pt-4 pb-3">{@render brand()}</div>
      <div class="min-h-0 flex-1 overflow-y-auto px-3 pt-1 pb-6">
        <DocsNav {lang} {ui} groups={nav} {base} />
      </div>
    </div>
  </aside>

  <div class="lg:pl-[18rem]">
    <header class="sticky top-0 z-30 border-b border-transparent bg-app/85 backdrop-blur lg:border-0">
      <div class="flex h-16 items-center gap-2 px-4 sm:px-6">
        <button
          type="button"
          onclick={openMenu}
          aria-haspopup="dialog"
          aria-expanded={menuOpen}
          aria-controls="docs-menu"
          class="inline-flex h-10 shrink-0 items-center rounded-lg border border-rule bg-surface px-3 text-[0.9375rem] font-medium text-ink lg:hidden"
        >
          {ui.menu}
        </button>
        <div class="flex items-center gap-2.5 lg:hidden">
          <a href={localePath(lang, '/')} aria-label={dict.header.homeLabel} class="flex items-center">
            <img src="/mira.svg" alt="" width="28" height="28" class="size-7" />
          </a>
        </div>

        <div class="ml-auto flex min-w-0 flex-1 items-center justify-end gap-1.5">
          <a href={localePath(lang, '/')} class={topLink}>{dict.nav.home}</a>
          {#if base !== '/docs'}<a href={localePath(lang, '/docs')} class={topLink}>{dict.nav.docs}</a>{/if}
          {#if base !== '/research'}<a href={localePath(lang, '/research')} class={topLink}>{dict.nav.research}</a>{/if}
          <a href={localePath(lang, '/package')} class={topLink}>{dict.nav.package}</a>
          {#if search}
            <DocsSearch {lang} {ui} class="max-w-60 min-w-0 flex-1 sm:flex-none sm:basis-60" />
          {/if}
          <a
            href={GITHUB_URL}
            target="_blank"
            rel="noopener noreferrer"
            aria-label="GitHub"
            class="inline-flex size-10 shrink-0 items-center justify-center rounded-lg text-ink-soft transition-colors hover:bg-hover/60 hover:text-ink"
          >
            <svg viewBox="0 0 16 16" width="20" height="20" fill="currentColor" aria-hidden="true">
              <path d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27s1.36.09 2 .27c1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.01 8.01 0 0 0 16 8c0-4.42-3.58-8-8-8Z" />
            </svg>
          </a>
          <LanguageSwitch
            {lang}
            label={dict.common.languageLabel}
            names={dict.common.languageNames}
            switchTo={dict.common.switchTo}
            class="hidden sm:flex"
          />
          <a href={localePath(lang, '/docs/quickstart')} class="btn btn-primary hidden md:inline-flex">{ui.installCta}</a>
        </div>
      </div>
    </header>

    {@render children()}
  </div>

  <dialog
    bind:this={dialog}
    id="docs-menu"
    aria-labelledby="docs-menu-title"
    onclose={syncMenuOpen}
    oncancel={() => setTimeout(syncMenuOpen, 0)}
    onclick={(event) => {
      if (event.target === event.currentTarget) closeMenu();
    }}
    class="m-0 h-dvh max-h-dvh w-[min(21rem,88vw)] max-w-none overflow-y-auto border-r border-rule bg-surface p-0 text-ink backdrop:bg-ink/40"
  >
    <div class="flex items-center justify-between border-b border-rule px-4 py-3">
      <h2 id="docs-menu-title" class="sr-only">{ui.menuTitle}</h2>
      <div class="flex items-center gap-2.5">{@render brand()}</div>
      <button
        type="button"
        onclick={closeMenu}
        aria-label={ui.closeMenu}
        class="inline-flex h-10 items-center rounded-lg border border-rule px-3 text-[0.9375rem] font-medium text-ink"
      >
        {ui.close}
      </button>
    </div>
    <div class="px-3 py-4">
      <DocsNav {lang} {ui} groups={nav} {base} onNavigate={closeMenu} />
    </div>
  </dialog>
</div>

<style>
  /* A modal dialog does not stop the page behind it from scrolling. */
  :global(html:has(#docs-menu[open])) {
    overflow: hidden;
  }
</style>
