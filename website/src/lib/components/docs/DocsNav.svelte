<script lang="ts">
  import { page } from '$app/state';
  import { localePath, stripLocale, type Locale } from '$i18n/config';
  import { docPath, slugFromPathname } from '$lib/docs-content';
  import type { NavGroup } from './types';

  const ITEM =
    '-ml-px block border-l-2 py-2 pr-2 pl-3 text-[0.9375rem] leading-5 transition-colors duration-(--dur-fast) ease-out hover:bg-marker lg:py-1.5';

  /**
   * Documentation navigation: group labels in small capitals, the pages as a plain list with a hairline
   * on the left. The current page has an ink rule and aria-current. No pills, no cards.
   */
  let {
    lang,
    label,
    overview,
    groups,
    onNavigate
  }: {
    lang: Locale;
    label: string;
    overview: string;
    groups: NavGroup[];
    /** Called after a link is chosen, e.g. to close the mobile drawer. */
    onNavigate?: () => void;
  } = $props();

  const pathname = $derived(stripLocale(page.url.pathname));
  const currentSlug = $derived(slugFromPathname(pathname));
  const onIndex = $derived(/^\/docs\/?$/.test(pathname));
  const tone = (active: boolean) => (active ? 'border-ink font-semibold text-ink' : 'border-transparent text-ink-soft');
</script>

<nav aria-label={label}>
  <ul class="space-y-7">
    <li>
      <ul class="border-l border-rule">
        <li>
          <a
            href={localePath(lang, '/docs')}
            aria-current={onIndex ? 'page' : undefined}
            onclick={onNavigate}
            class="{ITEM} {tone(onIndex)}"
          >
            {overview}
          </a>
        </li>
      </ul>
    </li>
    {#each groups as group (group.id)}
      <li>
        <p class="mb-1.5 text-[0.75rem] leading-5 font-semibold tracking-[0.08em] text-muted-foreground uppercase">
          {group.label}
        </p>
        <ul class="border-l border-rule">
          {#each group.pages as item (item.slug)}
            {@const active = item.slug === currentSlug}
            <li>
              <a
                href={localePath(lang, docPath(item.slug))}
                aria-current={active ? 'page' : undefined}
                onclick={onNavigate}
                class="{ITEM} {tone(active)}"
              >
                {item.title}
              </a>
            </li>
          {/each}
        </ul>
      </li>
    {/each}
  </ul>
</nav>
