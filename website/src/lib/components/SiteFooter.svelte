<script lang="ts">
  import { localePath, type Locale } from '$i18n/config';
  import type { Dictionary } from '$i18n';
  import { GITHUB_URL, HF_URL, INSTALL_COMMAND, NAV_ITEMS, PYPI_URL } from '$lib/site';
  import CopyCommand from './CopyCommand.svelte';
  import ExtLink from './ExtLink.svelte';
  import MarkPaths from './MarkPaths.svelte';
  import Wave from './Wave.svelte';

  /** The closing band repeats the title with the install command. Below it the links and the name span the window. */
  let { lang, dict }: { lang: Locale; dict: Dictionary } = $props();
  const hint = $derived(dict.common.opensInNewTab);
  const columnTitle = 'text-[0.9375rem] font-bold';
  const columnLink = 'inline-block py-1.5 text-[0.9375rem]';
</script>

<footer>
  <Wave fill="var(--brand)" />
  <div class="on-brand">
    <div class="shell flex flex-col items-center pt-14 pb-16 text-center sm:pt-20 sm:pb-20">
      <p class="section-title max-w-[18ch]">{dict.home.hero.title}</p>
      <div class="mt-8 flex w-full flex-col items-center justify-center gap-3 sm:flex-row">
        <CopyCommand
          command={INSTALL_COMMAND}
          label={dict.home.hero.copyLabel}
          labels={dict.common.copy}
          tone="deep"
          class="w-full max-w-[24rem] text-left"
        />
        <a href={localePath(lang, '/docs')} class="btn btn-light btn-lg">{dict.home.hero.tryCta}</a>
      </div>
    </div>

    <!-- From here on the footer uses the whole window. -->
    <div class="across border-t border-white/24 pt-10 sm:pt-12">
      <div class="flex flex-wrap items-start justify-between gap-x-16 gap-y-8">
        <p class="max-w-[34ch] text-[1.125rem] leading-[1.55] text-on-brand-soft">{dict.footer.blurb}</p>
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
      </div>

      <!-- The logo and the name as one drawing, as wide as the window. textLength keeps the width exact. -->
      <svg class="wordmark" viewBox="8 6 392 88" aria-hidden="true" focusable="false">
        <svg x="0" y="0" width="100" height="100" viewBox="3 3 26 26"><MarkPaths /></svg>
        <text x="102" y="90" textLength="296" lengthAdjust="spacingAndGlyphs">MIRA</text>
      </svg>

      <p class="border-t border-white/24 py-6 text-[0.875rem]">{dict.footer.licence}</p>
    </div>
  </div>
</footer>

<style>
  .across {
    padding-inline: clamp(1.25rem, 4vw, 4rem);
  }
  .wordmark {
    display: block;
    width: 100%;
    height: auto;
    margin-block: clamp(2.5rem, 6vw, 6rem) clamp(1.5rem, 4vw, 4rem);
    fill: #ffffff;
    user-select: none;
  }
  .wordmark text {
    font-size: 112px;
    font-weight: 800;
    letter-spacing: -0.03em;
  }
</style>
