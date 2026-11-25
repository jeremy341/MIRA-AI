/**
 * Typed loader for the detection photos in `static/figures/`.
 *
 * Contract (the files are produced by a separate step, never by site code):
 *   static/figures/detect-NN.jpg        clean photo, no boxes drawn in
 *   src/lib/figures-data/detections.json  array of FigureEntry (see below)
 *
 * The JSON is imported at build time, so the static build contains the data. A malformed entry never
 * fails the build: it is dropped, and the page renders a labelled placeholder instead.
 *
 * Box format: [x1, y1, x2, y2], each normalised to 0..1 against the image width and height.
 */

import detectionsJson from "./figures-data/detections.json";
import { CLASSES, type ClassId } from "./site";

export type FigureDetection = {
  cls: ClassId;
  /** 0..1 */
  confidence: number;
  /** [x1, y1, x2, y2] normalised 0..1 */
  box: [number, number, number, number];
};

export type FigureEntry = {
  /** File name inside static/figures, e.g. "detect-01.jpg". */
  file: string;
  width: number;
  height: number;
  /** Ground-truth class of the main object in the photo. */
  /** Ground-truth class. "cardboard" marks an out-of-scope photo: MIRA has no cardboard class. */
  trueClass: ClassId | "cardboard";
  model: string;
  /** Confidence threshold used for the detections. */
  conf: number;
  /** Where the photo comes from (dataset or description). */
  source: string;
  note: string;
  detections: FigureDetection[];
};

const CLASS_IDS = new Set<string>(CLASSES.map((c) => c.id));

const clamp01 = (n: number) => Math.min(1, Math.max(0, n));

function isFiniteNumber(value: unknown): value is number {
  return typeof value === "number" && Number.isFinite(value);
}

function parseDetection(raw: unknown): FigureDetection | null {
  if (typeof raw !== "object" || raw === null) return null;
  const r = raw as Record<string, unknown>;
  if (typeof r.cls !== "string" || !CLASS_IDS.has(r.cls)) return null;
  if (!isFiniteNumber(r.confidence)) return null;
  if (!Array.isArray(r.box) || r.box.length !== 4 || !r.box.every(isFiniteNumber)) return null;
  const [a, b, c, d] = r.box as number[];
  const x1 = clamp01(Math.min(a, c));
  const x2 = clamp01(Math.max(a, c));
  const y1 = clamp01(Math.min(b, d));
  const y2 = clamp01(Math.max(b, d));
  if (x2 - x1 <= 0 || y2 - y1 <= 0) return null;
  return { cls: r.cls as ClassId, confidence: clamp01(r.confidence), box: [x1, y1, x2, y2] };
}

/** Validate one JSON entry. Returns null for anything that does not match the contract. */
export function parseFigureEntry(raw: unknown): FigureEntry | null {
  if (typeof raw !== "object" || raw === null) return null;
  const r = raw as Record<string, unknown>;
  if (typeof r.file !== "string" || !/^[\w.-]+$/.test(r.file)) return null;
  if (!isFiniteNumber(r.width) || !isFiniteNumber(r.height) || r.width <= 0 || r.height <= 0) return null;
  if (typeof r.trueClass !== "string" || !(CLASS_IDS.has(r.trueClass) || r.trueClass === "cardboard")) return null;
  const detections = Array.isArray(r.detections)
    ? r.detections.map(parseDetection).filter((d): d is FigureDetection => d !== null)
    : [];
  return {
    file: r.file,
    width: r.width,
    height: r.height,
    trueClass: r.trueClass as FigureEntry["trueClass"],
    model: typeof r.model === "string" ? r.model : "",
    conf: isFiniteNumber(r.conf) ? r.conf : 0.25,
    source: typeof r.source === "string" ? r.source : "",
    note: typeof r.note === "string" ? r.note : "",
    detections,
  };
}

/** Parse the whole JSON document. Entries that break the contract are dropped. */
export function parseFigureEntries(raw: unknown): FigureEntry[] {
  if (!Array.isArray(raw)) return [];
  return raw.map(parseFigureEntry).filter((e): e is FigureEntry => e !== null);
}

/** The entries of src/lib/figures-data/detections.json that follow the contract. */
export function loadFigures(): FigureEntry[] {
  return parseFigureEntries(detectionsJson as unknown);
}

export function getFigure(file: string): FigureEntry | null {
  return loadFigures().find((e) => e.file === file) ?? null;
}

/** Photos of something MIRA has no class for (cardboard). The model cannot be right about them. */
export function isOutOfScope(entry: FigureEntry): boolean {
  return entry.trueClass === "cardboard";
}

/**
 * A photo is a failure example when it is in scope and the model found nothing or never produced the true class.
 * (The contract has no explicit flag. The first failure in file order is the one the Home page shows.)
 */
export function isFailure(entry: FigureEntry): boolean {
  if (isOutOfScope(entry)) return false;
  return entry.detections.length === 0 || !entry.detections.some((d) => d.cls === entry.trueClass);
}

export function firstFailure(entries: readonly FigureEntry[]): FigureEntry | null {
  return entries.find(isFailure) ?? null;
}

export function firstOutOfScope(entries: readonly FigureEntry[]): FigureEntry | null {
  return entries.find(isOutOfScope) ?? null;
}

/** The detection with the highest confidence, or null. */
export function topDetection(entry: FigureEntry): FigureDetection | null {
  return entry.detections.reduce<FigureDetection | null>(
    (best, d) => (best === null || d.confidence > best.confidence ? d : best),
    null,
  );
}
