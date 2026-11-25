<script lang="ts">
  import type { Locale } from '$i18n/config';
  import { pageMetadata } from '$lib/metadata';
  import { structuredDataScript } from '$lib/structured-data';

  /**
   * Each localized page renders this once: title, description, canonical, hreflang (en, de, x-default), Open Graph,
   * Twitter card and structured data. This is the only metadata source for localized routes, keeping share cards,
   * locale and site identity consistent. `path` has no language prefix ("/" for Home, "/docs/cli" for a doc).
   * Home keeps its title; every other page gets " | MIRA" in <title>, og:title and twitter:title.
   */
  let {
    lang,
    path,
    title,
    description,
    noindex = false
  }: { lang: Locale; path: string; title: string; description: string; noindex?: boolean } = $props();

  const meta = $derived(pageMetadata(lang, path, title, description));
  const structuredData = $derived(
    structuredDataScript({
      lang,
      path,
      canonicalUrl: meta.canonicalUrl,
      title: meta.shareTitle,
      description: meta.description
    })
  );
</script>

<svelte:head>
  <title>{meta.shareTitle}</title>
  <meta name="description" content={meta.description} />
  {#if noindex}<meta name="robots" content="noindex" />{/if}
  <link rel="canonical" href={meta.canonicalUrl} />
  {#each Object.entries(meta.hreflang) as [code, href] (code)}
    <link rel="alternate" hreflang={code} {href} />
  {/each}
  <meta property="og:type" content={meta.openGraph.type} />
  <meta property="og:site_name" content={meta.openGraph.siteName} />
  <meta property="og:title" content={meta.openGraph.title} />
  <meta property="og:description" content={meta.openGraph.description} />
  <meta property="og:url" content={meta.openGraph.url} />
  <meta property="og:locale" content={meta.openGraph.locale} />
  {#each meta.openGraph.alternateLocale as alternate (alternate)}
    <meta property="og:locale:alternate" content={alternate} />
  {/each}
  <meta property="og:image" content={meta.openGraph.image.url} />
  <meta property="og:image:width" content={String(meta.openGraph.image.width)} />
  <meta property="og:image:height" content={String(meta.openGraph.image.height)} />
  <meta property="og:image:alt" content={meta.openGraph.image.alt} />
  <meta property="og:image:type" content={meta.openGraph.image.type} />
  <meta name="twitter:card" content={meta.twitter.card} />
  <meta name="twitter:title" content={meta.twitter.title} />
  <meta name="twitter:description" content={meta.twitter.description} />
  <meta name="twitter:image" content={meta.twitter.image.url} />
  <meta name="twitter:image:alt" content={meta.twitter.image.alt} />
  {@html `<script type="application/ld+json">${structuredData}</script>`}
</svelte:head>
