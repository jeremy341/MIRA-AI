import { existsSync, readFileSync } from "node:fs";
import { resolve } from "node:path";
import { describe, expect, it } from "vitest";
import {
  bytesToMb,
  DATASET_RUNS,
  DATASET_SPLIT,
  EXP014_CLASSES,
  EXP018_019_CLASSES,
  EXP019_ALL,
  EXP019_EXPORTS,
  EXP019_TFLITE_320,
  EXPERIMENTS,
  experimentsByStage,
  FIELD_BENCHMARK,
  formatScore,
  getExperiment,
  PLANNED_EXPERIMENT,
  scoredExperiments,
} from "./experiments";
import { FACTS } from "./site";

const README_PATH = resolve(process.cwd(), "..", "README.md");

/** Every numeric score on a record, so range checks cannot miss a field. */
function scores(): number[] {
  return EXPERIMENTS.flatMap((e) =>
    [e.result?.value, e.map5095, e.precision, e.recall].filter((v): v is number => v != null),
  );
}

describe("experiment records", () => {
  it("has unique ids, EXP-001 to EXP-019 in order, and no planned run mixed in", () => {
    const ids = EXPERIMENTS.map((e) => e.id);
    expect(new Set(ids).size).toBe(ids.length);
    expect(ids).toEqual(Array.from({ length: 19 }, (_, i) => `EXP-${String(i + 1).padStart(3, "0")}`));
    expect(ids).not.toContain(PLANNED_EXPERIMENT.id);
    expect(EXPERIMENTS).toHaveLength(FACTS.experimentCount);
  });

  it("keeps every score within 0 to 100", () => {
    for (const value of scores()) {
      expect(value).toBeGreaterThanOrEqual(0);
      expect(value).toBeLessThanOrEqual(100);
    }
  });

  it("uses the right metric per stage and keeps stages contiguous", () => {
    for (const e of EXPERIMENTS) {
      if (e.result) {
        expect(e.result.name).toBe(e.stage === "A" ? "validation accuracy" : "mAP50");
      }
    }
    expect(experimentsByStage("A").map((e) => e.id)).toEqual(["EXP-001", "EXP-002", "EXP-003", "EXP-004"]);
    expect(experimentsByStage("B")).toHaveLength(15);
  });

  it("gives size-only export runs a size and no score", () => {
    for (const e of EXPERIMENTS.filter((x) => x.result === null)) {
      expect(e.kind).toBe("export");
      expect(e.modelSizeMb).not.toBeNull();
      expect(e.derivedFrom).not.toBeNull();
    }
  });

  it("only shows a derived experiment when its source exists", () => {
    for (const e of EXPERIMENTS.filter((x) => x.derivedFrom)) {
      expect(() => getExperiment(e.derivedFrom as string)).not.toThrow();
    }
  });

  it("lists scored detector runs for the chart", () => {
    expect(scoredExperiments("B").map((e) => e.id)).toEqual([
      "EXP-005",
      "EXP-006",
      "EXP-008",
      "EXP-009",
      "EXP-011",
      "EXP-013",
      "EXP-014",
      "EXP-015",
      "EXP-016",
      "EXP-017",
      "EXP-018",
      "EXP-019",
    ]);
    expect(scoredExperiments("A")).toHaveLength(4);
  });
});

describe("headline numbers", () => {
  it("matches the README results table and the shared FACTS", () => {
    expect(getExperiment("EXP-014").result?.value).toBe(60.7);
    expect(getExperiment("EXP-018").result?.value).toBe(90.6);
    expect(getExperiment("EXP-019").result?.value).toBe(90.58);
    expect(getExperiment("EXP-019").map5095).toBe(82.15);
    expect(getExperiment("EXP-019").precision).toBe(87.2);
    expect(getExperiment("EXP-019").recall).toBe(84.6);

    expect(getExperiment("EXP-014").result?.value).toBe(FACTS.exp014Map50);
    expect(getExperiment("EXP-018").result?.value).toBe(FACTS.exp018Map50);
    expect(getExperiment("EXP-019").result?.value).toBe(FACTS.exp019Map50);
    // FACTS rounds the logged 2.672 hours to two decimals.
    expect(getExperiment("EXP-019").trainingHours).toBeCloseTo(FACTS.exp019TrainingHours, 2);
  });

  it("agrees with the README text when the README is available", () => {
    if (!existsSync(README_PATH)) return; // running outside the monorepo checkout
    const readme = readFileSync(README_PATH, "utf8");
    expect(readme).toContain("| EXP-014 baseline | Earlier detector run | Recorded baseline | 60.7% |");
    expect(readme).toContain("| EXP-018 | YOLO11n | 415-image validation split | 90.6% |");
    expect(readme).toContain("| EXP-019 repeat | YOLO11n | 415-image validation split (repeat) | 90.58% |");
  });

  it("records the evaluation splits the README warns about", () => {
    expect(getExperiment("EXP-014").evaluation.images).toBe(1588);
    expect(getExperiment("EXP-018").evaluation.images).toBe(FACTS.validationImages);
    expect(getExperiment("EXP-019").evaluation.images).toBe(FACTS.validationImages);
    // The caveat is what stops the 60.7 vs 90.6 comparison being read as like-for-like.
    expect(getExperiment("EXP-014").caveat).toMatch(/not the 415-image/);
    expect(getExperiment("EXP-018").caveat).toMatch(/not like-for-like/);
    expect(getExperiment("EXP-019").caveat).toMatch(/test split was not evaluated/);
  });
});

