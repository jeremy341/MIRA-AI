import { describe, expect, it } from 'vitest';
import { extent, formatTick, linePath, linearScale, niceStep, niceTicks } from './scale';

describe('linearScale', () => {
  it('maps the domain onto the range, including a flipped range for the y axis', () => {
    const y = linearScale([0, 100], [200, 0]);
    expect(y(0)).toBe(200);
    expect(y(100)).toBe(0);
    expect(y(25)).toBe(150);
  });

  it('maps a flat domain to the start of the range instead of dividing by zero', () => {
    expect(linearScale([5, 5], [10, 90])(5)).toBe(10);
  });
});

describe('niceTicks', () => {
  it('uses round steps and covers the whole range', () => {
    expect(niceTicks(0, 100, 5)).toEqual([0, 20, 40, 60, 80, 100]);
    expect(niceTicks(0, 37, 4)).toEqual([0, 10, 20, 30, 40]);
  });

  it('keeps small fractions readable', () => {
    const ticks = niceTicks(0, 0.8, 4);
    expect(ticks[0]).toBe(0);
    expect(ticks.at(-1)).toBeGreaterThanOrEqual(0.8);
    expect(ticks.every((t) => Number.isFinite(t))).toBe(true);
  });

  it('gives at least two ticks for a flat range and for swapped bounds', () => {
    expect(niceTicks(7, 7).length).toBeGreaterThanOrEqual(2);
    expect(niceTicks(100, 0)[0]).toBe(0);
  });

  it('never invents a negative axis for a flat non-negative series', () => {
    expect(Math.min(...niceTicks(0, 0))).toBe(0);
    expect(Math.max(...niceTicks(0, 0))).toBeGreaterThan(0);
    expect(Math.min(...niceTicks(5, 5))).toBe(0);
    expect(Math.max(...niceTicks(-5, -5))).toBe(0);
  });

  it('chooses a step of 1, 2, 2.5, 5 or 10 times a power of ten', () => {
    expect(niceStep(100, 5)).toBe(20);
    expect(niceStep(1, 5)).toBe(0.2);
    expect(niceStep(0, 5)).toBe(1);
  });
});

describe('extent', () => {
  it('ignores nulls and non-finite values', () => {
    expect(extent([3, null, 9, Number.NaN, -1])).toEqual([-1, 9]);
  });

  it('is null when nothing is finite', () => {
    expect(extent([null, undefined])).toBeNull();
    expect(extent([])).toBeNull();
  });
});

describe('linePath', () => {
  const x = (v: number) => v * 10;
  const y = (v: number) => 100 - v;

  it('draws one move and then lines through the points', () => {
    expect(linePath([0, 1, 2], [10, 20, 30], x, y)).toBe('M0.0,90.0L10.0,80.0L20.0,70.0');
  });

  it('breaks the line at a null instead of drawing it as zero', () => {
    expect(linePath([0, 1, 2, 3], [10, null, 30, 40], x, y)).toBe('M0.0,90.0M20.0,70.0L30.0,60.0');
  });

  it('is empty when there is no finite point', () => {
    expect(linePath([0, 1], [null, null], x, y)).toBe('');
  });
});

describe('formatTick', () => {
  it('keeps whole numbers whole and fractions to two places', () => {
    expect(formatTick(1200)).toBe('1,200');
    expect(formatTick(0.456)).toBe('0.46');
    expect(formatTick(0.5)).toBe('0.5');
  });
});
