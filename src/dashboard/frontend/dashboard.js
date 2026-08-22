    (() => {
      "use strict";
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
        streaming: false,
        backendRunning: false,
        busy: false,
        cameraReady: false,
        modelReady: false,
        videoConnected: false,
        controlConnected: false,
        latestDetections: [],
        history: [],
        classCounts: Object.fromEntries(CLASSES.map(name => [name, 0])),
        totalDetections: 0,
        confidenceSum: 0,
        confidenceSamples: 0,
        backendAverageConfidence: null,
        fps: null,
        latency: null,
        sessionStartedAt: null,
        accumulatedSessionMs: 0,
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
        toastRegion: document.getElementById("toastRegion")
      };

      function updateStartButton() {
        const ready = state.cameraReady && state.modelReady;
        elements.startButton.disabled = state.busy || state.streaming || !ready;
        if (state.busy && !state.streaming) elements.startButton.textContent = "Starting…";
        else if (!ready) elements.startButton.textContent = "Preparing…";
        else elements.startButton.textContent = "Start Stream";
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
      Chart.defaults.font.family = '"IBM Plex Mono", monospace';
      Chart.defaults.font.size = 9;
      Chart.defaults.color = "#667069";
      Chart.defaults.animation.duration = 0;
      Chart.defaults.borderColor = "#d7d7d0";
      const distributionChart = new Chart(document.getElementById("distributionChart"), {
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
      const trendChart = new Chart(document.getElementById("trendChart"), {
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
      const breakdownChart = new Chart(document.getElementById("breakdownChart"), {
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
      const perfChart = new Chart(document.getElementById("perfChart"), {
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
      const sysChart = new Chart(document.getElementById("sysChart"), {
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
      function normalizeClass(value) {
        const name = String(value || "trash").toLowerCase();
        return CLASSES.includes(name) ? name : "trash";
      }
      function normalizeConfidence(value) {
        const number = Number(value);
        if (!Number.isFinite(number)) return 0;
        return Math.max(0, Math.min(1, number));
      }
      function normalizeDetection(item) {
        return {
          className: normalizeClass(item.class_name ?? item.class),
          confidence: normalizeConfidence(item.confidence),
          trackId: item.track_id ?? "—",
          timestamp: item.timestamp || new Date().toISOString(),
          bbox: Array.isArray(item.bbox) ? item.bbox : null
        };
      }
      function formatTime(timestamp, withDate = false) {
        const date = new Date(timestamp);
        if (Number.isNaN(date.getTime())) return "—";
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
        const controller = new AbortController();
        const timeout = window.setTimeout(() => controller.abort(), 15000);
        try {
          const response = await fetch(url, {
            ...options,
            headers: { "Content-Type": "application/json", ...(options.headers || {}) },
            signal: options.signal || controller.signal,
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
          state.frameLoaded = false;
          state.latestDetections = [];
          elements.cameraImage.classList.remove("visible");
          elements.cameraPlaceholder.style.display = "flex";
          elements.detectionCountValue.textContent = "0";
          elements.liveConfidenceValue.textContent = "— %";
          elements.fpsValue.textContent = "—";
          elements.latencyValue.textContent = "— ms";
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
            if (typeof payload.frame === "string") {
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
            elements.fpsValue.textContent = Number.isFinite(state.fps) ? state.fps.toFixed(1) : "—";
            elements.latencyValue.textContent = Number.isFinite(state.latency) ? `${state.latency.toFixed(1)} ms` : "— ms";
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
        if (payload.type === "statistics" && payload.statistics) { applyStatistics(payload.statistics); return; }
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
          if (payload.command === "load_model") state.modelReady = payload.success === true;
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
      }
      function processDetections(items) {
        const detections = items.map(normalizeDetection);
        state.latestDetections = detections;
        elements.detectionCountValue.textContent = String(detections.length);
        if (detections.length) {
          const average = detections.reduce((sum, item) => sum + item.confidence, 0) / detections.length;
          elements.liveConfidenceValue.textContent = `${Math.round(average * 100)} %`;
        } else {
          elements.liveConfidenceValue.textContent = "— %";
        }
        if (!detections.length) { drawBoundingBoxes([]); return; }
        detections.forEach(detection => {
          state.history.unshift(detection);
          state.history = state.history.slice(0, 50);
          state.classCounts[detection.className] += 1;
          state.totalDetections += 1;
          state.confidenceSum += detection.confidence;
          state.confidenceSamples += 1;
        });
        recordTrendPoint();
        renderRecent();
        renderSummary();
        scheduleChartUpdate();
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
          elements.summaryTopClass.textContent = topClass[1] > 0 ? CLASS_LABELS[topClass[0]] : "—";
          const avgConfidence = state.confidenceSamples > 0 ? Math.round((state.confidenceSum / state.confidenceSamples) * 100) : 0;
          elements.summaryConfidence.innerHTML = state.confidenceSamples > 0
            ? `${avgConfidence} <span class="summary-unit">%</span>`
            : `— <span class="summary-unit">%</span>`;
        } else {
          elements.summaryTopClass.textContent = "—";
          elements.summaryConfidence.innerHTML = `— <span class="summary-unit">%</span>`;
        }
      }
      function applyStatistics(statistics) {
        if (statistics.total_detections !== undefined) state.totalDetections = Number(statistics.total_detections) || 0;
        if (statistics.average_confidence !== undefined) state.backendAverageConfidence = Number(statistics.average_confidence) || null;
        if (statistics.class_counts && typeof statistics.class_counts === "object") {
          CLASSES.forEach(name => { if (statistics.class_counts[name] !== undefined) state.classCounts[name] = Number(statistics.class_counts[name]) || 0; });
        }
        renderSummary();
        scheduleChartUpdate();
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
        const imgRect = img.getBoundingClientRect();
        const stageRect = stage.getBoundingClientRect();
        const offsetX = imgRect.left - stageRect.left;
        const offsetY = imgRect.top - stageRect.top;
        const scaleX = imgRect.width / (img.naturalWidth || imgRect.width);
        const scaleY = imgRect.height / (img.naturalHeight || imgRect.height);
        detections.forEach(detection => {
          if (!detection.bbox || detection.bbox.length < 4) return;
          const [x1, y1, x2, y2] = detection.bbox;
          const sx = offsetX + x1 * scaleX;
          const sy = offsetY + y1 * scaleY;
          const sw = (x2 - x1) * scaleX;
          const sh = (y2 - y1) * scaleY;
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
          ctx.fillStyle = color;
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
      }
      function startStream() {
        if (state.streaming || state.busy) return;
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
        elements.navButtons.forEach(button => { button.classList.toggle("active", button.dataset.page === pageName); });
        elements.pages.forEach(page => { page.classList.toggle("active", page.id === `${pageName}Page`); });
      }
      elements.navButtons.forEach(button => { button.addEventListener("click", () => switchPage(button.dataset.page)); });
      elements.startButton.addEventListener("click", startStream);
      elements.stopButton.addEventListener("click", stopStream);
      let sessionTimer = null;
      function startSessionTimer() {
        if (sessionTimer) return;
        sessionTimer = setInterval(() => { if (state.streaming) { elements.summaryDuration.textContent = formatDuration(currentSessionMs()); } }, 1000);
      }
      elements.cameraImage.addEventListener("load", () => {
        state.frameLoaded = true;
        elements.cameraImage.classList.add("visible");
        elements.cameraPlaceholder.style.display = "none";
        drawBoundingBoxes(state.latestDetections);
      });
      // Settings — sliders
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

      // Settings — reset buttons restore defaults
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
              select.innerHTML = data.models.map(model => `
                <option value="${model.name}" ${model.recommended ? 'selected' : ''}>
                  ${model.label} (${model.size_mb} MB) ${model.recommended ? '\u2605 Recommended' : ''}
                </option>
              `).join("");
            }
          })
          .catch(() => {});
      }

      async function prepareDefaults() {
        const resVal = document.querySelector('input[name="cameraRes"]:checked')?.value || "640x360";
        const resolution = resVal.split("x");
        const cameraConfig = {
          index: parseInt(document.getElementById("cameraIndex").value, 10),
          width: parseInt(resolution[0], 10),
          height: parseInt(resolution[1], 10),
          fps: parseInt(document.getElementById("cameraFps").value, 10),
          autofocus: document.getElementById("cameraAutofocus").checked,
          auto_exposure: document.getElementById("cameraAutoExposure").checked
        };

        try {
          await fetchJSON("/api/camera/initialize", { method: "POST", body: JSON.stringify(cameraConfig) }, true);
          state.cameraReady = true;
        } catch (_) {
          showToast("Camera is not available. Check Settings and the camera index.", "warning");
        }

        const modelName = document.getElementById("modelSelect").value;
        if (modelName) {
          const modelConfig = {
            name: modelName,
            conf_threshold: parseFloat(document.getElementById("modelConf").value),
            reject_threshold: parseFloat(document.getElementById("modelReject").value),
            iou_threshold: parseFloat(document.getElementById("modelIou").value),
            enable_tracking: document.getElementById("modelTracking").checked,
            target_latency_ms: parseInt(document.getElementById("modelLatency").value, 10)
          };
          try {
            await fetchJSON("/api/model/load", { method: "POST", body: JSON.stringify(modelConfig) }, true);
            state.modelReady = true;
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
          if (state.streaming || state.busy) {
            showToast("Stop the stream before changing camera settings.", "warning");
            return;
          }
          const resVal = document.querySelector('input[name="cameraRes"]:checked')?.value || "640x360";
          const resolution = resVal.split("x");
          const config = {
            index: parseInt(document.getElementById("cameraIndex").value, 10),
            width: parseInt(resolution[0], 10),
            height: parseInt(resolution[1], 10),
            fps: parseInt(document.getElementById("cameraFps").value, 10),
            autofocus: document.getElementById("cameraAutofocus").checked,
            auto_exposure: document.getElementById("cameraAutoExposure").checked
          };
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
          if (state.streaming || state.busy) {
            showToast("Stop the stream before changing models.", "warning");
            return;
          }
          const config = {
            name: document.getElementById("modelSelect").value,
            conf_threshold: parseFloat(document.getElementById("modelConf").value),
            reject_threshold: parseFloat(document.getElementById("modelReject").value),
            iou_threshold: parseFloat(document.getElementById("modelIou").value),
            enable_tracking: document.getElementById("modelTracking").checked,
            target_latency_ms: parseInt(document.getElementById("modelLatency").value, 10)
          };
          const sent = sendControl({ command: "load_model", params: config });
          if (!sent) {
            fetchJSON("/api/model/load", { method: "POST", body: JSON.stringify(config) })
              .then(data => {
                state.modelReady = true;
                updateReadinessMessage();
                showToast(data.message || "Model loaded", "success");
              })
              .catch(() => {});
          }
        });
      }

      renderRecent();
      renderSummary();
      startSessionTimer();
      connectVideoSocket();
      connectControlSocket();
      loadModelOptions().finally(prepareDefaults);
      updateReadinessMessage();
    })();

