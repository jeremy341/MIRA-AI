/**
 * Pure layout of the experiment landscape (no three.js import, so it is cheap to load and easy to test).
 * One row of columns in log order: Stage A (EXP-001 to EXP-004), a gap, then Stage B (EXP-005 to EXP-019).
 * Column height = recorded score; entries without a score are flat tiles.
 */

export type LayoutRow = {
  id: string;
  short: string;
  stage: "A" | "B";
  value: number | null;
  highlight: boolean;
};

export type Column = {
  id: string;
  short: string;
  stage: "A" | "B";
  value: number | null;
  highlight: boolean;
  /** Centre of the column on the ground. */
  x: number;
  /** Footprint (square). */
  size: number;
  /** World height. */
  height: number;
};

export type AnchorKind = "id" | "value" | "axis" | "zone";

export type Anchor = {
  key: string;
  kind: AnchorKind;
  x: number;
  y: number;
  z: number;
  /** Which way a value label leans so neighbouring labels do not collide. */
  align?: "start" | "end";
};

export type Layout = {
  columns: Column[];
  anchors: Anchor[];
  minX: number;
  maxX: number;
  /** Height of the 100% line. */
  top: number;
  /** Half of the ground depth. */
  halfDepth: number;
  /** Heights of the reference lines (50% and 100%). */
  axisValues: number[];
};

/** World units per percentage point: 100% is 5 units tall. */
export const UNITS_PER_PERCENT = 0.05;
export const TILE_HEIGHT = 0.05;
export const SPACING = 1;
export const COLUMN_SIZE = 0.64;
export const ZONE_GAP = 1.4;
export const HALF_DEPTH = 1.6;

export const heightOf = (value: number | null): number => (value === null ? TILE_HEIGHT : value * UNITS_PER_PERCENT);

export function layoutRows(rows: readonly LayoutRow[]): Layout {
  const columns: Column[] = [];
  let x = 0;
  let previousStage: "A" | "B" | null = null;
  for (const row of rows) {
    if (previousStage !== null && row.stage !== previousStage) x += ZONE_GAP;
    columns.push({
      id: row.id,
      short: row.short,
      stage: row.stage,
      value: row.value,
      highlight: row.highlight,
      x,
      size: COLUMN_SIZE,
      height: heightOf(row.value),
    });
    x += SPACING;
    previousStage = row.stage;
  }
  const centre = (columns[0].x + columns[columns.length - 1].x) / 2;
  for (const column of columns) column.x -= centre;

  const minX = columns[0].x - SPACING / 2;
  const maxX = columns[columns.length - 1].x + SPACING / 2;
  const front = HALF_DEPTH * 0.45;

  const anchors: Anchor[] = [];
  for (const [index, column] of columns.entries()) {
    anchors.push({ key: `id:${column.id}`, kind: "id", x: column.x, y: 0, z: column.size / 2 + 0.05 });
    // Every column prints its value (the page hides labels that would overlap a more important one). A column next
    // to a highlighted one leans away from it, so the highlighted pair (EXP-018, EXP-019 are equally tall) stays legible.
    const next = columns[index + 1];
    const previous = columns[index - 1];
    const align =
      column.highlight && next?.highlight && next.value !== null
        ? "end"
        : column.highlight && previous?.highlight && previous.value !== null
          ? "start"
          : undefined;
    anchors.push({ key: `value:${column.id}`, kind: "value", x: column.x, y: column.height, z: 0, align });
  }
  const axisValues = [50, 100];
  for (const value of axisValues) {
    anchors.push({ key: `axis:${value}`, kind: "axis", x: minX + 0.05, y: heightOf(value), z: -HALF_DEPTH });
  }
  for (const stage of ["A", "B"] as const) {
    const zone = columns.filter((column) => column.stage === stage);
    const zoneCentre = (zone[0].x + zone[zone.length - 1].x) / 2;
    anchors.push({ key: `zone:${stage}`, kind: "zone", x: zoneCentre, y: 0, z: front + 0.9 });
  }

  return { columns, anchors, minX, maxX, top: heightOf(100), halfDepth: HALF_DEPTH, axisValues };
}
