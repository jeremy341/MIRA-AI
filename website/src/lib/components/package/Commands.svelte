<script lang="ts">
  import type { Locale } from '$i18n/config';
  import type { PackageCopy } from '$i18n/package';
  import Chapter from '../Chapter.svelte';
  import Heading from '../Heading.svelte';
  import Prose from '../Prose.svelte';
  import Rich from '../Rich.svelte';
  import { COMMAND_GROUPS, type CommandOption } from './package-data';

  /**
   * The sixteen subcommands, read from src/cli. A description list rather than a wide table: the command sits
   * beside its description on a wide screen and above it on a phone, so nothing scrolls sideways.
   */
  let { lang, t }: { lang: Locale; t: PackageCopy } = $props();

  const c = $derived(t.commands);

  /** "--model", "--camera (0)", "--formats tflite_int8 | onnx (tflite_int8)", "--models (required)". */
  function optionText(option: CommandOption, requiredWord: string): string {
    return [
      option.flag,
      option.value,
      option.def ? `(${option.def})` : null,
      option.required ? `(${requiredWord})` : null
    ]
      .filter(Boolean)
      .join(' ');
  }
</script>

<Chapter id="commands" title={c.title}>
  <Prose>
    <p><Rich text={c.intro} {lang} /></p>
  </Prose>

  <div class="mt-10 grid gap-12">
    {#each COMMAND_GROUPS as group (group.id)}
      {@const copy = c.groups[group.id]}
      {@const headingId = `commands-${group.id}`}
      <section aria-labelledby={headingId} class="min-w-0">
        <Heading as="h3" size="title" id={headingId} class="text-ink">{copy.title}</Heading>
        <p class="mt-1.5 max-w-[66ch] text-[0.9375rem] leading-snug text-ink-soft">
          <Rich text={copy.intro} {lang} />
        </p>
        <dl class="mt-4 border-t border-rule-strong">
          {#each group.rows as row (row.id)}
            <div class="grid gap-x-8 gap-y-1 border-b border-rule py-3 sm:grid-cols-[11rem_minmax(0,1fr)]">
              <dt class="font-mono text-[0.875rem] font-medium text-ink">{row.name}</dt>
              <dd class="min-w-0">
                <p class="max-w-[66ch] text-[0.9375rem] leading-snug text-ink-soft">{c.does[row.id]}</p>
                <p class="mt-1.5 font-mono text-[0.8125rem] leading-[1.55] break-words text-muted-foreground">
                  {#if row.options.length > 0}
                    {#each row.options as option, index (option.flag)}
                      <span>{index > 0 ? ', ' : ''}{optionText(option, c.required)}</span>
                    {/each}
                  {:else}
                    <span class="font-sans">{c.none}</span>
                  {/if}
                </p>
              </dd>
            </div>
          {/each}
        </dl>
      </section>
    {/each}
  </div>

  <p class="mt-4 max-w-[66ch] text-micro text-muted-foreground"><Rich text={c.caption} {lang} /></p>
</Chapter>
