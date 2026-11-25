<script lang="ts">
  import type { DocsUi } from '$i18n/docs/ui';
  import { docToMarkdown, type DocPage } from '$lib/docs-content';
  import { GITHUB_URL } from '$lib/site';

  /** Under the page title, as on Orchard's docs: copy the page as Markdown, and edit it on GitHub. */
  let { doc, ui, lang }: { doc: DocPage; ui: DocsUi; lang: string } = $props();

  let status = $state<'idle' | 'copied' | 'failed'>('idle');
  let timer: ReturnType<typeof setTimeout> | undefined;

  async function copy() {
    try {
      await navigator.clipboard.writeText(docToMarkdown(doc));
      status = 'copied';
    } catch {
      status = 'failed';
    }
    clearTimeout(timer);
    timer = setTimeout(() => (status = 'idle'), 2200);
  }

  const message = $derived(status === 'copied' ? ui.copiedMarkdown : status === 'failed' ? ui.copyMarkdownFailed : '');

  const action =
    'inline-flex items-center gap-1.5 rounded-lg px-2 py-1.5 text-[0.875rem] text-ink-soft transition-colors duration-(--dur-fast) hover:bg-hover/60 hover:text-ink';
</script>

<div class="mt-4 -ml-2 flex flex-wrap items-center gap-x-1 gap-y-1">
  <button type="button" onclick={copy} class={action}>
    <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
      <rect x="8" y="8" width="12" height="12" rx="2" />
      <path d="M16 8V6a2 2 0 0 0-2-2H6a2 2 0 0 0-2 2v8a2 2 0 0 0 2 2h2" />
    </svg>
    {message || ui.copyMarkdown}
  </button>
  <span class="sr-only" role="status" aria-live="polite">{message}</span>
  <a
    href="{GITHUB_URL}/blob/main/website/src/i18n/docs/{lang}.ts"
    target="_blank"
    rel="noopener noreferrer"
    class={action}
  >
    <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
      <path d="M4 20h4L19 9a2.8 2.8 0 0 0-4-4L4 16v4ZM13.5 6.5l4 4" />
    </svg>
    {ui.editOnGithub}
  </a>
</div>
