"""Shared visualization utilities for MIRA detection models."""
import cv2
import numpy as np


def draw_boxes(frame: np.ndarray, results, conf_threshold: float = 0.3) -> np.ndarray:
    """Draw bounding boxes on a frame from YOLO detection results."""
    h, w = frame.shape[:2]

    if results[0].boxes is None or len(results[0].boxes) == 0:
        return frame

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
        cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)

        label = f"{cls_name} {conf:.2f}"
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 0.6
        thickness = 2
        text_size = cv2.getTextSize(label, font, font_scale, thickness)[0]

        cv2.rectangle(frame, (x1, y1 - 25), (x1 + text_size[0], y1), color, -1)
        cv2.putText(frame, label, (x1, y1 - 5), font, font_scale, (0, 0, 0), thickness)

    return frame
