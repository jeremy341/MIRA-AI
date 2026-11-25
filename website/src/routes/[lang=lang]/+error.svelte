<script lang="ts">
  import { page } from '$app/state';
  import { isLocale } from '$i18n/config';
  import Canvas from '$lib/components/Canvas.svelte';
  import NotFoundView from '$lib/components/NotFoundView.svelte';

  // `notFound` inside a language: header and footer stay (this file renders inside the language layout), the message
  // is in that language.
  const lang = $derived(isLocale(page.params.lang) ? page.params.lang : 'en');
</script>

<svelte:head>
  <meta name="robots" content="noindex" />
</svelte:head>

<Canvas class="py-16 sm:py-24">
  <NotFoundView {lang} />
</Canvas>
