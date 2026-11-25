// MIRA Dashboard - live detection frontend
// hand-wired, no framework - keep it simple
const CLASSES = ["glass", "metal", "paper", "plastic", "trash"];
const CLASS_LABELS = {
  glass: "Glass",
  metal: "Metal",
  paper: "Paper",
  plastic: "Plastic",
  trash: "Trash"
};
const CLASS_COLORS = {
  glass: "#2d8c8c",
  metal: "#6e7185",
  paper: "#d19a2c",
  plastic: "#d85c48",
  trash: "#4c4a43"
};
const state = {
  // stream + backend
  streaming: false,
  backendRunning: false,
  busy: false,
  cameraReady: false,
  modelReady: false,
  videoConnected: false,
  controlConnected: false,
  // detections
  latestDetections: [],
  imageBusy: false,
  currentResultKey: "",
  history: [],
  classCounts: Object.fromEntries(CLASSES.map(name => [name, 0])),
  totalDetections: 0,
  confidenceSum: 0,
  confidenceSamples: 0,
  backendAverageConfidence: null,
  // perf
  fps: null,
  latency: null,
  sessionStartedAt: null,
  accumulatedSessionMs: 0,
  // charts - keep flat for now, splitting broke updates last time
  trendLabels: [],
  trendValues: Object.fromEntries(CLASSES.map(name => [name, []])),
  chartUpdatePending: false,
  lastChartUpdate: 0,
  frameLoaded: false,
  perfLabels: [],
  fpsHistory: [],
  latencyHistory: [],
  cpuHistory: [],
  memHistory: []
};
let videoSocket = null;
let controlSocket = null;
let videoReconnectTimer = null;
let controlReconnectTimer = null;
let pingTimer = null;
let streamReadyTimer = null;
const elements = {
  navButtons: document.querySelectorAll(".nav-button"),
  pages: document.querySelectorAll(".page"),
  modelName: document.getElementById("modelName"),
  connectionDot: document.getElementById("connectionDot"),
  connectionText: document.getElementById("connectionText"),
  headerStreamDot: document.getElementById("headerStreamDot"),
  headerStreamText: document.getElementById("headerStreamText"),
  cameraStatusLabel: document.getElementById("cameraStatusLabel"),
  liveBadge: document.getElementById("liveBadge"),
  startButton: document.getElementById("startButton"),
  stopButton: document.getElementById("stopButton"),
  cameraStage: document.getElementById("cameraStage"),
  cameraImage: document.getElementById("cameraImage"),
  cameraPlaceholder: document.getElementById("cameraPlaceholder"),
  detectionCanvas: document.getElementById("detectionCanvas"),
  fpsValue: document.getElementById("fpsValue"),
  latencyValue: document.getElementById("latencyValue"),
  detectionCountValue: document.getElementById("detectionCountValue"),
  liveConfidenceValue: document.getElementById("liveConfidenceValue"),
  cameraState: document.getElementById("cameraState"),
  distributionTotal: document.getElementById("distributionTotal"),
  distributionEmpty: document.getElementById("distributionEmpty"),
  classLegend: document.getElementById("classLegend"),
  recentList: document.getElementById("recentList"),
  recentCount: document.getElementById("recentCount"),
  summaryTotal: document.getElementById("summaryTotal"),
  summaryDuration: document.getElementById("summaryDuration"),
  summaryTopClass: document.getElementById("summaryTopClass"),
  summaryConfidence: document.getElementById("summaryConfidence"),
  trendEmpty: document.getElementById("trendEmpty"),
  breakdownEmpty: document.getElementById("breakdownEmpty"),
  perfEmpty: document.getElementById("perfEmpty"),
  sysEmpty: document.getElementById("sysEmpty"),
  toastRegion: document.getElementById("toastRegion"),
  source: document.getElementById("detectSource"),
  sourceTitle: document.getElementById("sourceTitle"),
  imageControls: document.getElementById("imageControls"),
  imageFile: document.getElementById("imageFile"),
  detectImageButton: document.getElementById("detectImageButton"),
  imageStatus: document.getElementById("imageStatus"),
  confidence: document.getElementById("displayConfidence"),
  confidenceValue: document.getElementById("displayConfidenceValue"),
  confidenceNote: document.getElementById("confidenceNote"),
  currentCount: document.getElementById("currentCount"),
  currentEmpty: document.getElementById("currentEmpty"),
  currentList: document.getElementById("currentDetections")
};

function isImageSource() {
  return elements.source.value === "image";
}

function updateStartButton() {
  const ready = state.cameraReady && state.modelReady;
  elements.startButton.disabled = state.busy || state.streaming || !ready;
  if (state.busy && !state.streaming) elements.startButton.textContent = "Starting…";
  else if (!ready) elements.startButton.textContent = "Preparing…";
  else elements.startButton.textContent = "Start Stream";
  elements.source.disabled = state.busy || state.streaming || state.imageBusy;
  elements.imageFile.disabled = state.imageBusy;
  elements.confidence.disabled = state.imageBusy;
  elements.detectImageButton.disabled = state.imageBusy || state.streaming || state.backendRunning
    || !state.modelReady || !elements.imageFile.files.length;
  elements.cameraStatusLabel.hidden = isImageSource();
  elements.detectImageButton.textContent = state.imageBusy ? "Detecting…" : "Detect image";
}

function updateReadinessMessage() {
  if (state.cameraReady && state.modelReady) {
    elements.cameraStatusLabel.textContent = "System ready";
    elements.cameraState.textContent = "Press Start Stream to begin detection.";
  } else if (!state.cameraReady && !state.modelReady) {
    elements.cameraStatusLabel.textContent = "Preparing camera and model";
    elements.cameraState.textContent = "The dashboard is setting up the default camera and model…";
  } else if (!state.cameraReady) {
    elements.cameraStatusLabel.textContent = "Camera needs attention";
    elements.cameraState.textContent = "Open Settings and check the camera configuration.";
  } else {
    elements.cameraStatusLabel.textContent = "Model needs attention";
    elements.cameraState.textContent = "Open Settings and check the model configuration.";
  }
  updateStartButton();
}
const chartAvailable = typeof Chart !== "undefined";
if (chartAvailable) {
  Chart.defaults.font.family = '"IBM Plex Mono", monospace';
  Chart.defaults.font.size = 9;
  Chart.defaults.color = "#667069";
  Chart.defaults.animation.duration = 0;
  Chart.defaults.borderColor = "#d7d7d0";
}

