<script lang="ts">
  /** Small line icons for the docs sidebar and cards. 24 x 24, stroke only, drawn for this site. */
  export type DocIconName =
    | 'rocket'
    | 'sliders'
    | 'layers'
    | 'camera'
    | 'monitor'
    | 'clock'
    | 'download'
    | 'compare'
    | 'upload'
    | 'chart'
    | 'arm'
    | 'database'
    | 'train'
    | 'chip'
    | 'box'
    | 'terminal'
    | 'plug'
    | 'alert'
    | 'help'
    | 'list'
    | 'doc'
    | 'home';

  let { name, size = 18, class: className = '' }: { name: DocIconName; size?: number; class?: string } = $props();

  const PATHS: Record<DocIconName, string> = {
    rocket: 'M5 15c-1.5 1.3-2 4-2 4s2.7-.5 4-2M9 15l-3-3c1-3 4-7 9-8l5-1-1 5c-1 5-5 8-8 9ZM14.5 9.5h.01',
    sliders: 'M4 6h9M17 6h3M4 12h3M11 12h9M4 18h11M19 18h1M13 4v4M7 10v4M17 16v4',
    layers: 'M12 3 3 8l9 5 9-5-9-5ZM3 13l9 5 9-5M3 17.5l9 5 9-5',
    camera: 'M4 8h3l1.5-2h7L17 8h3v11H4V8ZM12 17a3.5 3.5 0 1 0 0-7 3.5 3.5 0 0 0 0 7Z',
    monitor: 'M3 5h18v11H3V5ZM8 20h8M12 16v4',
    clock: 'M12 21a9 9 0 1 0 0-18 9 9 0 0 0 0 18ZM12 7v5l3 2',
    download: 'M12 4v11M7 11l5 5 5-5M5 20h14',
    compare: 'M4 5h7v14H4V5ZM13 5h7v14h-7V5ZM7.5 9v6M16.5 9v6',
    upload: 'M12 16V5M7 9l5-5 5 5M5 20h14',
    chart: 'M4 20V4M4 20h16M8 16v-5M12 16V8M16 16v-8',
    arm: 'M5 20h6M8 20v-6l5-5M13 9l5 2M13 9V4M18 11v4',
    database: 'M4 6c0-1.7 3.6-3 8-3s8 1.3 8 3-3.6 3-8 3-8-1.3-8-3ZM4 6v6c0 1.7 3.6 3 8 3s8-1.3 8-3V6M4 12v6c0 1.7 3.6 3 8 3s8-1.3 8-3v-6',
    train: 'M4 18c3-9 6-12 9-12s4 3 7 3M4 18h16M7 14l-2 .5M12 11l-1.5 1.5',
    chip: 'M7 7h10v10H7V7ZM10 10h4v4h-4v-4ZM9 3v4M15 3v4M9 17v4M15 17v4M3 9h4M3 15h4M17 9h4M17 15h4',
    box: 'M12 3 4 7v10l8 4 8-4V7l-8-4ZM4 7l8 4 8-4M12 11v10',
    terminal: 'M4 5h16v14H4V5ZM8 10l3 2.5L8 15M13 15h3',
    plug: 'M9 3v5M15 3v5M6 8h12v3a6 6 0 0 1-12 0V8ZM12 17v4',
    alert: 'M12 3 2.5 20h19L12 3ZM12 10v4.5M12 17.5h.01',
    help: 'M12 21a9 9 0 1 0 0-18 9 9 0 0 0 0 18ZM9.5 9.5a2.5 2.5 0 1 1 3.5 2.3c-.7.4-1 .9-1 1.7M12 17h.01',
    list: 'M8 6h12M8 12h12M8 18h12M4 6h.01M4 12h.01M4 18h.01',
    doc: 'M6 3h8l4 4v14H6V3ZM14 3v4h4M9 12h6M9 16h6',
    home: 'M4 11 12 4l8 7M6 10v10h12V10M10 20v-5h4v5'
  };
</script>

<svg
  viewBox="0 0 24 24"
  width={size}
  height={size}
  fill="none"
  stroke="currentColor"
  stroke-width="1.7"
  stroke-linecap="round"
  stroke-linejoin="round"
  aria-hidden="true"
  focusable="false"
  class="shrink-0 {className}"
>
  <path d={PATHS[name]} />
</svg>
