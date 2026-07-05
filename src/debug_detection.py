import cv2
import pathlib
import time
import argparse
from ultralytics import YOLO

# 1. ARGUMENT PARSING
parser = argparse.ArgumentParser(description="MIRA Live Diagnostic & Testing Suite")
parser.add_argument(
    "--model",
    type=str,
    default="mira_detector_wild.pt",
    help="Filename of the model in your /models directory"
)
parser.add_argument(
    "--imgsz",
    type=int,
    default=640,
    help="Image resolution for inference (typically 320 or 640)"
)
parser.add_argument(
    "--conf",
    type=float,
    default=0.35,
    help="Confidence threshold (0.10 to 1.00)"
)
parser.add_argument(
    "--iou",
    type=float,
    default=0.45,
    help="Intersection over Union threshold for Non-Maximum Suppression"
)
parser.add_argument(
    "--track",
    action="store_true",
    help="Enable persistent ByteTrack object tracking"
)
args = parser.parse_args()

# 2. PATH RESOLUTION
SCRIPT_DIR = pathlib.Path(__file__).resolve().parent
ROOT_DIR = SCRIPT_DIR.parent
MODEL_PATH = ROOT_DIR / "models" / args.model

if not MODEL_PATH.exists():
    raise FileNotFoundError(f"Model file not found at: {MODEL_PATH}")

print(f"Loading MIRA model: {MODEL_PATH}")
# If loading TFLite, we must specify the task dynamically
task_type = "detect" if MODEL_PATH.suffix == ".tflite" else None
model = YOLO(str(MODEL_PATH), task=task_type)

# 3. WEBCAM SETUP
cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
cap.set(cv2.CAP_PROP_AUTOFOCUS, 0)
cap.set(cv2.CAP_PROP_AUTO_EXPOSURE, 0)

print(f"Diagnostics active. Using {args.model} | imgsz={args.imgsz} | conf={args.conf} | track={args.track}")
print("Press 'q' in the window to exit.")

prev_time = time.perf_counter()

while True:
    ret, frame = cap.read()
    if not ret:
        print("Error: Camera frame capture failed.")
        break

    # 4. RUN INFERENCE DYNAMICALLY
    if args.track:
        results = model.track(
            frame,
            imgsz=args.imgsz,
            conf=args.conf,
            iou=args.iou,
            persist=True,
            verbose=False
        )
    else:
        results = model.predict(
            frame,
            imgsz=args.imgsz,
            conf=args.conf,
            iou=args.iou,
            verbose=False
        )

    # 5. VISUALIZATION
    annotated_frame = results[0].plot(conf=True, line_width=2, font_size=1, labels=True)

    # 6. BENCHMARK METRICS
    curr_time = time.perf_counter()
    fps = 1.0 / (curr_time - prev_time) if (curr_time - prev_time) > 0 else 0
    prev_time = curr_time

    latency_ms = results[0].speed['inference']
    status_label = f"Model: {args.model} | Latency: {latency_ms:.1f}ms | FPS: {fps:.1f}"

    cv2.putText(annotated_frame, status_label, (20, 40),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)

    cv2.imshow("MIRA Diagnostics Window", annotated_frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()