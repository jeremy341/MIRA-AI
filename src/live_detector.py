"""MIRA Live Detection — thin CLI wrapper around InferenceEngine."""
import argparse
from inference_engine import InferenceEngine

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

engine = InferenceEngine(
    model_name=args.model,
    camera_index=args.camera,
    cam_width=CAM_W,
    cam_height=CAM_H,
    target_latency_ms=args.target_latency,
    conf_threshold=args.conf,
    enable_tracking=True,
)
engine.run()
