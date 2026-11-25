/**
 * Errors from the API client. Pure, no DOM, covered by errors.test.ts.
 *
 * FastAPI answers an unknown route with 404 and `{"detail": "Not Found"}`. A known route
 * with an unknown id answers 404 with its own detail ("Session not found", for example).
 * `isRouteMissing` tells the two apart, so pages can show "not available yet" for a
 * missing endpoint and "not found" for a missing record.
 */

export type ApiErrorKind = 'http' | 'network' | 'timeout' | 'aborted' | 'invalid';

export interface ApiErrorInit {
  message: string;
  kind: ApiErrorKind;
  path: string;
  status?: number;
  detail?: unknown;
  missing?: string[];
}

export class ApiError extends Error {
  readonly kind: ApiErrorKind;
  readonly path: string;
  /** HTTP status, or 0 when no response arrived (network, timeout, abort). */
  readonly status: number;
  /** The raw `detail` value from the response body, when there was one. */
  readonly detail: unknown;
  /** Missing prerequisites from a 409 (`camera`, `model`) when the server sent them. */
  readonly missing: string[];

  constructor(init: ApiErrorInit) {
    super(init.message);
    this.name = 'ApiError';
    this.kind = init.kind;
    this.path = init.path;
    this.status = init.status ?? 0;
    this.detail = init.detail;
    this.missing = init.missing ?? [];
  }
}

/** Turns a non-2xx JSON body into an ApiError with a human message. */
export function errorFromResponse(status: number, path: string, body: unknown): ApiError {
  const detail = body && typeof body === 'object' && 'detail' in body ? (body as { detail: unknown }).detail : undefined;
  const { message, missing } = messageFromDetail(detail, status);
  return new ApiError({ kind: 'http', status, path, detail, message, missing });
}

function messageFromDetail(detail: unknown, status: number): { message: string; missing: string[] } {
  if (typeof detail === 'string' && detail.trim()) {
    return { message: detail, missing: [] };
  }
  if (detail && typeof detail === 'object' && !Array.isArray(detail)) {
    const record = detail as { message?: unknown; missing?: unknown };
    const missing = Array.isArray(record.missing) ? record.missing.filter((x): x is string => typeof x === 'string') : [];
    if (typeof record.message === 'string' && record.message.trim()) {
      return { message: record.message, missing };
    }
    return { message: `Request failed (HTTP ${status}).`, missing };
  }
  if (Array.isArray(detail)) {
    // FastAPI validation errors: [{loc: [...], msg: "..."}]
    const parts = detail
      .map((item) => {
        if (!item || typeof item !== 'object') return '';
        const { loc, msg } = item as { loc?: unknown; msg?: unknown };
        const field = Array.isArray(loc) ? loc.filter((p) => p !== 'body' && p !== 'query').join('.') : '';
        const text = typeof msg === 'string' ? msg : '';
        return field ? `${field}: ${text}` : text;
      })
      .filter(Boolean);
    return { message: parts.join('; ') || `Invalid input (HTTP ${status}).`, missing: [] };
  }
  return { message: `Request failed (HTTP ${status}).`, missing: [] };
}

/** True when the route itself does not exist on this server (or is a stub that answers 501). */
export function isRouteMissing(error: unknown): boolean {
  if (!(error instanceof ApiError)) return false;
  if (error.status === 501 || error.status === 405) return true;
  return error.status === 404 && error.detail === 'Not Found';
}

/** True for a 409 "wrong state" answer, such as "Stop the stream before changing camera settings". */
export function isConflict(error: unknown): boolean {
  return error instanceof ApiError && error.status === 409;
}

export function isAborted(error: unknown): boolean {
  return error instanceof ApiError && error.kind === 'aborted';
}

/** A sentence a person can read in a toast or an inline message. */
export function describeError(error: unknown, fallback = 'Something went wrong. Try again.'): string {
  if (!(error instanceof ApiError)) {
    return error instanceof Error && error.message ? error.message : fallback;
  }
  if (isRouteMissing(error)) return 'This is not available on the server yet.';
  switch (error.kind) {
    case 'timeout':
      return 'The server took too long to answer. Try again in a moment.';
    case 'network':
      return 'The dashboard cannot reach the server. Check that it is running.';
    case 'aborted':
      return 'The request was cancelled.';
    case 'invalid':
      return 'The server sent a response this dashboard cannot read.';
    default:
      return error.message || fallback;
  }
}
