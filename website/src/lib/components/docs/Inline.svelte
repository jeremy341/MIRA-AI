<script lang="ts">
  import { getDictionary } from '$i18n';
  import { localePath, type Locale } from '$i18n/config';
  import { parseInline } from '$lib/docs-content';
  import { splitNoBreak } from '$lib/rich';

  /**
   * Renders the small inline markup used in docs content: `code`, **bold** and [label](href).
   * Internal links get the language prefix; external links open in a new tab and say so to assistive tech.
   * The parser returns plain data, so no HTML is ever injected. Docs use `**bold**`, which Rich does not know,
   * and code spans with a grey wash, so this stays a local component.
   */
  let { text, lang }: { text: string; lang: Locale } = $props();

  const tokens = $derived(parseInline(text));
  const hint = $derived(getDictionary(lang).common.opensInNewTab);
</script>

{#each tokens as token}{#if token.type === 'text'}{token.value}{:else if token.type === 'code'}<code class="rounded bg-sunken px-1 py-px font-mono text-[0.875em] text-ink [overflow-wrap:anywhere]">{#each splitNoBreak(token.value) as word}{#if word.nowrap}<span class="whitespace-nowrap">{word.text}</span>{:else}{word.text}{/if}{/each}</code>{:else if token.type === 'bold'}<strong class="font-semibold text-ink">{token.value}</strong>{:else if token.href.startsWith('/')}<a href={localePath(lang, token.href)} class="nb-link text-ink">{token.label}</a>{:else if token.href.startsWith('#')}<a href={token.href} class="nb-link text-ink">{token.label}</a>{:else}<a href={token.href} target="_blank" rel="noopener noreferrer" class="nb-link text-ink">{token.label}<span class="sr-only"> {hint}</span></a>{/if}{/each}
