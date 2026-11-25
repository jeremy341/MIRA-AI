/**
 * Hash routes: #/detect (default), #/sessions, #/models, #/analytics, #/settings.
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

/** `#/settings` becomes "settings". Anything unknown, including an empty hash, becomes the default route. */
export function parseRoute(hash: string): RouteName {
  const cleaned = hash.replace(/^#\/?/, '').split(/[?#/]/)[0].trim().toLowerCase();
  return (ROUTES as readonly string[]).includes(cleaned) ? (cleaned as RouteName) : DEFAULT_ROUTE;
}

export function routeHref(name: RouteName): string {
  return `#/${name}`;
}
