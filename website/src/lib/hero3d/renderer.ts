/**
 * True when WebGL is being drawn by the processor. `failIfMajorPerformanceCaveat` does not catch every such case,
 * so the renderer's name is checked as well. A browser that hides the name is given the benefit of the doubt.
 */
export function isSoftwareRenderer(name: string): boolean {
  return /swiftshader|llvmpipe|softpipe|software|basic render/i.test(name);
}

/** About a 2000 x 2000 canvas. */
const MAX_PIXELS = 4_000_000;

/** The screen's pixel density, at most 2, and lower when a large canvas would otherwise pass MAX_PIXELS. */
export function pixelRatio(density: number, width: number, height: number): number {
  return Math.min(density || 1, 2, Math.sqrt(MAX_PIXELS / (width * height)));
}
