import streamlit as st
import cv2
from ultralytics import YOLO
import time
import pandas as pd
import pathlib
import numpy as np

# 1. PATH RESOLUTION
SCRIPT_DIR = pathlib.Path(__file__).resolve().parent
ROOT_DIR = SCRIPT_DIR.parent
MODELS_DIR = ROOT_DIR / "models"

if not MODELS_DIR.exists():
    st.error(f"Models directory not found at: {MODELS_DIR}")
    st.stop()

available_models = [
    p.name for p in MODELS_DIR.glob("*")
    if p.suffix in [".pt", ".tflite"] and "classifier" not in p.name.lower()
]

# Add experiment labels for context
MODEL_LABELS = {
    "mira_exp006.pt": "EXP-006 (YOLOv8n, multi-dataset)",
    "mira_exp006_int8.tflite": "EXP-006 INT8 (YOLOv8n, multi-dataset)",
    "mira_exp009_int8.tflite": "EXP-009 INT8 (inflated mAP)",
    "mira_exp011.pt": "EXP-011 (YOLOv8n, TACO-only)",
    "mira_exp011_int8.tflite": "EXP-011 INT8 (YOLOv8n, TACO-only)",
    "mira_exp013.pt": "EXP-013 (YOLO11n, TACO+TrashNet)",
    "mira_exp013_int8.tflite": "EXP-013 INT8 (YOLO11n, TACO+TrashNet)",
    "mira_exp014.pt": "EXP-014 (YOLO11n, +Roboflow)",
    "mira_exp014_int8.tflite": "EXP-014 INT8 (YOLO11n, +Roboflow)",
    "mira_exp015.pt": "EXP-015 (YOLO11n, +WaRP)",
    "mira_exp015_int8.tflite": "EXP-015 INT8 (YOLO11n, +WaRP)",
}
available_models_display = [
    f"{m}  [{MODEL_LABELS[m]}]" if m in MODEL_LABELS else m
    for m in available_models
]

if not available_models:
    st.error("No compatible detection models found inside the /models folder.")
    st.stop()

# 2. STREAMLIT PAGE CONFIGURATION
st.set_page_config(page_title="MIRA Control Center", layout="wide")
st.title("MIRA - Interactive Diagnostic Dashboard (Optimized)")

# 3. INTERACTIVE SIDEBAR CONTROLS
st.sidebar.header("Model Parameters")
selected_model_display = st.sidebar.selectbox("Active Model Brain", available_models_display, index=0)
# Map display name back to actual filename
selected_model = available_models[available_models_display.index(selected_model_display)]
camera_index = st.sidebar.number_input(
    "Camera Index", min_value=0, max_value=10, value=0, step=1,
    help="0 = default webcam. Change if you have multiple cameras."
)

imgsz = st.sidebar.select_slider("Inference Resolution (imgsz)", options=[160, 224, 320, 416, 640], value=320)
conf = st.sidebar.slider("Confidence Threshold", min_value=0.05, max_value=1.00, value=0.5, step=0.05)
iou = st.sidebar.slider("NMS IoU Threshold", min_value=0.10, max_value=1.00, value=0.45, step=0.05)
enable_tracking = st.sidebar.checkbox("Enable ByteTrack Tracking", value=True)

st.sidebar.header("System Execution")
run_camera = st.sidebar.checkbox("Start Live Feed", value=False, key="run_camera")

st.sidebar.header("System Status")
fps_display = st.sidebar.empty()
latency_display = st.sidebar.empty()


def request_rerun():
    rerun = getattr(st, "rerun", None)
    if rerun is None:
        rerun = getattr(st, "experimental_rerun", None)
    if rerun is not None:
        rerun()


# 4. CUSTOM BOX DRAWING (fixes tabletop scaling issues)
def draw_boxes_streamlit(frame, results, conf_threshold=0.3):
    """Draw bounding boxes with correct scaling for tabletop detection."""
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
        
        cv2.rectangle(annotated, (x1, y1 - 25), (x1 + text_size[0], y1), color, -1)
        cv2.putText(annotated, label, (x1, y1 - 5), font, font_scale, (0, 0, 0), thickness)
    
    return annotated