// helper so we don't copy the same Chart boilerplate five times
function makeChart(id, cfg) {
  return chartAvailable
    ? new Chart(document.getElementById(id), cfg)
    : { data: cfg.data, update() {} };
}
const distributionChart = makeChart("distributionChart", {
  type: "doughnut",
  type: "doughnut",
  data: {
    labels: CLASSES.map(name => CLASS_LABELS[name]),
    datasets: [{
      data: CLASSES.map(() => 0),
      backgroundColor: CLASSES.map(name => CLASS_COLORS[name]),
      borderColor: "#f8f6ef",
      borderWidth: 3,
      hoverOffset: 2
    }]
  },
  options: {
    responsive: true,
    maintainAspectRatio: false,
    cutout: "66%",
    plugins: {
      legend: { display: false },
      tooltip: { callbacks: { label: context => ` ${context.label}: ${context.raw}` } }
    }
  }
});
const trendChart = makeChart("trendChart", {
  type: "line",
  data: {
    labels: [],
    datasets: CLASSES.map(name => ({
      label: CLASS_LABELS[name],
      data: [],
      borderColor: CLASS_COLORS[name],
      backgroundColor: CLASS_COLORS[name],
      pointRadius: 0,
      pointHoverRadius: 3,
      borderWidth: 2,
      tension: 0.18
    }))
  },
  options: {
    responsive: true,
    maintainAspectRatio: false,
    interaction: { mode: "index", intersect: false },
    scales: {
      x: { grid: { display: false }, ticks: { maxTicksLimit: 8, maxRotation: 0 } },
      y: { beginAtZero: true, ticks: { precision: 0, maxTicksLimit: 6 } }
    },
    plugins: { legend: { position: "top", align: "start", labels: { boxWidth: 10, boxHeight: 3, padding: 13, usePointStyle: false } } }
  }
});
const breakdownChart = makeChart("breakdownChart", {
  type: "bar",
  data: {
    labels: CLASSES.map(name => CLASS_LABELS[name]),
    datasets: [{
      data: CLASSES.map(() => 0),
      backgroundColor: CLASSES.map(name => CLASS_COLORS[name]),
      borderWidth: 0,
      barThickness: 15
    }]
  },
  options: {
    indexAxis: "y",
    responsive: true,
    maintainAspectRatio: false,
    scales: {
      x: { beginAtZero: true, ticks: { precision: 0, maxTicksLimit: 5 } },
      y: { grid: { display: false } }
    },
    plugins: { legend: { display: false }, tooltip: { callbacks: { label: context => ` ${context.raw} Objects` } } }
  }
});
const perfChart = makeChart("perfChart", {
  type: "line",
  data: {
    labels: [],
    datasets: [
      { label: "FPS", data: [], borderColor: "#58b87c", backgroundColor: "#58b87c", yAxisID: "y", pointRadius: 0, pointHoverRadius: 3, borderWidth: 2, tension: 0.18 },
      { label: "Latency (ms)", data: [], borderColor: "#e76f3c", backgroundColor: "#e76f3c", yAxisID: "y1", pointRadius: 0, pointHoverRadius: 3, borderWidth: 2, tension: 0.18 }
    ]
  },
  options: {
    responsive: true,
    maintainAspectRatio: false,
    interaction: { mode: "index", intersect: false },
    scales: {
      x: { grid: { display: false }, ticks: { maxTicksLimit: 6, maxRotation: 0 } },
      y: { type: "linear", display: true, position: "left", beginAtZero: true, title: { display: true, text: "FPS", font: { size: 8, family: "'IBM Plex Mono', monospace" } }, ticks: { precision: 0, maxTicksLimit: 5 } },
      y1: { type: "linear", display: true, position: "right", beginAtZero: true, grid: { drawOnChartArea: false }, title: { display: true, text: "ms", font: { size: 8, family: "'IBM Plex Mono', monospace" } }, ticks: { precision: 0, maxTicksLimit: 5 } }
    },
    plugins: { legend: { position: "top", align: "start", labels: { boxWidth: 10, boxHeight: 3, padding: 10, usePointStyle: false, font: { size: 8 } } } }
  }
});
const sysChart = makeChart("sysChart", {
  type: "line",
  data: {
    labels: [],
    datasets: [
      { label: "CPU %", data: [], borderColor: "#6e7185", backgroundColor: "#6e7185", yAxisID: "y", pointRadius: 0, pointHoverRadius: 3, borderWidth: 2, tension: 0.18 },
      { label: "Memory %", data: [], borderColor: "#d19a2c", backgroundColor: "#d19a2c", yAxisID: "y1", pointRadius: 0, pointHoverRadius: 3, borderWidth: 2, tension: 0.18 }
    ]
  },
  options: {
    responsive: true,
    maintainAspectRatio: false,
    interaction: { mode: "index", intersect: false },
    scales: {
      x: { grid: { display: false }, ticks: { maxTicksLimit: 6, maxRotation: 0 } },
      y: { type: "linear", display: true, position: "left", min: 0, max: 100, title: { display: true, text: "CPU %", font: { size: 8, family: "'IBM Plex Mono', monospace" } }, ticks: { precision: 0, maxTicksLimit: 5 } },
      y1: { type: "linear", display: true, position: "right", min: 0, max: 100, grid: { drawOnChartArea: false }, title: { display: true, text: "Memory %", font: { size: 8, family: "'IBM Plex Mono', monospace" } }, ticks: { precision: 0, maxTicksLimit: 5 } }
    },
    plugins: { legend: { position: "top", align: "start", labels: { boxWidth: 10, boxHeight: 3, padding: 10, usePointStyle: false, font: { size: 8 } } } }
  }
});
function websocketURL(path) {
  const protocol = location.protocol === "https:" ? "wss:" : "ws:";
  return `${protocol}//${location.host}${path}`;
}
// waste classes are fixed - fallback to trash if unknown
function toWasteClass(value) {
  const name = String(value || "trash").toLowerCase();
  return CLASSES.includes(name) ? name : "trash";
}
const normalizeClass = toWasteClass; // keep old name for compat

