<script lang="ts">
  import type { Snippet } from 'svelte';
  import type { Dictionary } from '$i18n';
  import type { Locale } from '$i18n/config';
  import { fmt } from '$i18n/format';
  import type { PackageCopy } from '$i18n/package';
  import { INSTALL_COMMAND } from '$lib/site';
  import Canvas from '../Canvas.svelte';
  import CopyCommand from '../CopyCommand.svelte';
  import Heading from '../Heading.svelte';
  import Rich from '../Rich.svelte';
  import { LICENSE_NAME, PACKAGE_VERSION, PYTHON_REQUIREMENT, REPOSITORY_VERSION } from './package-data';

  /** Page title, the two-sentence summary, the one-line install, the package facts and the contents list. */
  let { lang, dict, t }: { lang: Locale; dict: Dictionary; t: PackageCopy } = $props();

  const h = $derived(t.header);
</script>

{#snippet fact(term: string, value: Snippet)}
  <div class="grid grid-cols-[7.5rem_minmax(0,1fr)] items-baseline gap-4 border-t border-rule py-3 first:border-ink">
    <dt class="text-[0.875rem] text-muted-foreground">{term}</dt>
    <dd class="min-w-0 text-[0.9375rem] text-ink">{@render value()}</dd>
  </div>
{/snippet}

{#snippet pypiValue()}<span class="font-mono tabular">{PACKAGE_VERSION}</span>{/snippet}
{#snippet pythonValue()}
  <span class="font-mono">{h.facts.pythonValue}</span>
  <span class="mt-1 block text-micro font-normal text-muted-foreground">
    {fmt(h.facts.pythonNote, { requires: PYTHON_REQUIREMENT })}
  </span>
{/snippet}
{#snippet licenceValue()}{LICENSE_NAME}{/snippet}
{#snippet bundledValue()}{h.facts.bundledValue}{/snippet}

<section aria-labelledby="package-title" class="pb-12 pt-8 sm:pb-16 sm:pt-12">
  <Canvas>
    <div class="grid gap-10 lg:grid-cols-[minmax(0,7fr)_minmax(0,5fr)] lg:gap-16">
      <div class="min-w-0">
        <Heading as="h1" size="display" id="package-title" class="max-w-[18ch] text-ink">{h.title}</Heading>
        <p class="mt-5 max-w-[46ch] font-serif text-lede text-ink-soft">
          <Rich text={h.lede} {lang} />
        </p>
        <CopyCommand
          command={INSTALL_COMMAND}
          label={h.installLabel}
          labels={dict.common.copy}
          class="mt-7 max-w-[26rem]"
        />
        <p class="mt-2 max-w-[46ch] text-micro text-muted-foreground">{h.installNote}</p>
      </div>

      <div class="min-w-0 self-end">
        <dl aria-label={h.factsLabel} class="border-b border-rule">
          {@render fact(h.facts.pypi, pypiValue)}
          {@render fact(h.facts.python, pythonValue)}
          {@render fact(h.facts.licence, licenceValue)}
          {@render fact(h.facts.bundled, bundledValue)}
        </dl>
        <p class="mt-3 max-w-[46ch] text-micro text-muted-foreground">
          <Rich text={fmt(h.versionNote, { repoVersion: REPOSITORY_VERSION, version: PACKAGE_VERSION })} {lang} />
        </p>
      </div>
    </div>
  </Canvas>
</section>
