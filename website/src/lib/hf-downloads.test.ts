import { afterEach, describe, expect, it, vi } from "vitest";
import {
  CACHE_KEY,
  fetchDownloads,
  HF_API_URL,
  isValidCount,
  parseDownloads,
  parseDownloadStats,
  readCachedDownloads,
  resolveDownloads,
  writeCachedDownloads,
  type StorageLike,
} from "./hf-downloads";
import { FALLBACK_DOWNLOADS } from "./site";

function memoryStorage(initial: Record<string, string> = {}): StorageLike & { data: Record<string, string> } {
  const data = { ...initial };
  return {
    data,
    getItem: (key) => (key in data ? data[key] : null),
    setItem: (key, value) => {
      data[key] = value;
    },
  };
}

const throwingStorage: StorageLike = {
  getItem: () => {
    throw new Error("blocked");
  },
  setItem: () => {
    throw new Error("quota");
  },
};

function jsonResponse(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

afterEach(() => {
  vi.useRealTimers();
});

describe("isValidCount", () => {
  it("accepts finite non-negative integers", () => {
    expect(isValidCount(0)).toBe(true);
    expect(isValidCount(10096)).toBe(true);
  });

  it("rejects everything else", () => {
    for (const bad of [
      -1,
      1.5,
      NaN,
      Infinity,
      -Infinity,
      "10096",
      null,
      undefined,
      {},
      [],
      Number.MAX_SAFE_INTEGER + 2,
    ]) {
      expect(isValidCount(bad)).toBe(false);
    }
  });
});

describe("parseDownloads", () => {
  it("reads downloadsAllTime", () => {
    expect(parseDownloads({ downloadsAllTime: 10096, id: "Jeremy341/MIRA-AI" })).toBe(10096);
    expect(parseDownloads({ downloadsAllTime: 0 })).toBe(0);
  });

  it("returns null for missing or invalid values", () => {
    expect(parseDownloads(null)).toBeNull();
    expect(parseDownloads("10096")).toBeNull();
    expect(parseDownloads({})).toBeNull();
    expect(parseDownloads({ downloads: 5 })).toBeNull();
    expect(parseDownloads({ downloadsAllTime: "10096" })).toBeNull();
    expect(parseDownloads({ downloadsAllTime: -3 })).toBeNull();
    expect(parseDownloads({ downloadsAllTime: 12.5 })).toBeNull();
    expect(parseDownloads({ downloadsAllTime: null })).toBeNull();
  });
});

describe("parseDownloadStats", () => {
  it("reads both the all-time and the 30-day count", () => {
    expect(parseDownloadStats({ downloadsAllTime: 10096, downloads: 3473 })).toEqual({
      allTime: 10096,
      last30Days: 3473,
    });
    expect(parseDownloadStats({ downloadsAllTime: 5, downloads: 0 })).toEqual({ allTime: 5, last30Days: 0 });
  });

  it("omits the 30-day count when it is missing or invalid, with no invented value", () => {
    expect(parseDownloadStats({ downloadsAllTime: 10096 })).toEqual({ allTime: 10096, last30Days: null });
    for (const bad of [-1, 1.5, NaN, "3473", null, {}]) {
      expect(parseDownloadStats({ downloadsAllTime: 10096, downloads: bad })).toEqual({
        allTime: 10096,
        last30Days: null,
      });
    }
  });

  it("returns null when the all-time count is missing or invalid", () => {
    expect(parseDownloadStats({ downloads: 3473 })).toBeNull();
    expect(parseDownloadStats({ downloadsAllTime: "x", downloads: 3 })).toBeNull();
    expect(parseDownloadStats(null)).toBeNull();
    expect(parseDownloadStats("nope")).toBeNull();
  });
});

describe("localStorage cache", () => {
  it("round-trips a good value", () => {
    const storage = memoryStorage();
    expect(writeCachedDownloads(10234, storage, 1)).toBe(true);
    expect(readCachedDownloads(storage)).toBe(10234);
  });

  it("ignores corrupt or invalid stored data", () => {
    expect(readCachedDownloads(memoryStorage({ [CACHE_KEY]: "not json" }))).toBeNull();
    expect(readCachedDownloads(memoryStorage({ [CACHE_KEY]: JSON.stringify({ value: -4 }) }))).toBeNull();
    expect(readCachedDownloads(memoryStorage({ [CACHE_KEY]: JSON.stringify(42) }))).toBeNull();
    expect(readCachedDownloads(memoryStorage())).toBeNull();
  });

  it("never throws when storage is blocked or missing", () => {
    expect(readCachedDownloads(throwingStorage)).toBeNull();
    expect(writeCachedDownloads(5, throwingStorage)).toBe(false);
    expect(readCachedDownloads(null)).toBeNull();
    expect(writeCachedDownloads(5, null)).toBe(false);
  });

  it("refuses to cache an invalid value", () => {
    const storage = memoryStorage();
    expect(writeCachedDownloads(-1, storage)).toBe(false);
    expect(storage.data[CACHE_KEY]).toBeUndefined();
  });
});

describe("HF_API_URL", () => {
  it("asks for both the 30-day and the all-time download counts", () => {
    expect(HF_API_URL).toBe(
      "https://huggingface.co/api/models/Jeremy341/MIRA-AI?expand[]=downloads&expand[]=downloadsAllTime",
    );
  });
});

describe("fetchDownloads", () => {
  it("requests the Hugging Face API and returns both counts", async () => {
    const fetchImpl = vi.fn(async () => jsonResponse({ downloadsAllTime: 10096, downloads: 3473 }));
    await expect(fetchDownloads({ fetchImpl: fetchImpl as unknown as typeof fetch })).resolves.toEqual({
      allTime: 10096,
      last30Days: 3473,
    });
    expect(fetchImpl).toHaveBeenCalledWith(
      HF_API_URL,
      expect.objectContaining({ headers: { Accept: "application/json" } }),
    );
  });

  it("still succeeds without a 30-day count", async () => {
    const fetchImpl = vi.fn(async () => jsonResponse({ downloadsAllTime: 10096 }));
    await expect(fetchDownloads({ fetchImpl: fetchImpl as unknown as typeof fetch })).resolves.toEqual({
      allTime: 10096,
      last30Days: null,
    });
  });

  it("rejects on HTTP errors and invalid bodies", async () => {
    await expect(
      fetchDownloads({ fetchImpl: (async () => jsonResponse({}, 503)) as unknown as typeof fetch }),
    ).rejects.toThrow(/HTTP 503/);
    await expect(
      fetchDownloads({ fetchImpl: (async () => jsonResponse({ downloadsAllTime: "x" })) as unknown as typeof fetch }),
    ).rejects.toThrow(/invalid/);
  });

  it("aborts after the timeout", async () => {
    vi.useFakeTimers();
    const hanging = ((_url: string, init?: RequestInit) =>
      new Promise((_resolve, reject) => {
        init?.signal?.addEventListener("abort", () => reject(new Error("aborted")));
      })) as unknown as typeof fetch;
    const pending = expect(fetchDownloads({ fetchImpl: hanging, timeoutMs: 5000 })).rejects.toThrow("aborted");
    await vi.advanceTimersByTimeAsync(5000);
    await pending;
  });
});

describe("resolveDownloads", () => {
  it("returns live and writes the cache on success", async () => {
    const storage = memoryStorage();
    const reading = await resolveDownloads({
      storage,
      fetchImpl: (async () => jsonResponse({ downloadsAllTime: 10321, downloads: 3500 })) as unknown as typeof fetch,
    });
    expect(reading).toEqual({ value: 10321, last30Days: 3500, source: "live" });
    expect(readCachedDownloads(storage)).toBe(10321);
  });

  it("returns live with no 30-day figure when the API omits it", async () => {
    const reading = await resolveDownloads({
      storage: memoryStorage(),
      fetchImpl: (async () => jsonResponse({ downloadsAllTime: 10321 })) as unknown as typeof fetch,
    });
    expect(reading).toEqual({ value: 10321, last30Days: null, source: "live" });
  });

  it("falls back to the cached value when the request fails", async () => {
    const storage = memoryStorage();
    writeCachedDownloads(10200, storage);
    const reading = await resolveDownloads({
      storage,
      fetchImpl: (async () => {
        throw new TypeError("network");
      }) as unknown as typeof fetch,
    });
    // A cached all-time value can be old, so the 30-day figure is never shown from cache.
    expect(reading).toEqual({ value: 10200, last30Days: null, source: "cached" });
  });

  it("falls back to the constant when nothing is cached", async () => {
    const reading = await resolveDownloads({
      storage: memoryStorage(),
      fetchImpl: (async () => jsonResponse({ downloadsAllTime: -1 })) as unknown as typeof fetch,
    });
    expect(reading).toEqual({ value: FALLBACK_DOWNLOADS, last30Days: null, source: "fallback" });
  });

  it("survives blocked storage on both paths", async () => {
    const ok = await resolveDownloads({
      storage: throwingStorage,
      fetchImpl: (async () => jsonResponse({ downloadsAllTime: 7 })) as unknown as typeof fetch,
    });
    expect(ok).toEqual({ value: 7, last30Days: null, source: "live" });
    const failed = await resolveDownloads({
      storage: throwingStorage,
      fetchImpl: (async () => {
        throw new Error("offline");
      }) as unknown as typeof fetch,
    });
    expect(failed).toEqual({ value: FALLBACK_DOWNLOADS, last30Days: null, source: "fallback" });
  });

  it("returns null when the caller aborts", async () => {
    const controller = new AbortController();
    controller.abort();
    const reading = await resolveDownloads({
      storage: memoryStorage(),
      signal: controller.signal,
      fetchImpl: ((_url: string, init?: RequestInit) =>
        Promise.reject(init?.signal?.reason ?? new Error("aborted"))) as unknown as typeof fetch,
    });
    expect(reading).toBeNull();
  });
});
