<script lang="ts">
  import Prose from '../Prose.svelte';
  import Rich from '../Rich.svelte';
  import { fill, type SectionProps } from './context';
  import NumChapter from './NumChapter.svelte';

  /** The closing note: where the datasets, the log and the models live. */
  let { lang, t, vars }: SectionProps = $props();
</script>

<NumChapter id="data" n={8} title={t.data.title} class="pb-16 sm:pb-24">
  <Prose>
    <p><Rich text={fill(vars, t.data.p1)} {lang} /></p>
  </Prose>
</NumChapter>
