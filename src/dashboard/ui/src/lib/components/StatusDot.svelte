<script lang="ts">
  interface Props {
    tone?: 'neutral' | 'success' | 'warning' | 'danger' | 'accent';
    /** A slow pulse for "live" states. Stops with reduced motion. */
    pulse?: boolean;
  }

  let { tone = 'neutral', pulse = false }: Props = $props();
</script>

<span class="dot {tone}" class:pulse aria-hidden="true"></span>

<style>
  .dot {
    display: inline-block;
    width: 0.5rem;
    height: 0.5rem;
    flex-shrink: 0;
    border-radius: 50%;
    background: var(--rule-strong);
  }
  .success {
    background: #2a8a4a;
  }
  .warning {
    background: #b98a00;
  }
  .danger {
    background: var(--destructive);
  }
  .accent {
    background: var(--accent);
  }
  .pulse {
    animation: pulse 1.6s ease-in-out infinite;
  }
  @keyframes pulse {
    0%,
    100% {
      opacity: 1;
    }
    50% {
      opacity: 0.35;
    }
  }
  @media (prefers-reduced-motion: reduce) {
    .pulse {
      animation: none;
    }
  }
</style>
