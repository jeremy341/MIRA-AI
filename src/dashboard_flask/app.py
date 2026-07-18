"""MIRA Control Center — Flask + SocketIO real-time dashboard."""

import base64
import os
import sys
import threading
import time
from pathlib import Path

import cv2
from flask import Flask, render_template
from flask_socketio import SocketIO
from ultralytics import YOLO

_src_dir = str(Path(__file__).resolve().parent.parent)
if _src_dir not in sys.path:
    sys.path.insert(0, _src_dir)
from config import (
    CLASS_NAMES as CLASSES,
    DETECTION_DIR,
    DETECTION_MODEL_LABELS as MODEL_LABELS,
    REJECT_THRESHOLD,
    setup_camera_properties,
)
from visualize import draw_boxes

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("FLASK_SECRET_KEY", os.urandom(24).hex())
socketio = SocketIO(
    app, cors_allowed_origins="*", async_mode="threading"
)

# ---------------------------------------------------------------------------
# Global state
# ---------------------------------------------------------------------------
camera_thread: threading.Thread | None = None
camera_running = False
camera_lock = threading.Lock()

current_model: YOLO | None = None
model_name: str = ""
model_lock = threading.Lock()

inventory: dict[str, int] = {c: 0 for c in CLASSES}
inventory_lock = threading.Lock()
config_lock = threading.Lock()
state_reset_event = threading.Event()

DETECTION_DUP_WINDOW = 2.0
IOU_OVERLAP_THRESHOLD = 0.3

