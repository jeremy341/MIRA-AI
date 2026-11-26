/**
 * The three.js side of the hero logo. This module (and `three` itself) is only ever loaded through a dynamic
 * import from HeroMark.svelte, after the page has painted.
 *
 * Each logo piece is its outline pushed into depth with rounded edges, lit by a soft studio environment. The logo
 * follows a pointer that is over it, sways a little on its own and comes apart as the hero scrolls away.
 */
import {
  AmbientLight,
  DirectionalLight,
  ExtrudeGeometry,
  Group,
  Mesh,
  MeshPhysicalMaterial,
  PerspectiveCamera,
  PMREMGenerator,
  Scene,
  Shape,
  Vector2,
  WebGLRenderer,
} from "three";
import { RoomEnvironment } from "three/examples/jsm/environments/RoomEnvironment.js";
import { PIECES, type PieceKind } from "./logo";
import { ENTRANCE_SECONDS, poseOf } from "./pose";
import { isSoftwareRenderer, pixelRatio } from "./renderer";

/** The canvas is this much wider than the 26-unit logo box, so pieces have room to fly and turn. */
export const BLEED = 1.5;
const LOGO_BOX = 26;
const FOV = 20;

/** Colours of static/mira.svg on the blue band: [front, sides]. */
const COLOURS: Record<PieceKind, readonly [number, number]> = {
  corner: [0xa9bbf0, 0x7e93da],
  letter: [0xffffff, 0xbccaf8],
  dot: [0xb9c9ff, 0x8aa0ec],
};
const THICKNESS: Record<PieceKind, number> = { corner: 1.1, letter: 2, dot: 1.6 };

export type HeroSceneOptions = {
  canvas: HTMLCanvasElement;
  /** False starts with the logo already assembled. */
  entrance: boolean;
  /** 0 while the hero is in place, rising to 1 as it scrolls away. */
  spread: () => number;
  onFirstFrame: () => void;
  /** The GPU context was lost: the page should show the flat logo. */
  onContextLost: () => void;
};

export type HeroScene = {
  setRunning: (running: boolean) => void;
  /** Pointer position over the logo, each axis from -1 to 1. (0, 0) is the resting angle. */
  setPointer: (x: number, y: number) => void;
  resize: () => void;
  dispose: () => void;
};

