/**
 * The three.js side of the experiment landscape. This module (and `three` itself) is only ever loaded through a
 * dynamic import from ExperimentLandscape.svelte, after the card is near the viewport.
 *
 * It draws a plain 3D bar chart: boxes on a faint ground grid, two reference planes (50% and 100%, each an outlined
 * rectangle with a faint fill), a slow sideways sweep, drag to rotate, hover and click picking. No glow, particles or
 * decoration. All colours come from the CSS tokens of the page (read again when the theme changes).
 */
import {
  AmbientLight,
  BoxGeometry,
  BufferGeometry,
  Color,
  DirectionalLight,
  DoubleSide,
  EdgesGeometry,
  Float32BufferAttribute,
  LineBasicMaterial,
  LineSegments,
  Mesh,
  MeshBasicMaterial,
  MeshLambertMaterial,
  PerspectiveCamera,
  PlaneGeometry,
  Raycaster,
  Scene,
  Vector2,
  Vector3,
  WebGLRenderer,
} from "three";
import type { Column, Layout } from "./layout";

export type Point = { x: number; y: number };

export type SceneOptions = {
  host: HTMLElement;
  layout: Layout;
  /** Overlay elements of the page that follow 3D anchors. Keys are Anchor.key plus "tip". */
  onProject: (positions: Map<string, Point>) => void;
  /** The active column changed (hover, keyboard focus or click). */
  onActive: (id: string | null) => void;
  /** The GPU context was lost and did not come back in time: the page should fall back to flat bars. */
  onContextLost: () => void;
};

export type SceneHandle = {
  setVisible: (visible: boolean) => void;
  setFocus: (id: string | null) => void;
  clearSelection: () => void;
  /** Back to the default angle (also drops the selection). */
  resetView: () => void;
  refreshTheme: () => void;
  resize: () => void;
  dispose: () => void;
};

// A narrow field of view keeps the perspective mild, so a column at the near end is not drawn much taller than the
// same column at the far end. The camera looks down a little steeper than before so tops and planes stay readable.
const FOV = 12;
const BASE_AZIMUTH = -0.2;
const SWEEP = 0.18;
const SWEEP_PERIOD = 26; // seconds
const MIN_AZIMUTH = -1.0;
const MAX_AZIMUTH = 1.0;
const MIN_ELEVATION = 0.2;
const MAX_ELEVATION = 1.0;
const BASE_ELEVATION = 0.58;
const IDLE_RESUME_MS = 3500;
/** How long a lost WebGL context may take to come back before the page gives up on 3D. */
const CONTEXT_RESTORE_MS = 2500;

const clamp = (value: number, min: number, max: number) => Math.min(max, Math.max(min, value));

type Palette = {
  accent: Color;
  accentHover: Color;
  stageA: Color;
  stageB: Color;
  tile: Color;
  edge: Color;
  grid: Color;
  axis: Color;
};

function readPalette(host: HTMLElement): Palette {
  const css = getComputedStyle(host);
  const read = (name: string, fallback: string) => new Color(css.getPropertyValue(name).trim() || fallback);
  return {
    accent: read("--mira-accent", "#4565b6"),
    accentHover: read("--mira-accent-hover", "#4565b6"),
    stageA: read("--mira-stage-a", "#7e89a8"),
    stageB: read("--mira-stage-b", "#333c58"),
    tile: read("--mira-border", "#e3e3e3"),
    edge: read("--mira-text", "#1f1f1f"),
    grid: read("--mira-border-strong", "#8a8a8a"),
    axis: read("--mira-muted", "#535253"),
  };
}