describe("per-class results", () => {
  it("covers the five classes in dataset order with scores in range", () => {
    for (const table of [EXP014_CLASSES, EXP018_019_CLASSES]) {
      expect(table.map((r) => r.cls)).toEqual(["glass", "metal", "paper", "plastic", "trash"]);
      for (const r of table) {
        for (const v of [r.precision, r.recall, r.map50, r.map5095]) {
          expect(v).toBeGreaterThanOrEqual(0);
          expect(v).toBeLessThanOrEqual(100);
        }
      }
    }
    for (const v of Object.values(EXP019_ALL)) {
      expect(v).toBeGreaterThanOrEqual(0);
      expect(v).toBeLessThanOrEqual(100);
    }
  });

  it("matches the EXP-014 to EXP-018 per-class comparison in the log", () => {
    const old = Object.fromEntries(EXP014_CLASSES.map((r) => [r.cls, r.map50]));
    const next = Object.fromEntries(EXP018_019_CLASSES.map((r) => [r.cls, r.map50]));
    expect(old).toEqual({ glass: 50.2, metal: 71.3, paper: 82.9, plastic: 72.1, trash: 26.9 });
    expect(next).toEqual({ glass: 90.8, metal: 94.8, paper: 88.7, plastic: 81.1, trash: 97.5 });
  });

  it("keeps plastic recall as the weak spot quoted on the Home page", () => {
    const plastic = EXP018_019_CLASSES.find((r) => r.cls === "plastic");
    expect(plastic?.recall).toBe(FACTS.exp019PlasticRecall);
  });
});

describe("dataset, exports and planned run", () => {
  it("sums the dataset split to the recorded image counts", () => {
    expect(DATASET_SPLIT.train).toBe(FACTS.trainImages);
    expect(DATASET_SPLIT.val).toBe(FACTS.validationImages);
    expect(DATASET_SPLIT.test).toBe(FACTS.testImages);
    expect(DATASET_SPLIT.train + DATASET_SPLIT.val + DATASET_SPLIT.test).toBe(6898);
    expect(DATASET_SPLIT.boxesPerClassMin).toBeLessThan(DATASET_SPLIT.boxesPerClassMax);
  });

  it("lists dataset runs whose scores match their experiment records", () => {
    expect(DATASET_RUNS.find((r) => r.label === "EXP-014")?.map50).toBe(60.7);
    expect(DATASET_RUNS.find((r) => r.label.startsWith("EXP-018"))?.map50).toBe(90.6);
    for (const run of DATASET_RUNS) {
      const first = run.label.split(" ")[0];
      expect(getExperiment(first).result?.value).toBe(run.map50);
    }
  });

  it("converts export sizes to decimal MB as printed in the old site", () => {
    const sizes = Object.fromEntries(EXP019_EXPORTS.map((f) => [f.file, bytesToMb(f.bytes)]));
    expect(sizes).toEqual({
      "mira_exp019.pt": "5.47",
      "mira_exp019_int8_320.tflite": "3.02",
      "mira_exp019_int8_640.tflite": "3.04",
      "mira_exp019.onnx": "10.61",
    });
    expect(EXP019_TFLITE_320.map50).toBe(86.2);
  });

  it("keeps the field benchmark apart from mAP50 and EXP-018/019", () => {
    expect(FIELD_BENCHMARK.bestModel).toBe("mira_exp014.pt");
    expect(FIELD_BENCHMARK.bestF1).toBe(85.8);
    expect(FIELD_BENCHMARK.modelsTested).toBe(11);
  });

  it("marks EXP-020 as planned with no results", () => {
    expect(PLANNED_EXPERIMENT.status).toBe("planned");
    expect(PLANNED_EXPERIMENT.sourceMix.reduce((sum, s) => sum + s.share, 0)).toBe(100);
    expect(Object.keys(PLANNED_EXPERIMENT)).not.toContain("result");
    expect(Object.keys(PLANNED_EXPERIMENT)).not.toContain("map50");
    const roboflow = PLANNED_EXPERIMENT.sourceMix.find((s) => s.source === "Roboflow");
    expect(roboflow?.share).toBe(70);
  });
});

describe("formatScore", () => {
  it("keeps the digits the log prints", () => {
    expect(formatScore(61)).toBe("61.0");
    expect(formatScore(60.7)).toBe("60.7");
    expect(formatScore(90.58)).toBe("90.58");
    expect(formatScore(87.42)).toBe("87.42");
  });
});
