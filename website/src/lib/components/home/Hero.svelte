<script lang="ts">
  import type { Dictionary } from '$i18n';
  import type { Locale } from '$i18n/config';
  import { fmt, formatInt } from '$i18n/format';
  import { INSTALL_COMMAND } from '$lib/site';
  import type { HfDownloads } from '$lib/use-hf-downloads.svelte';
  import CopyCommand from '../CopyCommand.svelte';
  import Wave from '../Wave.svelte';
  import HeroMark from './HeroMark.svelte';

  let { lang, dict, downloads }: { lang: Locale; dict: Dictionary; downloads: HfDownloads } = $props();

  const t = $derived(dict.home.hero);
  /** The product name inside the title is set heavier. The title text itself is unchanged. */
  const titleParts = $derived(t.title.split(/(MIRA)/));
</script>

<section aria-labelledby="hero-title" class="hero on-brand">
  <div class="shell !max-w-[90rem] hero-grid">
    <div class="hero-text">
      <a href="#downloads" class="pill">
        <span class="pill-dot" class:is-live={downloads.status === 'live'} aria-hidden="true"></span>
        <span class="tabular">{fmt(dict.home.downloads.pill, { n: formatInt(lang, downloads.value) })}</span>
      </a>
      <h1 id="hero-title" class="hero-title">
        {#each titleParts as part, index (index)}{#if part === 'MIRA'}<strong>{part}</strong>{:else}{part}{/if}{/each}
      </h1>
      <p class="hero-lede mt-5 max-w-[30ch] text-[clamp(1.1875rem,1rem+0.9vw,1.75rem)] leading-[1.45] text-on-brand-soft">
        {t.lede}
      </p>
      <CopyCommand
        command={INSTALL_COMMAND}
        label={t.copyLabel}
        labels={dict.common.copy}
        tone="deep"
        class="hero-install mt-8 w-full max-w-[25rem]"
      />
      <div class="mt-4 flex flex-wrap gap-3">
        <a href="#try" class="btn btn-light btn-lg">{t.tryCta}</a>
        <a href="#results" class="btn btn-quiet btn-lg">{t.resultsCta}</a>
      </div>
    </div>
    <div class="hero-mark"><HeroMark /></div>
  </div>

  <div class="hero-edge">
    <a href="#downloads" class="cue">
      {t.scrollCue}
      <svg viewBox="0 0 16 16" width="18" height="18" aria-hidden="true">
        <path d="M8 3v10M3.5 8.5 8 13l4.500-4.500" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" />
      </svg>
    </a>
    <Wave fill="var(--tint)" />
  </div>
</section>

<style>
  .hero {
    display: flex;
    flex-direction: column;
    /* Header (4.75rem) plus hero fill the first screen, so the wave sits at its bottom edge. */
    min-height: clamp(34rem, calc(100svh - 4.75rem), 90rem);
    overflow: hidden;
  }
  .hero-grid {
    position: relative;
    display: grid;
    flex: 1;
    align-content: center;
    gap: 2.5rem;
    padding-block: 2.5rem 3rem;
  }
  .hero-text {
    position: relative;
    z-index: 1;
    min-width: 0;
  }
  .pill {
    display: inline-flex;
    min-height: 2.75rem;
    align-items: center;
    gap: 0.625rem;
    margin-bottom: 1.25rem;
    padding: 0.5rem 1rem;
    border-radius: 0.625rem;
    background: rgb(255 255 255 / 14%);
    box-shadow: inset 0 0 0 1px rgb(255 255 255 / 28%);
    font-size: 1rem;
    font-weight: 700;
    line-height: 1.35;
  }
  .pill:hover {
    background: var(--brand-deep);
  }
  .pill-dot {
    flex-shrink: 0;
    width: 0.625rem;
    height: 0.625rem;
    border-radius: 50%;
    background: rgb(255 255 255 / 55%);
  }
  .pill-dot.is-live {
    background: #5ee6a0;
  }
  .hero-title {
    max-width: 12ch;
    font-size: clamp(2.75rem, 1.2rem + 5.4vw, 5.5rem);
    font-weight: 500;
    line-height: 1.08;
    letter-spacing: -0.03em;
  }
  .hero-title strong {
    font-weight: 800;
  }
  .hero-mark {
    width: min(100%, 22rem);
    justify-self: center;
  }
  @media (min-width: 64rem) {
    .hero-grid {
      grid-template-columns: minmax(0, 7fr) minmax(0, 6fr);
      align-items: center;
    }
    .hero-mark {
      /* The height limit keeps the wave on screen on short laptop screens. */
      width: min(112%, 42rem, max(22rem, calc(100svh - 11rem)));
      justify-self: start;
      margin-block: -2rem;
    }
  }
  /* Short laptop screens: the text is what sets the height there, so it is set tighter to keep the wave on screen. */
  @media (min-width: 64rem) and (max-height: 48rem) {
    .hero-grid {
      padding-block: 0.75rem 1rem;
    }
    .pill {
      margin-bottom: 0.75rem;
    }
    .hero-title {
      font-size: clamp(2.75rem, 8svh, 4rem);
    }
    .hero-lede {
      margin-top: 0.75rem;
      font-size: 1.125rem;
    }
    .hero-text > :global(.hero-install) {
      margin-top: 1rem;
    }
  }
  .hero-edge {
    position: relative;
  }
  .cue {
    position: absolute;
    z-index: 1;
    bottom: 0.25rem;
    left: 50%;
    display: inline-flex;
    min-height: 3rem;
    align-items: center;
    gap: 0.625rem;
    padding: 0 1.125rem;
    border-radius: 0.625rem;
    background: var(--tint-strong);
    color: var(--brand-ink);
    font-size: 1rem;
    font-weight: 600;
    white-space: nowrap;
    box-shadow: 0 14px 28px -16px rgb(10 18 48 / 60%);
    translate: -50% 0;
  }
  .cue:hover {
    background: #ffffff;
  }
</style>
