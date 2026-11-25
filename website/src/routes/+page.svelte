<script lang="ts">
  import { onMount } from 'svelte';
  import { pickLocale } from '$i18n/config';
  import { de } from '$i18n/de';
  import { en } from '$i18n/en';
  import { SITE_URL } from '$lib/site';

  /**
   * "/" sends the visitor to the first supported language in the browser's language list (pickLocale), else to
   * /en. The redirect is client side (a static site has no server). Without JavaScript, or while it runs, the page
   * shows both languages as plain links. `replace` keeps "/" out of the history.
   */
  onMount(() => {
    // navigator.languages is the whole preference list ("en-US" first, "de" second still works); older browsers
    // only have navigator.language.
    const target = pickLocale(navigator.languages?.length ? navigator.languages : [navigator.language]);
    window.location.replace(`/${target}`);
  });
</script>

<svelte:head>
  <title>MIRA</title>
  <meta name="description" content="MIRA: Machine Intelligence for Recycling Automation. English / Deutsch." />
  <link rel="canonical" href="{SITE_URL}/" />
  <link rel="alternate" hreflang="en" href="{SITE_URL}/en" />
  <link rel="alternate" hreflang="de" href="{SITE_URL}/de" />
  <link rel="alternate" hreflang="x-default" href="{SITE_URL}/" />
</svelte:head>

<main class="mx-auto flex min-h-dvh max-w-[34rem] flex-col justify-center gap-6 px-5 py-12">
  <h1 class="font-serif text-hero text-ink"><span class="marker">MIRA</span></h1>
  <p class="font-serif text-lede text-ink-soft">
    <span lang="en">{en.redirect.message}</span> / <span lang="de">{de.redirect.message}</span>
  </p>
  <ul class="space-y-1 text-[1.125rem]">
    <li><a href="/en" lang="en" hreflang="en" class="nb-link inline-block py-2">English</a></li>
    <li><a href="/de" lang="de" hreflang="de" class="nb-link inline-block py-2">Deutsch</a></li>
  </ul>
  <noscript>
    <p lang="en" class="text-[0.875rem] text-muted-foreground">
      JavaScript is off, so the language is not chosen automatically. Please pick a link above.
    </p>
    <p lang="de" class="mt-2 text-[0.875rem] text-muted-foreground">
      JavaScript ist ausgeschaltet, deshalb wird die Sprache nicht automatisch gewählt. Bitte einen Link oben wählen.
    </p>
  </noscript>
</main>
