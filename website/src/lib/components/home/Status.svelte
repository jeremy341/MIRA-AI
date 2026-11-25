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
  import ExtLink from '../ExtLink.svelte';
  import Rich from '../Rich.svelte';
  import HomeSection from './HomeSection.svelte';

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

  const card = 'rounded-2xl border border-rule bg-surface p-5 shadow-[var(--shadow-raised)] sm:p-7';
</script>

{#snippet bullets(items: readonly string[])}
  <ul class="space-y-2.5 text-[0.9375rem] leading-snug text-ink-soft marker:text-ink">
    {#each items as item (item)}
      <li class="ml-5 list-disc pl-1"><Rich text={item} /></li>
    {/each}
  </ul>
{/snippet}

<HomeSection id="status" title={t.title}>
  <div class="grid grid-cols-[minmax(0,1fr)] gap-3 md:grid-cols-2">
    <div class={card}>
      <h3 class="text-[1.0625rem] font-semibold text-ink">{t.worksTitle}</h3>
      <div class="mt-4">{@render bullets(t.works)}</div>
    </div>
    <div class={card}>
      <h3 class="text-[1.0625rem] font-semibold text-ink">{t.openTitle}</h3>
      <div class="mt-4">{@render bullets(t.open)}</div>
    </div>
  </div>

  <p class="mt-3 rounded-2xl border border-accent/25 bg-accent-soft px-5 py-4 text-[0.9375rem] leading-[1.6] text-ink/85 sm:px-7">
    <Rich text={t.planned} />
  </p>

  <div class="mt-3 grid grid-cols-[minmax(0,1fr)] gap-3 lg:grid-cols-2">
    <div class={card}>
      <h3 class="text-[1.0625rem] font-semibold text-ink">{t.whoTitle}</h3>
      <div class="mt-3 space-y-3 text-[0.9375rem] leading-[1.6] text-ink-soft">
        <p><Rich text={t.who} /></p>
        <p><Rich text={t.transparency} /></p>
        <p><ExtLink href={LICENSE_URL} {hint}>{t.licence}</ExtLink></p>
      </div>
    </div>
    <div class={card}>
      <h3 class="text-[1.0625rem] font-semibold text-ink">{t.linksTitle}</h3>
      <ul class="mt-3 divide-y divide-rule">
        {#each links as link (link.href)}
          <li class="py-2.5 text-[0.9375rem] leading-snug first:pt-0 last:pb-0">
            <ExtLink href={link.href} {hint} class="font-medium">{link.name}</ExtLink>
            <span class="block text-ink-soft">{link.text}</span>
          </li>
        {/each}
      </ul>
    </div>
  </div>
</HomeSection>
