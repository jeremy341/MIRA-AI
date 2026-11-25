import { describe, expect, it } from "vitest";
import {
  firstFailure,
  firstOutOfScope,
  isFailure,
  isOutOfScope,
  parseFigureEntries,
  parseFigureEntry,
  topDetection,
  type FigureEntry,
} from "./figures";

const good = {
  file: "detect-01.jpg",
  width: 512,
  height: 384,
  trueClass: "glass",
  model: "mira_exp019",
  conf: 0.25,
  source: "TrashNet",
  note: "Correct detection.",
  detections: [{ cls: "glass", confidence: 0.92, box: [0, 0.0001, 0.9997, 1] }],
};

describe("parseFigureEntry", () => {
  it("accepts an entry that follows the contract", () => {
    const entry = parseFigureEntry(good);
    expect(entry?.file).toBe("detect-01.jpg");
    expect(entry?.detections).toHaveLength(1);
    expect(entry?.detections[0].box).toEqual([0, 0.0001, 0.9997, 1]);
  });

  it("clamps boxes into 0..1 and orders the corners", () => {
    const entry = parseFigureEntry({
      ...good,
      detections: [{ cls: "paper", confidence: 1.4, box: [1.2, 0.9, -0.1, 0.1] }],
    });
    expect(entry?.detections[0]).toEqual({ cls: "paper", confidence: 1, box: [0, 0.1, 1, 0.9] });
  });

  it("drops detections with an unknown class, bad numbers or an empty box", () => {
    const entry = parseFigureEntry({
      ...good,
      detections: [
        { cls: "cardboard", confidence: 0.9, box: [0, 0, 1, 1] },
        { cls: "glass", confidence: "high", box: [0, 0, 1, 1] },
        { cls: "glass", confidence: 0.5, box: [0.5, 0.5, 0.5, 0.9] },
        { cls: "glass", confidence: 0.5, box: [0, 0, 1] },
        { cls: "metal", confidence: 0.5, box: [0.1, 0.1, 0.4, 0.4] },
      ],
    });
    expect(entry?.detections.map((d) => d.cls)).toEqual(["metal"]);
  });

  it("rejects entries that break the contract", () => {
    expect(parseFigureEntry(null)).toBeNull();
    expect(parseFigureEntry({ ...good, file: "../secret.jpg" })).toBeNull();
    expect(parseFigureEntry({ ...good, width: 0 })).toBeNull();
    expect(parseFigureEntry({ ...good, trueClass: "bicycle" })).toBeNull();
  });
});

describe("out of scope photos", () => {
  it("accepts cardboard as a true class and never counts it as a failure", () => {
    const entry = parseFigureEntry({
      ...good,
      file: "detect-08.jpg",
      trueClass: "cardboard",
      detections: [{ cls: "paper", confidence: 0.93, box: [0, 0, 1, 1] }],
    }) as FigureEntry;
    expect(entry.trueClass).toBe("cardboard");
    expect(isOutOfScope(entry)).toBe(true);
    expect(isFailure(entry)).toBe(false);
    expect(firstOutOfScope([entry])?.file).toBe("detect-08.jpg");
  });
});

describe("parseFigureEntries", () => {
  it("returns an empty list for anything that is not an array", () => {
    expect(parseFigureEntries(undefined)).toEqual([]);
    expect(parseFigureEntries({})).toEqual([]);
  });

  it("keeps valid entries and skips the rest", () => {
    expect(parseFigureEntries([good, { nope: true }, { ...good, file: "detect-02.jpg" }])).toHaveLength(2);
  });
});

describe("failure helpers", () => {
  const hit = parseFigureEntry(good) as FigureEntry;
  const miss = parseFigureEntry({
    ...good,
    file: "detect-07.jpg",
    trueClass: "plastic",
    detections: [],
  }) as FigureEntry;
  const wrong = parseFigureEntry({
    ...good,
    file: "detect-09.jpg",
    trueClass: "plastic",
    detections: [{ cls: "glass", confidence: 0.6, box: [0, 0, 1, 1] }],
  }) as FigureEntry;

  it("treats no detection or a wrong class as a failure", () => {
    expect(isFailure(hit)).toBe(false);
    expect(isFailure(miss)).toBe(true);
    expect(isFailure(wrong)).toBe(true);
  });

  it("finds the first failure and the top detection", () => {
    expect(firstFailure([hit, miss, wrong])?.file).toBe("detect-07.jpg");
    expect(firstFailure([hit])).toBeNull();
    expect(topDetection(wrong)?.cls).toBe("glass");
    expect(topDetection(miss)).toBeNull();
  });
});

