<script lang="ts">
  import type { Dictionary } from '$i18n';
  import { fmt } from '$i18n/format';
  import {
    DATASET_ORIGINS_URL,
    EXPERIMENT_LOG_URL,
    GITHUB_URL,
    HF_URL,
    LICENSE_URL,
    PYPI_LATEST_VERSION,
    PYPI_URL
  } from '$lib/site';
  import Chapter from '../Chapter.svelte';
  import ExtLink from '../ExtLink.svelte';
  import Prose from '../Prose.svelte';
  import Rich from '../Rich.svelte';

  let { dict }: { dict: Dictionary } = $props();

  const t = $derived(dict.home.status);
  const hint = $derived(dict.common.opensInNewTab);
  const links = $derived([
    { href: GITHUB_URL, name: t.links.github.name, text: t.links.github.text },
    { href: PYPI_URL, name: t.links.pypi.name, text: fmt(t.links.pypi.text, { version: PYPI_LATEST_VERSION }) },
    { href: HF_URL, name: t.links.huggingface.name, text: t.links.huggingface.text },
    { href: DATASET_ORIGINS_URL, name: t.links.datasets.name, text: t.links.datasets.text },
    { href: EXPERIMENT_LOG_URL, name: t.links.log.name, text: t.links.log.text }
  ]);
</script>

{#snippet bullets(items: readonly string[])}
  <ul class="space-y-2.5 text-[1.0625rem] leading-snug text-ink-soft marker:text-ink">
    {#each items as item (item)}
      <li class="ml-5 list-disc pl-1"><Rich text={item} /></li>
    {/each}
  </ul>
{/snippet}

<Chapter id="status" title={t.title}>
  <div class="grid gap-10 md:grid-cols-2 md:gap-16">
    <div>
      <h3 class="font-serif text-title text-ink">{t.worksTitle}</h3>
      <div class="mt-4">{@render bullets(t.works)}</div>
    </div>
    <div>
      <h3 class="font-serif text-title text-ink">{t.openTitle}</h3>
      <div class="mt-4">{@render bullets(t.open)}</div>
    </div>
  </div>

  <Prose class="mt-10 border-t border-rule pt-8">
    <p><Rich text={t.planned} /></p>
  </Prose>

  <div class="mt-10 grid gap-10 border-t border-ink pt-8 lg:grid-cols-[minmax(0,6fr)_minmax(0,6fr)] lg:gap-16">
    <div>
      <h3 class="font-serif text-title text-ink">{t.whoTitle}</h3>
      <Prose class="mt-3">
        <p><Rich text={t.who} /></p>
        <p><Rich text={t.transparency} /></p>
        <p><ExtLink href={LICENSE_URL} {hint}>{t.licence}</ExtLink></p>
      </Prose>
    </div>
    <div>
      <h3 class="font-serif text-title text-ink">{t.linksTitle}</h3>
      <ul class="mt-3 space-y-3.5">
        {#each links as link (link.href)}
          <li class="text-[0.9375rem] leading-snug">
            <ExtLink href={link.href} {hint} class="font-medium">{link.name}</ExtLink>
            <span class="block text-ink-soft">{link.text}</span>
          </li>
        {/each}
      </ul>
    </div>
  </div>
</Chapter>
