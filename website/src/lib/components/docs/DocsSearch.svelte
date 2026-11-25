<script lang="ts">
  import { goto } from '$app/navigation';
  import { localePath, type Locale } from '$i18n/config';
  import type { DocsUi } from '$i18n/docs/ui';
  import { fmt } from '$i18n/format';
  import { loadSearchIndex, searchDocs, type SearchEntry, type SearchResult } from '$lib/docs-content';
  import { isSearchShortcut, MIN_QUERY_LENGTH, moveActive, searchStatus, splitTryHint } from './search-logic';

  /**
   * Client-side search over every page, heading and paragraph of the docs in the CURRENT language.
   * The text of that language loads on first focus, so a page that is only read costs nothing.
   * ARIA combobox with a listbox popup. `Alt+/` focuses the visible search (a chord, so it never fires while
   * someone types; WCAG 2.1.4), Arrow keys move through results, Enter opens the active one, Escape closes the
   * results first and clears the box second.
   */
  let {
    lang,
    ui,
    class: className = ''
  }: { lang: Locale; ui: DocsUi; class?: string } = $props();

  const labels = $derived(ui.search);
  const baseId = $props.id();
  const listId = `${baseId}-results`;

  let input = $state<HTMLInputElement>();
  let root = $state<HTMLDivElement>();

  // The index belongs to the language it was built for, so a client side switch from /en to /de never searches stale text.
  let loaded = $state<{ lang: Locale; entries: SearchEntry[] } | null>(null);
  let query = $state('');
  let open = $state(false);
  let active = $state(0);

  const index = $derived(loaded && loaded.lang === lang ? loaded.entries : null);

  function ensureIndex() {
    if (index) return;
    const requested = lang;
    loadSearchIndex(requested).then(
      (entries) => (loaded = { lang: requested, entries }),
      () => (loaded = { lang: requested, entries: [] })
    );
  }

  const trimmed = $derived(query.trim());
  const searching = $derived(trimmed.length >= MIN_QUERY_LENGTH);
  const results = $derived(searching && index ? searchDocs(trimmed, index) : []);
  const expanded = $derived(open && searching && index !== null);
  const status = $derived(searchStatus(labels, query, results.length, index !== null));
  const hint = $derived(splitTryHint(labels.tryHint));

  function onWindowKeydown(event: KeyboardEvent) {
    if (!isSearchShortcut(event)) return;
    // Two searches exist (sidebar and mobile bar), only one is displayed.
    if (!input || input.offsetParent === null) return;
    event.preventDefault();
    input.focus();
    input.select();
  }

  function go(result: SearchResult) {
    open = false;
    query = '';
    input?.blur();
    goto(localePath(lang, result.entry.href));
  }

  function onKeydown(event: KeyboardEvent) {
    if (event.key === 'ArrowDown') {
      if (!searching) return;
      event.preventDefault();
      if (!open) {
        open = true;
        return;
      }
      active = moveActive(active, 1, results.length);
    } else if (event.key === 'ArrowUp') {
      if (!searching) return;
      event.preventDefault();
      active = moveActive(active, -1, results.length);
    } else if (event.key === 'Enter') {
      if (expanded && results[active]) {
        event.preventDefault();
        go(results[active]);
      }
    } else if (event.key === 'Escape') {
      if (expanded) {
        event.preventDefault();
        open = false;
      } else if (query) {
        event.preventDefault();
        query = '';
      }
    }
  }

  function onFocusout(event: FocusEvent) {
    if (!root?.contains(event.relatedTarget as Node | null)) open = false;
  }
</script>

<svelte:window onkeydown={onWindowKeydown} />