export function createScene(options: SceneOptions): SceneHandle {
  const { host, layout } = options;

  const canvas = document.createElement("canvas");
  canvas.setAttribute("aria-hidden", "true");
  canvas.className = "ls-canvas";
  host.prepend(canvas);

  let renderer: WebGLRenderer;
  try {
    renderer = new WebGLRenderer({ canvas, antialias: true, alpha: true, powerPreference: "low-power" });
  } catch (error) {
    canvas.remove();
    throw error;
  }
  renderer.setClearColor(0x000000, 0);

  const scene = new Scene();
  const camera = new PerspectiveCamera(FOV, 2, 0.1, 200);
  scene.add(new AmbientLight(0xffffff, 1.5));
  const sun = new DirectionalLight(0xffffff, 2.1);
  sun.position.set(-6, 12, 9);
  scene.add(sun);

  let palette = readPalette(host);

  /* Columns ---------------------------------------------------------------- */
  const boxGeometry = new BoxGeometry(1, 1, 1);
  boxGeometry.translate(0, 0.5, 0);
  const edgeGeometry = new EdgesGeometry(boxGeometry);
  const edgeMaterial = new LineBasicMaterial({ color: palette.edge, transparent: true, opacity: 0.3 });

  type Entry = { column: Column; mesh: Mesh; material: MeshLambertMaterial };
  const entries: Entry[] = layout.columns.map((column) => {
    const material = new MeshLambertMaterial({ color: palette.stageB });
    const mesh = new Mesh(boxGeometry, material);
    mesh.position.set(column.x, 0, 0);
    mesh.scale.set(column.size, column.height, column.size);
    mesh.userData.id = column.id;
    mesh.add(new LineSegments(edgeGeometry, edgeMaterial));
    scene.add(mesh);
    return { column, mesh, material };
  });
  const byId = new Map(entries.map((entry) => [entry.column.id, entry]));
  const meshes = entries.map((entry) => entry.mesh);

  /* Ground grid and reference lines ---------------------------------------- */
  const gridMaterial = new LineBasicMaterial({ color: palette.grid, transparent: true, opacity: 0.22 });
  const gridPoints: number[] = [];
  const gx0 = Math.floor(layout.minX) - 0.5;
  const gx1 = Math.ceil(layout.maxX) + 0.5;
  const gz = layout.halfDepth;
  for (let x = gx0; x <= gx1 + 0.001; x += 1) gridPoints.push(x, 0, -gz, x, 0, gz);
  for (let z = -gz; z <= gz + 0.001; z += 0.8) gridPoints.push(gx0, 0, z, gx1, 0, z);
  const gridGeometry = new BufferGeometry();
  gridGeometry.setAttribute("position", new Float32BufferAttribute(gridPoints, 3));
  scene.add(new LineSegments(gridGeometry, gridMaterial));

  // Reference planes (50% and 100%): an outlined rectangle over the whole ground plus a faint fill, and four posts
  // at the corners so the planes read as a frame around the columns.
  const axisMaterial = new LineBasicMaterial({ color: palette.axis, transparent: true, opacity: 0.75 });
  const axisPoints: number[] = [];
  for (const anchor of layout.anchors) {
    if (anchor.kind !== "axis") continue;
    const y = anchor.y;
    axisPoints.push(gx0, y, -gz, gx1, y, -gz, gx1, y, -gz, gx1, y, gz, gx1, y, gz, gx0, y, gz, gx0, y, gz, gx0, y, -gz);
  }
  for (const [px, pz] of [
    [gx0, -gz],
    [gx1, -gz],
    [gx1, gz],
    [gx0, gz],
  ] as const) {
    axisPoints.push(px, 0, pz, px, layout.top, pz);
  }
  const axisGeometry = new BufferGeometry();
  axisGeometry.setAttribute("position", new Float32BufferAttribute(axisPoints, 3));
  scene.add(new LineSegments(axisGeometry, axisMaterial));

  const planeMaterial = new MeshBasicMaterial({
    color: palette.axis,
    transparent: true,
    opacity: 0.07,
    depthWrite: false,
    side: DoubleSide,
  });
  const planeGeometry = new PlaneGeometry(gx1 - gx0, gz * 2);
  planeGeometry.rotateX(-Math.PI / 2);
  planeGeometry.translate((gx0 + gx1) / 2, 0, 0);
  for (const anchor of layout.anchors) {
    if (anchor.kind !== "axis") continue;
    const plane = new Mesh(planeGeometry, planeMaterial);
    plane.position.y = anchor.y;
    plane.renderOrder = 2;
    scene.add(plane);
  }

  /* State ------------------------------------------------------------------ */
  let azimuth = BASE_AZIMUTH;
  let elevation = BASE_ELEVATION;
  let distance = 20;
  let hoverId: string | null = null;
  let focusId: string | null = null;
  let selectedId: string | null = null;
  let activeId: string | null = null;
  let visible = true;
  let disposed = false;
  let contextLost = false;
  let restoreTimer = 0;
  let frame = 0;
  let lastTime = 0;
  let sweepClock = 0;
  let idleSince = 0;
  let width = 0;
  let height = 0;

  const target = new Vector3(0, layout.top * 0.4, 0);
  const projected = new Vector3();

  function applyCamera() {
    const cosEl = Math.cos(elevation);
    camera.position.set(
      target.x + distance * cosEl * Math.sin(azimuth),
      target.y + distance * Math.sin(elevation),
      target.z + distance * cosEl * Math.cos(azimuth),
    );
    camera.lookAt(target);
    camera.updateMatrixWorld();
  }

  function fit() {
    const aspect = width / Math.max(height, 1);
    const tan = Math.tan((FOV * Math.PI) / 360);
    // The frame (ground grid, planes and posts) is a little wider than the row of columns: the grid starts half a
    // cell outside the first and last column and snaps to whole units.
    const frameHalfWidth = (Math.ceil(layout.maxX) + 0.5 - (Math.floor(layout.minX) - 0.5)) / 2;
    // Width of the frame as seen at the widest idle sweep angle (dragging further may clip the corners).
    const limit = Math.abs(BASE_AZIMUTH) + SWEEP + 0.1;
    const projectedHalfWidth = frameHalfWidth * Math.cos(limit) + layout.halfDepth * Math.sin(limit);
    // Height of the frame on screen at the base elevation, plus room for the labels above and below.
    const halfHeight = (layout.top * Math.cos(BASE_ELEVATION) + 2 * layout.halfDepth * Math.sin(BASE_ELEVATION)) / 2 + 0.9;
    const byWidth = projectedHalfWidth / (tan * aspect);
    const byHeight = halfHeight / tan;
    distance = Math.max(byWidth, byHeight) * 1.08;
  }

  function colourFor(entry: Entry, active: boolean): Color {
    if (active) return palette.accentHover;
    if (entry.column.highlight) return palette.accent;
    if (entry.column.value === null) return palette.tile;
    return entry.column.stage === "A" ? palette.stageA : palette.stageB;
  }

  function paint() {
    for (const entry of entries) entry.material.color.copy(colourFor(entry, entry.column.id === activeId));
  }

  function project(point: Vector3): Point {
    projected.copy(point).project(camera);
    return { x: ((projected.x + 1) / 2) * width, y: ((1 - projected.y) / 2) * height };
  }

  const world = new Vector3();
  function updateOverlay() {
    const positions = new Map<string, Point>();
    for (const anchor of layout.anchors) positions.set(anchor.key, project(world.set(anchor.x, anchor.y, anchor.z)));
    if (activeId) {
      const entry = byId.get(activeId);
      if (entry) positions.set("tip", project(world.set(entry.column.x, entry.column.height, 0)));
    }
    options.onProject(positions);
  }

  function render() {
    applyCamera();
    renderer.render(scene, camera);
    updateOverlay();
  }

  function setActive() {
    const next = selectedId ?? focusId ?? hoverId;
    if (next === activeId) return;
    activeId = next;
    paint();
    options.onActive(activeId);
    if (!running()) render();
  }

  /* Loop ------------------------------------------------------------------- */
  const running = () => visible && !document.hidden && !contextLost && !disposed;

  function tick(time: number) {
    frame = 0;
    if (!running()) return;
    const dt = lastTime ? Math.min((time - lastTime) / 1000, 0.1) : 0;
    lastTime = time;
    const interacting = pointerDown !== null || activeId !== null || time - idleSince < IDLE_RESUME_MS;
    if (!interacting) {
      sweepClock += dt;
      const phase = (sweepClock / SWEEP_PERIOD) * Math.PI * 2;
      // Ease back towards the sweep line so releasing a drag does not jump.
      const goal = BASE_AZIMUTH + Math.sin(phase) * SWEEP;
      azimuth += (goal - azimuth) * Math.min(1, dt * 1.5);
      elevation += (BASE_ELEVATION - elevation) * Math.min(1, dt * 0.8);
    }
    render();
    schedule();
  }

  function schedule() {
    if (!frame && running()) frame = requestAnimationFrame(tick);
  }

  function restart() {
    lastTime = 0;
    if (running()) {
      render();
      schedule();
    }
  }

  /* Picking and dragging --------------------------------------------------- */
  const raycaster = new Raycaster();
  const pointer = new Vector2();
  function pick(event: PointerEvent): string | null {
    const rect = canvas.getBoundingClientRect();
    pointer.set(((event.clientX - rect.left) / rect.width) * 2 - 1, -(((event.clientY - rect.top) / rect.height) * 2 - 1));
    raycaster.setFromCamera(pointer, camera);
    const hit = raycaster.intersectObjects(meshes, false)[0];
    return hit ? (hit.object.userData.id as string) : null;
  }

  type Drag = { pointerId: number; startX: number; startY: number; azimuth: number; elevation: number; moved: boolean };
  let pointerDown: Drag | null = null;

  function onPointerDown(event: PointerEvent) {
    if (event.pointerType === "mouse" && event.button !== 0) return;
    pointerDown = {
      pointerId: event.pointerId,
      startX: event.clientX,
      startY: event.clientY,
      azimuth,
      elevation,
      moved: false,
    };
    try {
      canvas.setPointerCapture(event.pointerId);
    } catch {
      /* capture is a convenience */
    }
  }

  function onPointerMove(event: PointerEvent) {
    if (pointerDown && pointerDown.pointerId === event.pointerId) {
      const dx = event.clientX - pointerDown.startX;
      const dy = event.clientY - pointerDown.startY;
      if (!pointerDown.moved && Math.hypot(dx, dy) > 5) pointerDown.moved = true;
      if (pointerDown.moved) {
        azimuth = clamp(pointerDown.azimuth - dx * 0.006, MIN_AZIMUTH, MAX_AZIMUTH);
        elevation = clamp(pointerDown.elevation + dy * 0.004, MIN_ELEVATION, MAX_ELEVATION);
        idleSince = performance.now();
        if (!running()) render();
      }
      return;
    }
    if (event.pointerType === "mouse") {
      const id = pick(event);
      if (id !== hoverId) {
        hoverId = id;
        canvas.style.cursor = id ? "pointer" : "grab";
        setActive();
      }
    }
  }

  function onPointerUp(event: PointerEvent) {
    const drag = pointerDown;
    if (!drag || drag.pointerId !== event.pointerId) return;
    pointerDown = null;
    idleSince = performance.now();
    try {
      canvas.releasePointerCapture(event.pointerId);
    } catch {
      /* already released */
    }
    if (!drag.moved) {
      const id = pick(event);
      selectedId = id && id !== selectedId ? id : null;
      if (event.pointerType === "mouse") hoverId = id;
      setActive();
    }
  }

  function onPointerCancel() {
    pointerDown = null;
  }

  function onPointerLeave(event: PointerEvent) {
    if (event.pointerType !== "mouse" || pointerDown) return;
    hoverId = null;
    setActive();
  }

  canvas.style.cursor = "grab";
  canvas.addEventListener("pointerdown", onPointerDown);
  canvas.addEventListener("pointermove", onPointerMove);
  canvas.addEventListener("pointerup", onPointerUp);
  canvas.addEventListener("pointercancel", onPointerCancel);
  canvas.addEventListener("pointerleave", onPointerLeave);

  // A lost context is not final: preventDefault lets the browser restore it (three.js re-uploads its resources).
  // Only when it has not come back after CONTEXT_RESTORE_MS does the page fall back to flat bars.
  function onContextLost(event: Event) {
    event.preventDefault();
    contextLost = true;
    window.clearTimeout(restoreTimer);
    restoreTimer = window.setTimeout(() => {
      if (contextLost && !disposed) options.onContextLost();
    }, CONTEXT_RESTORE_MS);
  }
  function onContextRestored() {
    window.clearTimeout(restoreTimer);
    contextLost = false;
    paint();
    restart();
  }
  canvas.addEventListener("webglcontextlost", onContextLost);
  canvas.addEventListener("webglcontextrestored", onContextRestored);

  const onVisibility = () => restart();
  document.addEventListener("visibilitychange", onVisibility);

  /* Sizing ----------------------------------------------------------------- */
  function resize() {
    const rect = host.getBoundingClientRect();
    const w = Math.max(1, Math.round(rect.width));
    const h = Math.max(1, Math.round(rect.height));
    if (w === width && h === height) return;
    width = w;
    height = h;
    renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
    renderer.setSize(w, h, false);
    camera.aspect = w / h;
    camera.updateProjectionMatrix();
    fit();
    if (!running()) render();
  }

  const observer = new ResizeObserver(() => resize());
  observer.observe(host);
  resize();
  paint();
  render();
  schedule();

  return {
    setVisible(next) {
      if (visible === next) return;
      visible = next;
      if (next) restart();
    },
    setFocus(id) {
      focusId = id;
      setActive();
    },
    clearSelection() {
      selectedId = null;
      setActive();
    },
    resetView() {
      selectedId = null;
      hoverId = null;
      azimuth = BASE_AZIMUTH;
      elevation = BASE_ELEVATION;
      sweepClock = 0;
      idleSince = performance.now();
      setActive();
      if (!running()) render();
    },
    refreshTheme() {
      palette = readPalette(host);
      edgeMaterial.color.copy(palette.edge);
      gridMaterial.color.copy(palette.grid);
      axisMaterial.color.copy(palette.axis);
      planeMaterial.color.copy(palette.axis);
      paint();
      if (!running()) render();
    },
    resize,
    dispose() {
      if (disposed) return;
      disposed = true;
      if (frame) cancelAnimationFrame(frame);
      observer.disconnect();
      document.removeEventListener("visibilitychange", onVisibility);
      canvas.removeEventListener("pointerdown", onPointerDown);
      canvas.removeEventListener("pointermove", onPointerMove);
      canvas.removeEventListener("pointerup", onPointerUp);
      canvas.removeEventListener("pointercancel", onPointerCancel);
      canvas.removeEventListener("pointerleave", onPointerLeave);
      canvas.removeEventListener("webglcontextlost", onContextLost);
      canvas.removeEventListener("webglcontextrestored", onContextRestored);
      window.clearTimeout(restoreTimer);
      planeGeometry.dispose();
      planeMaterial.dispose();
      boxGeometry.dispose();
      edgeGeometry.dispose();
      gridGeometry.dispose();
      axisGeometry.dispose();
      edgeMaterial.dispose();
      gridMaterial.dispose();
      axisMaterial.dispose();
      for (const entry of entries) entry.material.dispose();
      renderer.dispose();
      renderer.forceContextLoss();
      canvas.remove();
    },
  };
}
