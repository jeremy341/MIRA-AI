import { api, describeError, isRouteMissing } from '../api';
import type { ModelInfo, SessionSummary, StatusResponse } from '../types';

/** How often the status poll runs. The server status is cheap to read. */
export const STATUS_POLL_MS = 2000;
/** When the v1 sessions route is missing, check again this often (in poll ticks). */
const SESSIONS_RETRY_TICKS = 15;

/**
 * Server status and the active session, shared by the status bar and the pages.
 * Polls /api/status while the page is visible; pauses while the tab is hidden.
 */
class SystemStore {
  status = $state.raw<StatusResponse | null>(null);
  statusError = $state<string | null>(null);
  activeSession = $state.raw<SessionSummary | null>(null);
  /** 'unknown' until the first answer, 'ready' once /api/v1/sessions answers, 'unavailable' on a missing route. */
  sessions = $state<'unknown' | 'ready' | 'unavailable'>('unknown');
  models = $state.raw<ModelInfo[] | null>(null);
  modelsError = $state<string | null>(null);
  private ticks = 0;

  get streaming(): boolean {
    return this.status?.streaming ?? false;
  }

  get cameraReady(): boolean {
    return this.status?.camera_initialized ?? false;
  }

  get modelLoaded(): boolean {
    return this.status?.model_loaded ?? false;
  }

  async refreshStatus(): Promise<void> {
    try {
      this.status = await api.legacy.getStatus();
      this.statusError = null;
    } catch (error) {
      this.statusError = describeError(error, 'The server did not answer.');
    }
  }

  async refreshSession(): Promise<void> {
    try {
      const page = await api.v1.listSessions({ status: 'active', limit: 1 });
      this.activeSession = page.sessions[0] ?? null;
      this.sessions = 'ready';
    } catch (error) {
      if (isRouteMissing(error)) {
        this.sessions = 'unavailable';
        this.activeSession = null;
      }
      // Other errors keep the last known session. The status bar shows the server state.
    }
  }

  async refreshModels(): Promise<void> {
    try {
      const response = await api.legacy.listModels();
      this.models = response.models;
      this.modelsError = null;
    } catch (error) {
      this.modelsError = describeError(error, 'The model list could not be loaded.');
    }
  }

  /** Starts the poll. Returns a function that stops it. */
  startPolling(): () => void {
    const tick = () => {
      if (typeof document !== 'undefined' && document.hidden) return;
      this.ticks += 1;
      void this.refreshStatus();
      if (this.sessions !== 'unavailable' || this.ticks % SESSIONS_RETRY_TICKS === 0) {
        void this.refreshSession();
      }
    };
    const onVisibility = () => {
      if (typeof document !== 'undefined' && !document.hidden) tick();
    };
    tick();
    const timer = setInterval(tick, STATUS_POLL_MS);
    if (typeof document !== 'undefined') document.addEventListener('visibilitychange', onVisibility);
    return () => {
      clearInterval(timer);
      if (typeof document !== 'undefined') document.removeEventListener('visibilitychange', onVisibility);
    };
  }
}

export const system = new SystemStore();
