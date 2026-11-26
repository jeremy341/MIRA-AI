import { describe, expect, it } from "vitest";
import { afterReading, statusFromSource, type Shown } from "./use-hf-downloads.svelte";

describe("statusFromSource", () => {
  it("gives live, cached and built-in readings their own status", () => {
    expect(statusFromSource("live")).toBe("live");
    expect(statusFromSource("cached")).toBe("cached");
    expect(statusFromSource("fallback")).toBe("fallback");
  });
});

describe("afterReading", () => {
  const shown: Shown = { value: 200, last30Days: 30, status: "live" };

  it("takes a new live reading", () => {
    expect(afterReading(shown, { value: 205, last30Days: 33, source: "live" }, true)).toEqual({
      value: 205,
      last30Days: 33,
      status: "live",
    });
  });

  it("keeps the live number when a refresh fails, and says it is cached", () => {
    for (const source of ["cached", "fallback"] as const) {
      expect(afterReading(shown, { value: 100, last30Days: null, source }, true)).toEqual({
        value: 200,
        last30Days: null,
        status: "cached",
      });
    }
  });

  it("uses the stored or built-in value when nothing live was ever shown", () => {
    const start: Shown = { value: 100, last30Days: null, status: "checking" };
    expect(afterReading(start, { value: 150, last30Days: null, source: "cached" }, false)).toEqual({
      value: 150,
      last30Days: null,
      status: "cached",
    });
  });
});
