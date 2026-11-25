/**
 * Turns raw state into the words and tones the top status bar shows. Pure, covered by status-summary.test.ts.
 */
import type { LinkInfo, LinkState } from './realtime/reconnect';
import type { SessionSummary, StatusResponse } from './types';

export type Tone = 'neutral' | 'success' | 'warning' | 'danger' | 'accent';

export interface Summary {
  text: string;
  tone: Tone;
}

export function describeModel(status: StatusResponse | null, appliedName: string | null, statusError: string | null): Summary {
  if (!status) {
    return statusError ? { text: 'Server offline', tone: 'danger' } : { text: 'Checking', tone: 'neutral' };
  }
  if (!status.model_loaded) return { text: 'No model', tone: 'neutral' };
  return { text: appliedName ?? 'Model loaded', tone: 'success' };
}

export function describeConnection(link: LinkState, info: LinkInfo, statusError: string | null): Summary {
  if (statusError && link !== 'open') return { text: 'Server offline', tone: 'danger' };
  switch (link) {
    case 'open':
      return { text: 'Connected', tone: 'success' };
    case 'connecting':
      return { text: 'Connecting', tone: 'warning' };
    case 'reconnecting':
      return {
        text: info.retryInMs !== null ? `Reconnecting in ${Math.ceil(info.retryInMs / 1000)} s` : 'Reconnecting',
        tone: 'warning',
      };
    case 'unavailable':
      return { text: 'Live link unavailable', tone: 'danger' };
    case 'closed':
      return { text: 'Offline', tone: 'neutral' };
  }
}

/** `framesFresh` is true when a frame arrived recently. A stream that has not produced one yet is "Starting". */
export function describeStream(status: StatusResponse | null, framesFresh: boolean): Summary {
  if (!status) return { text: 'Unknown', tone: 'neutral' };
  if (status.streaming) {
    return framesFresh ? { text: 'Live', tone: 'success' } : { text: 'Starting', tone: 'warning' };
  }
  return { text: 'Stopped', tone: 'neutral' };
}

export function describeSession(activeSession: SessionSummary | null, sessionsState: 'unknown' | 'ready' | 'unavailable'): Summary {
  if (activeSession) return { text: activeSession.name, tone: 'accent' };
  if (sessionsState === 'unknown') return { text: 'Checking', tone: 'neutral' };
  return { text: 'No session', tone: 'neutral' };
}
