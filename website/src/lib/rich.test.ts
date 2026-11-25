import { describe, expect, it } from "vitest";
import { parseRich, splitNoBreak } from "./rich";

describe("parseRich", () => {
  it("returns plain text as one part", () => {
    expect(parseRich("Hello world")).toEqual([{ kind: "text", text: "Hello world" }]);
  });

  it("parses marker, code and links", () => {
    const parts = parseRich("A ==big== `mira live --conf` [Research](/research) and [GitHub](https://example.org).");
    expect(parts.map((p) => p.kind)).toEqual(["text", "mark", "text", "code", "text", "link", "text", "link", "text"]);
    expect(parts[1]).toEqual({ kind: "mark", text: "big" });
    expect(parts[5]).toMatchObject({ kind: "link", href: "/research", internal: true });
    expect(parts[7]).toMatchObject({ kind: "link", href: "https://example.org", internal: false });
  });

  it("keeps experiment ids and mira-ai on one line", () => {
    const parts = parseRich("EXP-019 uses mira-ai");
    expect(parts.filter((p) => p.kind === "nobreak").map((p) => (p as { text: string }).text)).toEqual([
      "EXP-019",
      "mira-ai",
    ]);
  });

  it("never turns raw HTML in a string into markup", () => {
    const parts = parseRich("<img src=x onerror=alert(1)> ==x==");
    expect(parts[0]).toEqual({ kind: "text", text: "<img src=x onerror=alert(1)> " });
  });

  it("treats a protocol-relative link as external", () => {
    expect(parseRich("[x](//evil.test)")[0]).toMatchObject({ internal: false });
  });
});

describe("splitNoBreak", () => {
  it("keeps short words together and lets spaces wrap", () => {
    expect(splitNoBreak("mira live --conf")).toEqual([
      { text: "mira", nowrap: true },
      { text: " ", nowrap: false },
      { text: "live", nowrap: true },
      { text: " ", nowrap: false },
      { text: "--conf", nowrap: true },
    ]);
  });

  it("lets a very long word break", () => {
    expect(splitNoBreak("x".repeat(40))[0].nowrap).toBe(false);
  });
});
