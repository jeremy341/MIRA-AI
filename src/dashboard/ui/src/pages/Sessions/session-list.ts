/**
 * Rules for the session list, pure. Covered by session-list.test.ts.
 */
import type { SessionSource, SessionStatus, SessionSummary } from '../../lib/types';

export const PAGE_SIZE = 20;

/** Newest first by start time. The server does not promise an order, so the page sorts. */
export function sortNewestFirst<T extends { started_at: string }>(rows: readonly T[]): T[] {
  return [...rows].sort((a, b) => Date.parse(b.started_at) - Date.parse(a.started_at));
}

/** Adds a page to the list. A session that shows up twice (a new one started while paging) appears once. */
export function mergeSessionPages(current: readonly SessionSummary[], next: readonly SessionSummary[]): SessionSummary[] {
  const byId = new Map<string, SessionSummary>();
  for (const session of [...current, ...next]) byId.set(session.id, session);
  return sortNewestFirst([...byId.values()]);
}

/** A camera session that is still recording. The badge says "Live". */
export function isLive(session: Pick<SessionSummary, 'source' | 'status'>): boolean {
  return session.source === 'camera' && session.status === 'active';
}

/** An active session cannot be deleted: a camera session is live, an import is still running. */
export function canDelete(session: Pick<SessionSummary, 'status'>): boolean {
  return session.status !== 'active';
}

/** Why the delete button is off, in a sentence for the page. Null when deleting is allowed. */
export function deleteBlockedReason(session: Pick<SessionSummary, 'source' | 'status'>): string | null {
  if (canDelete(session)) return null;
  return isLive(session)
    ? 'This camera session is live. Stop it on Detect before deleting it.'
    : 'This import is still running. It can be deleted once it finishes or is cancelled.';
}

export function sourceLabel(source: SessionSource): string {
  switch (source) {
    case 'camera':
      return 'Camera';
    case 'image':
      return 'Image';
    case 'video':
      return 'Video';
    case 'batch':
      return 'Batch';
  }
}

export function statusLabel(status: SessionStatus): string {
  switch (status) {
    case 'active':
      return 'Running';
    case 'completed':
      return 'Completed';
    case 'failed':
      return 'Failed';
  }
}

/** "Load more" is offered while the list is shorter than the server's total. */
export function hasMore(loaded: number, total: number): boolean {
  return loaded < total;
}
