/**
 * Fan-out for the mock events feed (/ws/v1/events). The mock backend publishes here when something
 * happens (an arm command completes, a job moves), and every open mock events socket forwards it.
 */
import type { EventType } from '../types';

export type MockEventListener = (type: EventType, data: unknown) => void;

const listeners = new Set<MockEventListener>();

export function subscribeMockEvents(listener: MockEventListener): () => void {
  listeners.add(listener);
  return () => {
    listeners.delete(listener);
  };
}

export function publishMockEvent(type: EventType, data: unknown): void {
  for (const listener of [...listeners]) listener(type, data);
}

export function mockEventListenerCount(): number {
  return listeners.size;
}
