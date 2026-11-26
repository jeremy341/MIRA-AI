import { resolveDownloads, type DownloadReading, type DownloadSource } from "./hf-downloads";
import { repeatWhileVisible } from "./repeat-while-visible";
import { FALLBACK_DOWNLOADS } from "./site";

export type DownloadStatus = "checking" | "live" | "cached" | "fallback";

/** Maps where a reading came from to the badge status. Each source has its own, so a built-in value is never called cached. */
export function statusFromSource(source: DownloadSource): Exclude<DownloadStatus, "checking"> {
  return source;
}

export type Shown = { value: number; last30Days: number | null; status: DownloadStatus };

/**
 * What to show after a reading. Once a live count has been on screen, a failed refresh keeps that number and only
 * marks it as cached. It must not swap in an older stored or built-in value, which would make the count go down.
 */
export function afterReading(shown: Shown, reading: DownloadReading, hadLive: boolean): Shown {
  if (hadLive && reading.source !== "live") return { value: shown.value, last30Days: null, status: "cached" };
  return { value: reading.value, last30Days: reading.last30Days, status: statusFromSource(reading.source) };
}

/**
 * Client-side Hugging Face download count as Svelte state. The initial values equal what the static HTML
 * contains (FALLBACK_DOWNLOADS, status "checking"), so the number is never empty. `start()` asks the Hugging
 * Face API (5 s timeout, localStorage fallback, see hf-downloads.ts) and returns a stop function for onMount.
 * With `refreshMs` it asks again at that interval while the page is visible.
 *
 *   checking: the request is running, the built-in value is shown.
 *   live: the API answered with a valid count the last time it was asked.
 *   cached: the request failed; `value` is the last good count, from this visit or from localStorage.
 *   fallback: the request failed and nothing was stored; `value` is the built-in FALLBACK_DOWNLOADS.
 *
 * `last30Days` is only ever set by a live answer; it has no fallback and is never cached.
 */
export class HfDownloads {
  value = $state(FALLBACK_DOWNLOADS);
  last30Days = $state<number | null>(null);
  status = $state<DownloadStatus>("checking");
  #hadLive = false;

  start(refreshMs?: number): () => void {
    const controller = new AbortController();
    const read = () =>
      void resolveDownloads({ signal: controller.signal }).then((reading) => {
        if (!reading) return;
        const next = afterReading(this, reading, this.#hadLive);
        this.#hadLive ||= reading.source === "live";
        this.value = next.value;
        this.last30Days = next.last30Days;
        this.status = next.status;
      });
    read();
    const stopRepeating = refreshMs ? repeatWhileVisible(read, refreshMs) : undefined;
    return () => {
      stopRepeating?.();
      controller.abort();
    };
  }
}
