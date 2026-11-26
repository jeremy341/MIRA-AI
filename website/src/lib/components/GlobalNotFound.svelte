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

<header class="on-brand">
  <Canvas class="flex items-center py-3">
    <a
      href="/"
      aria-label="MIRA"
      class="inline-flex min-h-11 items-center gap-2.5 text-[1.625rem] leading-none font-extrabold"
    >
      <img src="/mira.svg" alt="" width="36" height="36" class="size-9" />
      <span>MIRA</span>
    </a>
  </Canvas>
</header>
<main id="main">
  <Canvas class="grid gap-14 py-16 sm:py-24 md:grid-cols-2 md:gap-16">
    <NotFoundView lang="en" />
    <NotFoundView lang="de" as="h2" />
  </Canvas>
</main>
