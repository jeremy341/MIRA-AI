<script lang="ts">
  import type { Dictionary } from '$i18n';
  import Chapter from '../Chapter.svelte';
  import MarginNote from '../MarginNote.svelte';
  import Prose from '../Prose.svelte';
  import Rich from '../Rich.svelte';

  let { dict }: { dict: Dictionary } = $props();
  const t = $derived(dict.home.problem);
</script>

<Chapter id="problem" title={t.title}>
  <Prose>
    <p><Rich text={t.p1} /></p>
    <MarginNote><Rich text={t.note} /></MarginNote>
    <p><Rich text={t.p2} /></p>
  </Prose>

  <ol aria-label={t.triedLabel} class="mt-8 max-w-[44rem] border-t border-ink">
    {#each t.tried as step (step.name)}
      <li class="grid gap-x-6 gap-y-0.5 border-b border-rule py-3 sm:grid-cols-[9.5rem_1fr]">
        <span class="font-mono text-[0.9375rem] font-medium text-ink">{step.name}</span>
        <span class="text-[0.9375rem] leading-snug text-ink-soft"><Rich text={step.text} /></span>
      </li>
    {/each}
  </ol>

  <Prose class="mt-8">
    <p><Rich text={t.p3} /></p>
  </Prose>
</Chapter>
