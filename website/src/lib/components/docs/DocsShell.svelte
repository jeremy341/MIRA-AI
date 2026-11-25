<script lang="ts">
  import { onMount, type Snippet } from 'svelte';
  import { page } from '$app/state';
  import type { Locale } from '$i18n/config';
  import type { DocsUi } from '$i18n/docs/ui';
  import Canvas from '../Canvas.svelte';
  import DocsNav from './DocsNav.svelte';
  import DocsSearch from './DocsSearch.svelte';
  import type { NavGroup } from './types';

  /**
   * Docs chrome. From lg: a sticky sidebar (search on top, then the page list) next to the article, and
   * from xl a slim "on this page" list. Below lg: a thin sticky bar with a contents button and the search,
   * and the same navigation in a modal drawer. The drawer is a native <dialog>, so focus is trapped,
   * Escape closes it and focus returns to the button.
   *
   * `children` is placed in the grid next to the sidebar (article and, at xl, the table of contents).
   */
  let {
    lang,
    ui,
    nav,
    children
  }: { lang: Locale; ui: DocsUi; nav: NavGroup[]; children: Snippet } = $props();

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

  // Close it if the viewport grows to the two-column layout.
  onMount(() => {
    const query = window.matchMedia('(min-width: 1024px)');
    const onChange = (event: MediaQueryListEvent) => {
      if (event.matches) dialog?.close();
    };
    query.addEventListener('change', onChange);
    return () => query.removeEventListener('change', onChange);
  });
</script>

<div>
  <div class="sticky top-0 z-30 border-b border-rule bg-paper lg:hidden">
    <Canvas class="flex h-14 items-center gap-3">
      <button
        type="button"
        onclick={openMenu}
        aria-haspopup="dialog"
        aria-expanded={menuOpen}
        aria-controls="docs-menu"
        class="inline-flex h-11 shrink-0 items-center px-1 text-[0.9375rem] font-medium text-ink underline decoration-1 underline-offset-[0.25em] transition-colors duration-(--dur-fast) ease-out hover:bg-marker"
      >
        {ui.menu}
      </button>
      <DocsSearch {lang} {ui} />
    </Canvas>
  </div>

  <Canvas class="lg:grid lg:grid-cols-[13rem_minmax(0,1fr)] lg:gap-x-10 xl:grid-cols-[13rem_minmax(0,1fr)_11rem]">
    <!-- Only the page list scrolls, so the search results can open over the article instead of being clipped to the column. -->
    <aside
      aria-label={ui.sectionName}
      class="sticky top-6 hidden self-start py-12 pr-2 lg:col-start-1 lg:row-start-1 lg:block"
    >
      <DocsSearch {lang} {ui} class="mb-8" />
      <div class="max-h-[calc(100dvh-14rem)] overflow-y-auto">
        <DocsNav {lang} label={ui.navLabel} overview={ui.overview} groups={nav} />
      </div>
    </aside>
    {@render children()}
  </Canvas>

  <dialog
    bind:this={dialog}
    id="docs-menu"
    aria-labelledby="docs-menu-title"
    onclose={syncMenuOpen}
    oncancel={() => setTimeout(syncMenuOpen, 0)}
    onclick={(event) => {
      if (event.target === event.currentTarget) closeMenu();
    }}
    class="m-0 h-dvh max-h-dvh w-[min(21rem,88vw)] max-w-none overflow-y-auto border-r border-ink bg-paper p-0 text-ink backdrop:bg-ink/40"
  >
    <div class="flex items-center justify-between border-b border-rule py-1.5 pr-3 pl-5">
      <h2 id="docs-menu-title" class="font-serif text-[1.375rem] font-medium">{ui.menuTitle}</h2>
      <button
        type="button"
        onclick={closeMenu}
        aria-label={ui.closeMenu}
        class="inline-flex h-11 min-w-11 items-center justify-center px-2 text-[0.9375rem] font-medium text-ink underline decoration-1 underline-offset-[0.25em] transition-colors duration-(--dur-fast) ease-out hover:bg-marker"
      >
        {ui.close}
      </button>
    </div>
    <div class="px-5 py-6">
      <DocsNav {lang} label={ui.navLabel} overview={ui.overview} groups={nav} onNavigate={closeMenu} />
    </div>
  </dialog>
</div>

<style>
  /* A modal dialog does not stop the page behind it from scrolling. */
  :global(html:has(#docs-menu[open])) {
    overflow: hidden;
  }
</style>
