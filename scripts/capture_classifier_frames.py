import argparse
import sys
from pathlib import Path
import cv2
import datetime

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
from config import DATA_CLASSES_DIR as DATA_DIR
from config import setup_camera_properties
from logger import logger

# ---------------------------------------------------------------------------
# 1. ARGUMENT PARSING
# ---------------------------------------------------------------------------
parser = argparse.ArgumentParser(description="MIRA Frame Capture Tool")
parser.add_argument(
    "--camera", type=int, default=0,
    help="Camera device index (default: 0)."
)
parser.add_argument(
    "--resolution", type=str, default="640x360",
    choices=["640x360", "1280x720", "1920x1080"],
    help="Camera capture resolution (default: 640x360). Use 640x360 when collecting "
         "data for models trained on that resolution."
)
args = parser.parse_args()
CAM_W, CAM_H = (int(v) for v in args.resolution.split("x"))

# ---------------------------------------------------------------------------
# 3. CAMERA SETUP
# ---------------------------------------------------------------------------
logger.info(f"Opening camera {args.camera} at {CAM_W}x{CAM_H}...")
cap = cv2.VideoCapture(args.camera, cv2.CAP_DSHOW)  # DirectShow: lower latency on Windows
if not cap.isOpened():
    raise RuntimeError(f"Failed to open webcam index {args.camera}.")

# MJPG decodes ~3-5x faster than YUY2 and unlocks higher frame-rates
setup_camera_properties(cap, CAM_W, CAM_H)

# Warmup: let auto-exposure settle so the first saved frames aren't washed out
WARMUP = 10
logger.info(f"Warming up camera ({WARMUP} frames)...")
for _ in range(WARMUP):
    cap.read()

# ---------------------------------------------------------------------------
# 4. CLASS → FOLDER MAPPING
# ---------------------------------------------------------------------------
CLASSES = {
    "1": ("glass",   DATA_DIR / "glass"),
    "2": ("metal",   DATA_DIR / "metal"),
    "3": ("paper",   DATA_DIR / "paper"),
    "4": ("plastic", DATA_DIR / "plastic"),
    "5": ("trash",   DATA_DIR / "trash"),
}

for _, folder in CLASSES.values():
    folder.mkdir(parents=True, exist_ok=True)

logger.info("MIRA Camera Frame Capture Active.")
logger.info("Press 1 (Glass), 2 (Metal), 3 (Paper), 4 (Plastic), or 5 (Trash) to save a frame.")
logger.info("Press 'q' to quit.")

# ---------------------------------------------------------------------------
# 5. CAPTURE LOOP
# ---------------------------------------------------------------------------
try:
    while True:
        ret, frame = cap.read()
        if not ret:
            break

        display_frame = frame.copy()
        cv2.putText(display_frame,
                    "1: Glass | 2: Metal | 3: Paper | 4: Plastic | 5: Trash | q: Quit",
                    (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
        cv2.putText(display_frame,
                    f"Camera: {args.camera} | {CAM_W}x{CAM_H}",
                    (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 200, 255), 1)
        cv2.imshow("MIRA Frame Capture", display_frame)

        key = cv2.waitKey(1) & 0xFF

        if key == ord("q"):
            break

        try:
            key_char = chr(key)
            if key_char in CLASSES:
                label, folder = CLASSES[key_char]
                # Microseconds in filename prevent collisions during rapid capture
                filename  = f"{label}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S_%f')}.jpg"
                filepath  = folder / filename
                cv2.imwrite(str(filepath), frame)
                logger.info(f"Saved: {filepath}")
        except ValueError:
            pass  # ignore non-ASCII key codes
finally:
    cap.release()
    cv2.destroyAllWindows()

