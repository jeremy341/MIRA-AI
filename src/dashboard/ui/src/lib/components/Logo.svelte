<script lang="ts">
  interface Props {
    size?: number;
  }

  let { size = 32 }: Props = $props();
</script>

<!--
  The MIRA mark: a viewfinder with an M inside. The valley of the M holds one dot, the object the camera picked out.
  Keep this in step with public/favicon.svg.
-->
<svg class="logo" viewBox="0 0 32 32" width={size} height={size} aria-hidden="true" focusable="false">
  <rect width="32" height="32" rx="9" fill="var(--ink)" />
  <path
    d="M6.5 11.5v-3a2 2 0 0 1 2-2h3M20.5 6.5h3a2 2 0 0 1 2 2v3M25.5 20.5v3a2 2 0 0 1-2 2h-3M11.5 25.5h-3a2 2 0 0 1-2-2v-3"
    fill="none"
    stroke="var(--surface)"
    stroke-opacity="0.45"
    stroke-width="1.8"
    stroke-linecap="round"
  />
  <path d="M10.5 20.5v-9l5.5 6.2 5.5-6.2v9" fill="none" stroke="var(--surface)" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round" />
  <circle cx="16" cy="22.4" r="1.9" fill="#7b9be6" />
</svg>

<style>
  .logo {
    display: block;
    flex-shrink: 0;
  }
</style>