# Live config (updated by frontend via SocketIO)
live_config = {
    "conf": 0.25,
    "reject": REJECT_THRESHOLD,
    "iou": 0.45,
    "imgsz": 640,
    "tracking": True,
    "camera_index": 0,
    "camera_width": 640,
    "camera_height": 360,
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


def _iou(a, b):
    """Compute IoU between two boxes [x1, y1, x2, y2]."""
    ix1 = max(a[0], b[0])
    iy1 = max(a[1], b[1])
    ix2 = min(a[2], b[2])
    iy2 = min(a[3], b[3])
    inter = max(0.0, ix2 - ix1) * max(0.0, iy2 - iy1)
    area_a = (a[2] - a[0]) * (a[3] - a[1])
    area_b = (b[2] - b[0]) * (b[3] - b[1])
    denom = area_a + area_b - inter
    return inter / denom if denom > 0 else 0.0


# ---------------------------------------------------------------------------
# Camera + inference thread
# ---------------------------------------------------------------------------
def _camera_loop():
    """Main loop: capture frame, run inference, emit via SocketIO."""
    global camera_running

    idx = live_config["camera_index"]
    cap = cv2.VideoCapture(idx, cv2.CAP_DSHOW if sys.platform == "win32" else 0)
    if not cap.isOpened():
        socketio.emit("error", {"message": f"Kamera {idx} konnte nicht geoeffnet werden."})
        camera_running = False
        socketio.emit("camera_stopped", {})
        return

    cam_w = live_config.get("camera_width", 640)
    cam_h = live_config.get("camera_height", 360)
    setup_camera_properties(cap, cam_w, cam_h)
    for _ in range(10):
        cap.read()
    consecutive_errors = 0

    with inventory_lock:
        for k in inventory:
            inventory[k] = 0

    fps_counter: list[float] = []
    seen_local: set[int] = set()
    seen_boxes: dict[str, list[tuple[list[float], float]]] = {c: [] for c in CLASSES}
    counts_local = {c: 0 for c in CLASSES}
    sum_conf_local = {c: 0.0 for c in CLASSES}
    count_conf_local = {c: 0 for c in CLASSES}
    session_start = time.perf_counter()
    last_emitted_inventory = {c: 0 for c in CLASSES}
    _emitted_started = False

    try:
        while camera_running:
            if state_reset_event.is_set():
                state_reset_event.clear()
                seen_local = set()
                seen_boxes = {c: [] for c in CLASSES}
                counts_local = {c: 0 for c in CLASSES}
                sum_conf_local = {c: 0.0 for c in CLASSES}
                count_conf_local = {c: 0 for c in CLASSES}
                last_emitted_inventory = {c: 0 for c in CLASSES}

            ret, frame = cap.read()
            if not ret:
                continue

            t0 = time.perf_counter()

            with model_lock:
                model = current_model
                is_tflite = model is not None and model_name.endswith(".tflite") and "int8" in model_name.lower()

            if model is None:
                time.sleep(0.05)
                continue

            with config_lock:
                cfg_conf = live_config["conf"]
                cfg_reject = live_config["reject"]
                cfg_iou = live_config["iou"]
                cfg_imgsz = live_config["imgsz"]
                cfg_tracking = live_config["tracking"]

            conf = cfg_conf
            if is_tflite:
                conf = min(conf, 0.25)

            try:
                if is_tflite:
                    results = model.predict(
                        frame,
                        imgsz=cfg_imgsz,
                        conf=conf,
                        iou=cfg_iou,
                        verbose=False,
                        half=False,
                    )
                elif cfg_tracking:
                    results = model.track(
                        frame,
                        # Note: persist=True maintains tracker state across frames.
                        # Tracker resets when model is reloaded via handle_load_model.
                        persist=True,
                        imgsz=cfg_imgsz,
                        conf=conf,
                        iou=cfg_iou,
                        verbose=False,
                    )
                else:
                    results = model.predict(
                        frame,
                        imgsz=cfg_imgsz,
                        conf=conf,
                        iou=cfg_iou,
                        verbose=False,
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

            # Tracking counts — use track IDs if available, else IoU-based dedup
            boxes = getattr(results[0], "boxes", None)
            if boxes is not None and len(boxes) > 0:
                try:
                    class_ids = boxes.cls.cpu().numpy().astype(int)
                    confs = boxes.conf.cpu().numpy()
                    boxes_xyxy = boxes.xyxy.cpu().numpy()
                except (AttributeError, TypeError):
                    class_ids = []
                    confs = []
                    boxes_xyxy = []

                box_ids = getattr(boxes, "id", None)
                if box_ids is not None:
                    track_ids = box_ids.cpu().numpy().astype(int)
                    now = time.time()
                    for tid, cid, cconf, box in zip(track_ids, class_ids, confs, boxes_xyxy, strict=False):
                        cname = results[0].names[cid]
                        if cname not in counts_local:
                            continue
                        if cconf >= cfg_reject:
                            sum_conf_local[cname] += float(cconf)
                            count_conf_local[cname] += 1
                        if tid not in seen_local and cconf >= cfg_reject:
                            box_list = box.tolist()
                            seen_boxes[cname] = [(b, t) for b, t in seen_boxes[cname] if now - t < DETECTION_DUP_WINDOW]
                            is_dup = any(_iou(box_list, b) > IOU_OVERLAP_THRESHOLD for b, _ in seen_boxes[cname])
                            if not is_dup:
                                seen_local.add(tid)
                                seen_boxes[cname].append((box_list, now))
                                counts_local[cname] += 1
                                socketio.emit(
                                    "detection",
                                    {
                                        "material": cname,
                                        "confidence": round(float(cconf), 3),
                                        "timestamp": now,
                                        "count": counts_local[cname],
                                    },
                                )
                else:
                    now = time.time()
                    for cid, cconf, box in zip(class_ids, confs, boxes_xyxy, strict=False):
                        cname = results[0].names[cid]
                        if cname not in counts_local:
                            continue
                        if cconf >= cfg_reject:
                            sum_conf_local[cname] += float(cconf)
                            count_conf_local[cname] += 1
                            seen_boxes[cname] = [(b, t) for b, t in seen_boxes[cname] if now - t < DETECTION_DUP_WINDOW]
                            box_list = box.tolist()
                            is_dup = any(_iou(box_list, b) > IOU_OVERLAP_THRESHOLD for b, _ in seen_boxes[cname])
                            if not is_dup:
                                seen_boxes[cname].append((box_list, now))
                                counts_local[cname] += 1
                                socketio.emit(
                                    "detection",
                                    {
                                        "material": cname,
                                        "confidence": round(float(cconf), 3),
                                        "timestamp": now,
                                        "count": counts_local[cname],
                                    },
                                )

            # Emit counts
            avg_conf_local = {}
            for c in CLASSES:
                avg_conf_local[c] = (
                    round(sum_conf_local[c] / count_conf_local[c], 3) if count_conf_local[c] > 0 else 0.0
                )

            inventory_payload = dict(counts_local)
            inventory_payload["avg_conf"] = avg_conf_local
            inventory_payload["uptime"] = round(time.perf_counter() - session_start)

            with inventory_lock:
                inventory.update({k: counts_local[k] for k in CLASSES})

            annotated = draw_boxes(frame, results, conf, cfg_reject, CLASSES)
            _, jpeg = cv2.imencode(".jpg", annotated, [cv2.IMWRITE_JPEG_QUALITY, 80])
            frame_b64 = base64.b64encode(jpeg).decode("utf-8")

            socketio.emit("frame", {"image": frame_b64})
            socketio.emit(
                "metrics",
                {
                    "fps": round(avg_fps, 1),
                    "latency": round(latency_ms, 1),
                    "objects": len(boxes) if boxes is not None else 0,
                },
            )
            if not _emitted_started:
                _emitted_started = True
                socketio.emit("camera_started", {})
            if counts_local != last_emitted_inventory:
                socketio.emit("inventory", inventory_payload)
                last_emitted_inventory = dict(counts_local)

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
    socketio.emit(
        "init",
        {
            "models": get_available_models(),
            "config": live_config,
            "inventory": {**dict(inventory), "avg_conf": {c: 0.0 for c in CLASSES}, "uptime": 0},
            "camera_running": camera_running,
        },
    )


@socketio.on("disconnect")
def handle_disconnect():
    pass


@socketio.on("start_camera")
def handle_start_camera(data=None):
    global camera_running, camera_thread
    with model_lock:
        if current_model is None:
            socketio.emit("error", {"message": "Kein Modell geladen. Bitte Modell auswaehlen."})
            return

    if data:
        with config_lock:
            live_config.update(
                {
                    "conf": data.get("conf", live_config["conf"]),
                    "reject": data.get("reject", live_config["reject"]),
                    "iou": data.get("iou", live_config["iou"]),
                    "imgsz": data.get("imgsz", live_config["imgsz"]),
                    "tracking": data.get("tracking", live_config["tracking"]),
                    "camera_index": data.get("camera_index", live_config["camera_index"]),
                }
            )

    with camera_lock:
        if camera_running:
            return
        camera_running = True
        camera_thread = threading.Thread(target=_camera_loop, daemon=True)
        camera_thread.start()


@socketio.on("stop_camera")
def handle_stop_camera():
    global camera_running, camera_thread
    with camera_lock:
        camera_running = False
        if camera_thread and camera_thread.is_alive():
            camera_thread.join(timeout=3)
        camera_thread = None


@socketio.on("load_model")
def handle_load_model(data):
    global current_model, model_name
    new_name = data.get("model", "")
    if not new_name:
        return
    if "/" in new_name or "\\" in new_name or ".." in new_name:
        socketio.emit("error", {"message": "Invalid model name."})
        return

    def _load():
        global current_model, model_name
        try:
            m = load_model(new_name)
            with model_lock:
                current_model = m
                model_name = new_name
            # Reset inventory when switching models
            with inventory_lock:
                for k in CLASSES:
                    inventory[k] = 0
            state_reset_event.set()
            socketio.emit("inventory", {**dict(inventory), "avg_conf": {c: 0.0 for c in CLASSES}, "uptime": 0})
            socketio.emit("model_loaded", {"model": new_name})
        except Exception as e:
            socketio.emit("error", {"message": f"Modell-Fehler: {e}"})

    threading.Thread(target=_load, daemon=True).start()


@socketio.on("update_config")
def handle_update_config(data):
    with config_lock:
        for key in ("conf", "reject", "iou", "imgsz", "tracking", "camera_index", "camera_width", "camera_height"):
            if key in data:
                live_config[key] = data[key]
        if live_config["reject"] < live_config["conf"]:
            live_config["reject"] = live_config["conf"]


@socketio.on("reset_inventory")
def handle_reset_inventory():
    with inventory_lock:
        for k in CLASSES:
            inventory[k] = 0
    state_reset_event.set()
    socketio.emit("inventory", {**dict(inventory), "avg_conf": {c: 0.0 for c in CLASSES}, "uptime": 0})


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
    print("\n  MIRA Control Center")
    print(f"  http://localhost:{port}\n")
    socketio.run(app, host=host, port=port, debug=debug)


if __name__ == "__main__":
    run_dashboard(debug=False)
