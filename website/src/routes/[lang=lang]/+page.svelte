<script lang="ts">
  import { onMount } from 'svelte';
  import { getDictionary } from '$i18n';
  import Seo from '$lib/components/Seo.svelte';
  import Downloads from '$lib/components/home/Downloads.svelte';
  import Evidence from '$lib/components/home/Evidence.svelte';
  import Hero from '$lib/components/home/Hero.svelte';
  import Landscape from '$lib/components/home/Landscape.svelte';
  import Problem from '$lib/components/home/Problem.svelte';
  import Status from '$lib/components/home/Status.svelte';
  import TryIt from '$lib/components/home/TryIt.svelte';
  import WhatItIs from '$lib/components/home/WhatItIs.svelte';
  import { HfDownloads } from '$lib/use-hf-downloads.svelte';

  let { data } = $props();

  const lang = $derived(data.lang);
  const dict = $derived(getDictionary(lang));

  /** One counter feeds the hero pill and the band below it. It asks again every five minutes. */
  const downloads = new HfDownloads();
  onMount(() => downloads.start(5 * 60 * 1000));
</script>

<Seo {lang} path="/" title={dict.meta.title} description={dict.meta.description} />

<Hero {lang} {dict} {downloads} />
<Downloads {lang} {dict} source={downloads} />
<WhatItIs {lang} {dict} />
<Landscape {lang} {dict} />
<Problem {dict} />
<Evidence {lang} {dict} />
<TryIt {lang} {dict} />
<Status {dict} />
