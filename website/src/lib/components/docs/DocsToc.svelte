<script lang="ts">
  import type { TocItem } from './types';

  /**
   * "On this page", pinned on the right from xl: every section with its sub-headings. The heading nearest the
   * top of the viewport is the current one (aria-current="location") and gets a filled row.
   */
  let { items, label }: { items: TocItem[]; label: string } = $props();

  let activeId = $state<string | null>(null);

  $effect(() => {
    activeId = items[0]?.id ?? null;
    const elements = items
      .map((item) => document.getElementById(item.id))
      .filter((element): element is HTMLElement => element !== null);
    if (elements.length === 0 || typeof IntersectionObserver === 'undefined') return;

    const visible = new Set<string>();
    const observer = new IntersectionObserver(
      (entries) => {
        for (const entry of entries) {
          if (entry.isIntersecting) visible.add(entry.target.id);
          else visible.delete(entry.target.id);
        }
        const first = items.find((item) => visible.has(item.id));
        if (first) activeId = first.id;
      },
      // The band from just under the top bar to the upper third of the viewport.
      { rootMargin: '-72px 0px -65% 0px' }
    );
    elements.forEach((element) => observer.observe(element));
    return () => observer.disconnect();
  });
</script>

{#if items.length >= 2}
  <nav
    aria-label={label}
    class="sticky top-20 hidden max-h-[calc(100dvh-6rem)] w-[14rem] self-start overflow-y-auto pb-8 xl:block"
  >
    <p class="mb-2 px-2.5 text-[0.9375rem] font-semibold text-ink">{label}</p>
    <ul>
      {#each items as item (item.id)}
        {@const current = item.id === activeId}
        <li>
          <a
            href="#{item.id}"
            aria-current={current ? 'location' : undefined}
            class="block rounded-lg px-2.5 py-1.5 text-[0.875rem] leading-[1.35] transition-colors duration-(--dur-fast) ease-out {item.level === 3
              ? 'ml-3'
              : ''} {current ? 'bg-sunken font-semibold text-ink' : 'text-ink-soft hover:text-ink'}"
          >
            {item.title}
          </a>
        </li>
      {/each}
    </ul>
  </nav>
{/if}
