"""MIRA Control Center — Flask + SocketIO real-time dashboard."""
import base64
import json
import os
import sys
import time
import threading
from pathlib import Path

import cv2
from flask import Flask, render_template
from flask_socketio import SocketIO
from ultralytics import YOLO

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from config import (
    DETECTION_DIR,
    DETECTION_MODEL_LABELS as MODEL_LABELS,
    BYTE_TRACK_CONFIG_PATH,
    setup_camera_properties,
)
from visualize import draw_boxes

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("FLASK_SECRET_KEY", os.urandom(24).hex())
socketio = SocketIO(app, cors_allowed_origins="*", async_mode="threading")

# ---------------------------------------------------------------------------
# Global state
# ---------------------------------------------------------------------------
camera_thread: threading.Thread | None = None
camera_running = False
camera_lock = threading.Lock()

current_model: YOLO | None = None
model_name: str = ""
model_lock = threading.Lock()

inventory: dict[str, int] = {c: 0 for c in ["glass", "metal", "paper", "plastic", "trash"]}
seen_ids: set[int] = set()
inventory_lock = threading.Lock()

# Live config (updated by frontend via SocketIO)
live_config = {
    "conf": 0.5,
    "iou": 0.45,
    "imgsz": 320,
    "tracking": True,
    "camera_index": 0,
}


def get_available_models() -> list[dict]:
    """Return list of detection models with labels."""
    models = []
    for p in sorted(DETECTION_DIR.iterdir()):
        if p.suffix in (".pt", ".tflite") and "classifier" not in p.name.lower():
            label = MODEL_LABELS.get(p.name, p.name)
            models.append({"file": p.name, "label": label})
    return models


def load_model(name: str) -> YOLO:
    """Load a YOLO model from the detection directory."""
    path = DETECTION_DIR / name
    task_type = "detect" if path.suffix == ".tflite" else None
    return YOLO(str(path), task=task_type)


# ---------------------------------------------------------------------------
# Camera + inference thread
# ---------------------------------------------------------------------------
def _camera_loop():
    """Main loop: capture frame, run inference, emit via SocketIO."""
    global camera_running

    idx = live_config["camera_index"]
    cap = cv2.VideoCapture(idx, cv2.CAP_DSHOW)
    if not cap.isOpened():
        socketio.emit("error", {"message": f"Kamera {idx} konnte nicht geoeffnet werden."})
        camera_running = False
        socketio.emit("camera_stopped", {})
        return

    setup_camera_properties(cap, 640, 360)
    for _ in range(10):
        cap.read()
    consecutive_errors = 0

    fps_counter: list[float] = []
    seen_local: set[int] = set()
    counts_local = {c: 0 for c in inventory}

    try:
        while camera_running:
            ret, frame = cap.read()
            if not ret:
                continue

            t0 = time.perf_counter()

            with model_lock:
                model = current_model
                is_tflite = (
                    model is not None
                    and model_name.endswith(".tflite")
                    and "int8" in model_name.lower()
                )

            if model is None:
                time.sleep(0.05)
                continue

            conf = live_config["conf"]
            if is_tflite:
                conf = min(conf, 0.25)

            try:
                if is_tflite:
                    results = model.predict(
                        frame, imgsz=live_config["imgsz"],
                        conf=conf, iou=live_config["iou"], verbose=False,
                    )
                elif live_config["tracking"]:
                    results = model.track(
                        frame, persist=True, imgsz=live_config["imgsz"],
                        conf=conf, iou=live_config["iou"], verbose=False,
                        tracker=str(BYTE_TRACK_CONFIG_PATH),
                    )
                else:
                    results = model.predict(
                        frame, imgsz=live_config["imgsz"],
                        conf=conf, iou=live_config["iou"], verbose=False,
                    )
            except Exception as e:
                consecutive_errors += 1
                if consecutive_errors >= 30:
                    print(f"[MIRA] 30 consecutive inference errors: {e}")
                    socketio.emit("error", {"message": f"Inference-Fehler: {e}"})
                    consecutive_errors = 0
                continue

            consecutive_errors = 0

            t1 = time.perf_counter()
            latency_ms = (t1 - t0) * 1000
            fps_counter.append(t1 - t0)
            if len(fps_counter) > 30:
                fps_counter.pop(0)
            avg_fps = 1.0 / (sum(fps_counter) / len(fps_counter)) if fps_counter else 0

            # Tracking counts
            if results[0].boxes is not None and results[0].boxes.id is not None:
                track_ids = results[0].boxes.id.cpu().numpy().astype(int)
                class_ids = results[0].boxes.cls.cpu().numpy().astype(int)
                for tid, cid in zip(track_ids, class_ids):
                    if tid not in seen_local:
                        seen_local.add(tid)
                        cname = results[0].names[cid]
                        if cname in counts_local:
                            counts_local[cname] += 1

            # Emit counts
            with inventory_lock:
                inventory.update(counts_local)

            annotated = draw_boxes(frame, results, conf)
            _, jpeg = cv2.imencode(".jpg", annotated, [cv2.IMWRITE_JPEG_QUALITY, 80])
            frame_b64 = base64.b64encode(jpeg).decode("utf-8")

            socketio.emit("frame", {"image": frame_b64})
            socketio.emit("metrics", {
                "fps": round(avg_fps, 1),
                "latency": round(latency_ms, 1),
                "objects": len(results[0].boxes) if results[0].boxes is not None else 0,
            })
            socketio.emit("inventory", dict(counts_local))

            # Target ~20 FPS
            elapsed = time.perf_counter() - t0
            sleep_time = max(0, 0.05 - elapsed)
            if sleep_time > 0:
                time.sleep(sleep_time)
    finally:
        cap.release()
        camera_running = False
        socketio.emit("camera_stopped", {})


