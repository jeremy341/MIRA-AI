<script lang="ts">
  interface Props {
    size?: 'sm' | 'md';
    /** Announced to screen readers. Leave empty when a visible label sits next to the spinner. */
    label?: string;
  }

  let { size = 'md', label = 'Loading' }: Props = $props();
</script>

<span class="spinner {size}" role="status" aria-label={label || undefined}>
  <span class="ring" aria-hidden="true"></span>
</span>

<style>
  .spinner {
    display: inline-grid;
    place-items: center;
    flex-shrink: 0;
  }
  .ring {
    display: block;
    width: 1.125rem;
    height: 1.125rem;
    border: 2px solid currentColor;
    border-right-color: transparent;
    border-radius: 50%;
    opacity: 0.8;
    animation: spin 0.8s linear infinite;
  }
  .sm .ring {
    width: 0.875rem;
    height: 0.875rem;
  }
  @keyframes spin {
    to {
      transform: rotate(360deg);
    }
  }
  @media (prefers-reduced-motion: reduce) {
    .ring {
      animation-duration: 2.4s;
    }
  }
</style>
