/**
 * Hash routes: #/detect (default), #/sessions, #/sessions/<id>, #/models, #/analytics, #/settings.
 * Pure helpers here; the reactive wrapper is in stores/router.svelte.ts.
 */
export const ROUTES = ['detect', 'sessions', 'models', 'analytics', 'settings'] as const;
export type RouteName = (typeof ROUTES)[number];

export const DEFAULT_ROUTE: RouteName = 'detect';

export const ROUTE_TITLES: Record<RouteName, string> = {
  detect: 'Detect',
  sessions: 'Sessions',
  models: 'Models',
  analytics: 'Analytics',
  settings: 'Settings',
};

/** Routes that take one more path segment, such as `#/sessions/<id>`. */
const ROUTES_WITH_ID: readonly RouteName[] = ['sessions'];

export interface RouteLocation {
  name: RouteName;
  /** The second path segment, decoded, for routes that take one (sessions). Otherwise null. */
  id: string | null;
  /** False when the hash named no known route (including an empty hash). The store rewrites those. */
  known: boolean;
}

/** Reads a hash into a route, an optional id and whether the route was recognised. */
export function parseLocation(hash: string): RouteLocation {
  const [path] = hash.replace(/^#\/?/, '').split(/[?#]/);
  const [head = '', tail] = path.split('/');
  const cleaned = head.trim().toLowerCase();
  const known = (ROUTES as readonly string[]).includes(cleaned);
  const name = known ? (cleaned as RouteName) : DEFAULT_ROUTE;
  let id: string | null = null;
  if (known && ROUTES_WITH_ID.includes(name) && tail) {
    try {
      id = decodeURIComponent(tail);
    } catch {
      id = null;
    }
  }
  return { name, id, known };
}

/** `#/settings` becomes "settings". Anything unknown, including an empty hash, becomes the default route. */
export function parseRoute(hash: string): RouteName {
  return parseLocation(hash).name;
}

export function routeHref(name: RouteName, id?: string | null): string {
  if (id && ROUTES_WITH_ID.includes(name)) return `#/${name}/${encodeURIComponent(id)}`;
  return `#/${name}`;
}
