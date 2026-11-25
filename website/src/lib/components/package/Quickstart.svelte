<script lang="ts">
  import type { Dictionary } from '$i18n';
  import type { Locale } from '$i18n/config';
  import type { PackageCopy } from '$i18n/package';
  import Chapter from '../Chapter.svelte';
  import CopyCommand from '../CopyCommand.svelte';
  import Heading from '../Heading.svelte';
  import MarginNote from '../MarginNote.svelte';
  import Rich from '../Rich.svelte';
  import { QUICKSTART_COMMANDS } from './package-data';

  /**
   * Four steps. The last one (live detection) is the point, so it comes first; the three checks that lead
   * up to it sit in a disclosure below it. All four state what you should see.
   */
  let { lang, dict, t }: { lang: Locale; dict: Dictionary; t: PackageCopy } = $props();

  const q = $derived(t.quickstart);
  const liveStep = $derived(q.steps[3]);
</script>

<Chapter id="quickstart" title={q.title}>
  <div class="max-w-[44rem]">
    <Heading as="h3" size="title" class="text-ink">{liveStep.title}</Heading>
    <p class="mt-1.5 text-[0.9375rem] leading-snug text-ink-soft">{liveStep.text}</p>
    <CopyCommand
      command={QUICKSTART_COMMANDS[3]}
      label={liveStep.copyLabel}
      labels={dict.common.copy}
      class="mt-3"
    />
    <p class="mt-3 text-[0.9375rem] leading-snug text-ink-soft">
      <span class="font-semibold text-ink">{q.youSee}: </span>
      <Rich text={liveStep.expected} {lang} />
    </p>
    <details class="mt-5 border-t border-rule pt-3">
      <summary class="cursor-pointer text-sm font-medium">{q.checkInstall}</summary>
      <ul class="mt-4 space-y-4">
        {#each q.steps.slice(0, 3) as step, index (step.title)}
          <li>
            <CopyCommand command={QUICKSTART_COMMANDS[index]} label={step.copyLabel} labels={dict.common.copy} />
            <p class="mt-2 text-sm text-ink-soft"><Rich text={step.expected} {lang} /></p>
          </li>
        {/each}
      </ul>
    </details>
  </div>
  <div class="mt-6 flow-root max-w-[66ch]">
    <MarginNote class="mt-0"><Rich text={q.modelNote} {lang} /></MarginNote>
    <p class="text-[0.9375rem] leading-snug text-ink-soft"><Rich text={q.dashboard} {lang} /></p>
  </div>
</Chapter>
