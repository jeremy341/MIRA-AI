<script lang="ts">
  import type { TocItem } from './types';

  /**
   * "On this page": a slim list for wide screens, sections with their sub-headings. The link for the
   * heading currently near the top of the viewport gets aria-current="location" and an ink rule.
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
      // The band from just under the top edge to the upper third of the viewport.
      { rootMargin: '-40px 0px -65% 0px' }
    );
    elements.forEach((element) => observer.observe(element));
    return () => observer.disconnect();
  });
</script>

{#if items.length >= 2}
  <nav
    aria-label={label}
    class="sticky top-6 hidden max-h-[calc(100dvh-3rem)] self-start overflow-y-auto py-12 xl:col-start-3 xl:row-start-1 xl:block"
  >
    <p class="mb-2 text-[0.75rem] leading-5 font-semibold tracking-[0.08em] text-muted-foreground uppercase">{label}</p>
    <ul class="border-l border-rule">
      {#each items as item (item.id)}
        {@const current = item.id === activeId}
        <li>
          <a
            href="#{item.id}"
            aria-current={current ? 'location' : undefined}
            class="-ml-px block border-l-2 py-1.5 pr-2 text-[0.8125rem] leading-[1.35] transition-colors duration-(--dur-fast) ease-out hover:bg-marker {item.level === 3
              ? 'pl-6'
              : 'pl-3'} {current ? 'border-ink font-semibold text-ink' : 'border-transparent text-ink-soft'}"
          >
            {item.title}
          </a>
        </li>
      {/each}
    </ul>
  </nav>
{/if}