function clampConfidence(value) {
  const n = Number(value);
  if (!Number.isFinite(n)) return 0;
  return Math.max(0, Math.min(1, n));
}
const normalizeConfidence = clampConfidence;

function normalizeDetection(item) {
  return {
    className: toWasteClass(item.class_name ?? item.class),
    confidence: clampConfidence(item.confidence),
    trackId: item.track_id ?? "-",
    timestamp: item.timestamp || new Date().toISOString(),
    bbox: Array.isArray(item.bbox) ? item.bbox : null
  };
}
function formatTime(timestamp, withDate = false) {
  const date = new Date(timestamp);
  if (Number.isNaN(date.getTime())) return "-";
  const options = withDate
    ? { day: "2-digit", month: "2-digit", year: "2-digit", hour: "2-digit", minute: "2-digit", second: "2-digit" }
    : { hour: "2-digit", minute: "2-digit", second: "2-digit" };
  return new Intl.DateTimeFormat("de-DE", options).format(date);
}
function formatDuration(milliseconds) {
  const totalSeconds = Math.max(0, Math.floor(milliseconds / 1000));
  const hours = Math.floor(totalSeconds / 3600);
  const minutes = Math.floor((totalSeconds % 3600) / 60);
  const seconds = totalSeconds % 60;
  if (hours > 0) {
    return [hours, minutes, seconds].map(v => String(v).padStart(2, "0")).join(":");
  }
  return [minutes, seconds].map(v => String(v).padStart(2, "0")).join(":");
}
function currentSessionMs() {
  const activeMs = state.streaming && state.sessionStartedAt ? Date.now() - state.sessionStartedAt : 0;
  return state.accumulatedSessionMs + activeMs;
}
function showToast(message, type = "success") {
  const toast = document.createElement("div");
  toast.className = `toast ${type}`;
  toast.innerHTML = `<span class="toast-bar"></span><span class="toast-message"></span><button class="toast-close" type="button" aria-label="Close notification">×</button>`;
  toast.querySelector(".toast-message").textContent = message;
  toast.querySelector(".toast-close").addEventListener("click", () => toast.remove());
  elements.toastRegion.appendChild(toast);
  window.setTimeout(() => { if (toast.isConnected) toast.remove(); }, 4500);
}
async function fetchJSON(url, options = {}, silent = false) {
  const { timeoutMs = 15000, ...requestOptions } = options;
  const controller = new AbortController();
  const externalSignal = options.signal;
  const abortExternal = () => controller.abort();
  if (externalSignal) {
    if (externalSignal.aborted) controller.abort();
    else externalSignal.addEventListener("abort", abortExternal, { once: true });
  }
  const timeout = window.setTimeout(function() { controller.abort(); }, timeoutMs);
  try {
    const response = await fetch(url, {
      ...requestOptions,
      headers: { "Content-Type": "application/json", ...(options.headers || {}) },
      signal: controller.signal,
    });
    let data = {};
    try { data = await response.json(); } catch (_) { data = {}; }
    if (!response.ok) throw new Error(data.message || data.detail?.message || data.detail || `HTTP ${response.status}`);
    return data;
  } catch (error) {
    const message = error.name === "AbortError" ? "The dashboard request timed out." : error.message;
    if (!silent) showToast(`API error: ${message}`, "error");
    throw new Error(message);
  } finally {
    window.clearTimeout(timeout);
    externalSignal?.removeEventListener("abort", abortExternal);
  }
}
function updateConnectionUI() {
  const connected = state.videoConnected || state.controlConnected;
  elements.connectionDot.classList.toggle("connected", connected);
  elements.connectionDot.classList.toggle("disconnected", !connected);
  if (state.videoConnected && state.controlConnected) elements.connectionText.textContent = "WebSocket connected";
  else if (connected) elements.connectionText.textContent = "Partially connected";
  else elements.connectionText.textContent = "WebSocket disconnected";

  const statusEl = document.getElementById("telemetryStatus");
  if (statusEl) {
    statusEl.textContent = connected ? "MONITORING ACTIVE" : "DISCONNECTED";
    statusEl.style.color = connected ? "var(--green)" : "var(--danger)";
  }
}
function setStreaming(streaming, message = "") {
  if (state.streaming === streaming) {
    if (message) { elements.cameraStatusLabel.textContent = message; elements.cameraState.textContent = message; }
    return;
  }
  if (streaming) state.sessionStartedAt = Date.now();
  else if (state.sessionStartedAt) { state.accumulatedSessionMs += Date.now() - state.sessionStartedAt; state.sessionStartedAt = null; }
  state.streaming = streaming;
  updateStartButton();
  elements.stopButton.disabled = !streaming || state.busy;
  elements.liveBadge.classList.toggle("visible", streaming);
  elements.headerStreamDot.classList.toggle("streaming", streaming);
  elements.headerStreamText.textContent = streaming ? "LIVE" : "READY";
  elements.cameraStatusLabel.textContent = message || (streaming ? "Streaming active" : "System ready");
  elements.cameraState.textContent = message || (streaming ? "Waiting for camera frame…" : "Waiting for stream…");
  if (!streaming) {
    if (!isImageSource()) clearPreview();
    elements.fpsValue.textContent = "-";
    elements.latencyValue.textContent = "- ms";
    clearBoundingBoxes();
    updateCharts();
    renderRecent();
    renderSummary();
  }
}
function setBusy(busy) {
  state.busy = busy;
  updateStartButton();
  elements.stopButton.disabled = busy || !state.streaming;
  elements.stopButton.textContent = busy && state.streaming ? "Stopping…" : "Stop";
}
function sendControl(payload) {
  if (!controlSocket || controlSocket.readyState !== WebSocket.OPEN) return false;
  try { controlSocket.send(JSON.stringify(payload)); return true; }
  catch (error) { showToast(`Control channel error (Steuerkanal): ${error.message}`, "error"); return false; }
}
function connectVideoSocket() {
  clearTimeout(videoReconnectTimer);
  try { videoSocket = new WebSocket(websocketURL("/ws/video")); }
  catch (error) { state.videoConnected = false; updateConnectionUI(); videoReconnectTimer = setTimeout(connectVideoSocket, 3000); return; }
  videoSocket.addEventListener("open", () => {
    state.videoConnected = true;
    updateConnectionUI();
    clearInterval(pingTimer);
    pingTimer = setInterval(() => { if (videoSocket && videoSocket.readyState === WebSocket.OPEN) { try { videoSocket.send("ping"); } catch (_) {} } }, 15000);
  });
  videoSocket.addEventListener("message", event => {
    if (event.data === "pong") return;
    let payload;
    try { payload = JSON.parse(event.data); } catch (_) { return; }
    handleVideoMessage(payload);
  });
  videoSocket.addEventListener("error", () => { state.videoConnected = false; updateConnectionUI(); });
  videoSocket.addEventListener("close", event => {
    state.videoConnected = false;
    updateConnectionUI();
    clearInterval(pingTimer);
    console.warn(`[MIRA] Video socket closed (${event.code}): ${event.reason || "no reason provided"}`);
    videoReconnectTimer = setTimeout(connectVideoSocket, 3000);
  });
}
function connectControlSocket() {
  clearTimeout(controlReconnectTimer);
  try { controlSocket = new WebSocket(websocketURL("/ws/control")); }
  catch (error) { state.controlConnected = false; updateConnectionUI(); controlReconnectTimer = setTimeout(connectControlSocket, 3000); return; }
  controlSocket.addEventListener("open", () => {
    state.controlConnected = true;
    updateConnectionUI();
    sendControl({ command: "get_status" });
    sendControl({ command: "get_statistics", params: { period: 60 } });
  });
  controlSocket.addEventListener("message", event => {
    let payload;
    try { payload = JSON.parse(event.data); } catch (_) { return; }
    handleControlMessage(payload);
  });
  controlSocket.addEventListener("error", () => { state.controlConnected = false; updateConnectionUI(); });
  controlSocket.addEventListener("close", () => { state.controlConnected = false; updateConnectionUI(); controlReconnectTimer = setTimeout(connectControlSocket, 3000); });
}
function handleVideoMessage(payload) {
  switch (payload.type) {
  case "frame":
      if (!isImageSource() && typeof payload.frame === "string" && (state.streaming || state.backendRunning || state.busy)) {
        state.frameLoaded = false;
        processDetections(Array.isArray(payload.detections) ? payload.detections : []);
        elements.cameraImage.src = payload.frame.startsWith("data:") ? payload.frame : `data:image/jpeg;base64,${payload.frame}`;
        if ((state.busy || state.backendRunning) && !state.streaming) {
          clearTimeout(streamReadyTimer);
          setStreaming(true, "Live");
          setBusy(false);
          showToast("Stream is live", "success");
        }
      }
      break;
    case "metrics":
      state.fps = Number(payload.fps);
      state.latency = Number(payload.inference_latency_ms);
      elements.fpsValue.textContent = Number.isFinite(state.fps) ? state.fps.toFixed(1) : "-";
      elements.latencyValue.textContent = Number.isFinite(state.latency) ? `${state.latency.toFixed(1)} ms` : "- ms";
      const now = formatTime(new Date().toISOString());
      state.perfLabels.push(now);
      state.fpsHistory.push(Number.isFinite(state.fps) ? state.fps : 0);
      state.latencyHistory.push(Number.isFinite(state.latency) ? state.latency : 0);
      state.cpuHistory.push(Number.isFinite(payload.cpu_percent) ? payload.cpu_percent : 0);
      state.memHistory.push(Number.isFinite(payload.memory_percent) ? payload.memory_percent : 0);
      if (state.perfLabels.length > 60) {
        state.perfLabels.shift();
        state.fpsHistory.shift();
        state.latencyHistory.shift();
        state.cpuHistory.shift();
        state.memHistory.shift();
      }
      updatePerfCharts();
      break;
    case "status":
      handleStatus(payload.status, payload.message);
      break;
  }
}
function handleControlMessage(payload) {
  if (payload.type === "status") { handleStatus(payload.status, payload.message); return; }
  if (payload.type === "statistics" && payload.statistics) {
    applyStatistics(payload.statistics);
    loadRecentDetections();
    return;
  }
  if (payload.type === "error") {
    if (state.busy) {
      setBusy(false);
      setStreaming(false, payload.message || "Command failed");
    }
    showToast(payload.message || "Unknown control error", "error");
    return;
  }
  if (payload.type === "response") {
    if (payload.command === "set_camera_config") state.cameraReady = payload.success === true;
    if (payload.command === "load_model") {
      state.modelReady = payload.success === true;
      if (state.modelReady) elements.modelName.textContent = document.getElementById("modelSelect").value;
    }
    if (payload.command === "set_camera_config" || payload.command === "load_model") updateReadinessMessage();
    showToast(payload.message || (payload.success ? "Command completed" : "Command failed"), payload.success ? "success" : "error");
  }
}
function handleStatus(status, message) {
  const lower = String(status || "").toLowerCase();
  const running = ["running", "streaming", "active"].includes(lower);
  const idle = ["idle", "stopped", "ready"].includes(lower);
  const errorState = ["error", "failed"].includes(lower);
  const initializing = ["initializing", "loading"].includes(lower);
  const paused = ["paused"].includes(lower);
  if (running) {
    state.backendRunning = true;
    elements.cameraStatusLabel.textContent = message || "Starting inference…";
    elements.cameraState.textContent = state.streaming ? "Waiting for camera frame…" : "Waiting for first frame…";
  }
  if (idle) {
    state.backendRunning = false;
    setStreaming(false, message || "System ready");
  }
  elements.cameraStatusLabel.textContent = message || (running ? "Streaming active" : "System ready");
  elements.cameraState.textContent = message || (running ? "Waiting for camera frame…" : "Waiting for stream…");
  if (errorState) {
    state.backendRunning = false;
    if (String(message || "").toLowerCase().includes("camera")) state.cameraReady = false;
    if (String(message || "").toLowerCase().includes("model")) state.modelReady = false;
    showToast(message || "System error", "error");
    setBusy(false);
    setStreaming(false, message || "System error");
  }
  if (initializing) {
    elements.cameraStatusLabel.textContent = message || "Initializing";
    elements.cameraState.textContent = message || "Initializing…";
  }
  updateStartButton();
}
function processDetections(items) {
  state.latestDetections = items.map(normalizeDetection);
}

