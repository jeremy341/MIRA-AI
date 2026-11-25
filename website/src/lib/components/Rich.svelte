<script lang="ts">
  import { page } from '$app/state';
  import { isLocale, localePath, type Locale } from '$i18n/config';
  import { parseRich } from '$lib/rich';

  /**
   * Renders the small inline markup used in dictionary strings: ==marker==, `code` and [label](href).
   * Internal links ("/research") get the language prefix (from `lang`, else from the current URL).
   * Experiment ids (EXP-019), `mira-ai` and every word inside a code span stay on one line.
   * The parser returns plain data, so no HTML is ever injected.
   */
  let { text, lang }: { text: string; lang?: Locale } = $props();

  const parts = $derived(parseRich(text));
  const currentLang = $derived<Locale>(lang ?? (isLocale(page.params.lang) ? page.params.lang : 'en'));
</script>

{#each parts as part}{#if part.kind === 'text'}{part.text}{:else if part.kind === 'mark'}<span class="marker">{part.text}</span>{:else if part.kind === 'code'}<code class="font-mono text-[0.9em] text-ink">{#each part.words as word}{#if word.nowrap}<span class="whitespace-nowrap">{word.text}</span>{:else}{word.text}{/if}{/each}</code>{:else if part.kind === 'nobreak'}<span class="whitespace-nowrap">{part.text}</span>{:else if part.internal}<a href={localePath(currentLang, part.href)} class="nb-link">{part.text}</a>{:else}<a href={part.href} target="_blank" rel="noopener noreferrer" class="nb-link">{part.text}</a>{/if}{/each}
