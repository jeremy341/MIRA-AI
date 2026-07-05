import argparse
import cv2
import pathlib
import threading
import time
from ultralytics import YOLO

# ---------------------------------------------------------------------------
# 1. ARGUMENT PARSING
# ---------------------------------------------------------------------------
parser = argparse.ArgumentParser(description="MIRA Live Detection")
parser.add_argument(
    "--model", type=str, default="mira_detector_wild_int8.tflite",
    help="Model filename inside the models/ folder (default: mira_detector_wild_int8.tflite). "
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
args = parser.parse_args()
CAM_W, CAM_H = (int(v) for v in args.resolution.split("x"))


# ---------------------------------------------------------------------------
# 2. THREADED CAMERA STREAM
#    Runs capture in a background thread so the main loop always reads the
#    most recent frame instead of a stale buffered one. This is the single
#    biggest latency improvement for real-time inference loops.
# ---------------------------------------------------------------------------
class CameraStream:
    """
    Background-threaded OpenCV camera reader.

    Why this helps:
    - cap.read() blocks until the next frame arrives from the driver.
    - If inference takes longer than one frame period the buffer fills up,
      causing visible lag that compounds over time.
    - Running capture on its own thread means the main loop always gets the
      newest frame the moment it asks for one.
    """

    WARMUP_FRAMES = 10  # discard first N frames so auto-exposure can settle

    def __init__(self, index: int, width: int, height: int):
        # Use DirectShow on Windows: honours CAP_PROP_BUFFERSIZE and has
        # lower driver overhead than the default MSMF backend.
        self.cap = cv2.VideoCapture(index, cv2.CAP_DSHOW)
        if not self.cap.isOpened():
            raise RuntimeError(f"Failed to open camera index {index}.")

        # MJPG is decoded ~3-5x faster than the default YUY2 / YUYV format
        # and lets the camera deliver higher frame-rates at all resolutions.
        self.cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*"MJPG"))
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH,  width)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
        self.cap.set(cv2.CAP_PROP_FPS,          30)
        # Buffer size 1 = always deliver the latest frame, never queue stale ones
        self.cap.set(cv2.CAP_PROP_BUFFERSIZE,   1)
        self.cap.set(cv2.CAP_PROP_AUTOFOCUS,    0)
        self.cap.set(cv2.CAP_PROP_AUTO_EXPOSURE, 1)  # manual exposure mode

        # Warmup: let auto-exposure settle before inference starts
        print(f"Warming up camera {index} ({self.WARMUP_FRAMES} frames)...")
        for _ in range(self.WARMUP_FRAMES):
            self.cap.read()

        self.ret, self.frame = self.cap.read()
        self._lock   = threading.Lock()
        self._running = True
        self._thread  = threading.Thread(target=self._reader, daemon=True)
        self._thread.start()

    def _reader(self):
        """Continuously grab frames in the background."""
        while self._running:
            ret, frame = self.cap.read()
            with self._lock:
                self.ret   = ret
                self.frame = frame

    def read(self):
        """Return a copy of the latest frame (thread-safe)."""
        with self._lock:
            return self.ret, self.frame.copy() if self.ret else (False, None)

    def release(self):
        self._running = False
        self._thread.join(timeout=2)
        self.cap.release()


# ---------------------------------------------------------------------------
# 3. PATH RESOLUTION & MODEL LOAD
# ---------------------------------------------------------------------------
SCRIPT_DIR  = pathlib.Path(__file__).resolve().parent
ROOT_DIR    = SCRIPT_DIR.parent
MODELS_DIR  = ROOT_DIR / "models"
MODEL_PATH  = MODELS_DIR / args.model

# Print available models so the user knows their options
available = sorted(p.name for p in MODELS_DIR.glob("*") if p.suffix in (".pt", ".tflite", ".keras"))
print("\nAvailable models in models/:")
for name in available:
    marker = "  <-- selected" if name == args.model else ""
    print(f"  {name}{marker}")
print()

if not MODEL_PATH.exists():
    raise FileNotFoundError(
        f"Model '{args.model}' not found in {MODELS_DIR}.\n"
        f"Available models: {', '.join(available)}"
    )

print(f"Loading {args.model}...")
task_type = "detect" if MODEL_PATH.suffix == ".tflite" else None
model = YOLO(MODEL_PATH, task=task_type)

# Detect expected input shape dynamically:
# TFLite/LiteRT edge models are exported at 320 for CPU speed, PyTorch models use 640.
img_size = 320 if MODEL_PATH.suffix == ".tflite" else 640


# ---------------------------------------------------------------------------
# 4. OPEN CAMERA STREAM
# ---------------------------------------------------------------------------
print(f"Opening camera {args.camera} at {CAM_W}x{CAM_H}...")
stream = CameraStream(args.camera, CAM_W, CAM_H)
print("MIRA Live Detection active. Press 'q' to exit.")

prev_time = time.perf_counter()

# ---------------------------------------------------------------------------
# 5. MAIN INFERENCE LOOP
# ---------------------------------------------------------------------------
try:
    while True:
        ret, frame = stream.read()
        if not ret or frame is None:
            print("Warning: dropped frame.")
            continue

        # Run inference — dynamically matched to model (320 for TFLite, 640 for PyTorch)
        # conf=0.35 ignores low-confidence background noise
        # persist=True enables ByteTrack object tracking
        results = model.track(
            frame,
            imgsz=img_size,
            conf=0.35,
            persist=True,
            verbose=False
        )

        # Draw bounding boxes — .plot() handles scaling automatically
        annotated_frame = results[0].plot(
            conf=True,
            line_width=2,
            font_size=1,
            labels=True
        )

        # FPS & latency overlay
        curr_time   = time.perf_counter()
        fps         = 1.0 / max(curr_time - prev_time, 1e-6)
        prev_time   = curr_time
        latency_ms  = results[0].speed["inference"]

        status_text = (
            f"Cam: {args.camera} | {CAM_W}x{CAM_H} | "
            f"Latency: {latency_ms:.1f}ms | FPS: {fps:.1f}"
        )
        cv2.putText(annotated_frame, status_text, (20, 40),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)

        cv2.imshow("MIRA Real-Time Multi-Object Detection", annotated_frame)

        if cv2.waitKey(1) & 0xFF == ord("q"):
            break
finally:
    stream.release()
    cv2.destroyAllWindows()