export function createHeroScene(options: HeroSceneOptions): HeroScene {
  const { canvas } = options;
  // Throws when WebGL is not available, or only as slow software rendering (no usable graphics card), where
  // drawing this would keep the processor busy. The caller keeps the flat logo then.
  const renderer = new WebGLRenderer({ canvas, antialias: true, alpha: true, failIfMajorPerformanceCaveat: true });
  renderer.setClearColor(0x000000, 0);
  const gl = renderer.getContext();
  const info = gl.getExtension("WEBGL_debug_renderer_info");
  if (isSoftwareRenderer(String(gl.getParameter(info ? info.UNMASKED_RENDERER_WEBGL : gl.RENDERER)))) {
    renderer.dispose();
    renderer.forceContextLoss();
    throw new Error("WebGL runs in software here");
  }

  const scene = new Scene();
  const generator = new PMREMGenerator(renderer);
  const room = new RoomEnvironment();
  const environment = generator.fromScene(room, 0.035);
  scene.environment = environment.texture;
  scene.environmentIntensity = 0.5;

  // Even light in the blue of the page, a white light from the front right and a periwinkle one from the left,
  // which keeps the sides of the pieces apart from the band behind them.
  const base = new AmbientLight(0xdfe6ff, 0.48);
  const front = new DirectionalLight(0xffffff, 0.95);
  front.position.set(14, 18, 34);
  const left = new DirectionalLight(0x8ea6f0, 1);
  left.position.set(-36, -6, 10);
  scene.add(base, front, left);

  const camera = new PerspectiveCamera(FOV, 1, 1, 400);
  camera.position.z = (LOGO_BOX * BLEED) / 2 / Math.tan((FOV * Math.PI) / 360);

  const logo = new Group();
  scene.add(logo);

  const meshes = PIECES.map((piece) => {
    const depth = THICKNESS[piece.kind];
    const bevel = 0.28;
    const geometry = new ExtrudeGeometry(new Shape(piece.outline.map(([x, y]) => new Vector2(x, y))), {
      depth,
      bevelThickness: bevel,
      bevelSize: bevel,
      // The bevel grows outward by default; pull it in so the piece keeps the width of the flat logo.
      bevelOffset: -bevel,
      bevelSegments: 5,
      curveSegments: 1,
    });
    geometry.translate(0, 0, -depth / 2);
    const materials = COLOURS[piece.kind].map(
      (color) => new MeshPhysicalMaterial({ color, roughness: 0.27, clearcoat: 0.5, clearcoatRoughness: 0.4 }),
    );
    const mesh = new Mesh(geometry, materials);
    logo.add(mesh);
    return { piece, mesh, geometry, materials };
  });

  let frame = 0;
  let elapsed = options.entrance ? 0 : ENTRANCE_SECONDS;
  let previous = 0;
  let spread = options.spread();
  const pointer = { x: 0, y: 0 };
  const eased = { x: 0, y: 0 };
  let painted = false;
  let disposed = false;

  function draw(step: number) {
    const follow = 1 - Math.exp(-step * 4.5);
    eased.x += (pointer.x - eased.x) * follow;
    eased.y += (pointer.y - eased.y) * follow;
    spread += (options.spread() - spread) * (1 - Math.exp(-step * 9));

    for (const { piece, mesh } of meshes) {
      const pose = poseOf(piece, elapsed, spread);
      mesh.position.set(pose.position.x, pose.position.y, pose.position.z);
      mesh.rotation.set(pose.rotation.x, pose.rotation.y, pose.rotation.z);
      mesh.scale.setScalar(pose.scale);
      mesh.visible = pose.scale > 0;
    }
    logo.rotation.set(
      0.08 + eased.y * 0.26 + Math.sin(elapsed * 0.53) * 0.045,
      -0.3 + eased.x * 0.45 + Math.sin(elapsed * 0.37) * 0.13 + spread * 0.5,
      Math.sin(elapsed * 0.29) * 0.025,
    );
    logo.position.y = Math.sin(elapsed * 0.8) * 0.28;
    renderer.render(scene, camera);
    if (!painted) {
      painted = true;
      options.onFirstFrame();
    }
  }

  function tick(now: number) {
    // The first frame after a pause must not jump ahead by the length of the pause.
    const step = previous ? Math.min(0.05, (now - previous) / 1000) : 0;
    previous = now;
    elapsed += step;
    draw(step);
    frame = requestAnimationFrame(tick);
  }

  function resize() {
    const width = canvas.clientWidth;
    const height = canvas.clientHeight;
    if (!width || !height || disposed) return;
    renderer.setPixelRatio(pixelRatio(window.devicePixelRatio, width, height));
    renderer.setSize(width, height, false);
    camera.aspect = width / height;
    camera.updateProjectionMatrix();
    if (painted) draw(0);
  }

  const lost = (event: Event) => {
    event.preventDefault();
    options.onContextLost();
  };
  canvas.addEventListener("webglcontextlost", lost);
  resize();

  return {
    setRunning(running) {
      if (disposed) return;
      if (running && !frame) {
        previous = 0;
        frame = requestAnimationFrame(tick);
      } else if (!running && frame) {
        cancelAnimationFrame(frame);
        frame = 0;
      }
    },
    setPointer(x, y) {
      pointer.x = x;
      pointer.y = y;
    },
    resize,
    dispose() {
      if (disposed) return;
      disposed = true;
      cancelAnimationFrame(frame);
      canvas.removeEventListener("webglcontextlost", lost);
      for (const { geometry, materials } of meshes) {
        geometry.dispose();
        for (const material of materials) material.dispose();
      }
      environment.dispose();
      room.dispose();
      generator.dispose();
      renderer.dispose();
    },
  };
}
