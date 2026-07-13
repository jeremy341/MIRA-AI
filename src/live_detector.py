import argparse
import cv2
import pathlib
import sys
import threading
import time
import numpy as np
from ultralytics import YOLO
from collections import deque

# ---------------------------------------------------------------------------
# 1. ARGUMENT PARSING
# ---------------------------------------------------------------------------
parser = argparse.ArgumentParser(description="MIRA Live Detection (Optimized)")
parser.add_argument(
    "--model", type=str, default="mira_exp014.pt",
    help="Model filename inside the models/ folder (default: mira_exp014.pt). "
         "Run without arguments to see all available models printed on startup."
)
parser.add_argument(
    "--camera", type=int, default=0,
    help="Camera device index (default: 0)."
)
parser.add_argument(
    "--resolution", type=str, default="640x360",
    choices=["640x360", "1280x720", "1920x1080"],
    help="Camera capture resolution (default: 640x360). "
         "Does not affect model inference — YOLO resizes to imgsz=640 internally."
)
parser.add_argument(
    "--target-latency", type=int, default=50,
    help="Target latency in ms (default: 50). Frames are skipped to meet target."
)
parser.add_argument(
    "--conf", type=float, default=0.5,
    help="Confidence threshold (default: 0.5). Higher = fewer false positives."
)
args = parser.parse_args()
CAM_W, CAM_H = (int(v) for v in args.resolution.split("x"))


# ---------------------------------------------------------------------------
# 2. THREADED CAMERA STREAM WITH ADAPTIVE FRAME SKIPPING
# ---------------------------------------------------------------------------
class CameraStream:
    """
    Optimized camera reader with adaptive frame skipping.
    - Discards frames if inference can't keep up
    - Always returns the freshest frame for minimal latency
    """

    WARMUP_FRAMES = 10

    def __init__(self, index: int, width: int, height: int):
        self.cap = cv2.VideoCapture(index, cv2.CAP_DSHOW)
        if not self.cap.isOpened():
            raise RuntimeError(f"Failed to open camera index {index}.")

        self.cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*"MJPG"))
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH,  width)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
        self.cap.set(cv2.CAP_PROP_FPS,          30)
        self.cap.set(cv2.CAP_PROP_BUFFERSIZE,   1)
        self.cap.set(cv2.CAP_PROP_AUTOFOCUS,    0)
        self.cap.set(cv2.CAP_PROP_AUTO_EXPOSURE, 1)

        print(f"Warming up camera {index} ({self.WARMUP_FRAMES} frames)...")
        for _ in range(self.WARMUP_FRAMES):
            self.cap.read()

        self.ret, self.frame = self.cap.read()
        self._lock   = threading.Lock()
        self._running = True
        self._thread  = threading.Thread(target=self._reader, daemon=True)
        self._thread.start()
        self.frames_dropped = 0

    def _reader(self):
        """Continuously grab frames, discarding old ones."""
        while self._running:
            ret, frame = self.cap.read()
            with self._lock:
                self.ret   = ret
                self.frame = frame

    def read(self):
        """Return the freshest frame (thread-safe)."""
        with self._lock:
            return self.ret, self.frame.copy() if self.ret else (False, None)

    def release(self):
        self._running = False
        self._thread.join(timeout=2)
        self.cap.release()


# ---------------------------------------------------------------------------
# 3. PATH RESOLUTION & MODEL LOAD (with TFLite int8 optimization)
# ---------------------------------------------------------------------------
SCRIPT_DIR  = pathlib.Path(__file__).resolve().parent
ROOT_DIR    = SCRIPT_DIR.parent
MODELS_DIR  = ROOT_DIR / "models" / "detection"
MODEL_PATH  = MODELS_DIR / args.model

available = sorted(p.name for p in MODELS_DIR.glob("*") if p.suffix in (".pt", ".tflite", ".keras"))
print("\nAvailable models in models/:")
for name in available:
    marker = "  <-- selected" if name == args.model else ""
    int8_marker = " [INT8 - Recommended for speed]" if "int8" in name.lower() else ""
    print(f"  {name}{marker}{int8_marker}")
print()

if not MODEL_PATH.exists():
    raise FileNotFoundError(
        f"Model '{args.model}' not found in {MODELS_DIR}.\n"
        f"Available models: {', '.join(available)}"
    )

print(f"Loading {args.model}...")

if "classifier" in args.model.lower():
    print(f"\nERROR: '{args.model}' is a CLASSIFIER model, not a detector.")
    print("Live detection requires a detection model (.pt or detection .tflite).")
    print(f"Use 'mira eval-class --model {args.model} --exp <folder>' instead.")
    sys.exit(1)

task_type = "detect" if MODEL_PATH.suffix == ".tflite" else None
model = YOLO(MODEL_PATH, task=task_type)