<!-- svelte-ignore a11y_no_static_element_interactions -->
<div bind:this={root} role="search" class="relative min-w-0 flex-1 {className}" onfocusout={onFocusout}>
  <label for="{baseId}-input" class="sr-only">{labels.label}</label>
  <input
    bind:this={input}
    id="{baseId}-input"
    type="text"
    role="combobox"
    autocomplete="off"
    autocorrect="off"
    autocapitalize="none"
    spellcheck={false}
    enterkeyhint="search"
    aria-autocomplete="list"
    aria-expanded={expanded}
    aria-controls={expanded && results.length ? listId : undefined}
    aria-activedescendant={expanded && results[active] ? `${baseId}-opt-${active}` : undefined}
    aria-keyshortcuts="Control+K Meta+K Alt+/"
    placeholder={labels.placeholder}
    value={query}
    oninput={(event) => {
      ensureIndex();
      query = event.currentTarget.value;
      active = 0;
      open = true;
    }}
    onfocus={() => {
      ensureIndex();
      open = true;
    }}
    onkeydown={onKeydown}
    class="h-10 w-full rounded-lg border border-rule bg-surface pr-14 pl-9 text-base text-ink shadow-[var(--shadow-raised)] transition-colors placeholder:text-muted-foreground focus-visible:border-accent lg:text-[0.9375rem]"
  />
  <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" aria-hidden="true" class="pointer-events-none absolute top-1/2 left-3 -translate-y-1/2 text-muted-foreground"><circle cx="11" cy="11" r="6.5" /><path d="m16 16 4 4" /></svg>
  {#if !query}
    <kbd
      aria-hidden="true"
      class="pointer-events-none absolute top-1/2 right-2.5 hidden h-5 -translate-y-1/2 items-center justify-center rounded border border-rule px-1.5 font-mono text-[0.6875rem] text-muted-foreground sm:inline-flex"
    >
      Ctrl K
    </kbd>
  {/if}

  <div role="status" aria-live="polite" class="sr-only">{status}</div>

  {#if expanded}
    <div
      class="fixed inset-x-4 top-[4.25rem] z-50 max-h-[min(26rem,70dvh)] overflow-y-auto rounded-xl border border-rule bg-surface shadow-[var(--shadow-overlay)] sm:inset-x-8 lg:absolute lg:inset-x-auto lg:right-0 lg:top-[calc(100%+0.375rem)] lg:w-[26rem]"
    >
      {#if results.length === 0}
        <p class="px-4 py-4 text-[0.9375rem] leading-6 text-ink-soft">
          {fmt(labels.noResults, { query: trimmed })} {hint.head}<code class="font-mono text-[0.875em] text-ink">{labels.hintFlag}</code
          >{hint.middle}{labels.hintWords}{hint.tail}
        </p>
      {:else}
        <ul id={listId} role="listbox" aria-label={labels.results}>
          {#each results as result, position (result.entry.href)}
            <!-- Options are driven from the input (aria-activedescendant); the click is the pointer path to the same action. -->
            <!-- svelte-ignore a11y_click_events_have_key_events -->
            <li
              id="{baseId}-opt-{position}"
              role="option"
              aria-selected={position === active}
              onmousedown={(event) => event.preventDefault()}
              onmousemove={() => (active = position)}
              onclick={() => go(result)}
              class="cursor-pointer border-b border-rule px-4 py-3 last:border-b-0 aria-selected:bg-marker/40"
            >
              <div class="flex items-baseline justify-between gap-3">
                <span class="min-w-0 truncate font-serif text-[1.0625rem] font-medium text-ink">
                  {result.entry.kind === 'page' ? result.entry.pageTitle : result.entry.heading}
                </span>
                <span class="shrink-0 text-[0.75rem] text-muted-foreground">
                  {result.entry.kind === 'page' ? ui.groups[result.entry.group] : result.entry.pageTitle}
                </span>
              </div>
              <p class="mt-1 line-clamp-2 text-[0.8125rem] leading-5 text-ink-soft [overflow-wrap:anywhere]">
                {#if result.matchRange}{result.snippet.slice(0, result.matchRange[0])}<mark class="bg-marker/70 px-px text-ink">{result.snippet.slice(result.matchRange[0], result.matchRange[1])}</mark>{result.snippet.slice(result.matchRange[1])}{:else}{result.snippet}{/if}
              </p>
            </li>
          {/each}
        </ul>
      {/if}
    </div>
  {/if}
</div>
