<script lang="ts">
  import type { Locale } from '$i18n/config';
  import { NOT_FOUND_COPY } from '$i18n/not-found';
  import Heading from './Heading.svelte';
  import Prose from './Prose.svelte';

  /** One language of the 404 message: a serif title, one sentence and a link home. `lang` marks the text language. */
  let { lang, as = 'h1' }: { lang: Locale; as?: 'h1' | 'h2' } = $props();
  const copy = $derived(NOT_FOUND_COPY[lang]);
</script>

<section {lang} aria-labelledby="not-found-{lang}">
  <Heading id="not-found-{lang}" {as} size="display" class="text-ink">{copy.title}</Heading>
  <Prose class="mt-4"><p>{copy.text}</p></Prose>
  <p class="mt-6">
    <a href="/{lang}" class="btn btn-lg btn-secondary px-1">{copy.home}</a>
  </p>
</section>