function visibleDetections() {
  const confidence = Number(elements.confidence.value) / 100;
  return state.latestDetections.filter(detection => detection.confidence >= confidence);
}

function renderCurrentDetections() {
  const detections = visibleDetections();
  const key = detections.map(item => `${item.className}:${Math.round(item.confidence * 100)}`).join(",");
  const emptyMessage = state.frameLoaded ? "No objects above the selected confidence." : isImageSource()
    ? "Choose an image and run detection."
    : "Start the camera to see its current frame.";
  if (elements.currentEmpty.textContent !== emptyMessage) elements.currentEmpty.textContent = emptyMessage;
  elements.currentEmpty.hidden = detections.length > 0;
  if (state.currentResultKey === key) return;
  state.currentResultKey = key;
  elements.currentCount.textContent = String(detections.length);
  elements.detectionCountValue.textContent = String(detections.length);
  elements.currentList.replaceChildren(...detections.map(detection => {
    const item = document.createElement("li");
    const label = document.createElement("span");
    const confidence = document.createElement("strong");
    label.textContent = CLASS_LABELS[detection.className];
    label.style.setProperty("--object-color", CLASS_COLORS[detection.className]);
    confidence.textContent = `${Math.round(detection.confidence * 100)}%`;
    item.append(label, confidence);
    return item;
  }));
  if (detections.length) {
    const average = detections.reduce((sum, item) => sum + item.confidence, 0) / detections.length;
    elements.liveConfidenceValue.textContent = `${Math.round(average * 100)} %`;
  } else {
    elements.liveConfidenceValue.textContent = "- %";
  }
}
function recordTrendPoint() {
  const time = formatTime(new Date().toISOString());
  const lastLabel = state.trendLabels[state.trendLabels.length - 1];
  if (lastLabel === time) {
    CLASSES.forEach(name => { state.trendValues[name][state.trendValues[name].length - 1] = state.classCounts[name]; });
    return;
  }
  state.trendLabels.push(time);
  CLASSES.forEach(name => { state.trendValues[name].push(state.classCounts[name]); });
  if (state.trendLabels.length > 36) {
    state.trendLabels.shift();
    CLASSES.forEach(name => state.trendValues[name].shift());
  }
}
function scheduleChartUpdate() {
  if (state.chartUpdatePending) return;
  const elapsed = performance.now() - state.lastChartUpdate;
  const delay = Math.max(0, 250 - elapsed);
  state.chartUpdatePending = true;
  setTimeout(() => { state.chartUpdatePending = false; state.lastChartUpdate = performance.now(); updateCharts(); }, delay);
}
function updateCharts() {
  const values = CLASSES.map(name => state.classCounts[name]);
  const total = values.reduce((sum, value) => sum + value, 0);
  distributionChart.data.datasets[0].data = values;
  distributionChart.update("none");
  trendChart.data.labels = [...state.trendLabels];
  trendChart.data.datasets.forEach((dataset, index) => { dataset.data = [...state.trendValues[CLASSES[index]]]; });
  trendChart.update("none");
  const sorted = CLASSES.map(name => ({ name, count: state.classCounts[name] })).sort((a, b) => b.count - a.count);
  breakdownChart.data.labels = sorted.map(item => CLASS_LABELS[item.name]);
  breakdownChart.data.datasets[0].data = sorted.map(item => item.count);
  breakdownChart.data.datasets[0].backgroundColor = sorted.map(item => CLASS_COLORS[item.name]);
  breakdownChart.update("none");
  elements.distributionTotal.textContent = `${total} ${total === 1 ? "Object" : "Objects"}`;
  elements.distributionEmpty.classList.toggle("visible", total === 0);
  elements.trendEmpty.classList.toggle("visible", state.trendLabels.length === 0);
  elements.breakdownEmpty.classList.toggle("visible", total === 0);
  renderLegend();
}
function renderLegend() {
  elements.classLegend.innerHTML = CLASSES.map(name => `
    <div class="legend-item">
      <span class="legend-swatch" style="background:${CLASS_COLORS[name]}"></span>
      <span class="legend-name">${CLASS_LABELS[name]}</span>
      <span class="legend-count">${state.classCounts[name]}</span>
    </div>
  `).join("");
}
function renderRecent() {
  const items = state.history.slice(0, 12);
  elements.recentCount.textContent = `${state.history.length} Entries`;
  if (!items.length) {
    elements.recentList.innerHTML = '<div class="empty-state">No detections yet.<br />Waiting for model data.</div>';
    return;
  }
  elements.recentList.innerHTML = items.map(detection => `
    <div class="recent-row">
      <span class="class-marker" style="background:${CLASS_COLORS[detection.className]}"></span>
      <span class="class-name">${CLASS_LABELS[detection.className]}</span>
      <span class="confidence">${Math.round(detection.confidence * 100)} %</span>
      <span class="timestamp">${formatTime(detection.timestamp)}</span>
    </div>
  `).join("");
}
function updatePerfCharts() {
  const labels = [...state.perfLabels];
  const hasData = labels.length > 0;
  elements.perfEmpty.classList.toggle("visible", !hasData);
  elements.sysEmpty.classList.toggle("visible", !hasData);
  perfChart.data.labels = labels;
  perfChart.data.datasets[0].data = [...state.fpsHistory];
  perfChart.data.datasets[1].data = [...state.latencyHistory];
  perfChart.update("none");
  sysChart.data.labels = labels;
  sysChart.data.datasets[0].data = [...state.cpuHistory];
  sysChart.data.datasets[1].data = [...state.memHistory];
  sysChart.update("none");
}
function renderSummary() {
  elements.summaryTotal.textContent = String(state.totalDetections);
  elements.summaryDuration.textContent = formatDuration(currentSessionMs());
  if (state.totalDetections > 0) {
    const topClass = Object.entries(state.classCounts).sort((a, b) => b[1] - a[1])[0];
    elements.summaryTopClass.textContent = topClass[1] > 0 ? CLASS_LABELS[topClass[0]] : "-";
    const avgConfidence = state.confidenceSamples > 0 ? Math.round((state.confidenceSum / state.confidenceSamples) * 100) : 0;
    elements.summaryConfidence.innerHTML = state.confidenceSamples > 0
      ? `${avgConfidence} <span class="summary-unit">%</span>`
      : `- <span class="summary-unit">%</span>`;
  } else {
    elements.summaryTopClass.textContent = "-";
    elements.summaryConfidence.innerHTML = `- <span class="summary-unit">%</span>`;
  }
}
function applyStatistics(statistics) {
  if (statistics.total_detections !== undefined) state.totalDetections = Number(statistics.total_detections) || 0;
  if (statistics.average_confidence !== undefined) {
    const average = Number(statistics.average_confidence);
    state.backendAverageConfidence = Number.isFinite(average) ? average : null;
    state.confidenceSamples = state.totalDetections;
    state.confidenceSum = state.backendAverageConfidence === null
      ? 0
      : state.backendAverageConfidence * state.confidenceSamples;
  }
  const counts = statistics.class_counts && typeof statistics.class_counts === "object"
    ? statistics.class_counts
    : {};
  CLASSES.forEach(name => { state.classCounts[name] = Number(counts[name]) || 0; });
  recordTrendPoint();
  renderSummary();
  scheduleChartUpdate();
}
async function loadRecentDetections() {
  try {
    const data = await fetchJSON("/api/detections/recent?limit=50", {}, true);
    if (!Array.isArray(data.detections)) return;
    state.history = data.detections.map(normalizeDetection).slice(0, 50);
    renderRecent();
  } catch (_) {
    // The statistics message is still useful when the optional history request fails.
  }
}
function drawBoundingBoxes(detections) {
  const canvas = elements.detectionCanvas;
  const stage = elements.cameraStage;
  const ctx = canvas.getContext("2d");
  canvas.width = stage.clientWidth;
  canvas.height = stage.clientHeight;
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  if (!detections.length || !state.frameLoaded) return;
  const img = elements.cameraImage;
  if (!img.naturalWidth || !img.naturalHeight) return;
  const scale = Math.min(canvas.width / img.naturalWidth, canvas.height / img.naturalHeight);
  const offsetX = (canvas.width - img.naturalWidth * scale) / 2;
  const offsetY = (canvas.height - img.naturalHeight * scale) / 2;
  detections.forEach(detection => {
    if (!detection.bbox || detection.bbox.length < 4) return;
    const [x1, y1, x2, y2] = detection.bbox;
    const sx = offsetX + x1 * scale;
    const sy = offsetY + y1 * scale;
    const sw = (x2 - x1) * scale;
    const sh = (y2 - y1) * scale;
    const color = CLASS_COLORS[detection.className] || "#ffffff";
    ctx.strokeStyle = color;
    ctx.lineWidth = 2;
    ctx.strokeRect(sx, sy, sw, sh);
    const label = `${CLASS_LABELS[detection.className]} ${Math.round(detection.confidence * 100)}%`;
    ctx.font = "600 10px 'IBM Plex Mono', monospace";
    const textWidth = ctx.measureText(label).width;
    const labelHeight = 18;
    const labelY = Math.max(0, sy - labelHeight);
    const textY = labelY + 13;
    ctx.fillStyle = "#18231e";
    ctx.fillRect(sx, labelY, textWidth + 10, labelHeight);
    ctx.fillStyle = "#ffffff";
    ctx.fillText(label, sx + 5, textY);
  });
}
function clearBoundingBoxes() {
  const canvas = elements.detectionCanvas;
  const ctx = canvas.getContext("2d");
  ctx.clearRect(0, 0, canvas.width, canvas.height);
}
function resetSessionStats() {
  state.history = [];
  state.classCounts = Object.fromEntries(CLASSES.map(name => [name, 0]));
  state.totalDetections = 0;
  state.confidenceSum = 0;
  state.confidenceSamples = 0;
  state.trendLabels = [];
  state.trendValues = Object.fromEntries(CLASSES.map(name => [name, []]));
  state.accumulatedSessionMs = 0;
  state.sessionStartedAt = null;
  state.perfLabels = [];
  state.fpsHistory = [];
  state.latencyHistory = [];
  state.cpuHistory = [];
  state.memHistory = [];
  state.backendAverageConfidence = null;
}
function startStream() {
  if (state.streaming || state.busy || isImageSource()) return;
  resetSessionStats();
  setBusy(true);
  clearTimeout(streamReadyTimer);
  streamReadyTimer = setTimeout(() => {
    if (state.busy && !state.streaming) {
      setBusy(false);
      handleStatus("error", "No camera frame received.");
      fetchJSON("/api/stream/stop", { method: "POST" }, true).catch(() => {});
    }
  }, 15000);
  fetchJSON("/api/stream/start", { method: "POST" })
    .then(data => { handleStatus(data.status || "running", data.message || "Stream starting…"); })
    .catch(() => {
      clearTimeout(streamReadyTimer);
      setBusy(false);
    });
}
function stopStream() {
  if (!state.streaming || state.busy) return;
  setBusy(true);
  clearTimeout(streamReadyTimer);
  fetchJSON("/api/stream/stop", { method: "POST" })
    .then(data => {
      if (!data.success) throw new Error(data.message || "The stream could not be stopped.");
      showToast(data.message || "Stream stopped", "success");
      handleStatus("stopped", "Stream stopped");
    })
    .catch(() => { handleStatus("error", "The stream could not be stopped."); })
    .finally(() => setBusy(false));
}
function switchPage(pageName) {
  elements.navButtons.forEach(button => {
    const active = button.dataset.page === pageName;
    button.classList.toggle("active", active);
    if (active) button.setAttribute("aria-current", "page");
    else button.removeAttribute("aria-current");
  });
  elements.pages.forEach(page => { page.classList.toggle("active", page.id === `${pageName}Page`); });
  document.querySelector(".workspace").scrollTop = 0;
  if (pageName === "dashboard") drawBoundingBoxes(visibleDetections());
}
// nav + stream buttons - keep simple, no delegate
elements.navButtons.forEach(function(button) { button.addEventListener("click", function() { switchPage(button.dataset.page); }); });
elements.startButton.addEventListener("click", startStream);
elements.stopButton.addEventListener("click", stopStream);

