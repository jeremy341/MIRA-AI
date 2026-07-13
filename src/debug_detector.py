import cv2
import pathlib
import time
import argparse
import numpy as np
from ultralytics import YOLO

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
parser.add_argument(
    "--use-int8",
    action="store_true",
    help="Use INT8 quantized models for faster inference (use with mira_*_int8_*.tflite)"
)
args = parser.parse_args()

# 2. PATH RESOLUTION
SCRIPT_DIR = pathlib.Path(__file__).resolve().parent
ROOT_DIR = SCRIPT_DIR.parent
MODEL_PATH = ROOT_DIR / "models" / "detection" / args.model

if not MODEL_PATH.exists():
    raise FileNotFoundError(f"Model file not found at: {MODEL_PATH}")

print(f"Loading MIRA model: {MODEL_PATH}")
task_type = "detect" if MODEL_PATH.suffix == ".tflite" else None
model = YOLO(str(MODEL_PATH), task=task_type)

# 3. CUSTOM BOX DRAWING (fixes scaling/transparency issues)
def draw_boxes_optimized(frame, results, conf_threshold=0.3):
    """Enhanced box drawing with proper scaling."""
    h, w = frame.shape[:2]
    annotated = frame.copy()
    
    if results[0].boxes is None or len(results[0].boxes) == 0:
        return annotated
    
    boxes = results[0].boxes
    for i, box in enumerate(boxes):
        conf = float(box.conf[0])
        if conf < conf_threshold:
            continue
        
        x1, y1, x2, y2 = box.xyxy[0].cpu().numpy().astype(int)
        cls_id = int(box.cls[0])
        cls_name = results[0].names[cls_id]
        
        x1, y1, x2, y2 = max(0, x1), max(0, y1), min(w, x2), min(h, y2)
        
        color = (0, 255, 0) if i % 2 == 0 else (255, 0, 0)
        cv2.rectangle(annotated, (x1, y1), (x2, y2), color, 2)
        
        label = f"{cls_name} {conf:.2f}"
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 0.6
        thickness = 2
        text_size = cv2.getTextSize(label, font, font_scale, thickness)[0]
        
        cv2.rectangle(annotated, (x1, y1 - 25), (x1 + text_size[0], y1), color, -1)
        cv2.putText(annotated, label, (x1, y1 - 5), font, font_scale, (255, 255, 255), thickness)
    
    return annotated

# 4. WEBCAM SETUP (optimized)
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

    # 5. RUN INFERENCE DYNAMICALLY
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

    # 6. VISUALIZATION (using optimized box drawing)
    annotated_frame = draw_boxes_optimized(frame, results, args.conf)

    # 7. BENCHMARK METRICS
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