<script lang="ts" module>
  let counter = 0;
  function nextTitleId(): string {
    counter += 1;
    return `dialog-title-${counter}`;
  }
</script>

<script lang="ts">
  import type { Snippet } from 'svelte';
  import IconButton from './IconButton.svelte';

  interface Props {
    open: boolean;
    title: string;
    onclose?: () => void;
    children: Snippet;
    actions?: Snippet;
  }

  let { open = $bindable(false), title, onclose, children, actions }: Props = $props();

  let dialog: HTMLDialogElement | undefined = $state();
  const titleId = nextTitleId();

  // The native dialog gives focus trapping, Escape to close and the backdrop for free.
  $effect(() => {
    const element = dialog;
    if (!element) return;
    if (open && !element.open) element.showModal();
    if (!open && element.open) element.close();
  });

  function handleClose() {
    open = false;
    onclose?.();
  }

  function handleBackdropClick(event: MouseEvent) {
    if (event.target === dialog) handleClose();
  }
</script>

<dialog bind:this={dialog} class="dialog" aria-labelledby={titleId} onclose={handleClose} onclick={handleBackdropClick}>
  <div class="inner">
    <header class="head">
      <h2 id={titleId} class="title">{title}</h2>
      <IconButton icon="close" label="Close" onclick={handleClose} />
    </header>
    <div class="body">{@render children()}</div>
    {#if actions}<footer class="foot">{@render actions()}</footer>{/if}
  </div>
</dialog>

<style>
  .dialog {
    width: min(32rem, calc(100vw - 2rem));
    max-height: calc(100dvh - 2rem);
    padding: 0;
    border: 0;
    border-radius: var(--radius-panel);
    background: var(--raised);
    box-shadow: var(--shadow-overlay);
    color: var(--ink);
  }
  .dialog::backdrop {
    background: rgb(31 31 31 / 35%);
  }
  .inner {
    display: grid;
    gap: var(--space-4);
    padding: var(--space-5);
  }
  .head {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: var(--space-3);
  }
  .title {
    font-size: var(--text-title);
    font-weight: var(--font-weight-semibold);
  }
  .body {
    font-size: var(--text-small);
    color: var(--ink-soft);
    line-height: 1.55;
  }
  .foot {
    display: flex;
    flex-wrap: wrap;
    justify-content: flex-end;
    gap: var(--space-2);
  }
</style>
