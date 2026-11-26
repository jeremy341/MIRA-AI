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
  import RuleList from '../RuleList.svelte';
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
</script>

<HomeSection id="status" title={t.title}>
  <div class="grid grid-cols-[minmax(0,1fr)] gap-10 md:grid-cols-2 lg:gap-16">
    <div class="min-w-0">
      <h3 class="text-[1.375rem] font-semibold text-brand-ink">{t.worksTitle}</h3>
      <RuleList items={t.works} done />
    </div>
    <div class="min-w-0">
      <h3 class="text-[1.375rem] font-semibold text-brand-ink">{t.openTitle}</h3>
      <RuleList items={t.open} done={false} />
    </div>
  </div>

  <p class="mt-8 rounded-2xl bg-tint px-5 py-4 text-[0.9375rem] leading-[1.6] text-brand-ink sm:px-7">
    <Rich text={t.planned} />
  </p>

  <div class="mt-16 grid grid-cols-[minmax(0,1fr)] gap-10 sm:mt-24 lg:grid-cols-[minmax(0,5fr)_minmax(0,7fr)] lg:gap-16">
    <div class="min-w-0">
      <h3 class="section-title text-ink">{t.whoTitle}</h3>
      <div class="mt-5 space-y-3 text-[1rem] leading-[1.65] text-ink-soft">
        <p><Rich text={t.who} /></p>
        <p><Rich text={t.transparency} /></p>
        <p><ExtLink href={LICENSE_URL} {hint}>{t.licence}</ExtLink></p>
      </div>
    </div>
    <div class="min-w-0">
      <h3 class="text-[1.375rem] font-semibold text-brand-ink">{t.linksTitle}</h3>
      <ul class="mt-4 divide-y divide-rule border-y border-rule">
        {#each links as link (link.href)}
          <li class="py-4 leading-snug">
            <ExtLink href={link.href} {hint} class="text-[1.0625rem] font-semibold">{link.name}</ExtLink>
            <span class="mt-1 block text-[0.9375rem] text-ink-soft">{link.text}</span>
          </li>
        {/each}
      </ul>
    </div>
  </div>
</HomeSection>
