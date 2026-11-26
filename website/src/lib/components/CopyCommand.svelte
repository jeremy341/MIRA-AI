<script lang="ts" module>
  export type CopyLabels = {
    copy: string;
    copied: string;
    failed: string;
    /** Contains {command}. */
    labelFor: string;
    copiedMessage: string;
    failedMessage: string;
  };

  const DEFAULT_LABELS: CopyLabels = {
    copy: 'Copy',
    copied: 'Copied',
    failed: 'Failed',
    labelFor: 'Copy: {command}',
    copiedMessage: 'Copied to clipboard',
    failedMessage: 'Copy failed, select the command and copy it manually'
  };

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

  /**
   * A command on a ruled line (not a box) with a text "Copy" button. The button is a real <button> with a
   * stable accessible name; the result is announced through a polite live region.
   */
  let {
    command,
    prompt = '$',
    label,
    labels = DEFAULT_LABELS,
    tone = 'light',
    class: className = ''
  }: {
    /** The exact text that is copied, e.g. `pip install mira-ai`. */
    command: string;
    /** Visible prompt character before the command. It is not copied. Pass "" to hide. */
    prompt?: string;
    /** Names the copy button for assistive tech, e.g. "Copy install command". Defaults to `labels.labelFor`. */
    label?: string;
    labels?: CopyLabels;
    /** light: a white field. deep: for blue grounds. night: inside a dark terminal. */
    tone?: 'light' | 'deep' | 'night';
    class?: string;
  } = $props();

  const TONES = {
    light: 'on-light border-rule bg-surface shadow-[var(--shadow-raised)]',
    deep: 'border-white/16 bg-brand-deep text-white',
    night: 'border-white/12 bg-white/6 text-white'
  } as const;
  const dark = $derived(tone !== 'light');

  let state = $state<'idle' | 'copied' | 'failed'>('idle');
  let timer: ReturnType<typeof setTimeout> | null = null;

  onDestroy(() => {
    if (timer) clearTimeout(timer);
  });

  async function copy() {
    const ok = await writeClipboard(command);
    state = ok ? 'copied' : 'failed';
    if (timer) clearTimeout(timer);
    timer = setTimeout(() => (state = 'idle'), 2200);
  }

  const message = $derived(
    state === 'copied' ? labels.copiedMessage : state === 'failed' ? labels.failedMessage : ''
  );
</script>

<div
  class="flex max-w-full items-stretch overflow-hidden rounded-lg border font-mono text-[0.875rem] leading-6 {TONES[tone]} {className}"
>
  <code class="flex min-w-0 flex-1 items-center gap-2.5 px-3 py-2.5 break-words whitespace-pre-wrap">
    {#if prompt}<span aria-hidden="true" class="select-none {dark ? 'text-white/70' : 'text-muted-foreground'}">{prompt}</span>{/if}
    <span>{command}</span>
  </code>
  <button
    type="button"
    onclick={copy}
    aria-label={label ?? fmt(labels.labelFor, { command })}
    class="flex min-h-11 min-w-[5.5rem] shrink-0 items-center justify-center px-3 font-sans text-[0.875rem] font-medium underline underline-offset-[0.25em] transition-colors duration-(--dur-fast) ease-out {dark ? 'hover:bg-white/12' : 'hover:bg-marker'}"
  >
    <span aria-hidden="true">{state === 'copied' ? labels.copied : state === 'failed' ? labels.failed : labels.copy}</span>
  </button>
  <span role="status" aria-live="polite" class="sr-only">{message}</span>
</div>
