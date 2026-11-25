<script lang="ts">
  import type { Dictionary } from '$i18n';
  import type { PackageCopy } from '$i18n/package';
  import Chapter from '../Chapter.svelte';
  import CopyCommand from '../CopyCommand.svelte';
  import Heading from '../Heading.svelte';
  import Prose from '../Prose.svelte';
  import { INSTALL_POWERSHELL, INSTALL_UNIX } from './package-data';

  /** Install: the same four steps for Windows PowerShell and for macOS and Linux, as two plain labelled blocks. */
  let { dict, t }: { dict: Dictionary; t: PackageCopy } = $props();

  const i = $derived(t.install);
  const blocks = $derived([
    { key: 'windows', ...i.windows, command: INSTALL_POWERSHELL },
    { key: 'unix', ...i.unix, command: INSTALL_UNIX }
  ]);
</script>

<Chapter id="install" title={i.title}>
  <Prose>
    <p>{i.p1}</p>
  </Prose>
  <div class="mt-8 grid gap-10 md:grid-cols-2 md:gap-12">
    {#each blocks as block (block.key)}
      <div class="min-w-0">
        <Heading as="h3" size="title" class="text-ink">{block.label}</Heading>
        <CopyCommand command={block.command} prompt="" label={block.copyLabel} labels={dict.common.copy} class="mt-3" />
        <p class="mt-2 max-w-[46ch] text-micro text-muted-foreground">{block.note}</p>
      </div>
    {/each}
  </div>
</Chapter>
