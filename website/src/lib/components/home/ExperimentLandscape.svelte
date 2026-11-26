<script lang="ts">
  /**
   * Experiment landscape: the documented experiments as a 3D bar chart.
   *
   * Isolated on purpose: remove the <Landscape> section from the Home page and nothing else changes. three.js is
   * imported dynamically, and only when the
   * card is near the viewport (an IntersectionObserver with a 400px margin), the viewer does not prefer reduced motion, the card is wide enough,
   * the device is not a phone held sideways, and WebGL works. This is checked again whenever the card or the screen changes. In every other case this component renders the same data as flat HTML bars (also the server
   * output, so it works without JavaScript). The choice never depends on the page language.
   *
   * Props
   *   rows    LandscapeRow[] from $lib/landscape-data (the single source also used by the table)
   *   lang    "en" | "de"
   *   labels  texts of the chart (see Labels below)
   */
  import { onMount, tick } from 'svelte';
  import type { LandscapeRow } from '$lib/landscape-data';
  import type { Locale } from '$i18n/config';
  import { layoutRows } from '$lib/landscape/layout';
  import { flatReason, SIDEWAYS_PHONE_QUERY } from '$lib/landscape/mode';
  import type { Point, SceneHandle } from '$lib/landscape/scene';

  type Labels = {
    chartLabel: string;
    stageA: string;
    stageB: string;
    metricA: string;
    metricB: string;
    noScore: string;
    noScoreShort: string;
    axisTick: string;
    highlighted: string;
    /** Interaction hint of the 3D chart. */
    hint: string;
    /** Caption line of the flat bars. */
    hintFlat: string;
    resetView: string;
  };

  let { rows, lang, labels }: { rows: LandscapeRow[]; lang: Locale; labels: Labels } = $props();

  // The parent remounts this component when the language changes ({#key}), so the rows are read once.
  // svelte-ignore state_referenced_locally
  const layout = layoutRows(rows);
  // svelte-ignore state_referenced_locally
  const rowById = new Map(rows.map((row) => [row.id, row]));
  const zoneRows = (stage: 'A' | 'B') => rows.filter((row) => row.stage === stage);
  const stageTitle = (stage: 'A' | 'B') => (stage === 'A' ? labels.stageA : labels.stageB);
  const stageMetric = (stage: 'A' | 'B') => (stage === 'A' ? labels.metricA : labels.metricB);
  const axisText = (value: number) => labels.axisTick.replace('{n}', String(value));
  /** The unit is dropped on the columns that are not highlighted (the axis labels carry it): shorter labels overlap less. */
  const shortValue = (text: string) => text.replace(/\s*%$/, '');
  const describe = (row: LandscapeRow) =>
    row.value === null
      ? `${row.id}, ${row.model}, ${labels.noScore}`
      : `${row.id}, ${row.model}, ${row.metric} ${row.valueText}, ${row.split}`;

  /** 'flat' until the 3D scene has drawn its first frame. */
  let mode = $state<'flat' | '3d'>('flat');
  let mounted3d = $state(false);
  let activeId = $state<string | null>(null);
  let reason = $state('server');
  /** Roving tabindex: the group is one Tab stop and the arrow keys move between the columns. */
  let roving = $state(layout.columns[0]?.id ?? '');

  let root: HTMLDivElement | undefined = $state();
  let stage: HTMLDivElement | undefined = $state();
  let tip: HTMLDivElement | undefined = $state();
  const labelEls: Record<string, HTMLElement | undefined> = {};

  const active = $derived(activeId ? (rowById.get(activeId) ?? null) : null);

  /** Cached label widths (they change with the font or the theme, not per frame). */
  const widths = new Map<string, number>();
  let widthsScale = 0;
  const valueKeys = layout.columns.map((column) => `value:${column.id}`);
  const valueAlign = new Map(layout.anchors.filter((anchor) => anchor.kind === 'value').map((anchor) => [anchor.key, anchor.align]));
  const highlighted = valueKeys.filter((key) => rowById.get(key.slice(6))?.highlight);
  const others = valueKeys.filter((key) => !rowById.get(key.slice(6))?.highlight);

  /**
   * Every column prints its value. Labels are shown in priority order (highlighted columns first, then the others
   * from left to right) and a label that would overlap one already shown is hidden. The active column's own label is
   * hidden as well, because the tooltip prints its value.
   */
  /** Screen pixels per CSS pixel of the 16px design: the label offsets are rem and grow on large screens. */
  const rootScale = () => parseFloat(getComputedStyle(document.documentElement).fontSize) / 16;

  function declutter(positions: Map<string, Point>) {
    const u = rootScale();
    if (u !== widthsScale) {
      widths.clear();
      widthsScale = u;
    }
    const shown: Array<{ left: number; right: number; top: number; bottom: number }> = [];
    for (const key of [...highlighted, ...others]) {
      const el = labelEls[key];
      const point = positions.get(key);
      if (!el || !point) continue;
      let width = widths.get(key) ?? 0;
      if (!width) {
        width = el.offsetWidth;
        if (width) widths.set(key, width);
      }
      const align = valueAlign.get(key);
      const left = align === 'end' ? point.x - width + 8 * u : align === 'start' ? point.x - 8 * u : point.x - width / 2;
      const box = { left: left - 3 * u, right: left + width + 3 * u, top: point.y - 27 * u, bottom: point.y - 10 * u };
      const hit = shown.some((other) => box.left < other.right && box.right > other.left && box.top < other.bottom && box.bottom > other.top);
      const hidden = hit || key === `value:${activeId}`;
      el.dataset.hidden = hidden ? 'true' : 'false';
      if (!hidden) shown.push(box);
    }
  }

  function position(positions: Map<string, Point>) {
    for (const [key, point] of positions) {
      const el = key === 'tip' ? tip : labelEls[key];
      if (!el) continue;
      let x = point.x;
      let y = point.y;
      if (key === 'tip' && stage) {
        // Above the column when there is room. Otherwise to the side of it (away from the nearer edge), so the tooltip
        // does not sit on top of the columns around the active one.
        const w = el.offsetWidth;
        const h = el.offsetHeight;
        const u = rootScale();
        const roomAbove = point.y >= h + 22 * u;
        let side: 'above' | 'left' | 'right' = 'above';
        if (!roomAbove) side = point.x - w - 24 * u >= 4 && (point.x > stage.clientWidth / 2 || point.x + w + 24 * u > stage.clientWidth - 4) ? 'left' : 'right';
        if (side === 'above') {
          x = Math.min(Math.max(x, w / 2 + 8), stage.clientWidth - w / 2 - 8);
        } else {
          y = Math.min(Math.max(y, h / 2 + 6), stage.clientHeight - h / 2 - 6);
        }
        el.dataset.side = side;
      }
      el.style.setProperty('--x', `${x.toFixed(1)}px`);
      el.style.setProperty('--y', `${y.toFixed(1)}px`);
    }
    declutter(positions);
  }

  let scene: SceneHandle | null = null;

  function fallback(why: string) {
    reason = why;
    mode = 'flat';
    scene?.dispose();
    scene = null;
    mounted3d = false;
    activeId = null;
  }

  function onEscape(event: KeyboardEvent) {
    if (event.key === 'Escape') scene?.clearSelection();
  }

  onMount(() => {
    const card = root;
    if (!card) return;
    const motion = matchMedia('(prefers-reduced-motion: reduce)');
    const sideways = matchMedia(SIDEWAYS_PHONE_QUERY);

    /** 'idle': flat bars, free to try 3D. 'wanted': waiting for the card to come near, loading it, or showing it. */
    let state: 'idle' | 'wanted' = 'idle';
    /** Set when 3D failed. A later size change must not try it again. */
    let broken = false;
    /** Goes up whenever 3D is torn down, so that a load still in flight knows it is too late. */
    let generation = 0;
    let cleanups: Array<() => void> = [];

    function tearDown() {
      generation += 1;
      for (const cleanup of cleanups.splice(0)) cleanup();
      state = 'idle';
    }

    function fail(why: string) {
      broken = true;
      tearDown();
      fallback(why);
    }

    async function start(mine: number) {
      mounted3d = true;
      await tick();
      if (mine !== generation || !stage) return;
      try {
        // A failed chunk request is retried once, so a network blip does not decide the mode. WebGL support is
        // tested by creating the renderer itself (it throws when there is no context): there is no probe canvas
        // whose context could compete with the real one.
        const module = await import('$lib/landscape/scene').catch(() => import('$lib/landscape/scene'));
        if (mine !== generation || !stage) return;
        scene = module.createScene({
          host: stage,
          layout,
          onProject: position,
          onActive: (id) => (activeId = id),
          onContextLost: () => fail('context-lost'),
        });
      } catch (error) {
        if (mine === generation) fail(error instanceof Error && /webgl|context/i.test(error.message) ? 'no-webgl' : 'error');
        return;
      }
      mode = '3d';
      reason = '3d';

      const visibility = new IntersectionObserver((entries) => {
        for (const entry of entries) scene?.setVisible(entry.isIntersecting);
      });
      visibility.observe(card!);
      window.addEventListener('keydown', onEscape);
      cleanups.push(() => {
        visibility.disconnect();
        window.removeEventListener('keydown', onEscape);
      });
    }

    /** Pick flat or 3D for the current screen. The flat bars need no download, so they are decided at once. */
    function choose() {
      const why = flatReason({
        reducedMotion: motion.matches,
        width: card!.getBoundingClientRect().width,
        sidewaysPhone: sideways.matches
      });
      if (why) {
        tearDown();
        fallback(why);
      } else if (state === 'idle' && !broken) {
        state = 'wanted';
        const mine = generation;
        // three.js is fetched only when the card comes within 400px of the screen.
        const near = new IntersectionObserver(
          (entries) => {
            if (!entries.some((entry) => entry.isIntersecting)) return;
            near.disconnect();
            start(mine);
          },
          { rootMargin: '400px 0px' }
        );
        near.observe(card!);
        cleanups.push(() => near.disconnect());
      }
    }

    const sizes = new ResizeObserver(choose);
    sizes.observe(card);
    motion.addEventListener('change', choose);
    sideways.addEventListener('change', choose);
    choose();

    return () => {
      sizes.disconnect();
      motion.removeEventListener('change', choose);
      sideways.removeEventListener('change', choose);
      tearDown();
      scene?.dispose();
      scene = null;
    };
  });

  function onKey(event: KeyboardEvent) {
    const target = event.target as HTMLElement;
    if (!target.classList?.contains('ls-id')) return;
    const buttons = Array.from(stage?.querySelectorAll<HTMLButtonElement>('button.ls-id') ?? []);
    const index = buttons.indexOf(target as HTMLButtonElement);
    if (index < 0) return;
    let next: HTMLButtonElement | undefined;
    if (event.key === 'ArrowRight' || event.key === 'ArrowDown') next = buttons[Math.min(index + 1, buttons.length - 1)];
    else if (event.key === 'ArrowLeft' || event.key === 'ArrowUp') next = buttons[Math.max(index - 1, 0)];
    else if (event.key === 'Home') next = buttons[0];
    else if (event.key === 'End') next = buttons[buttons.length - 1];
    if (!next) return;
    event.preventDefault();
    next.focus();
  }

  function resetView() {
    scene?.resetView();
  }
