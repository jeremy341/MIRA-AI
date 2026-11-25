import { describe, expect, it } from "vitest";
import { getDictionary } from "$i18n";
import { EXPERIMENTS } from "./experiments";
import { HIGHLIGHT_IDS, landscapeRows } from "./landscape-data";
import { TILE_HEIGHT, UNITS_PER_PERCENT, layoutRows } from "./landscape/layout";

describe("landscape data", () => {
  const rows = landscapeRows("en", getDictionary("en").home.landscape);

  it("covers all 19 documented experiments in log order", () => {
    expect(rows.map((row) => row.id)).toEqual(EXPERIMENTS.map((experiment) => experiment.id));
    expect(rows).toHaveLength(19);
  });

  it("has 16 columns (12 detectors by mAP50, 4 classifiers by accuracy) and 3 flat tiles", () => {
    const columns = rows.filter((row) => row.value !== null);
    expect(columns.filter((row) => row.stage === "B")).toHaveLength(12);
    expect(columns.filter((row) => row.stage === "A")).toHaveLength(4);
    expect(rows.filter((row) => row.value === null).map((row) => row.id)).toEqual(["EXP-007", "EXP-010", "EXP-012"]);
  });

  it("takes every value straight from the experiment record", () => {
    for (const row of rows) {
      const experiment = EXPERIMENTS.find((entry) => entry.id === row.id)!;
      expect(row.value).toBe(experiment.result ? experiment.result.value : null);
      expect(row.stage).toBe(experiment.stage);
    }
  });

  it("highlights exactly the three shipped models", () => {
    expect(rows.filter((row) => row.highlight).map((row) => row.id)).toEqual([...HIGHLIGHT_IDS]);
  });

  it("prints the values the table shows in both languages", () => {
    const de = landscapeRows("de", getDictionary("de").home.landscape);
    expect(rows.find((row) => row.id === "EXP-019")!.valueText).toBe("90.58%");
    expect(de.find((row) => row.id === "EXP-019")!.valueText).toBe("90,58 %");
    expect(rows.find((row) => row.id === "EXP-001")!.valueText).toBe("61.0%");
    expect(rows.find((row) => row.id === "EXP-007")!.valueText).toBe(getDictionary("en").home.landscape.noScore);
    expect(rows.find((row) => row.id === "EXP-018")!.split).toContain("415");
    expect(de.find((row) => row.id === "EXP-014")!.split).toContain("1.588");
  });
});

describe("landscape layout", () => {
  const layout = layoutRows(landscapeRows("en", getDictionary("en").home.landscape));

  it("makes column height equal to the recorded score", () => {
    for (const column of layout.columns) {
      if (column.value === null) expect(column.height).toBe(TILE_HEIGHT);
      else expect(column.height).toBeCloseTo(column.value * UNITS_PER_PERCENT, 10);
    }
  });

  it("keeps Stage A left of Stage B with a gap, and no two columns overlap", () => {
    const xs = layout.columns.map((column) => column.x);
    expect(xs).toEqual(xs.toSorted((a, b) => a - b));
    const lastA = layout.columns.filter((column) => column.stage === "A").at(-1)!;
    const firstB = layout.columns.find((column) => column.stage === "B")!;
    expect(firstB.x - lastA.x).toBeGreaterThan(1.2);
    for (let i = 1; i < xs.length; i++) expect(xs[i] - xs[i - 1]).toBeGreaterThanOrEqual(0.9);
  });

  it("anchors a label under every column and a value above highlighted columns and tiles", () => {
    for (const column of layout.columns) expect(layout.anchors.some((anchor) => anchor.key === `id:${column.id}`)).toBe(true);
    const valueKeys = layout.anchors.filter((anchor) => anchor.kind === "value").map((anchor) => anchor.key);
    expect(valueKeys).toEqual(
      expect.arrayContaining(["value:EXP-014", "value:EXP-018", "value:EXP-019", "value:EXP-007", "value:EXP-010", "value:EXP-012"]),
    );
  });
});
