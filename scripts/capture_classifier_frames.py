import argparse
import sys
import platform
from pathlib import Path
import cv2
import datetime

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
from config import CLASS_NAMES, DATA_CLASSES_DIR as DATA_DIR
from config import setup_camera_properties
from logger import logger


def main() -> None:
    parser = argparse.ArgumentParser(description="MIRA Frame Capture Tool")
    parser.add_argument("--camera", type=int, default=0, help="Camera device index (default: 0).")
    parser.add_argument(
        "--resolution",
        type=str,
        default="640x360",
        choices=["640x360", "1280x720", "1920x1080"],
        help="Camera capture resolution (default: 640x360). Use 640x360 when collecting "
        "data for models trained on that resolution.",
    )
    args = parser.parse_args()
    cam_w, cam_h = (int(v) for v in args.resolution.split("x"))

    # Use DirectShow on Windows for lower latency; default backend elsewhere
    backend = cv2.CAP_DSHOW if platform.system() == "Windows" else 0
    logger.info("Opening camera %d at %dx%d...", args.camera, cam_w, cam_h)
    cap = cv2.VideoCapture(args.camera, backend)
    if not cap.isOpened():
        raise RuntimeError(f"Failed to open webcam index {args.camera}.")

    setup_camera_properties(cap, cam_w, cam_h)

    warmup = 10
    logger.info("Warming up camera (%d frames)...", warmup)
    for _ in range(warmup):
        cap.read()

    classes = {str(i + 1): (name, DATA_DIR / name) for i, name in enumerate(CLASS_NAMES)}
    for _, folder in classes.values():
        folder.mkdir(parents=True, exist_ok=True)

    logger.info("MIRA Camera Frame Capture Active.")
    logger.info("Press 1 (Glass), 2 (Metal), 3 (Paper), 4 (Plastic), or 5 (Trash) to save a frame.")
    logger.info("Press 'q' to quit.")

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                logger.warning("Camera read failed; retrying...")
                continue

            display_frame = frame.copy()
            cv2.putText(
                display_frame,
                "1: Glass | 2: Metal | 3: Paper | 4: Plastic | 5: Trash | q: Quit",
                (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (0, 255, 0),
                2,
            )
            cv2.putText(
                display_frame,
                f"Camera: {args.camera} | {cam_w}x{cam_h}",
                (10, 60),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (0, 200, 255),
                1,
            )
            cv2.imshow("MIRA Frame Capture", display_frame)

            key = cv2.waitKey(1) & 0xFF

            if key == ord("q"):
                break

            try:
                key_char = chr(key)
                if key_char in classes:
                    label, folder = classes[key_char]
                    filename = f"{label}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S_%f')}.jpg"
                    filepath = folder / filename
                    cv2.imwrite(str(filepath), frame)
                    logger.info("Saved: %s", filepath)
            except ValueError:
                pass
    finally:
        cap.release()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