function clearPreview() {
  state.frameLoaded = false;
  state.latestDetections = [];
  elements.cameraImage.removeAttribute("src");
  elements.cameraImage.classList.remove("visible");
  elements.cameraPlaceholder.style.display = "flex";
  clearBoundingBoxes();
  renderCurrentDetections();
}

function updateSource() {
  const image = isImageSource();
  elements.sourceTitle.textContent = image ? "Image preview" : "Camera preview";
  elements.cameraImage.alt = image ? "Analyzed image" : "Live camera frame";
  elements.cameraStage.dataset.source = elements.source.value;
  elements.imageControls.hidden = !image;
  elements.startButton.hidden = image;
  elements.stopButton.hidden = image;
  document.querySelector(".preview-footer").hidden = image;
  elements.cameraPlaceholder.querySelector(".placeholder-title").textContent = image ? "No image analyzed" : "No active camera stream";
  elements.cameraPlaceholder.querySelector(".placeholder-text").textContent = image ? "Choose a JPEG or PNG to begin." : "Use Start Stream when the camera is ready.";
  elements.confidenceNote.textContent = image ? "Sets the threshold for the next image run." : "Filters the preview. Set camera inference thresholds in Settings.";
  elements.imageStatus.textContent = "";
  clearPreview();
  updateStartButton();
}

