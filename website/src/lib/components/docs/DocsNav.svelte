<script lang="ts">
  import { page } from '$app/state';
  import { localePath, stripLocale, type Locale } from '$i18n/config';
  import { fmt } from '$i18n/format';
  import type { DocsUi } from '$i18n/docs/ui';
  import DocIcon from './DocIcon.svelte';
  import { docIcon } from './labels';
  import type { NavGroup } from './types';

  /**
   * Docs sidebar navigation, in the style of Orchard's docs: a filter box, then groups with small
   * headings. Each page has an icon; the current page is a filled row and opens its own sections
   * underneath. Typing in the filter narrows the list across all groups.
   */
  let {
    lang,
    ui,
    groups,
    base = '/docs',
    onNavigate
  }: {
    lang: Locale;
    ui: DocsUi;
    groups: NavGroup[];
    /** Path of the section the list belongs to: the docs or the research report. */
    base?: string;
    /** Called after a link is chosen, e.g. to close the mobile drawer. */
    onNavigate?: () => void;
  } = $props();

  const pathname = $derived(stripLocale(page.url.pathname));
  const currentSlug = $derived.by(() => {
    if (!pathname.startsWith(`${base}/`)) return undefined;
    const rest = pathname.slice(base.length + 1).replace(/\/$/, '');
    return rest && !rest.includes('/') ? rest : undefined;
  });
  const onIndex = $derived(pathname === base || pathname === `${base}/`);
  const sections = $derived(
    (page.data as { doc?: { slug: string; sections: { id: string; title: string }[] } }).doc ?? null
  );

  let filter = $state('');
  const needle = $derived(filter.trim().toLowerCase());
  const visible = $derived(
    groups
      .map((group) => ({
        ...group,
        pages: needle ? group.pages.filter((item) => item.title.toLowerCase().includes(needle)) : group.pages
      }))
      .filter((group) => group.pages.length > 0)
  );

  // Groups can be folded by hand. The group of the current page and every group while filtering stay open.
  let folded = $state<Record<string, boolean>>({});
  const isOpen = (group: NavGroup) =>
    needle !== '' || group.pages.some((item) => item.slug === currentSlug) || !folded[group.id];

  let filterInput = $state<HTMLInputElement>();
  function onWindowKeydown(event: KeyboardEvent) {
    if (event.key !== '/' || event.altKey || event.ctrlKey || event.metaKey) return;
    const target = event.target as HTMLElement | null;
    if (target && (target.tagName === 'INPUT' || target.tagName === 'TEXTAREA' || target.isContentEditable)) return;
    if (!filterInput || filterInput.offsetParent === null) return;
    event.preventDefault();
    filterInput.focus();
  }

  const row =
    'flex min-h-9 items-center gap-2.5 rounded-lg px-2.5 py-1.5 text-[0.9375rem] leading-5 transition-colors duration-(--dur-fast) ease-out';
  const rowTone = (active: boolean) =>
    active ? 'bg-brand font-semibold text-white' : 'text-ink-soft hover:bg-tint hover:text-brand-ink';
</script>

<svelte:window onkeydown={onWindowKeydown} />

<div class="relative">
  <label for="docs-filter" class="sr-only">{ui.filterSidebar}</label>
  <input
    bind:this={filterInput}
    bind:value={filter}
    id="docs-filter"
    type="text"
    autocomplete="off"
    spellcheck={false}
    placeholder={ui.filterSidebar}
    class="h-10 w-full rounded-lg border border-rule bg-sunken/70 pr-8 pl-3 text-[0.9375rem] text-ink placeholder:text-muted-foreground focus-visible:border-accent"
  />
  {#if !filter}
    <kbd
      aria-hidden="true"
      class="pointer-events-none absolute top-1/2 right-2.5 hidden -translate-y-1/2 font-mono text-[0.75rem] text-muted-foreground lg:block"
    >
      /
    </kbd>
  {/if}
</div>

<nav aria-label={ui.navLabel} class="mt-4">
  {#if !needle}
    <a
      href={localePath(lang, base)}
      aria-current={onIndex ? 'page' : undefined}
      onclick={onNavigate}
      class="{row} {rowTone(onIndex)}"
    >
      <DocIcon name="home" size={18} />
      {ui.overview}
    </a>
  {/if}

  {#each visible as group (group.id)}
    {@const open = isOpen(group)}
    <div class="mt-5">
      <button
        type="button"
        aria-expanded={open}
        aria-label={fmt(ui.toggleGroup, { title: group.label })}
        onclick={() => (folded[group.id] = open)}
        class="flex w-full items-center justify-between px-2.5 py-1 text-left text-[0.8125rem] font-semibold text-muted-foreground hover:text-ink"
      >
        {group.label}
        <svg
          viewBox="0 0 12 12"
          width="0.625rem"
          height="0.625rem"
          fill="none"
          stroke="currentColor"
          stroke-width="1.6"
          stroke-linecap="round"
          aria-hidden="true"
          class="transition-transform duration-(--dur-fast) {open ? '' : '-rotate-90'}"
        >
          <path d="m2.5 4.5 3.5 3.5 3.5-3.5" />
        </svg>
      </button>

      {#if open}
        <ul class="mt-1 space-y-0.5">
          {#each group.pages as item (item.slug)}
            {@const active = item.slug === currentSlug}
            <li>
              <a
                href={localePath(lang, `${base}/${item.slug}`)}
                aria-current={active ? 'page' : undefined}
                onclick={onNavigate}
                class="{row} {rowTone(active)}"
              >
                <DocIcon name={docIcon(item.slug)} size={18} />
                {item.title}
              </a>
              {#if active && sections && sections.slug === item.slug && sections.sections.length > 1}
                <ul class="mt-0.5 mb-1 ml-[1.375rem] space-y-0.5 border-l border-rule pl-2.5">
                  {#each sections.sections as section (section.id)}
                    <li>
                      <a
                        href="#{section.id}"
                        onclick={onNavigate}
                        class="block rounded-md px-2 py-1 text-[0.875rem] leading-5 text-ink-soft hover:bg-hover/60 hover:text-ink"
                      >
                        {section.title}
                      </a>
                    </li>
                  {/each}
                </ul>
              {/if}
            </li>
          {/each}
        </ul>
      {/if}
    </div>
  {/each}

  {#if needle && visible.length === 0}
    <p class="px-2.5 py-3 text-[0.9375rem] text-ink-soft">{ui.noMatches}</p>
  {/if}
</nav>
