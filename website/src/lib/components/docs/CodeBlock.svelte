<script lang="ts" module>
  async function writeClipboard(text: string): Promise<boolean> {
    try {
      if (navigator.clipboard?.writeText) {
        await navigator.clipboard.writeText(text);
        return true;
      }
    } catch {
      // Fall through to the legacy path (insecure context, permission denied).
    }
    try {
      const area = document.createElement('textarea');
      area.value = text;
      area.setAttribute('readonly', '');
      area.style.position = 'fixed';
      area.style.opacity = '0';
      document.body.appendChild(area);
      area.select();
      const ok = document.execCommand('copy');
      area.remove();
      return ok;
    } catch {
      return false;
    }
  }
</script>

<script lang="ts">
  import { onDestroy } from 'svelte';
  import { fmt } from '$i18n/format';
  import type { CodeLabels } from './types';

  /**
   * A listing in a manual: an ink rule on top, a caption with the copy button, the code on the surface
   * colour. Long lines scroll inside a labelled, keyboard focusable region, never the page.
   * Sample output (`output`) has no copy button and a lighter look. Not CopyCommand: that one is a single
   * command line, this one holds multi-line code, a caption and a scroll region.
   */
  let {
    code,
    label,
    output = false,
    labels
  }: {
    code: string;
    /** Shown in the caption, e.g. "Windows PowerShell" or "mira.yaml". */
    label?: string;
    output?: boolean;
    labels: CodeLabels;
  } = $props();

  const captionId = $props.id();

  let state = $state<'idle' | 'copied' | 'failed'>('idle');
  let timer: ReturnType<typeof setTimeout> | null = null;

  onDestroy(() => {
    if (timer) clearTimeout(timer);
  });

  async function copy() {
    const ok = await writeClipboard(code);
    state = ok ? 'copied' : 'failed';
    if (timer) clearTimeout(timer);
    timer = setTimeout(() => (state = 'idle'), 2200);
  }

  const title = $derived(label ?? (output ? labels.outputLabel : labels.terminal));
  const message = $derived(
    state === 'copied' ? labels.copiedMessage : state === 'failed' ? labels.failedMessage : ''
  );
</script>

<figure
  class="my-6 max-w-full min-w-0 overflow-hidden rounded-xl border border-rule bg-surface shadow-[var(--shadow-raised)]"
>
  <figcaption
    id={captionId}
    class="flex min-h-10 items-center justify-between gap-3 border-b border-rule/70 pr-1 pl-3 text-[0.8125rem] text-muted-foreground"
  >
    <span class="min-w-0 truncate">{title}</span>
    {#if !output}
      <button
        type="button"
        onclick={copy}
        aria-label={fmt(labels.copyCodeLabel, { title })}
        class="inline-flex h-10 min-w-[5.5rem] shrink-0 items-center justify-center px-2.5 text-[0.8125rem] font-medium text-ink rounded-lg transition-colors duration-(--dur-fast) ease-out hover:bg-hover/60"
      >
        <span aria-hidden="true">{state === 'copied' ? labels.copied : state === 'failed' ? labels.failed : labels.copy}</span>
      </button>
    {/if}
  </figcaption>
  <!-- A scrollable region must be reachable by keyboard so its overflow can be scrolled. -->
  <!-- svelte-ignore a11y_no_noninteractive_tabindex -->
  <div role="region" tabindex="0" aria-labelledby={captionId} class="overflow-x-auto">
    <!-- One-line listings (synopses) wrap instead of hiding their end; multi-line code scrolls. -->
    <pre
      class="m-0 px-3 py-3.5 font-mono text-[0.8125rem] leading-6 sm:text-[0.875rem] {code.includes('\n')
        ? 'w-max min-w-full'
        : 'whitespace-pre-wrap [overflow-wrap:anywhere]'} {output ? 'text-ink-soft' : 'text-ink'}"><code>{code}</code></pre>
  </div>
  <span role="status" aria-live="polite" class="sr-only">{message}</span>
</figure>