async function detectSelectedImage() {
  const file = elements.imageFile.files[0];
  if (!file || elements.detectImageButton.disabled) return;
  clearPreview();
  if (!["image/jpeg", "image/png"].includes(file.type) || file.size > 8 * 1024 * 1024) {
    elements.imageStatus.textContent = "Choose a JPEG or PNG up to 8 MB and 16 megapixels.";
    return;
  }
  if (typeof createImageBitmap === "function") {
    try {
      const bitmap = await createImageBitmap(file);
      const megapixels = bitmap.width * bitmap.height / 1_000_000;
      bitmap.close();
      if (megapixels > 16) {
        elements.imageStatus.textContent = "Choose an image no larger than 16 megapixels.";
        return;
      }
    } catch (_) {
      // The server decodes and validates the image as well; let it report the problem.
    }
  }
  state.imageBusy = true;
  elements.imageStatus.textContent = "Uploading image for detection…";
  updateStartButton();
  try {
    const result = await fetchJSON(`/api/detect/image?confidence=${Number(elements.confidence.value) / 100}`, {
      method: "POST",
      headers: { "Content-Type": file.type },
      body: file,
      timeoutMs: 60000,
    }, true);
    processDetections(result.detections);
    elements.cameraImage.src = result.image;
    const { length } = result.detections;
    elements.imageStatus.textContent = `${length} ${length === 1 ? "object" : "objects"} detected.`;
  } catch (error) {
    elements.imageStatus.textContent = error.message;
  } finally {
    state.imageBusy = false;
    updateStartButton();
  }
}