# ---------------------------------------------------------------------------
# SocketIO events
# ---------------------------------------------------------------------------
@socketio.on("connect")
def handle_connect():
    socketio.emit("init", {
        "models": get_available_models(),
        "config": live_config,
        "inventory": dict(inventory),
    })


@socketio.on("start_camera")
def handle_start_camera(data=None):
    global camera_running, camera_thread
    with model_lock:
        if current_model is None:
            socketio.emit("error", {"message": "Kein Modell geladen. Bitte Modell auswaehlen."})
            return

    if data:
        live_config.update({
            "conf": data.get("conf", live_config["conf"]),
            "iou": data.get("iou", live_config["iou"]),
            "imgsz": data.get("imgsz", live_config["imgsz"]),
            "tracking": data.get("tracking", live_config["tracking"]),
            "camera_index": data.get("camera_index", live_config["camera_index"]),
        })

    with camera_lock:
        if camera_running:
            return
        camera_running = True
        camera_thread = threading.Thread(target=_camera_loop, daemon=True)
        camera_thread.start()


@socketio.on("stop_camera")
def handle_stop_camera():
    global camera_running, camera_thread
    camera_running = False
    if camera_thread and camera_thread.is_alive():
        camera_thread.join(timeout=3)


@socketio.on("load_model")
def handle_load_model(data):
    global current_model, model_name
    new_name = data.get("model", "")
    if not new_name:
        return
    try:
        m = load_model(new_name)
        with model_lock:
            current_model = m
            model_name = new_name
        socketio.emit("model_loaded", {"model": new_name})
    except Exception as e:
        socketio.emit("error", {"message": f"Modell-Fehler: {e}"})


@socketio.on("update_config")
def handle_update_config(data):
    for key in ("conf", "iou", "imgsz", "tracking", "camera_index"):
        if key in data:
            live_config[key] = data[key]


@socketio.on("reset_inventory")
def handle_reset_inventory():
    with inventory_lock:
        for k in inventory:
            inventory[k] = 0
    socketio.emit("inventory", dict(inventory))


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------
@app.route("/")
def index():
    return render_template("index.html")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
def run_dashboard(host="0.0.0.0", port=5000, debug=False):
    print(f"\n  MIRA Control Center")
    print(f"  http://localhost:{port}\n")
    socketio.run(app, host=host, port=port, debug=debug, allow_unsafe_werkzeug=True)


if __name__ == "__main__":
    run_dashboard(debug=True)
