<script lang="ts">
  import { onMount } from 'svelte';
  import { afterNavigate } from '$app/navigation';
  import { page } from '$app/state';
  import { LOCALES, switchLocalePath, type Locale } from '$i18n/config';
  import { fmt } from '$i18n/format';

  /**
   * Two links, EN and DE, to the SAME page in the other language, keeping the #section the visitor is at. The
   * current language is marked with aria-current and an ink underline (the marker is kept for the wordmark and one
   * key number). Each link carries `lang` and `hreflang` so screen readers pronounce it correctly.
   */
  let {
    lang,
    label,
    names,
    switchTo,
    class: className = ''
  }: {
    lang: Locale;
    /** Accessible name of the group, e.g. "Language". */
    label: string;
    names: Record<Locale, string>;
    /** Contains {language}, e.g. "Switch to {language}". */
    switchTo: string;
    class?: string;
  } = $props();

  // The static HTML has no fragment; the real one is read after hydration, on every hashchange and after every
  // client side navigation.
  let hash = $state('');
  onMount(() => {
    const update = () => (hash = window.location.hash);
    update();
    window.addEventListener('hashchange', update);
    return () => window.removeEventListener('hashchange', update);
  });
  afterNavigate(() => {
    hash = window.location.hash;
  });
</script>

<nav aria-label={label} class="flex items-center text-[0.875rem] {className}">
  <ul class="flex items-center gap-1">
    {#each LOCALES as locale (locale)}
      {@const current = locale === lang}
      <li>
        <a
          href="{switchLocalePath(page.url.pathname, locale)}{hash}"
          lang={locale}
          hreflang={locale}
          aria-current={current ? 'true' : undefined}
          aria-label={current ? names[locale] : fmt(switchTo, { language: names[locale] })}
          class="inline-flex min-h-11 min-w-9 items-center justify-center border-b-2 px-1.5 font-mono text-[0.8125rem] tracking-wide uppercase sm:min-h-9 {current
            ? 'border-ink font-semibold text-ink'
            : 'border-transparent text-ink-soft hover:bg-marker'}"
        >
          {locale}
        </a>
      </li>
    {/each}
  </ul>
</nav>
