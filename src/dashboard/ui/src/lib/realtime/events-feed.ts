/**
 * The events socket (`/ws/v1/events`). Parses the `{type, ts, data}` envelopes and fans them out
 * to subscribers. Reconnects with backoff; after repeated failures it becomes 'unavailable'
 * (the server does not have the endpoint yet) and stops retrying.
 */
import type { BusEvent, EventsSocketMessage, EventType } from '../types';
import { ReconnectingSocket, type LinkInfo, type LinkState } from './reconnect';
import { openWebSocket } from './transport';

export const EVENTS_PATH = '/ws/v1/events';

export type EventHandler = (event: BusEvent) => void;

/** Parses one message. Returns null for `ping`, `hello` and anything that is not a bus event. */
export function parseEventMessage(text: string): BusEvent | null {
  let value: unknown;
  try {
    value = JSON.parse(text);
  } catch {
    return null;
  }
  if (!value || typeof value !== 'object') return null;
  const message = value as EventsSocketMessage;
  if (message.type === 'hello' || message.type === 'ping') return null;
  if (typeof message.type !== 'string' || !('data' in message)) return null;
  return message as BusEvent;
}

export class EventsFeed {
  private readonly handlers = new Set<EventHandler>();
  private readonly socket: ReconnectingSocket;
  private readonly listeners = new Set<(state: LinkState, info: LinkInfo) => void>();

  constructor(open: (path: string) => Promise<WebSocket> = openWebSocket) {
    this.socket = new ReconnectingSocket({
      path: EVENTS_PATH,
      open,
      maxAttempts: 6,
      baseDelayMs: 1_000,
      maxDelayMs: 30_000,
      onMessage: (text) => {
        const event = parseEventMessage(text);
        if (!event) return;
        for (const handler of this.handlers) handler(event);
      },
      onState: (state, info) => {
        for (const listener of this.listeners) listener(state, info);
      },
    });
  }

  get state(): LinkState {
    return this.socket.state;
  }

  start(): void {
    this.socket.start();
  }

  stop(): void {
    this.socket.stop();
  }

  retryNow(): void {
    this.socket.retryNow();
  }

  /** Subscribe to every event, or only to the given types. Returns an unsubscribe function. */
  subscribe(handler: EventHandler, types?: readonly EventType[]): () => void {
    const wrapped: EventHandler = types
      ? (event) => {
          if (types.includes(event.type)) handler(event);
        }
      : handler;
    this.handlers.add(wrapped);
    return () => {
      this.handlers.delete(wrapped);
    };
  }

  onLinkState(listener: (state: LinkState, info: LinkInfo) => void): () => void {
    this.listeners.add(listener);
    return () => {
      this.listeners.delete(listener);
    };
  }
}

export const eventsFeed = new EventsFeed();
