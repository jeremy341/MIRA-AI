/**
 * Where each logo piece is at a given moment. Two things pull a piece away from its place: the entrance (it flies
 * in and settles on a spring) and scrolling away from the hero (the logo comes apart, and closes again on the way
 * back). Plain math without three.js.
 */
import type { Piece } from "./logo";

export type Vec = { x: number; y: number; z: number };
export type Pose = { position: Vec; rotation: Vec; scale: number };

/** Resting depth: the corners sit behind the letter and the dot in front, so the layers shift when the logo turns. */
const REST_DEPTH = { corner: -1.1, letter: 0.4, dot: 2.1 } as const;
const START_DELAY = {
  "top-left": 0.05,
  "top-right": 0.13,
  "bottom-right": 0.21,
  "bottom-left": 0.29,
  letter: 0.34,
  dot: 0.78,
};
/** After this many seconds the entrance is over. */
export const ENTRANCE_SECONDS = 2.4;

/** An under-damped spring from 0 to 1: it passes the target once and settles. */
export function spring(seconds: number): number {
  if (seconds <= 0) return 0;
  if (seconds >= 1.6) return 1;
  const decay = 5.2;
  const swing = 8.4;
  return 1 - Math.exp(-decay * seconds) * (Math.cos(swing * seconds) + (decay / swing) * Math.sin(swing * seconds));
}

/** How far away and how turned a piece is when it is fully apart. */
function apart(piece: Piece): { shift: Vec; turn: Vec } {
  const [x, y] = piece.home;
  if (piece.kind === "letter") return { shift: { x: 0, y: 0.8, z: -14 }, turn: { x: 0.35, y: -1.5, z: 0 } };
  if (piece.kind === "dot") return { shift: { x: 0, y: -5.5, z: 11 }, turn: { x: 1.2, y: 0, z: 0 } };
  return {
    shift: { x: x * 0.62, y: y * 0.62, z: 7 },
    turn: { x: -Math.sign(y) * 0.9, y: Math.sign(x) * 0.9, z: -Math.sign(x * y) * 0.45 },
  };
}

/**
 * @param entrance seconds since the entrance began; pass ENTRANCE_SECONDS or more to skip it
 * @param spread   0 assembled, 1 fully scrolled away
 */
export function poseOf(piece: Piece, entrance: number, spread: number): Pose {
  const delay = START_DELAY[piece.id as keyof typeof START_DELAY] ?? 0;
  const arrived = spring(entrance - delay);
  // Scrolling opens the logo half as far as the entrance, so it stays readable.
  const open = 1 - arrived + 0.5 * Math.min(1, Math.max(0, spread));
  const { shift, turn } = apart(piece);
  return {
    position: {
      x: piece.home[0] + shift.x * open,
      y: piece.home[1] + shift.y * open,
      z: REST_DEPTH[piece.kind] + shift.z * open,
    },
    rotation: { x: turn.x * open, y: turn.y * open, z: turn.z * open },
    // A piece grows out of nothing as it starts to move.
    scale: Math.min(1, Math.max(0, (entrance - delay) / 0.25)),
  };
}