</script>

<div class="ls" bind:this={root} data-mode={mode} data-reason={reason}>
  {#if mounted3d}
    <!-- The arrow keys move between the column buttons inside; the group itself is not a control. -->
    <!-- svelte-ignore a11y_no_noninteractive_element_interactions -->
    <div
      class="ls-stage"
      class:ready={mode === '3d'}
      bind:this={stage}
      role="group"
      aria-label={labels.chartLabel}
      onkeydown={onKey}
    >
      {#each layout.anchors as anchor (anchor.key)}
        {#if anchor.kind === 'id'}
          {@const id = anchor.key.slice(3)}
          {@const row = rowById.get(id)}
          {#if row}
            <button
              type="button"
              class="ls-lab ls-id"
              class:hl={row.highlight}
              class:on={activeId === id}
              aria-label={describe(row)}
              tabindex={roving === id ? 0 : -1}
              bind:this={labelEls[anchor.key]}
              onfocus={() => {
                roving = id;
                scene?.setFocus(id);
              }}
              onblur={() => scene?.setFocus(null)}
            >{row.short}</button>
          {/if}
        {:else if anchor.kind === 'value'}
          {@const row = rowById.get(anchor.key.slice(6))}
          {#if row}
            <span
              class="ls-lab ls-val"
              class:none={row.value === null}
              class:hl={row.highlight}
              class:al-end={anchor.align === 'end'}
              class:al-start={anchor.align === 'start'}
              data-hidden="false"
              aria-hidden="true"
              bind:this={labelEls[anchor.key]}
            >
              {row.value === null ? labels.noScoreShort : row.highlight ? row.valueText : shortValue(row.valueText)}
            </span>
          {/if}
        {:else if anchor.kind === 'axis'}
          <span class="ls-lab ls-axis" aria-hidden="true" bind:this={labelEls[anchor.key]}>{axisText(Number(anchor.key.slice(5)))}</span>
        {:else}
          <span class="ls-lab ls-zone" aria-hidden="true" bind:this={labelEls[anchor.key]}>
            {stageTitle(anchor.key.slice(5) as 'A' | 'B')}
          </span>
        {/if}
      {/each}
      {#if active}
        <div class="ls-tip" data-side="above" bind:this={tip} aria-hidden="true">
          <p class="ls-tip-id">
            <strong>{active.id}</strong>
            {#if active.highlight}<span class="ls-tip-badge">{labels.highlighted}</span>{/if}
          </p>
          <p class="ls-tip-model">{active.model}</p>
          <p class="ls-tip-value">
            {#if active.value === null}
              {labels.noScore}
            {:else}
              <span>{active.metric}</span> <strong>{active.valueText}</strong>
            {/if}
          </p>
          <p class="ls-tip-split">{active.split}</p>
        </div>
      {/if}
    </div>
  {/if}

  {#if mode === 'flat'}
    <div class="ls-flat" role="group" aria-label={labels.chartLabel}>
      {#each ['B', 'A'] as const as stageKey (stageKey)}
        <div class="ls-group" data-stage={stageKey}>
          <h3>
            {stageTitle(stageKey)}
            <span class="ls-metric">{stageMetric(stageKey)}</span>
          </h3>
          <ul>
            {#each zoneRows(stageKey) as row (row.id)}
              <li class:hl={row.highlight}>
                <span class="ls-flat-id">{row.id}</span>
                <span class="ls-track">
                  {#if row.value === null}
                    <span class="ls-none">{labels.noScore}</span>
                  {:else}
                    <span class="ls-fill" style:width="{row.value}%"></span>
                  {/if}
                </span>
                <span class="ls-flat-value">{row.value === null ? '' : row.valueText}</span>
              </li>
            {/each}
          </ul>
        </div>
      {/each}
    </div>
  {/if}

  <div class="ls-foot">
    <p class="ls-hint">{mode === '3d' ? labels.hint : labels.hintFlat}</p>
    {#if mode === '3d'}
      <button type="button" class="ls-reset" onclick={resetView}>{labels.resetView}</button>
    {/if}
  </div>
</div>

<style>
  .ls {
    --ls-h: clamp(18rem, 31vw, 25rem);
    position: relative;
    display: grid;
    grid-template-rows: auto auto;
    row-gap: 0.75rem;
    min-width: 0;
    color: var(--mira-text);
    font-size: 0.8125rem;
  }

  /* 3D stage ---------------------------------------------------------- */
  .ls-stage {
    position: relative;
    grid-area: 1 / 1;
    height: var(--ls-h);
    overflow: hidden;
    container-type: inline-size;
    visibility: hidden;
  }
  .ls-stage.ready {
    visibility: visible;
  }
  .ls :global(.ls-canvas) {
    position: absolute;
    inset: 0;
    display: block;
    width: 100%;
    height: 100%;
    touch-action: pan-y;
  }
  .ls-lab {
    position: absolute;
    top: 0;
    left: 0;
    margin: 0;
    padding: 0;
    border: 0;
    background: none;
    transform: translate3d(var(--x, -999px), var(--y, -999px), 0);
    color: var(--mira-muted);
    font-family: var(--mira-font-mono);
    font-size: 0.6875rem;
    line-height: 1;
    white-space: nowrap;
    pointer-events: none;
  }
  .ls-id {
    translate: -50% 0.3125rem;
    padding: 0.3125rem 0.25rem;
    border-radius: 0.25rem;
    cursor: pointer;
    pointer-events: auto;
  }
  .ls-id.hl {
    color: var(--mira-link);
    font-weight: 700;
  }
  .ls-id.on {
    background: var(--mira-note-bg);
    color: var(--mira-note-title);
  }
  .ls-id:focus-visible {
    outline: 2px solid var(--mira-focus);
    outline-offset: 1px;
  }
  .ls-val {
    translate: -50% calc(-100% - 0.75rem);
    color: var(--mira-muted);
    font-weight: 400;
    /* A halo in the card colour keeps the number legible where it crosses a reference line. */
    text-shadow:
      0 0 2px var(--mira-surface),
      0 0 3px var(--mira-surface),
      0 0 4px var(--mira-surface);
  }
  .ls-val.hl {
    color: var(--mira-text);
    font-weight: 700;
  }
  /* The attributes are set from script (per frame), so Svelte cannot see them in the markup: :global keeps the rule. */
  .ls-val:global([data-hidden='true']) {
    visibility: hidden;
  }
  .ls-val.al-end {
    translate: calc(-100% + 0.5rem) calc(-100% - 0.75rem);
  }
  .ls-val.al-start {
    translate: -0.5rem calc(-100% - 0.75rem);
  }
  .ls-val.none {
    font-family: var(--mira-font-sans);
  }
  .ls-axis {
    /* Left of its anchor, so the tick does not run into the value above the first column. */
    translate: calc(-100% - 0.375rem) calc(-100% - 0.125rem);
  }
  .ls-zone {
    translate: -50% 0;
    color: var(--mira-text);
    font-family: var(--mira-font-sans);
    font-size: 0.75rem;
    font-weight: 700;
  }
  @container (max-width: 760px) {
    .ls-id {
      padding-inline: 0.125rem;
    }
  }

  .ls-tip {
    position: absolute;
    top: 0;
    left: 0;
    z-index: 2;
    width: max-content;
    max-width: 17rem;
    padding: 0.625rem 0.75rem;
    border: 1px solid var(--mira-border-strong);
    border-radius: var(--mira-radius-control);
    background: var(--mira-raised);
    box-shadow: var(--mira-shadow-raised);
    transform: translate3d(var(--x, -999px), var(--y, -999px), 0);
    translate: -50% calc(-100% - 0.875rem);
    pointer-events: none;
    line-height: 1.4;
  }
  .ls-tip:global([data-side='left']) {
    translate: calc(-100% - 1.375rem) -50%;
  }
  .ls-tip:global([data-side='right']) {
    translate: 1.375rem -50%;
  }
  .ls-tip p {
    margin: 0;
  }
  .ls-tip-id {
    display: flex;
    flex-wrap: wrap;
    gap: 0.375rem;
    align-items: center;
    font-size: 0.875rem;
  }
  .ls-tip-badge {
    padding: 0.0625rem 0.375rem;
    border-radius: 999px;
    background: var(--mira-badge-bg);
    color: var(--mira-badge-text);
    font-size: 0.6875rem;
    font-weight: 600;
  }
  .ls-tip-model {
    color: var(--mira-muted);
  }
  .ls-tip-value {
    margin-top: 0.25rem !important;
    font-size: 0.9375rem;
  }
  .ls-tip-value span {
    color: var(--mira-muted);
    font-size: 0.8125rem;
  }
  .ls-tip-split {
    margin-top: 0.125rem !important;
    color: var(--mira-muted);
    font-size: 0.75rem;
  }

  /* Footer: hint line and the reset button -------------------------------- */
  .ls-foot {
    grid-area: 2 / 1;
    display: flex;
    flex-wrap: wrap;
    gap: 0.5rem 1rem;
    align-items: center;
    justify-content: space-between;
  }
  .ls-hint {
    margin: 0;
    color: var(--mira-muted);
    font-size: 0.8125rem;
  }
  .ls-reset {
    padding: 0.375rem 0.75rem;
    border: 1px solid var(--mira-border-strong);
    border-radius: var(--mira-radius-control);
    background: var(--mira-surface);
    color: var(--mira-text);
    font: inherit;
    font-size: 0.8125rem;
    font-weight: 600;
    cursor: pointer;
  }
  .ls-reset:hover {
    background: var(--mira-bg);
  }
  .ls-reset:focus-visible {
    outline: 2px solid var(--mira-focus);
    outline-offset: 2px;
  }

  /* Flat fallback ------------------------------------------------------ */
  .ls-flat {
    grid-area: 1 / 1;
    display: grid;
    gap: 1.5rem 2.5rem;
    min-width: 0;
  }
  .ls-group h3 {
    display: flex;
    flex-wrap: wrap;
    gap: 0.25rem 0.75rem;
    align-items: baseline;
    margin: 0 0 0.5rem;
    font-size: 0.9375rem;
    font-weight: 700;
  }
  .ls-metric {
    color: var(--mira-muted);
    font-size: 0.8125rem;
    font-weight: 400;
  }
  .ls-group ul {
    display: grid;
    gap: 0.3125rem;
    margin: 0;
    padding: 0;
    list-style: none;
  }
  .ls-group li {
    display: grid;
    grid-template-columns: 4.25rem minmax(0, 1fr) 4.25rem;
    gap: 0.625rem;
    align-items: center;
    margin: 0;
  }
  .ls-flat-id {
    color: var(--mira-muted);
    font-family: var(--mira-font-mono);
    font-size: 0.75rem;
  }
  .hl .ls-flat-id {
    color: var(--mira-link);
    font-weight: 700;
  }
  .ls-track {
    display: flex;
    align-items: center;
    height: 0.875rem;
    border-radius: 999px;
    background: var(--mira-table-head);
  }
  .ls-fill {
    display: block;
    height: 100%;
    border-radius: 999px;
    background: var(--mira-stage-b);
  }
  .ls-group[data-stage='A'] .ls-fill {
    background: var(--mira-stage-a);
  }
  .hl .ls-fill {
    background: var(--mira-accent);
  }
  .ls-none {
    padding-inline: 0.5rem;
    color: var(--mira-muted);
    font-size: 0.6875rem;
    white-space: nowrap;
  }
  .ls-flat-value {
    font-family: var(--mira-font-mono);
    font-size: 0.75rem;
    text-align: end;
    white-space: nowrap;
  }
  .hl .ls-flat-value {
    font-weight: 700;
  }

  @media (min-width: 52rem) {
    .ls-flat {
      grid-template-columns: minmax(0, 1.3fr) minmax(0, 1fr);
      align-items: start;
    }
  }

  @media (prefers-reduced-motion: reduce) {
    .ls-reset {
      transition: none;
    }
  }
</style>
