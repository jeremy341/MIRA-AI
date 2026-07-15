"""MIRA Live Diagnostic & Testing Suite — thin CLI wrapper around InferenceEngine."""
import argparse
import cv2
import time
from inference_engine import InferenceEngine
from visualize import draw_boxes

parser = argparse.ArgumentParser(description="MIRA Live Diagnostic & Testing Suite (Optimized)")
parser.add_argument(
    "--model", type=str, default="mira_exp014.pt",
    help="Filename of the model in your /models directory"
)
parser.add_argument(
    "--imgsz", type=int, default=None,
    help="Image resolution for inference (typically 320 or 640). Defaults to model-specific size."
)
parser.add_argument(
    "--conf", type=float, default=0.5,
    help="Confidence threshold (0.10 to 1.00)"
)
parser.add_argument(
    "--iou", type=float, default=0.45,
    help="Intersection over Union threshold for Non-Maximum Suppression"
)
parser.add_argument(
    "--track", action="store_true", default=True,
    help="Enable persistent ByteTrack object tracking"
)
args = parser.parse_args()

engine = InferenceEngine(
    model_name=args.model,
    camera_index=0,
    cam_width=1280,
    cam_height=720,
    target_latency_ms=100,
    conf_threshold=args.conf,
    imgsz=args.imgsz,
    enable_tracking=args.track,
    iou_threshold=args.iou,
)

print(f"Diagnostics active. Using {args.model} | imgsz={args.imgsz or engine.img_size} | conf={args.conf} | track={args.track}")
print("Press 'q' in the window to exit.")

# Custom diagnostic loop with per-frame benchmark metrics
try:
    prev_time = time.perf_counter()
    frame_count = 0
    while True:
        ret, frame = engine.stream.read()
        if not ret:
            print("Error: Camera frame capture failed.")
            break

        frame_count += 1
        results = engine._infer(frame)
        annotated = draw_boxes(frame, results, args.conf)

        curr_time = time.perf_counter()
        elapsed = curr_time - prev_time
        fps = frame_count / elapsed if elapsed > 0 else 0

        if frame_count % 30 == 0:
            prev_time = curr_time
            frame_count = 0

        latency_ms = results[0].speed.get("inference", 0)
        detected_count = len(results[0].boxes) if results[0].boxes else 0

        status_label = (
            f"Model: {args.model} | Latency: {latency_ms:.1f}ms | FPS: {fps:.1f} | "
            f"Detections: {detected_count} | Tracking: {'ON' if args.track else 'OFF'}"
        )
        cv2.putText(
            annotated, status_label, (20, 40),
            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2,
        )

        cv2.imshow("MIRA Diagnostics Window (Optimized)", annotated)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
finally:
    engine.stream.release()
    cv2.destroyAllWindows()
