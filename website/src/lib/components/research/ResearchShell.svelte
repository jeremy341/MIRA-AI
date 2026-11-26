<script lang="ts">
  import { onMount, type Snippet } from 'svelte';
  import type { Locale } from '$i18n/config';
  import { DOCS_UI } from '$i18n/docs/ui';
  import Canvas from '../Canvas.svelte';

  /**
   * Orchard-style docs chrome for the research paper: a filterable section pane on the left,
   * the article in the middle and an "on this page" list on the right. Below lg the pane
   * becomes a native dialog, the same pattern the docs section uses.
   */
  let {
    lang,
    sections,
    label,
    children
  }: {
    lang: Locale;
    sections: { id: string; label: string }[];
    label?: string;
    children: Snippet;
  } = $props();

  const ui = $derived(DOCS_UI[lang]);
  const paneLabel = $derived(label ?? ui.sectionName);
  let filter = $state('');
  let active = $state<string>('');
  let dialog = $state<HTMLDialogElement>();
  let menuOpen = $state(false);

  const visible = $derived(sections.filter((s) => s.label.toLowerCase().includes(filter.trim().toLowerCase())));

  function openMenu() {
    if (dialog && !dialog.open) {
      dialog.showModal();
      menuOpen = true;
    }
  }
  const closeMenu = () => dialog?.close();
  const syncMenuOpen = () => (menuOpen = dialog?.open ?? false);

  onMount(() => {
    const targets = sections
      .map((section) => document.getElementById(section.id))
      .filter((element): element is HTMLElement => element !== null);
    if (targets.length === 0) return;
    active = targets[0].id;

    const observer = new IntersectionObserver(
      (entries) => {
        const hit = entries
          .filter((entry) => entry.isIntersecting)
          .sort((a, b) => a.boundingClientRect.top - b.boundingClientRect.top)[0];
        if (hit) active = hit.target.id;
      },
      { rootMargin: `-${6 * parseFloat(getComputedStyle(document.documentElement).fontSize)}px 0px -65% 0px`, threshold: 0 }
    );
    targets.forEach((target) => observer.observe(target));
    return () => observer.disconnect();
  });
</script>

