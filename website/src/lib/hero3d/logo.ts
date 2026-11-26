/**
 * The pieces of the logo in the coordinates of static/mira.svg (viewBox 32 x 32, y pointing down), converted to
 * scene coordinates: the centre of the logo at the origin and y pointing up. Plain data without three.js.
 */
import { arc, strokeOutline, type Pt } from "./outline";

export type PieceKind = "corner" | "letter" | "dot";

export type Piece = {
  id: string;
  kind: PieceKind;
  /** Closed outline around the piece's own centre. */
  outline: Pt[];
  /** Where that centre sits when the logo is assembled. */
  home: Pt;
};

const CENTRE = 16;
const ARC_STEPS = 24;
const QUARTER = Math.PI / 2;

/** One viewfinder corner: a straight arm, a quarter circle of radius 2 and a second arm. */
const CORNERS: Record<string, Pt[]> = {
  "top-left": [[6.5, 11.5], ...arc([8.5, 8.5], 2, Math.PI, QUARTER, ARC_STEPS), [11.5, 6.5]],
  "top-right": [[20.5, 6.5], ...arc([23.5, 8.5], 2, -QUARTER, QUARTER, ARC_STEPS), [25.5, 11.5]],
  "bottom-right": [[25.5, 20.5], ...arc([23.5, 23.5], 2, 0, QUARTER, ARC_STEPS), [20.5, 25.5]],
  "bottom-left": [[11.5, 25.5], ...arc([8.5, 23.5], 2, QUARTER, QUARTER, ARC_STEPS), [6.5, 20.5]],
};

const LETTER: Pt[] = [
  [10.5, 20.5],
  [10.5, 11.5],
  [16, 17.7],
  [21.5, 11.5],
  [21.5, 20.5],
];

const toScene = ([x, y]: Pt): Pt => [x - CENTRE, CENTRE - y];

function piece(id: string, kind: PieceKind, outline: Pt[]): Piece {
  const points = outline.map(toScene);
  const xs = points.map(([x]) => x);
  const ys = points.map(([, y]) => y);
  const home: Pt = [(Math.min(...xs) + Math.max(...xs)) / 2, (Math.min(...ys) + Math.max(...ys)) / 2];
  return { id, kind, home, outline: points.map(([x, y]): Pt => [x - home[0], y - home[1]]) };
}

export const PIECES: Piece[] = [
  ...Object.entries(CORNERS).map(([id, line]) => piece(id, "corner", strokeOutline(line, 1.8))),
  piece("letter", "letter", strokeOutline(LETTER, 2.6)),
  piece("dot", "dot", arc([16, 22.4], 1.9, 0, Math.PI * 2, 96).slice(0, -1)),
];
