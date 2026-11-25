/**
 * Hugging Face download counter, pure logic.
 *
 * The page server-renders FALLBACK_DOWNLOADS, then a client component asks the
 * public Hugging Face model API for `downloadsAllTime` (all time) and `downloads`
 * (the last 30 days). Everything here is framework-free so it can be unit tested
 * (see hf-downloads.test.ts).
 *
 * Failure policy: any network error, timeout, non-2xx status, non-JSON body or
 * invalid all-time value is swallowed by the caller and replaced by, in order,
 * the last good value stored in localStorage, then FALLBACK_DOWNLOADS.
 *
 * The 30-day figure has NO fallback and is never cached: it is only reported
 * when the live response carries a valid value, otherwise it is null and the UI
 * leaves it out.
 */

import { FALLBACK_DOWNLOADS, HF_REPO } from "./site";

export const HF_API_URL = `https://huggingface.co/api/models/${HF_REPO}?expand[]=downloads&expand[]=downloadsAllTime`;
export const FETCH_TIMEOUT_MS = 5000;
export const CACHE_KEY = "mira:hf-downloads:v1";

export type DownloadSource = "live" | "cached" | "fallback";

export type DownloadReading = {
  /** All-time downloads. */
  value: number;
  /** Downloads in the last 30 days. Only set for a live reading that carried a valid value. */
  last30Days: number | null;
  source: DownloadSource;
};

export type DownloadStats = {
  allTime: number;
  last30Days: number | null;
};

/** True for a finite, non-negative, safe integer. Rejects strings, NaN, Infinity, floats, negatives. */
export function isValidCount(value: unknown): value is number {
  return (
    typeof value === "number" &&
    Number.isFinite(value) &&
    Number.isInteger(value) &&
    value >= 0 &&
    value <= Number.MAX_SAFE_INTEGER
  );
}

/** Extract `downloadsAllTime` from an API response body, or null when it is missing or invalid. */
export function parseDownloads(body: unknown): number | null {
  if (typeof body !== "object" || body === null) return null;
  const value = (body as Record<string, unknown>).downloadsAllTime;
  return isValidCount(value) ? value : null;
}

/**
 * Extract both counts. `allTime` is required; `last30Days` (the API's `downloads`)
 * is null when missing or invalid. Returns null when the all-time count is unusable.
 */
export function parseDownloadStats(body: unknown): DownloadStats | null {
  const allTime = parseDownloads(body);
  if (allTime === null) return null;
  const recent = (body as Record<string, unknown>).downloads;
  return { allTime, last30Days: isValidCount(recent) ? recent : null };
}

/** Minimal slice of the Storage interface, so tests can pass a fake. */
export type StorageLike = Pick<Storage, "getItem" | "setItem">;

function defaultStorage(): StorageLike | null {
  try {
    return typeof window === "undefined" ? null : window.localStorage;
  } catch {
    // Accessing localStorage itself can throw (blocked site data, private mode).
    return null;
  }
}

/** Last good value, or null when nothing valid is stored or storage is unavailable. */
export function readCachedDownloads(storage: StorageLike | null = defaultStorage()): number | null {
  if (!storage) return null;
  try {
    const raw = storage.getItem(CACHE_KEY);
    if (raw === null) return null;
    const parsed: unknown = JSON.parse(raw);
    if (typeof parsed !== "object" || parsed === null) return null;
    const value = (parsed as Record<string, unknown>).value;
    return isValidCount(value) ? value : null;
  } catch {
    return null;
  }
}

/** Store a good value. Returns false when storage refused (quota, blocked, private mode). */
export function writeCachedDownloads(
  value: number,
  storage: StorageLike | null = defaultStorage(),
  now: number = Date.now(),
): boolean {
  if (!storage || !isValidCount(value)) return false;
  try {
    storage.setItem(CACHE_KEY, JSON.stringify({ value, at: now }));
    return true;
  } catch {
    return false;
  }
}

export type FetchOptions = {
  signal?: AbortSignal;
  timeoutMs?: number;
  fetchImpl?: typeof fetch;
};

/**
 * Fetch the download counts. Rejects on timeout, abort, HTTP error, malformed
 * JSON or an invalid all-time value. Callers treat every rejection the same.
 */
export async function fetchDownloads({
  signal,
  timeoutMs = FETCH_TIMEOUT_MS,
  fetchImpl = fetch,
}: FetchOptions = {}): Promise<DownloadStats> {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(new Error("timeout")), timeoutMs);
  const onExternalAbort = () => controller.abort(signal?.reason);
  if (signal) {
    if (signal.aborted) controller.abort(signal.reason);
    else signal.addEventListener("abort", onExternalAbort, { once: true });
  }
  try {
    const response = await fetchImpl(HF_API_URL, {
      signal: controller.signal,
      headers: { Accept: "application/json" },
      cache: "no-store",
    });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const stats = parseDownloadStats(await response.json());
    if (stats === null) throw new Error("invalid downloadsAllTime");
    return stats;
  } finally {
    clearTimeout(timer);
    signal?.removeEventListener("abort", onExternalAbort);
  }
}

/**
 * Resolve a reading using the failure policy above. Never rejects, except that
 * an externally aborted request resolves to null so the caller can ignore it.
 */
export async function resolveDownloads(
  options: FetchOptions & { storage?: StorageLike | null } = {},
): Promise<DownloadReading | null> {
  const { storage, ...fetchOptions } = options;
  const store = storage === undefined ? defaultStorage() : storage;
  try {
    const stats = await fetchDownloads(fetchOptions);
    writeCachedDownloads(stats.allTime, store);
    return { value: stats.allTime, last30Days: stats.last30Days, source: "live" };
  } catch {
    if (fetchOptions.signal?.aborted) return null;
    const cached = readCachedDownloads(store);
    if (cached !== null) return { value: cached, last30Days: null, source: "cached" };
    return { value: FALLBACK_DOWNLOADS, last30Days: null, source: "fallback" };
  }
}