<div>
  <div class="sticky top-0 z-30 border-b border-rule bg-app lg:hidden">
    <Canvas class="flex h-14 items-center gap-3">
      <button
        type="button"
        onclick={openMenu}
        aria-haspopup="dialog"
        aria-expanded={menuOpen}
        aria-controls="research-menu"
        class="inline-flex h-11 shrink-0 items-center rounded-lg px-2 text-[0.9375rem] font-medium text-ink underline decoration-1 underline-offset-[0.25em] transition-colors duration-(--dur-fast) ease-out hover:bg-accent-soft"
      >
        {ui.menu}
      </button>
      <span class="truncate text-[0.9375rem] font-semibold text-ink">{paneLabel}</span>
    </Canvas>
  </div>

  <Canvas
    class="lg:grid lg:grid-cols-[14rem_minmax(0,1fr)] lg:gap-x-8 xl:grid-cols-[14rem_minmax(0,1fr)_12rem] xl:gap-x-10"
  >
    <aside aria-label={paneLabel} class="sticky top-6 hidden self-start lg:col-start-1 lg:row-start-1 lg:block">
      <div class="rounded-xl border border-rule bg-surface p-3 shadow-[var(--shadow-raised)]">
        <label class="sr-only" for="research-filter">{ui.search.label}</label>
        <input
          id="research-filter"
          type="search"
          bind:value={filter}
          placeholder={ui.filterSections}
          class="h-10 w-full rounded-lg border border-rule bg-app px-3 text-[0.8125rem] text-ink placeholder:text-ink-faint focus-visible:border-accent"
        />
        <p class="mt-4 px-2 text-[0.6875rem] font-semibold tracking-[0.08em] text-ink-faint uppercase">
          {paneLabel}
        </p>
        <ul class="mt-1 space-y-px">
          {#each visible as section, i (section.id)}
            <li>
              <a
                href="#{section.id}"
                onclick={() => (active = section.id)}
                class="flex items-center gap-2 rounded-lg px-2.5 py-2 text-[0.8125rem] transition-colors duration-(--dur-fast) {active ===
                section.id
                  ? 'bg-accent-soft font-semibold text-accent-strong'
                  : 'text-ink-soft hover:bg-hover hover:text-ink'}"
              >
                <span class="w-4 shrink-0 font-mono text-[0.6875rem] text-ink-faint">{i + 1}</span>
                <span class="min-w-0 leading-snug">{section.label}</span>
              </a>
            </li>
          {/each}
        </ul>
      </div>
    </aside>

    <article class="research-article min-w-0 lg:col-start-2 lg:row-start-1">
      {@render children()}
    </article>

    <aside
      aria-label={ui.onThisPage}
      class="sticky top-6 hidden self-start xl:col-start-3 xl:row-start-1 xl:block"
    >
      <p class="border-b border-rule pb-2 text-[0.8125rem] font-semibold text-ink">{ui.onThisPage}</p>
      <ul class="mt-2 space-y-1">
        {#each sections as section (section.id)}
          <li>
            <a
              href="#{section.id}"
              onclick={() => (active = section.id)}
              class="block border-l-2 py-1 pl-3 text-[0.8125rem] leading-snug transition-colors {active === section.id
                ? 'border-accent font-semibold text-ink'
                : 'border-rule text-ink-soft hover:border-rule-strong hover:text-ink'}"
            >
              {section.label}
            </a>
          </li>
        {/each}
      </ul>
    </aside>
  </Canvas>

  <dialog
    bind:this={dialog}
    id="research-menu"
    aria-labelledby="research-menu-title"
    onclose={syncMenuOpen}
    oncancel={() => setTimeout(syncMenuOpen, 0)}
    onclick={(event) => {
      if (event.target === event.currentTarget) closeMenu();
    }}
    class="m-0 h-dvh max-h-dvh w-[min(21rem,88vw)] max-w-none overflow-y-auto border-r border-rule bg-surface p-0 text-ink backdrop:bg-ink/40"
  >
    <div class="flex items-center justify-between border-b border-rule py-1.5 pr-3 pl-5">
      <h2 id="research-menu-title" class="text-[1.125rem] font-semibold">{ui.menuTitle}</h2>
      <button
        type="button"
        onclick={closeMenu}
        aria-label={ui.closeMenu}
        class="inline-flex h-11 min-w-11 items-center justify-center rounded-lg px-2 text-[0.9375rem] font-medium text-ink underline decoration-1 underline-offset-[0.25em] transition-colors duration-(--dur-fast) ease-out hover:bg-accent-soft"
      >
        {ui.close}
      </button>
    </div>
    <nav aria-label={paneLabel} class="px-5 py-6">
      <ul class="space-y-1">
        {#each sections as section, i (section.id)}
          <li>
            <a
              href="#{section.id}"
              onclick={closeMenu}
              class="flex items-center gap-2 rounded-lg px-2 py-2 text-[0.9375rem] text-ink-soft transition-colors hover:bg-hover hover:text-ink"
            >
              <span class="w-4 shrink-0 font-mono text-[0.75rem] text-ink-faint">{i + 1}</span>
              <span>{section.label}</span>
            </a>
          </li>
        {/each}
      </ul>
    </nav>
  </dialog>
</div>

<style>
  /* Each paper section brings its own Canvas. In the two-column shell that padding would apply twice. */
  @media (min-width: 1024px) {
    :global(.research-article > header > div:first-child),
    :global(.research-article > section > div:first-child) {
      max-width: none;
      padding-inline: 0;
    }
  }

  :global(.research-article [role='note']) {
    float: none;
    width: auto;
    margin: 1.25rem 0;
    padding: 0 0 0 0.75rem;
    border-top: 0;
    border-left: 2px solid var(--brand);
  }

  :global(html:has(#research-menu[open])) {
    overflow: hidden;
  }
</style>