elements.source.addEventListener("change", updateSource);
elements.imageFile.addEventListener("change", () => {
  clearPreview();
  elements.imageStatus.textContent = "";
  updateStartButton();
});
elements.detectImageButton.addEventListener("click", detectSelectedImage);
elements.confidence.addEventListener("input", () => {
  elements.confidenceValue.value = `${elements.confidence.value}%`;
  if (isImageSource()) {
    if (state.frameLoaded || elements.cameraImage.hasAttribute("src")) {
      clearPreview();
      elements.imageStatus.textContent = "Run detection again to apply the new threshold.";
    }
    return;
  }
  renderCurrentDetections();
  drawBoundingBoxes(visibleDetections());
});
new ResizeObserver(() => drawBoundingBoxes(visibleDetections())).observe(elements.cameraStage);
let sessionTimer = null;
function startSessionTimer() {
  if (sessionTimer) return;
  sessionTimer = setInterval(() => { if (state.streaming) { elements.summaryDuration.textContent = formatDuration(currentSessionMs()); } }, 1000);
}
elements.cameraImage.addEventListener("load", () => {
  state.frameLoaded = true;
  elements.cameraImage.classList.add("visible");
  elements.cameraPlaceholder.style.display = "none";
  renderCurrentDetections();
  drawBoundingBoxes(visibleDetections());
});
const sliders = [
  { slider: document.getElementById("modelConf"), label: document.getElementById("modelConfVal") },
  { slider: document.getElementById("modelReject"), label: document.getElementById("modelRejectVal") },
  { slider: document.getElementById("modelIou"), label: document.getElementById("modelIouVal") }
];
sliders.forEach(({ slider, label }) => {
  if (slider && label) {
    const update = () => { label.textContent = Number(slider.value).toFixed(2); };
    slider.addEventListener("input", update);
    update();
  }
});