# 5. LOAD MODEL DYNAMICALLY
@st.cache_resource(show_spinner="Loading model brain...")
def load_selected_model(model_name):
    path = MODELS_DIR / model_name
    if "classifier" in model_name.lower():
        st.error(f"'{model_name}' is a classifier model. Use 'mira eval-class' instead.")
        st.stop()
    task_type = "detect" if path.suffix == ".tflite" else None
    return YOLO(str(path), task=task_type), "int8" in model_name.lower() and path.suffix == ".tflite"


model, is_tflite_int8 = load_selected_model(selected_model)

if is_tflite_int8:
    conf = min(conf, 0.25)
    st.sidebar.warning(f"INT8 model detected — conf capped at {conf:.2f}")

# 6. LAYOUT
col1, col2 = st.columns([2, 1])
image_placeholder = col1.empty()
chart_placeholder = col2.empty()

if "seen_ids" not in st.session_state:
    st.session_state.seen_ids = set()

if "counts" not in st.session_state:
    st.session_state.counts = {"glass": 0, "metal": 0, "paper": 0, "plastic": 0, "trash": 0}

# 7. LIVE INFERENCE LOOP
if run_camera:
    cap = cv2.VideoCapture(int(camera_index), cv2.CAP_DSHOW)
    if not cap.isOpened():
        st.error(f"Failed to open video capture device {int(camera_index)}.")
        st.session_state.run_camera = False
        st.stop()

    cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*"MJPG"))
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 360)
    cap.set(cv2.CAP_PROP_FPS, 30)
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
    cap.set(cv2.CAP_PROP_AUTOFOCUS, 0)
    cap.set(cv2.CAP_PROP_AUTO_EXPOSURE, 1)

    try:
        while st.session_state.get("run_camera", False):
            ret, frame = cap.read()
            if not ret:
                st.error("Failed to capture video.")
                st.session_state.run_camera = False
                break

            start_time = time.perf_counter()

            if is_tflite_int8:
                results = model.predict(frame, imgsz=imgsz, conf=conf, iou=iou, verbose=False)
            elif enable_tracking:
                results = model.track(frame, persist=True, imgsz=imgsz, conf=conf, iou=iou, verbose=False, tracker="bytetrack.yaml")
            else:
                results = model.predict(frame, imgsz=imgsz, conf=conf, iou=iou, verbose=False)

            end_time = time.perf_counter()

            latency_ms = (end_time - start_time) * 1000
            fps = 1.0 / (end_time - start_time) if (end_time - start_time) > 0 else 0

            fps_display.metric("FPS", f"{fps:.1f}")
            latency_display.metric("Latency", f"{latency_ms:.1f} ms")

            if results[0].boxes is not None and results[0].boxes.id is not None:
                track_ids = results[0].boxes.id.cpu().numpy().astype(int)
                class_ids = results[0].boxes.cls.cpu().numpy().astype(int)

                for track_id, class_id in zip(track_ids, class_ids):
                    if track_id not in st.session_state.seen_ids:
                        st.session_state.seen_ids.add(track_id)
                        class_name = model.names[class_id]
                        if class_name in st.session_state.counts:
                            st.session_state.counts[class_name] += 1

            annotated_frame = draw_boxes_streamlit(frame, results, conf)

            annotated_frame_rgb = cv2.cvtColor(annotated_frame, cv2.COLOR_BGR2RGB)
            image_placeholder.image(annotated_frame_rgb, channels="RGB", use_container_width=True)

            df = pd.DataFrame(list(st.session_state.counts.items()), columns=["Material", "Count"])
            chart_placeholder.bar_chart(df.set_index("Material"))

            time.sleep(0.01)
    finally:
        cap.release()
else:
    image_placeholder.info("System standby. Activate 'Start Live Feed' in the sidebar.")
