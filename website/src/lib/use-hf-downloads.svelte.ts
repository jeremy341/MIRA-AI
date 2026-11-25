import { resolveDownloads, type DownloadSource } from "./hf-downloads";
import { FALLBACK_DOWNLOADS } from "./site";

export type DownloadStatus = "checking" | "live" | "cached" | "fallback";

/** Maps where a reading came from to the badge status. Each source has its own, so a built-in value is never called cached. */
export function statusFromSource(source: DownloadSource): Exclude<DownloadStatus, "checking"> {
  return source;
}

/**
 * Client-side Hugging Face download count as Svelte state. The initial values equal what the static HTML
 * contains (FALLBACK_DOWNLOADS, status "checking"), so the number is never empty. `start()` asks the Hugging
 * Face API (5 s timeout, localStorage fallback, see hf-downloads.ts) and returns a stop function for onMount.
 *
 *   checking: the request is running, the built-in value is shown.
 *   live: the API answered with a valid count just now.
 *   cached: the request failed; `value` is the last good count from localStorage.
 *   fallback: the request failed and nothing was stored; `value` is the built-in FALLBACK_DOWNLOADS.
 *
 * `last30Days` is only ever set by a live answer; it has no fallback and is never cached.
 */
export class HfDownloads {
  value = $state(FALLBACK_DOWNLOADS);
  last30Days = $state<number | null>(null);
  status = $state<DownloadStatus>("checking");

  start(): () => void {
    const controller = new AbortController();
    resolveDownloads({ signal: controller.signal }).then((reading) => {
      if (!reading) return;
      this.value = reading.value;
      this.last30Days = reading.last30Days;
      this.status = statusFromSource(reading.source);
    });
    return () => controller.abort();
  }
}
