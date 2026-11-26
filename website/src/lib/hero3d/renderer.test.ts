import { describe, expect, it } from "vitest";
import { isSoftwareRenderer } from "./renderer";

describe("isSoftwareRenderer", () => {
  it("recognises renderers that run on the processor", () => {
    for (const name of [
      "ANGLE (Google, Vulkan 1.3.0 (SwiftShader Device (Subzero) (0x0000C0DE)), SwiftShader driver)",
      "llvmpipe (LLVM 15.0.7, 256 bits)",
      "ANGLE (Microsoft, Microsoft Basic Render Driver Direct3D11 vs_5_0 ps_5_0, D3D11)",
      "Software Rasterizer",
    ]) {
      expect(isSoftwareRenderer(name), name).toBe(true);
    }
  });

  it("leaves graphics chips and hidden names alone", () => {
    for (const name of [
      "ANGLE (AMD, AMD Radeon RX 5600 XT (0x0000731F) Direct3D11 vs_5_0 ps_5_0, D3D11)",
      "Apple GPU",
      "Mali-G78",
      "Adreno (TM) 640",
      "WebKit WebGL",
      "",
    ]) {
      expect(isSoftwareRenderer(name), name).toBe(false);
    }
  });
});
