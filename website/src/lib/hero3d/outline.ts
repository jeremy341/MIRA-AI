/**
 * The MIRA logo is drawn with strokes (static/mira.svg). A stroke has no area, so it cannot be given depth.
 * This module turns a stroked line into the closed outline that the stroke covers, with round caps and round
 * joins. It is plain geometry without three.js.
 */

export type Pt = readonly [number, number];

const CAP_STEPS = 28;
const JOIN_STEP = Math.PI / 36;

function direction(from: Pt, to: Pt): Pt {
  const length = Math.hypot(to[0] - from[0], to[1] - from[1]);
  return [(to[0] - from[0]) / length, (to[1] - from[1]) / length];
}

const leftNormal = ([x, y]: Pt): Pt => [-y, x];

/** Points on a circle, from the angle `from` through `sweep` radians. Both ends are included. */
export function arc(centre: Pt, radius: number, from: number, sweep: number, steps: number): Pt[] {
  return Array.from({ length: steps + 1 }, (_, step): Pt => {
    const angle = from + (sweep * step) / steps;
    return [centre[0] + radius * Math.cos(angle), centre[1] + radius * Math.sin(angle)];
  });
}

/** The edge to the left of the line, walking from its first point to its last. */
function leftEdge(line: readonly Pt[], half: number): Pt[] {
  const edge: Pt[] = [];
  const offset = (at: Pt, normal: Pt): Pt => [at[0] + normal[0] * half, at[1] + normal[1] * half];

  edge.push(offset(line[0]!, leftNormal(direction(line[0]!, line[1]!))));
  for (let index = 1; index < line.length - 1; index += 1) {
    const corner = line[index]!;
    const incoming = direction(line[index - 1]!, corner);
    const outgoing = direction(corner, line[index + 1]!);
    const before = leftNormal(incoming);
    const after = leftNormal(outgoing);
    const turn = Math.atan2(
      incoming[0] * outgoing[1] - incoming[1] * outgoing[0],
      incoming[0] * outgoing[0] + incoming[1] * outgoing[1],
    );
    if (turn < 0) {
      // The line turns away from this edge, so this is the outside of the corner: round it.
      const steps = Math.max(1, Math.ceil(-turn / JOIN_STEP));
      edge.push(...arc(corner, half, Math.atan2(before[1], before[0]), turn, steps));
    } else {
      // Inside of the corner: the two offset edges meet in one point.
      const scale = half / (1 + before[0] * after[0] + before[1] * after[1]);
      edge.push([corner[0] + (before[0] + after[0]) * scale, corner[1] + (before[1] + after[1]) * scale]);
    }
  }
  const last = line.length - 1;
  edge.push(offset(line[last]!, leftNormal(direction(line[last - 1]!, line[last]!))));
  return edge;
}

/** The half circle that closes the stroke at the end of `line`, without its two end points. */
function endCap(line: readonly Pt[], half: number): Pt[] {
  const end = line[line.length - 1]!;
  const normal = leftNormal(direction(line[line.length - 2]!, end));
  return arc(end, half, Math.atan2(normal[1], normal[0]), -Math.PI, CAP_STEPS).slice(1, -1);
}

/** The closed outline of `line` drawn with a pen `width` wide. The first point is not repeated at the end. */
export function strokeOutline(line: readonly Pt[], width: number): Pt[] {
  if (line.length < 2) throw new Error("a stroke needs at least two points");
  const half = width / 2;
  const back = [...line].reverse();
  // The right-hand edge is the left-hand edge of the same line walked backwards.
  return [...leftEdge(line, half), ...endCap(line, half), ...leftEdge(back, half), ...endCap(back, half)];
}
