<script lang="ts">
  import type { Dictionary } from '$i18n';
  import { INSTALL_COMMAND } from '$lib/site';
  import Canvas from '../Canvas.svelte';
  import CopyCommand from '../CopyCommand.svelte';
  import Heading from '../Heading.svelte';

  let { dict }: { dict: Dictionary } = $props();

  const t = $derived(dict.home.hero);
</script>

<section
  aria-labelledby="hero-title"
  class="flex min-h-[calc(100svh-6.25rem)] flex-col py-10 sm:min-h-[calc(100svh-4rem)] sm:py-16"
>
  <Canvas class="flex flex-1 flex-col items-center justify-center text-center">
    <div class="mx-auto flex w-full max-w-4xl flex-col items-center">
      <Heading as="h1" size="hero" id="hero-title" class="mx-auto max-w-[14ch] text-ink text-balance">
        {t.title}
      </Heading>
      <p class="mx-auto mt-6 max-w-[40ch] text-lg leading-relaxed text-ink-soft text-balance">{t.lede}</p>
      <div class="mt-8 flex flex-wrap items-center justify-center gap-3">
        <a href="#try" class="btn btn-primary btn-lg">{t.tryCta}</a>
        <a href="#results" class="btn btn-secondary btn-lg no-underline">
          {t.resultsCta}
        </a>
      </div>
      <CopyCommand
        command={INSTALL_COMMAND}
        label={t.copyLabel}
        labels={dict.common.copy}
        class="mx-auto mt-7 w-full max-w-[22rem]"
      />
    </div>
  </Canvas>
</section>
