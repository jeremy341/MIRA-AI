/**
 * Chart geometry, pure and covered by scale.test.ts. The SVG charts in components/charts/ use these
 * to turn data into pixels, so the maths can be checked without a browser.
 */

export type Domain = readonly [number, number];

/** Maps `domain` onto `range` linearly. A flat domain maps to the start of the range. */
export function linearScale(domain: Domain, range: Domain): (value: number) => number {
  const [d0, d1] = domain;
  const [r0, r1] = range;
  const span = d1 - d0;
  return (value: number) => (span === 0 ? r0 : r0 + ((value - d0) * (r1 - r0)) / span);
}

/** A "nice" step (1, 2, 2.5, 5 or 10 times a power of ten) that gives about `count` intervals. */
export function niceStep(span: number, count: number): number {
  const raw = Math.abs(span) / Math.max(1, count);
  if (raw === 0 || !Number.isFinite(raw)) return 1;
  const magnitude = 10 ** Math.floor(Math.log10(raw));
  const normalised = raw / magnitude;
  const nice = normalised <= 1 ? 1 : normalised <= 2 ? 2 : normalised <= 2.5 ? 2.5 : normalised <= 5 ? 5 : 10;
  return nice * magnitude;
}

/** Tick values that cover [min, max] with round steps. Always at least two ticks. */
export function niceTicks(min: number, max: number, count = 5): number[] {
  let low = Math.min(min, max);
  let high = Math.max(min, max);
  if (low === high) {
    low -= 1;
    high += 1;
  }
  const step = niceStep(high - low, count);
  const start = Math.floor(low / step) * step;
  const end = Math.ceil(high / step) * step;
  const decimals = Math.max(0, -Math.floor(Math.log10(step)) + 1);
  const ticks: number[] = [];
  for (let value = start; value <= end + step / 2; value += step) {
    ticks.push(Number(value.toFixed(decimals)));
  }
  return ticks;
}

/** The smallest and largest finite value, or null when there is none. */
export function extent(values: ReadonlyArray<number | null | undefined>): Domain | null {
  let low = Infinity;
  let high = -Infinity;
  for (const value of values) {
    if (typeof value !== 'number' || !Number.isFinite(value)) continue;
    if (value < low) low = value;
    if (value > high) high = value;
  }
  return low === Infinity ? null : [low, high];
}

/**
 * An SVG path through the points. A null value breaks the line, so a missing sample shows as a gap
 * and is never drawn as zero. Returns an empty string when no point is finite.
 */
export function linePath(
  xs: readonly number[],
  ys: ReadonlyArray<number | null | undefined>,
  x: (value: number) => number,
  y: (value: number) => number,
): string {
  let path = '';
  let pen = false;
  xs.forEach((value, index) => {
    const current = ys[index];
    if (typeof current !== 'number' || !Number.isFinite(current)) {
      pen = false;
      return;
    }
    path += `${pen ? 'L' : 'M'}${x(value).toFixed(1)},${y(current).toFixed(1)}`;
    pen = true;
  });
  return path;
}

/** Axis label text: whole numbers stay whole, fractions keep at most two decimals. */
export function formatTick(value: number): string {
  if (Number.isInteger(value)) return value.toLocaleString('en-US');
  return Number(value.toFixed(2)).toLocaleString('en-US', { maximumFractionDigits: 2 });
}
