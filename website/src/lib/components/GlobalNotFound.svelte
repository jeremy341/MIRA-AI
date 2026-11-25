<script lang="ts">
  import Canvas from './Canvas.svelte';
  import NotFoundView from './NotFoundView.svelte';

  /**
   * 404 for every URL that matches no route (written to build/404.html and used by the root +error.svelte). It has no
   * language layout, so it carries its own wordmark and shows both languages; each block has its own `lang`.
   */
</script>

<svelte:head>
  <title>Page not found | Seite nicht gefunden</title>
  <meta name="robots" content="noindex" />
</svelte:head>

<header class="border-b border-rule">
  <Canvas class="flex items-center py-1.5 sm:py-3">
    <a
      href="/"
      aria-label="MIRA"
      class="inline-flex min-h-11 items-center font-serif text-[1.625rem] leading-none font-semibold tracking-[0.04em] text-ink"
    >
      <span class="marker">MIRA</span>
    </a>
  </Canvas>
</header>
<main id="main">
  <Canvas class="grid gap-14 py-16 sm:py-24 md:grid-cols-2 md:gap-16">
    <NotFoundView lang="en" />
    <NotFoundView lang="de" as="h2" />
  </Canvas>
</main>
