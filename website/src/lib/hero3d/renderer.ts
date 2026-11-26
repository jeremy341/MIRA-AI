/**
 * True when WebGL is being drawn by the processor. `failIfMajorPerformanceCaveat` does not catch every such case,
 * so the renderer's name is checked as well. A browser that hides the name is given the benefit of the doubt.
 */
export function isSoftwareRenderer(name: string): boolean {
  return /swiftshader|llvmpipe|softpipe|software|basic render/i.test(name);
}
