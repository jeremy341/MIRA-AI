<script lang="ts">
  import { localePath, type Locale } from '$i18n/config';
  import type { Dictionary } from '$i18n';
  import { GITHUB_URL, HF_URL, INSTALL_COMMAND, NAV_ITEMS, PYPI_URL } from '$lib/site';
  import CopyCommand from './CopyCommand.svelte';
  import ExtLink from './ExtLink.svelte';
  import Wave from './Wave.svelte';

  /** The closing band repeats the title with the install command, then the links and a large wordmark. */
  let { lang, dict }: { lang: Locale; dict: Dictionary } = $props();
  const hint = $derived(dict.common.opensInNewTab);
  const columnTitle = 'text-[0.9375rem] font-bold';
  const columnLink = 'inline-block py-1.5 text-[0.9375rem]';
</script>

<footer>
  <Wave fill="var(--brand)" />
  <div class="on-brand">
    <div class="shell flex flex-col items-center pt-14 pb-16 text-center sm:pt-20 sm:pb-24">
      <p class="section-title max-w-[18ch]">{dict.home.hero.title}</p>
      <p class="section-lead max-w-[52ch]">{dict.footer.blurb}</p>
      <div class="mt-8 flex w-full flex-col items-center justify-center gap-3 sm:flex-row">
        <CopyCommand
          command={INSTALL_COMMAND}
          label={dict.home.hero.copyLabel}
          labels={dict.common.copy}
          tone="deep"
          class="w-full max-w-[21rem] text-left"
        />
        <a href={localePath(lang, '/docs')} class="btn btn-light btn-lg">{dict.home.hero.tryCta}</a>
      </div>
    </div>

    <div class="border-t border-white/24">
      <div class="shell pt-12 pb-8">
        <div class="flex flex-wrap gap-x-20 gap-y-8">
          <nav aria-label={dict.footer.pagesTitle}>
            <p class={columnTitle}>{dict.footer.pagesTitle}</p>
            <ul class="mt-2">
              <li><a href={localePath(lang, '/')} class="nb-link {columnLink}">{dict.nav.home}</a></li>
              {#each NAV_ITEMS as item (item.key)}
                <li><a href={localePath(lang, item.href)} class="nb-link {columnLink}">{dict.nav[item.key]}</a></li>
              {/each}
            </ul>
          </nav>
          <nav aria-label={dict.footer.projectTitle}>
            <p class={columnTitle}>{dict.footer.projectTitle}</p>
            <ul class="mt-2">
              <li><ExtLink href={GITHUB_URL} {hint} class={columnLink}>{dict.footer.github}</ExtLink></li>
              <li><ExtLink href={PYPI_URL} {hint} class={columnLink}>{dict.footer.pypi}</ExtLink></li>
              <li><ExtLink href={HF_URL} {hint} class={columnLink}>{dict.footer.huggingface}</ExtLink></li>
            </ul>
          </nav>
        </div>

        <p aria-hidden="true" class="wordmark">
          <img src="/mira.svg" alt="" width="200" height="200" loading="lazy" />
          <span>MIRA</span>
        </p>

        <p class="border-t border-white/24 pt-5 text-[0.875rem]">{dict.footer.licence}</p>
      </div>
    </div>
  </div>
</footer>

<style>
  .wordmark {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 0.14em;
    margin-block: 2.5rem 1.5rem;
    font-size: min(23vw, 18rem);
    font-weight: 800;
    line-height: 1;
    letter-spacing: -0.045em;
    user-select: none;
  }
  .wordmark img {
    width: 0.74em;
    height: 0.74em;
  }
</style>
