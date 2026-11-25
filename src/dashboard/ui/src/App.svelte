<script lang="ts">
  import { onMount, type Component } from 'svelte';
  import ToastRegion from './lib/components/ToastRegion.svelte';
  import Sidebar from './lib/layout/Sidebar.svelte';
  import StatusBar from './lib/layout/StatusBar.svelte';
  import { eventsFeed } from './lib/realtime/events-feed';
  import { router } from './lib/stores/router.svelte';
  import { live } from './lib/stores/live.svelte';
  import { system } from './lib/stores/system.svelte';
  import DetectPage from './pages/Detect/Detect.svelte';
  import SessionsPage from './pages/Sessions/Sessions.svelte';
  import ModelsPage from './pages/Models/Models.svelte';
  import AnalyticsPage from './pages/Analytics/Analytics.svelte';
  import SettingsPage from './pages/Settings/Settings.svelte';
  import { ROUTE_TITLES, type RouteName } from './lib/router';

  /** One component per route. Add a page here and in lib/router.ts (ROUTES). */
  const pages: Record<RouteName, Component> = {
    detect: DetectPage,
    sessions: SessionsPage,
    models: ModelsPage,
    analytics: AnalyticsPage,
    settings: SettingsPage,
  };

  const Current = $derived(pages[router.current]);

  let mounted = false;

  // Move focus to the page when the route changes, so keyboard and screen reader users land on the new content.
  $effect(() => {
    void router.current;
    if (!mounted) return;
    document.getElementById('main')?.focus({ preventScroll: false });
    document.title = `${ROUTE_TITLES[router.current]} · MIRA dashboard`;
  });

  onMount(() => {
    mounted = true;
    router.start();
    live.start();
    eventsFeed.start();
    const stopPolling = system.startPolling();
    void system.refreshModels();
    return () => {
      stopPolling();
      live.stop();
      eventsFeed.stop();
    };
  });
</script>

<div class="shell">
  <Sidebar />
  <div class="workspace">
    <StatusBar />
    <main id="main" class="content" tabindex="-1">
      <div class="page">
        <Current />
      </div>
    </main>
  </div>
  <ToastRegion />
</div>

<style>
  .shell {
    display: grid;
    grid-template-columns: var(--sidebar-width) minmax(0, 1fr);
    min-height: 100dvh;
  }
  .workspace {
    min-width: 0;
    display: flex;
    flex-direction: column;
  }
  .content {
    flex: 1;
    min-width: 0;
    padding: var(--page-pad) var(--page-pad) var(--space-12);
  }
  .content:focus {
    outline: none;
  }
  .page {
    max-width: var(--content-max);
    margin: 0 auto;
    min-width: 0;
  }
  @media (max-width: 899px) {
    .shell {
      grid-template-columns: minmax(0, 1fr);
    }
    .content {
      padding-bottom: 6rem;
    }
  }
  @media (max-width: 420px) {
    .content {
      padding-left: 16px;
      padding-right: 16px;
    }
  }
</style>
