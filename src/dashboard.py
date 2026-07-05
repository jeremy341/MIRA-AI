import streamlit as st
import cv2
from ultralytics import YOLO
import time
import pandas as pd
import pathlib

# 1. PATH RESOLUTION
SCRIPT_DIR = pathlib.Path(__file__).resolve().parent
ROOT_DIR = SCRIPT_DIR.parent
MODELS_DIR = ROOT_DIR / "models"

# Automatically scan models directory for detection-compatible files.
if not MODELS_DIR.exists():
    st.error(f"Models directory not found at: {MODELS_DIR}")
    st.stop()

available_models = [p.name for p in MODELS_DIR.glob("*") if p.suffix in [".pt", ".tflite"]]

if not available_models:
    st.error("No compatible detection models found inside the /models folder.")
    st.stop()

# 2. STREAMLIT PAGE CONFIGURATION
st.set_page_config(page_title="MIRA Control Center", layout="wide")
st.title("MIRA - Interactive Diagnostic Dashboard")

# 3. INTERACTIVE SIDEBAR CONTROLS [2]
st.sidebar.header("Model Parameters")
selected_model = st.sidebar.selectbox("Active Model Brain", available_models, index=0)
camera_index = st.sidebar.number_input(
    "Camera Index", min_value=0, max_value=10, value=0, step=1,
    help="0 = default webcam. Change if you have multiple cameras."
)

# Slide resolution, confidence, and NMS on the fly
imgsz = st.sidebar.select_slider("Inference Resolution (imgsz)", options=[160, 224, 320, 416, 640], value=640)
conf = st.sidebar.slider("Confidence Threshold", min_value=0.05, max_value=1.00, value=0.35, step=0.05)
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


# 4. LOAD MODEL DYNAMICALLY [2]
@st.cache_resource(show_spinner="Loading model brain...")
def load_selected_model(model_name):
    path = MODELS_DIR / model_name
    return YOLO(str(path))


model = load_selected_model(selected_model)

# 5. LAYOUT
col1, col2 = st.columns([2, 1])
image_placeholder = col1.empty()
chart_placeholder = col2.empty()

# Initialize database counts in session state
if "seen_ids" not in st.session_state:
    st.session_state.seen_ids = set()

if "counts" not in st.session_state:
    st.session_state.counts = {"glass": 0, "metal": 0, "paper": 0, "plastic": 0, "trash": 0}

# 6. LIVE INFERENCE LOOP
if run_camera:
    # DirectShow backend: lower latency than MSMF on Windows, honours buffer size
    cap = cv2.VideoCapture(int(camera_index), cv2.CAP_DSHOW)
    if not cap.isOpened():
        st.error(f"Failed to open video capture device {int(camera_index)}.")
        st.session_state.run_camera = False
        st.stop()

    # MJPG decodes ~3-5x faster than YUY2 and supports higher frame-rates
    cap.set(cv2.CAP_PROP_FOURCC,       cv2.VideoWriter_fourcc(*"MJPG"))
    cap.set(cv2.CAP_PROP_FRAME_WIDTH,  640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 360)
    cap.set(cv2.CAP_PROP_FPS,          30)
    cap.set(cv2.CAP_PROP_BUFFERSIZE,   1)   # always deliver the freshest frame
    cap.set(cv2.CAP_PROP_AUTOFOCUS,    0)
    cap.set(cv2.CAP_PROP_AUTO_EXPOSURE, 1)  # manual exposure mode

    try:
        ret, frame = cap.read()
        if not ret:
            st.error("Failed to capture video.")
            st.session_state.run_camera = False
            st.stop()

        start_time = time.perf_counter()

        # Run tracking or prediction based on checkbox [2]
        if enable_tracking:
            results = model.track(frame, persist=True, imgsz=imgsz, conf=conf, iou=iou, verbose=False)
        else:
            results = model.predict(frame, imgsz=imgsz, conf=conf, iou=iou, verbose=False)

        end_time = time.perf_counter()

        # Update metrics
        latency_ms = (end_time - start_time) * 1000
        fps = 1.0 / (end_time - start_time) if (end_time - start_time) > 0 else 0

        fps_display.metric("FPS", f"{fps:.1f}")
        latency_display.metric("Latency", f"{latency_ms:.1f} ms")

        # Parse tracking results to update the bar chart
        if results[0].boxes is not None and results[0].boxes.id is not None:
            track_ids = results[0].boxes.id.cpu().numpy().astype(int)
            class_ids = results[0].boxes.cls.cpu().numpy().astype(int)

            for track_id, class_id in zip(track_ids, class_ids):
                if track_id not in st.session_state.seen_ids:
                    st.session_state.seen_ids.add(track_id)
                    class_name = model.names[class_id]
                    if class_name in st.session_state.counts:
                        st.session_state.counts[class_name] += 1

        # Plot bounding boxes natively
        annotated_frame = results[0].plot(conf=True, line_width=2, font_size=1, labels=True)

        # Convert BGR (OpenCV) to RGB (Web/Streamlit)
        annotated_frame_rgb = cv2.cvtColor(annotated_frame, cv2.COLOR_BGR2RGB)
        image_placeholder.image(annotated_frame_rgb, channels="RGB", use_container_width=True)

        # Plot real-time sorted inventory chart
        df = pd.DataFrame(list(st.session_state.counts.items()), columns=["Material", "Count"])
        chart_placeholder.bar_chart(df.set_index("Material"))

        time.sleep(0.03)
        if st.session_state.get("run_camera", False):
            request_rerun()
    finally:
        cap.release()
else:
    image_placeholder.info("System standby. Activate 'Start Live Feed' in the sidebar.")
