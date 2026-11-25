/**
 * Opens WebSockets for the app. In mock mode the socket is a fake that follows the same
 * protocol (see lib/mock/mock-socket.ts). Covered by transport.test.ts for URL building.
 */

export interface LocationLike {
  protocol: string;
  host: string;
}

/** `/ws/video` becomes `ws://host/ws/video` on http pages and `wss://` on https pages. */
export function toWebSocketUrl(path: string, location: LocationLike): string {
  const scheme = location.protocol === 'https:' ? 'wss' : 'ws';
  return `${scheme}://${location.host}${path}`;
}

export async function openWebSocket(path: string): Promise<WebSocket> {
  if (__MIRA_MOCK__) {
    const { openMockSocket } = await import('../mock/mock-socket');
    return openMockSocket(path) as unknown as WebSocket;
  }
  const url = toWebSocketUrl(path, window.location);
  return new WebSocket(url);
}
