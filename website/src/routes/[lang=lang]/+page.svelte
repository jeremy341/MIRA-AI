<script lang="ts">
  import { getDictionary } from '$i18n';
  import Seo from '$lib/components/Seo.svelte';
  import Evidence from '$lib/components/home/Evidence.svelte';
  import Hero from '$lib/components/home/Hero.svelte';
  import Landscape from '$lib/components/home/Landscape.svelte';
  import Problem from '$lib/components/home/Problem.svelte';
  import ResultStrip from '$lib/components/home/ResultStrip.svelte';
  import Status from '$lib/components/home/Status.svelte';
  import TryIt from '$lib/components/home/TryIt.svelte';

  let { data } = $props();

  const lang = $derived(data.lang);
  const dict = $derived(getDictionary(lang));

</script>

<Seo {lang} path="/" title={dict.meta.title} description={dict.meta.description} />

<Hero {dict} />
<ResultStrip {lang} {dict} />
<Landscape {lang} {dict} />
<Problem {dict} />
<Evidence {lang} {dict} />
<TryIt {lang} {dict} />
<Status {dict} />
