<script lang="ts">
  import Icon, { type IconName } from '../components/Icon.svelte';
  import StatusDot from '../components/StatusDot.svelte';
  import { ROUTES, ROUTE_TITLES, routeHref, type RouteName } from '../router';
  import { router } from '../stores/router.svelte';
  import { system } from '../stores/system.svelte';

  const ICONS: Record<RouteName, IconName> = {
    detect: 'detect',
    sessions: 'sessions',
    models: 'models',
    analytics: 'analytics',
    settings: 'settings',
  };

  type Dot = 'success' | 'warning' | 'accent' | undefined;

  function dotFor(name: RouteName): Dot {
    switch (name) {
      case 'detect':
        return system.streaming ? 'success' : undefined;
      case 'sessions':
        return system.activeSession ? 'accent' : undefined;
      case 'models':
        return system.modelLoaded ? 'success' : undefined;
      case 'settings':
        return system.streaming ? 'warning' : undefined;
      default:
        return undefined;
    }
  }

  /** Words for screen readers that explain the dot (the colour alone is not enough). */
  function hintFor(name: RouteName): string {
    switch (name) {
      case 'detect':
        return system.streaming ? ', stream running' : '';
      case 'sessions':
        return system.activeSession ? ', a session is recording' : '';
      case 'models':
        return system.modelLoaded ? ', model loaded' : '';
      case 'settings':
        return system.streaming ? ', locked while the stream runs' : '';
      default:
        return '';
    }
  }

  const items = $derived(
    ROUTES.map((name) => ({
      name,
      label: ROUTE_TITLES[name],
      icon: ICONS[name],
      dot: dotFor(name),
      hint: hintFor(name),
    })),
  );
</script>

<aside class="sidebar">
  <div class="brand">
    <span class="mark" aria-hidden="true"><svg viewBox="0 0 24 24" width="18" height="18"><rect x="4" y="6" width="16" height="12" rx="3.5" fill="none" stroke="currentColor" stroke-width="2" /><rect x="9.5" y="9.5" width="5" height="5" rx="1.2" fill="var(--accent)" /></svg></span>
    <span class="word">
      <span class="name">MIRA</span>
      <span class="sub">Dashboard</span>
    </span>
  </div>

  <nav class="nav" aria-label="Main">
    {#each items as item (item.name)}
      {@const active = router.current === item.name}
      <a class="item" class:active href={routeHref(item.name)} aria-current={active ? 'page' : undefined}>
        <span class="icon"><Icon name={item.icon} size={20} /></span>
        <span class="label">{item.label}</span>
        {#if item.dot}<StatusDot tone={item.dot} pulse={item.name === 'detect' && system.streaming} />{/if}
        {#if item.hint}<span class="visually-hidden">{item.hint}</span>{/if}
      </a>
    {/each}
  </nav>
</aside>

<style>
  .sidebar {
    position: sticky;
    top: 0;
    z-index: 40;
    display: flex;
    flex-direction: column;
    gap: var(--space-6);
    height: 100dvh;
    padding: var(--space-5) var(--space-3);
    background: var(--surface);
    border-right: 1px solid var(--rule);
  }
  .brand {
    display: flex;
    align-items: center;
    gap: var(--space-2);
    padding: 0 var(--space-2);
  }
  .mark {
    display: grid;
    place-items: center;
    width: 2.25rem;
    height: 2.25rem;
    border-radius: var(--radius-control);
    background: var(--ink);
    color: var(--surface);
  }
  .word {
    display: grid;
    line-height: 1.15;
  }
  .name {
    font-weight: var(--font-weight-bold);
    letter-spacing: 0.02em;
  }
  .sub {
    font-size: var(--text-micro);
    color: var(--ink-soft);
  }
  .nav {
    display: grid;
    gap: var(--space-1);
  }
  .item {
    display: flex;
    align-items: center;
    gap: var(--space-3);
    min-height: 2.75rem;
    padding: 0 var(--space-3);
    border-radius: var(--radius-control);
    color: var(--ink-soft);
    font-size: var(--text-small);
    font-weight: var(--font-weight-medium);
    text-decoration: none;
    transition:
      background-color var(--dur-fast) ease-out,
      color var(--dur-fast) ease-out;
  }
  .item:hover {
    background: var(--hover);
    color: var(--ink);
  }
  .item.active {
    background: var(--accent-subtle);
    color: var(--accent-strong);
  }
  .item:focus-visible {
    outline: 2px solid var(--accent);
    outline-offset: 1px;
  }
  .icon {
    display: flex;
  }
  .label {
    flex: 1;
    min-width: 0;
  }

  /* Below 900 px the sidebar becomes a bottom tab bar. */
  @media (max-width: 899px) {
    .sidebar {
      position: fixed;
      top: auto;
      left: 0;
      right: 0;
      bottom: 0;
      width: 100%;
      max-width: 100vw;
      /* Fixed height, so the toast region can sit exactly above it. */
      height: calc(var(--tabbar-height) + env(safe-area-inset-bottom, 0px));
      flex-direction: row;
      align-items: stretch;
      padding: var(--space-1) var(--space-2) calc(var(--space-1) + env(safe-area-inset-bottom, 0px));
      border-right: 0;
      border-top: 1px solid var(--rule);
      box-shadow: 0 -4px 16px rgb(0 0 0 / 5%);
    }
    .brand {
      display: none;
    }
    .nav {
      flex: 1;
      grid-template-columns: repeat(5, minmax(0, 1fr));
      gap: 0;
    }
    .item {
      position: relative;
      flex-direction: column;
      justify-content: center;
      gap: 0.125rem;
      min-height: 3.25rem;
      padding: var(--space-1);
      font-size: 0.6875rem;
      text-align: center;
    }
    .label {
      flex: none;
    }
    .item :global(.dot) {
      position: absolute;
      top: 0.35rem;
      right: 0.65rem;
    }
  }
</style>
