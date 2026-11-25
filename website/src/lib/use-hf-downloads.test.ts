import { describe, expect, it } from "vitest";
import { statusFromSource } from "./use-hf-downloads.svelte";

describe("statusFromSource", () => {
  it("gives live, cached and built-in readings their own status", () => {
    expect(statusFromSource("live")).toBe("live");
    expect(statusFromSource("cached")).toBe("cached");
    expect(statusFromSource("fallback")).toBe("fallback");
  });
});
