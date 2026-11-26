import { describe, expect, it } from "vitest";
import { flatReason, MIN_3D_WIDTH } from "./mode";

const desktop = { reducedMotion: false, width: 1100, sidewaysPhone: false };

describe("flatReason", () => {
  it("allows 3D on a wide card", () => {
    expect(flatReason(desktop)).toBeNull();
    expect(flatReason({ ...desktop, width: MIN_3D_WIDTH })).toBeNull();
  });

  it("is flat on a narrow card, such as a phone held upright", () => {
    expect(flatReason({ ...desktop, width: MIN_3D_WIDTH - 1 })).toBe("narrow");
    expect(flatReason({ ...desktop, width: 318 })).toBe("narrow");
  });

  it("is flat on a phone held sideways even though the card is wide", () => {
    expect(flatReason({ ...desktop, width: 696, sidewaysPhone: true })).toBe("phone");
  });

  it("puts the reader's motion preference first", () => {
    expect(flatReason({ reducedMotion: true, width: 300, sidewaysPhone: true })).toBe("reduced-motion");
  });
});
