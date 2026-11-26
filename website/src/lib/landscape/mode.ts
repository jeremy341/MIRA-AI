/** When the experiment chart is drawn as flat bars instead of in 3D. */

/** Below this card width the 3D labels run into each other. This covers phones held upright. */
export const MIN_3D_WIDTH = 560;
/** A phone held sideways has a wider card than that, so it is told apart by touch input and a low screen. */
export const SIDEWAYS_PHONE_QUERY = "(pointer: coarse) and (max-height: 500px)";

export type FlatReason = "reduced-motion" | "narrow" | "phone";

/** The reason to show flat bars right now, or null when 3D is fine. */
export function flatReason(view: { reducedMotion: boolean; width: number; sidewaysPhone: boolean }): FlatReason | null {
  if (view.reducedMotion) return "reduced-motion";
  if (view.width < MIN_3D_WIDTH) return "narrow";
  if (view.sidewaysPhone) return "phone";
  return null;
}
