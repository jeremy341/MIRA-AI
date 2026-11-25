import { parseLocation, routeHref, type RouteName } from '../router';

/**
 * The current hash route and its optional id (`#/sessions/<id>`), kept in sync with `hashchange`.
 * Only unknown routes are rewritten; a known route keeps its full hash, id included.
 */
class RouterStore {
  current = $state<RouteName>('detect');
  id = $state<string | null>(null);
  private started = false;

  /** The route and id as a hash. Changes whenever either one changes, so effects can watch it. */
  get path(): string {
    return routeHref(this.current, this.id);
  }

  start(): void {
    if (this.started || typeof window === 'undefined') return;
    this.started = true;
    this.sync();
    window.addEventListener('hashchange', () => this.sync());
  }

  sync(): void {
    if (typeof window === 'undefined') return;
    const location = parseLocation(window.location.hash);
    this.current = location.name;
    this.id = location.id;
    // Normalise an unknown or empty hash to the default route. Known routes keep their hash as it is.
    if (!location.known) {
      window.history.replaceState(null, '', routeHref(location.name));
    }
  }

  navigate(name: RouteName, id?: string | null): void {
    if (typeof window === 'undefined') return;
    window.location.hash = routeHref(name, id);
  }
}

export const router = new RouterStore();