is_tflite_int8 = MODEL_PATH.suffix == ".tflite" and "int8" in args.model.lower()

if MODEL_PATH.suffix == ".tflite":
    from ai_edge_litert.interpreter import Interpreter as LiteRTInterpreter
    _tmp = LiteRTInterpreter(model_path=str(MODEL_PATH))
    _shape = _tmp.get_input_details()[0]["shape"]
    img_size = int(max(_shape))
    del _tmp
    if is_tflite_int8:
        print(f"TFLite INT8 model: input {img_size}x{img_size}, auto-setting conf=0.25 (INT8 reduces confidence)")
    else:
        print(f"TFLite model: input {img_size}x{img_size}")
else:
    img_size = 640
    print(f"PyTorch model: input {img_size}x{img_size}")

if is_tflite_int8:
    args.conf = 0.25
    print(f"Confidence threshold overridden to {args.conf} for INT8 model.")


# ---------------------------------------------------------------------------
# 4. CUSTOM BOX DRAWING (fixes scaling issues with tabletop setup)
# ---------------------------------------------------------------------------
def draw_boxes_corrected(frame, results, conf_threshold=0.3):
    """
    Manually draw bounding boxes with proper scaling.
    Ultralytics already scales boxes back to original frame coordinates.
    """
    h, w = frame.shape[:2]
    annotated = frame.copy()
    
    if results[0].boxes is None or len(results[0].boxes) == 0:
        return annotated
    
    boxes = results[0].boxes
    for box in boxes:
        conf = float(box.conf[0])
        if conf < conf_threshold:
            continue
        
        x1, y1, x2, y2 = box.xyxy[0].cpu().numpy().astype(int)
        cls_id = int(box.cls[0])
        cls_name = results[0].names[cls_id]
        
        x1, y1, x2, y2 = max(0, x1), max(0, y1), min(w, x2), min(h, y2)
        
        color = (0, 255, 0)
        cv2.rectangle(annotated, (x1, y1), (x2, y2), color, 2)
        
        label = f"{cls_name} {conf:.2f}"
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 0.6
        thickness = 2
        text_size = cv2.getTextSize(label, font, font_scale, thickness)[0]
        text_bg_x1, text_bg_y1 = x1, y1 - 25
        text_bg_x2, text_bg_y2 = x1 + text_size[0], y1
        
        cv2.rectangle(annotated, (text_bg_x1, text_bg_y1), (text_bg_x2, text_bg_y2), color, -1)
        cv2.putText(annotated, label, (x1, y1 - 5), font, font_scale, (0, 0, 0), thickness)
    
    return annotated


# ---------------------------------------------------------------------------
# 5. OPEN CAMERA STREAM
# ---------------------------------------------------------------------------
print(f"Opening camera {args.camera} at {CAM_W}x{CAM_H}...")
stream = CameraStream(args.camera, CAM_W, CAM_H)
print(f"MIRA Live Detection active (target latency: {args.target_latency}ms). Press 'q' to exit.")

prev_time = time.perf_counter()
latency_history = deque(maxlen=30)
skip_frame = False

# ---------------------------------------------------------------------------
# 6. MAIN INFERENCE LOOP (with adaptive frame skipping)
# ---------------------------------------------------------------------------
try:
    while True:
        ret, frame = stream.read()
        if not ret or frame is None:
            continue

        if skip_frame:
            skip_frame = False
            continue

        if is_tflite_int8:
            results = model.predict(
                frame,
                imgsz=img_size,
                conf=args.conf,
                verbose=False
            )
        else:
            results = model.track(
                frame,
                imgsz=img_size,
                conf=args.conf,
                persist=True,
                verbose=False,
                tracker="bytetrack.yaml"
            )

        annotated_frame = draw_boxes_corrected(frame, results, conf_threshold=args.conf)

        curr_time = time.perf_counter()
        frame_time = curr_time - prev_time
        prev_time = curr_time
        
        fps = 1.0 / max(frame_time, 1e-6)
        latency_ms = results[0].speed.get("inference", 0)
        latency_history.append(latency_ms)
        avg_latency = np.mean(latency_history)

        skip_frame = avg_latency > args.target_latency

        status_text = (
            f"Cam: {args.camera} | {CAM_W}x{CAM_H} | "
            f"Latency: {latency_ms:.1f}ms (avg: {avg_latency:.1f}ms) | FPS: {fps:.1f} | "
            f"Skip: {'ON' if skip_frame else 'OFF'}"
        )
        cv2.putText(annotated_frame, status_text, (20, 40),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)

        cv2.imshow("MIRA Real-Time Multi-Object Detection", annotated_frame)

        if cv2.waitKey(1) & 0xFF == ord("q"):
            break
finally:
    stream.release()
    cv2.destroyAllWindows()