const cameraResetDefaults = { index: 0, fps: 30, res: "640x360", autofocus: false, autoExposure: true };
const modelResetDefaults  = { conf: 0.5, reject: 0.55, iou: 0.45, tracking: true, latency: 50 };

document.getElementById("cameraSettingsForm")?.addEventListener("reset", () => {
  setTimeout(() => {
    document.getElementById("cameraIndex").value = cameraResetDefaults.index;
    document.getElementById("cameraFps").value = cameraResetDefaults.fps;
    const radio = document.querySelector(`input[name="cameraRes"][value="${cameraResetDefaults.res}"]`);
    if (radio) radio.checked = true;
    document.getElementById("cameraAutofocus").checked = cameraResetDefaults.autofocus;
    document.getElementById("cameraAutoExposure").checked = cameraResetDefaults.autoExposure;
  }, 0);
});

document.getElementById("modelSettingsForm")?.addEventListener("reset", () => {
  setTimeout(() => {
    const mc = document.getElementById("modelConf");
    const mr = document.getElementById("modelReject");
    const mi = document.getElementById("modelIou");
    if (mc) { mc.value = modelResetDefaults.conf; document.getElementById("modelConfVal").textContent = modelResetDefaults.conf.toFixed(2); }
    if (mr) { mr.value = modelResetDefaults.reject; document.getElementById("modelRejectVal").textContent = modelResetDefaults.reject.toFixed(2); }
    if (mi) { mi.value = modelResetDefaults.iou; document.getElementById("modelIouVal").textContent = modelResetDefaults.iou.toFixed(2); }
    const tracking = document.getElementById("modelTracking");
    if (tracking) tracking.checked = modelResetDefaults.tracking;
    const latency = document.getElementById("modelLatency");
    if (latency) latency.value = modelResetDefaults.latency;
  }, 0);
});


function loadModelOptions() {
  const select = document.getElementById("modelSelect");
  if (!select) return Promise.resolve();
  return fetchJSON("/api/models", {}, true)
    .then(data => {
      if (data.models && Array.isArray(data.models) && data.models.length > 0) {
        select.replaceChildren(...data.models.map(model => {
          const option = document.createElement("option");
          option.value = String(model.name);
          option.textContent = String(model.label) + " (" + String(model.size_mb) + " MB) "
            + (model.recommended ? "\u2605 Recommended" : "");
          option.selected = model.recommended === true;
          return option;
        }));
      }
    })
    .catch(() => {});
}

function readCameraConfig() {
  const resVal = document.querySelector('input[name="cameraRes"]:checked')?.value || "640x360";
  const resolution = resVal.split("x");
  return {
    index: parseInt(document.getElementById("cameraIndex").value, 10),
    width: parseInt(resolution[0], 10),
    height: parseInt(resolution[1], 10),
    fps: parseInt(document.getElementById("cameraFps").value, 10),
    autofocus: document.getElementById("cameraAutofocus").checked,
    auto_exposure: document.getElementById("cameraAutoExposure").checked
  };
}

function readModelConfig(name) {
  return {
    name,
    conf_threshold: parseFloat(document.getElementById("modelConf").value),
    reject_threshold: parseFloat(document.getElementById("modelReject").value),
    iou_threshold: parseFloat(document.getElementById("modelIou").value),
    enable_tracking: document.getElementById("modelTracking").checked,
    target_latency_ms: parseInt(document.getElementById("modelLatency").value, 10)
  };
}

async function prepareDefaults() {
  const cameraConfig = readCameraConfig();

  try {
    await fetchJSON("/api/camera/initialize", { method: "POST", body: JSON.stringify(cameraConfig) }, true);
    state.cameraReady = true;
  } catch (_) {
    showToast("Camera is not available. Check Settings and the camera index.", "warning");
  }

  const modelName = document.getElementById("modelSelect").value;
  if (modelName) {
    const modelConfig = readModelConfig(modelName);
    try {
      await fetchJSON("/api/model/load", { method: "POST", body: JSON.stringify(modelConfig) }, true);
      state.modelReady = true;
      elements.modelName.textContent = modelName;
    } catch (_) {
      showToast("The default model could not be loaded. Check Settings.", "warning");
    }
  }

  updateReadinessMessage();
}

const cameraForm = document.getElementById("cameraSettingsForm");
if (cameraForm) {
  cameraForm.addEventListener("submit", (e) => {
    e.preventDefault();
    if (state.streaming || state.busy || state.imageBusy) {
      showToast("Stop the stream before changing camera settings.", "warning");
      return;
    }
    const config = readCameraConfig();
    const sent = sendControl({ command: "set_camera_config", params: config });
    if (!sent) {
      fetchJSON("/api/camera/initialize", { method: "POST", body: JSON.stringify(config) })
        .then(data => {
          state.cameraReady = true;
          updateReadinessMessage();
          showToast(data.message || "Camera configured", "success");
        })
        .catch(() => {});
    }
  });
}

const modelForm = document.getElementById("modelSettingsForm");
if (modelForm) {
  modelForm.addEventListener("submit", (e) => {
    e.preventDefault();
    if (state.streaming || state.busy || state.imageBusy) {
      showToast("Stop the stream before changing models.", "warning");
      return;
    }
    const config = readModelConfig(document.getElementById("modelSelect").value);
    const sent = sendControl({ command: "load_model", params: config });
    if (!sent) {
      fetchJSON("/api/model/load", { method: "POST", body: JSON.stringify(config) })
        .then(data => {
          state.modelReady = true;
          elements.modelName.textContent = config.name;
          updateReadinessMessage();
          showToast(data.message || "Model loaded", "success");
        })
        .catch(() => {});
    }
  });
}

updateSource();
renderRecent();
renderSummary();
startSessionTimer();
connectVideoSocket();
connectControlSocket();
loadModelOptions().finally(prepareDefaults);
updateReadinessMessage();
