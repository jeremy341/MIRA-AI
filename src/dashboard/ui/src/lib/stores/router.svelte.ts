import { parseRoute, routeHref, type RouteName } from '../router';

/** The current hash route, kept in sync with `hashchange`. */
class RouterStore {
  current = $state<RouteName>('detect');
  private started = false;

  start(): void {
    if (this.started || typeof window === 'undefined') return;
    this.started = true;
    this.sync();
    window.addEventListener('hashchange', () => this.sync());
  }

  sync(): void {
    if (typeof window === 'undefined') return;
    const name = parseRoute(window.location.hash);
    this.current = name;
    // Normalise an unknown or empty hash to the default route.
    if (window.location.hash !== routeHref(name)) {
      window.history.replaceState(null, '', routeHref(name));
    }
  }

  navigate(name: RouteName): void {
    if (typeof window === 'undefined') return;
    window.location.hash = routeHref(name);
  }
}

export const router = new RouterStore();
