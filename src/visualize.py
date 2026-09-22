# Shared visualization utilities for MIRA detection models.

from __future__ import annotations

import cv2
import numpy as np

# Per-class colors (BGR format for OpenCV)
CLASS_COLORS: dict[str, tuple[int, int, int]] = {
    "glass": (0, 255, 0),
    "metal": (255, 165, 0),
    "paper": (0, 0, 255),
    "plastic": (255, 255, 0),
    "trash": (128, 0, 128),
}


def class_id_to_name(class_id: int, class_names: list[str] | None = None) -> str:
    available_names = class_names or []
    if 0 <= class_id < len(available_names):
        return available_names[class_id]
    return f"class_{class_id}"


def draw_boxes(
    frame: np.ndarray,
    results,
    conf_threshold: float = 0.3,
    reject_threshold: float = 0.55,
    class_names: list[str] | None = None,
) -> np.ndarray:
    frame_height, frame_width = frame.shape[:2]

    if not results:
        return frame
    if len(results) == 0:
        return frame
    if results[0].boxes is None:
        return frame
    if len(results[0].boxes) == 0:
        return frame

    boxes = results[0].boxes
    for box in boxes:
        if box.conf is None or len(box.conf) == 0:
            continue
        confidence = float(box.conf[0])
        if confidence < conf_threshold:
            continue

        coordinates = box.xyxy[0].cpu().numpy().astype(int)
        x1, y1, x2, y2 = coordinates
        if box.cls is None or len(box.cls) == 0:
            continue
        class_id = int(box.cls[0])
        if class_names:
            available_names = class_names
        else:
            available_names = results[0].names
        class_name = class_id_to_name(class_id, available_names)

        x1 = max(0, x1)
        y1 = max(0, y1)
        x2 = min(frame_width, x2)
        y2 = min(frame_height, y2)

        if confidence >= reject_threshold:
            color = (0, 255, 0)
            label = f"{class_name} {confidence:.2f}"
        else:
            color = (0, 200, 255)
            label = f"uncertain {confidence:.2f}"

        _draw_box(frame, x1, y1, x2, y2, color, label)

    return frame


def draw_detections(
    frame: np.ndarray,
    detections: list,
    class_names: list[str] | None = None,
) -> np.ndarray:
    if not detections:
        return frame

    frame_height, frame_width = frame.shape[:2]
    for detection in detections:
        x1, y1, x2, y2 = detection.bbox
        x1 = int(x1)
        y1 = int(y1)
        x2 = int(x2)
        y2 = int(y2)
        x1 = max(0, x1)
        y1 = max(0, y1)
        x2 = min(frame_width, x2)
        y2 = min(frame_height, y2)

        if hasattr(detection.class_name, "value"):
            class_name = detection.class_name.value
        else:
            class_name = str(detection.class_name)
        color = CLASS_COLORS.get(class_name, (255, 255, 255))

        label = f"{class_name}: {detection.confidence:.2f}"
        if detection.track_id is not None:
            label = f"[{detection.track_id}] {label}"

        _draw_box(frame, x1, y1, x2, y2, color, label)

    return frame


def _draw_box(
    frame: np.ndarray,
    x1: int,
    y1: int,
    x2: int,
    y2: int,
    color: tuple[int, int, int],
    label: str,
):
    cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)

    font_face = cv2.FONT_HERSHEY_SIMPLEX
    font_scale = 0.5
    thickness = 1
    text_width, text_height = cv2.getTextSize(label, font_face, font_scale, thickness)[0]

    label_y1 = max(0, y1 - text_height - 6)
    label_x2 = min(frame.shape[1], x1 + text_width + 4)
    cv2.rectangle(frame, (x1, label_y1), (label_x2, y1), color, -1)
    text_y = max(text_height, y1 - 3)
    cv2.putText(frame, label, (x1 + 2, text_y), font_face, font_scale, (0, 0, 0), thickness)
