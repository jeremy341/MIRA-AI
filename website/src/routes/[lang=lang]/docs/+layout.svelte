<script lang="ts">
  import DocsShell from '$lib/components/docs/DocsShell.svelte';

  /** Shared docs chrome: sidebar with search, mobile bar and drawer. Pages supply the article and the contents list. */
  let { data, children } = $props();
</script>

<DocsShell lang={data.lang} ui={data.ui} nav={data.nav} {children} />
