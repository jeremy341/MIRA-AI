<script lang="ts">
  import type { Dictionary } from '$i18n';
  import { localePath, type Locale } from '$i18n/config';
  import { fmt } from '$i18n/format';
  import type { PackageCopy } from '$i18n/package';
  import { GITHUB_URL, HF_URL, LICENSE_URL, PYPI_LATEST_VERSION, PYPI_URL } from '$lib/site';
  import Chapter from '../Chapter.svelte';
  import DownloadsStat from '../DownloadsStat.svelte';
  import ExtLink from '../ExtLink.svelte';

  /** Where everything is: three external sites, Docs and Research, the licence, and the live download figure. */
  let { lang, dict, t }: { lang: Locale; dict: Dictionary; t: PackageCopy } = $props();

  const l = $derived(t.links);
  const hint = $derived(dict.common.opensInNewTab);
  const external = $derived([
    { key: 'pypi', href: PYPI_URL, name: l.items.pypi.name, text: fmt(l.items.pypi.text, { version: PYPI_LATEST_VERSION }) },
    { key: 'github', href: GITHUB_URL, name: l.items.github.name, text: l.items.github.text },
    { key: 'huggingface', href: HF_URL, name: l.items.huggingface.name, text: l.items.huggingface.text }
  ]);
  const internal = $derived([
    { key: 'docs', href: localePath(lang, '/docs'), name: l.items.docs.name, text: l.items.docs.text },
    { key: 'research', href: localePath(lang, '/research'), name: l.items.research.name, text: l.items.research.text }
  ]);
</script>

<Chapter id="links" title={l.title}>
  <div class="max-w-[44rem] min-w-0">
    <h3 class="font-serif text-title text-ink">{l.listTitle}</h3>
    <ul class="mt-4 border-t border-ink">
      {#each external as link (link.key)}
        <li class="border-b border-rule py-3 text-[0.9375rem] leading-snug">
          <ExtLink href={link.href} {hint} class="font-medium">{link.name}</ExtLink>
          <span class="block text-ink-soft">{link.text}</span>
          {#if link.key === 'huggingface'}
            <DownloadsStat {lang} labels={l.downloads} />
          {/if}
        </li>
      {/each}
      {#each internal as link (link.key)}
        <li class="border-b border-rule py-3 text-[0.9375rem] leading-snug">
          <a href={link.href} class="nb-link font-medium">{link.name}</a>
          <span class="block text-ink-soft">{link.text}</span>
        </li>
      {/each}
      <li class="border-b border-rule py-3 text-[0.9375rem] leading-snug">
        <ExtLink href={LICENSE_URL} {hint} class="font-medium">{l.items.licence.name}</ExtLink>
        <span class="block text-ink-soft">{l.items.licence.text}</span>
      </li>
    </ul>
  </div>
</Chapter>
