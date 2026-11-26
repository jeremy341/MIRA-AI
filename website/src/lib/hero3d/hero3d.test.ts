import { describe, expect, it } from "vitest";
import { PIECES } from "./logo";
import { strokeOutline, type Pt } from "./outline";
import { ENTRANCE_SECONDS, poseOf, spring } from "./pose";

function distanceToLine(point: Pt, line: readonly Pt[]): number {
  let best = Infinity;
  for (let index = 1; index < line.length; index += 1) {
    const [ax, ay] = line[index - 1]!;
    const [bx, by] = line[index]!;
    const length = (bx - ax) ** 2 + (by - ay) ** 2;
    const t = Math.min(1, Math.max(0, ((point[0] - ax) * (bx - ax) + (point[1] - ay) * (by - ay)) / length));
    best = Math.min(best, Math.hypot(point[0] - ax - t * (bx - ax), point[1] - ay - t * (by - ay)));
  }
  return best;
}

/** True when two edges of the closed polygon cross each other. */
function crossesItself(polygon: readonly Pt[]): boolean {
  const side = (a: Pt, b: Pt, c: Pt) => Math.sign((b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0]));
  const count = polygon.length;
  for (let i = 0; i < count; i += 1) {
    for (let j = i + 2; j < count; j += 1) {
      if (i === 0 && j === count - 1) continue;
      const [a, b, c, d] = [polygon[i]!, polygon[(i + 1) % count]!, polygon[j]!, polygon[(j + 1) % count]!];
      if (side(a, b, c) * side(a, b, d) < 0 && side(c, d, a) * side(c, d, b) < 0) return true;
    }
  }
  return false;
}

describe("strokeOutline", () => {
  const line: Pt[] = [
    [0, 10],
    [0, 0],
    [6, 6],
    [12, 0],
    [12, 10],
  ];

  it("stays half a stroke width from the line on the outside of every corner", () => {
    for (const point of strokeOutline(line, 2)) {
      const distance = distanceToLine(point, line);
      // An inside corner is where the two edges meet, which is at least half a width from the corner.
      expect(distance).toBeGreaterThan(0.999);
      expect(distance).toBeLessThan(1.001);
    }
  });

  it("adds a round cap beyond both ends", () => {
    const ys = strokeOutline(
      [
        [0, 0],
        [0, 10],
      ],
      2,
    ).map(([, y]) => y);
    expect(Math.min(...ys)).toBeCloseTo(-1);
    expect(Math.max(...ys)).toBeCloseTo(11);
  });

  it("rejects a single point", () => {
    expect(() => strokeOutline([[0, 0]], 1)).toThrow();
  });
});

describe("logo pieces", () => {
  it("has four corners, the letter and the dot", () => {
    expect(PIECES.map((piece) => piece.kind).sort()).toEqual(["corner", "corner", "corner", "corner", "dot", "letter"]);
  });

  it("gives every piece an outline that does not cross itself", () => {
    for (const piece of PIECES) expect(crossesItself(piece.outline), piece.id).toBe(false);
  });

  it("matches the extent of static/mira.svg", () => {
    const all = PIECES.flatMap((piece) => piece.outline.map(([x, y]) => [x + piece.home[0], y + piece.home[1]]));
    const xs = all.map(([x]) => x!);
    const ys = all.map(([, y]) => y!);
    // The corners run from 6.5 to 25.5 with a 1.8 stroke: 5.6 to 26.4 in the SVG, centred on 16.
    expect(Math.min(...xs)).toBeCloseTo(-10.4, 1);
    expect(Math.max(...xs)).toBeCloseTo(10.4, 1);
    expect(Math.min(...ys)).toBeCloseTo(-10.4, 1);
    expect(Math.max(...ys)).toBeCloseTo(10.4, 1);
  });
});

describe("pose", () => {
  it("springs from 0 to 1 and passes the target once on the way", () => {
    expect(spring(-1)).toBe(0);
    expect(spring(0)).toBe(0);
    expect(Math.max(...Array.from({ length: 160 }, (_, i) => spring(i / 100)))).toBeGreaterThan(1.05);
    expect(spring(1.6)).toBe(1);
    expect(spring(1.59)).toBeCloseTo(1, 2);
  });

  it("puts every piece in its place after the entrance", () => {
    for (const piece of PIECES) {
      const pose = poseOf(piece, ENTRANCE_SECONDS, 0);
      expect(pose.position.x, piece.id).toBeCloseTo(piece.home[0]);
      expect(pose.position.y, piece.id).toBeCloseTo(piece.home[1]);
      expect(Math.abs(pose.rotation.x) + Math.abs(pose.rotation.y) + Math.abs(pose.rotation.z)).toBeCloseTo(0);
      expect(pose.scale).toBe(1);
    }
  });

  it("starts hidden and apart, and comes apart again when scrolled away", () => {
    for (const piece of PIECES) {
      expect(poseOf(piece, 0, 0).scale).toBe(0);
      const home = poseOf(piece, ENTRANCE_SECONDS, 0).position;
      const away = poseOf(piece, ENTRANCE_SECONDS, 1).position;
      expect(Math.hypot(away.x - home.x, away.y - home.y, away.z - home.z), piece.id).toBeGreaterThan(2);
      expect(poseOf(piece, ENTRANCE_SECONDS, 7).position).toEqual(away);
    }
  });
});
