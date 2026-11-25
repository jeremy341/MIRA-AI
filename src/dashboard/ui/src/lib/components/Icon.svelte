<script lang="ts" module>
  /** Hand-drawn 24 x 24 icons. Each entry is a list of path data strings. */
  export const ICON_PATHS = {
    detect: ['M4 9V6.5A2.5 2.5 0 0 1 6.5 4H9', 'M15 4h2.5A2.5 2.5 0 0 1 20 6.5V9', 'M20 15v2.5a2.5 2.5 0 0 1-2.5 2.5H15', 'M9 20H6.5A2.5 2.5 0 0 1 4 17.5V15', 'M12 8.5a3.5 3.5 0 1 0 0 7 3.5 3.5 0 0 0 0-7z'],
    sessions: ['M9 6.5h11', 'M9 12h11', 'M9 17.5h11', 'M4.5 6.5h.01', 'M4.5 12h.01', 'M4.5 17.5h.01'],
    models: ['M12 3.5l7.5 4.2v8.6L12 20.5l-7.5-4.2V7.7z', 'M4.5 7.7l7.5 4.2 7.5-4.2', 'M12 11.9v8.6'],
    analytics: ['M5 20V12', 'M12 20V5', 'M19 20v-6'],
    settings: ['M4 7.5h9', 'M17 7.5h3', 'M4 16.5h3', 'M11 16.5h9', 'M13 5.5v4', 'M7 14.5v4'],
    play: ['M8 5.5v13l10.5-6.5z'],
    stop: ['M7.5 7.5h9v9h-9z'],
    upload: ['M12 15.5V4', 'M7.5 8.5L12 4l4.5 4.5', 'M4.5 14.5v3.5a2 2 0 0 0 2 2h11a2 2 0 0 0 2-2v-3.5'],
    refresh: ['M19.5 12a7.5 7.5 0 1 1-2.2-5.3', 'M19.5 4.5v4h-4'],
    plus: ['M12 5.5v13', 'M5.5 12h13'],
    check: ['M5 12.5l4.5 4.5L19 7.5'],
    alert: ['M12 4.5l8.5 15h-17z', 'M12 10v4', 'M12 17.2v.01'],
    info: ['M12 20.5a8.5 8.5 0 1 0 0-17 8.5 8.5 0 0 0 0 17z', 'M12 11v5', 'M12 8v.01'],
    close: ['M6.5 6.5l11 11', 'M17.5 6.5l-11 11'],
    link: ['M9.5 14.5l5-5', 'M10 6.5l1.5-1.5a4 4 0 0 1 5.7 5.7L15.5 12.5', 'M14 17.5l-1.5 1.5a4 4 0 0 1-5.7-5.7l1.7-1.7'],
    camera: ['M4 8.5A2.5 2.5 0 0 1 6.5 6h1.7l1.3-2h4l1.3 2h1.7A2.5 2.5 0 0 1 20 8.5v8A2.5 2.5 0 0 1 17.5 19h-11A2.5 2.5 0 0 1 4 16.5z', 'M12 9.5a3.5 3.5 0 1 0 0 7 3.5 3.5 0 0 0 0-7z'],
    chevron: ['M9 6l6 6-6 6'],
    file: ['M7 3.5h7.5L19 8v12.5H7z', 'M14.5 3.5V8H19', 'M10 13h6', 'M10 16.5h6'],
    wifi: ['M4.5 9.5a11 11 0 0 1 15 0', 'M7.5 12.8a6.5 6.5 0 0 1 9 0', 'M10.5 16a2 2 0 0 1 3 0'],
    dot: ['M12 12h.01'],
  } as const;

  export type IconName = keyof typeof ICON_PATHS;
</script>

<script lang="ts">
  interface Props {
    name: IconName;
    size?: number;
    strokeWidth?: number;
    /** Fills the shape instead of stroking it (for play and stop). */
    filled?: boolean;
    label?: string;
  }

  let { name, size = 20, strokeWidth = 1.8, filled = false, label }: Props = $props();
</script>

<svg
  class="icon"
  width={size}
  height={size}
  viewBox="0 0 24 24"
  fill={filled ? 'currentColor' : 'none'}
  stroke={filled ? 'none' : 'currentColor'}
  stroke-width={strokeWidth}
  stroke-linecap="round"
  stroke-linejoin="round"
  aria-hidden={label ? undefined : 'true'}
  role={label ? 'img' : undefined}
  aria-label={label}
  focusable="false"
>
  {#each ICON_PATHS[name] as d (d)}
    <path {d} />
  {/each}
</svg>

<style>
  .icon {
    display: block;
    flex-shrink: 0;
  }
</style>
