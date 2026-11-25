<script lang="ts">
  import { getDictionary } from '$i18n';
  import SiteFooter from '$lib/components/SiteFooter.svelte';
  import SiteHeader from '$lib/components/SiteHeader.svelte';

  let { data, children } = $props();

  const lang = $derived(data.lang);
  const dict = $derived(getDictionary(lang));

  // The static HTML already carries the right <html lang> (hooks.server.ts). After a client side switch between
  // /en and /de the document is reused, so the attribute is updated here.
  $effect(() => {
    document.documentElement.lang = lang;
  });
</script>

<svelte:head>
  <meta name="application-name" content={dict.meta.siteName} />
  <meta name="keywords" content="MIRA, YOLO11n, recycling, waste detection, Jugend forscht, mira-ai" />
</svelte:head>

<a href="#main" class="skip-link">{dict.common.skipToContent}</a>
<SiteHeader {lang} {dict} />
<main id="main" tabindex="-1" class="outline-none">
  {@render children()}
</main>
<SiteFooter {lang} {dict} />
