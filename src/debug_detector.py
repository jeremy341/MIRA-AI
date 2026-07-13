import cv2
import time
import argparse
from ultralytics import YOLO

from config import DETECTION_DIR, get_tflite_imgsz
from visualize import draw_boxes

# 1. ARGUMENT PARSING
parser = argparse.ArgumentParser(description="MIRA Live Diagnostic & Testing Suite (Optimized)")
parser.add_argument(
    "--model",
    type=str,
    default="mira_exp014.pt",
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
    default=0.5,
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
MODEL_PATH = DETECTION_DIR / args.model

if not MODEL_PATH.exists():
    raise FileNotFoundError(f"Model file not found at: {MODEL_PATH}")

print(f"Loading MIRA model: {MODEL_PATH}")
task_type = "detect" if MODEL_PATH.suffix == ".tflite" else None
model = YOLO(str(MODEL_PATH), task=task_type)

# 3. WEBCAM SETUP (optimized)
cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
cap.set(cv2.CAP_PROP_AUTOFOCUS, 0)
cap.set(cv2.CAP_PROP_AUTO_EXPOSURE, 1)
cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

print(f"Diagnostics active. Using {args.model} | imgsz={args.imgsz} | conf={args.conf} | track={args.track}")
print("Press 'q' in the window to exit.")

prev_time = time.perf_counter()
frame_count = 0

while True:
    ret, frame = cap.read()
    if not ret:
        print("Error: Camera frame capture failed.")
        break

    frame_count += 1

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

    # 5. VISUALIZATION (using optimized box drawing)
    annotated_frame = draw_boxes(frame, results, args.conf)

    # 6. BENCHMARK METRICS
    curr_time = time.perf_counter()
    elapsed = curr_time - prev_time
    fps = frame_count / elapsed if elapsed > 0 else 0
    
    if frame_count % 30 == 0:
        prev_time = curr_time
        frame_count = 0

    latency_ms = results[0].speed.get('inference', 0)
    detected_count = len(results[0].boxes) if results[0].boxes else 0
    
    status_label = (
        f"Model: {args.model} | Latency: {latency_ms:.1f}ms | FPS: {fps:.1f} | "
        f"Detections: {detected_count} | Tracking: {'ON' if args.track else 'OFF'}"
    )

    cv2.putText(annotated_frame, status_label, (20, 40),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)

    cv2.imshow("MIRA Diagnostics Window (Optimized)", annotated_frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()