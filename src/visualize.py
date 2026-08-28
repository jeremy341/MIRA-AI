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
    names = class_names or []
    return f"class_{class_id}" if not 0 <= class_id < len(names) else names[class_id]


def draw_boxes(
    frame: np.ndarray,
    results,
    conf_threshold: float = 0.3,
    reject_threshold: float = 0.55,
    class_names: list[str] | None = None,
) -> np.ndarray:
    h, w = frame.shape[:2]

    if not results or len(results) == 0 or results[0].boxes is None or len(results[0].boxes) == 0:
        return frame

    boxes = results[0].boxes
    for box in boxes:
        if box.conf is None or len(box.conf) == 0:
            continue
        conf = float(box.conf[0])
        if conf < conf_threshold:
            continue

        x1, y1, x2, y2 = box.xyxy[0].cpu().numpy().astype(int)
        if box.cls is None or len(box.cls) == 0:
            continue
        cls_id = int(box.cls[0])
        names = class_names if class_names else results[0].names
        cls_name = class_id_to_name(cls_id, names)

        x1, y1 = max(0, x1), max(0, y1)
        x2, y2 = min(w, x2), min(h, y2)

        if conf >= reject_threshold:
            color = (0, 255, 0)
            label = f"{cls_name} {conf:.2f}"
        else:
            color = (0, 200, 255)
            label = f"uncertain {conf:.2f}"

        _draw_box(frame, x1, y1, x2, y2, color, label)

    return frame


def draw_detections(
    frame: np.ndarray,
    detections: list,
    class_names: list[str] | None = None,
) -> np.ndarray:
    if not detections:
        return frame

    h, w = frame.shape[:2]
    for det in detections:
        x1, y1, x2, y2 = det.bbox
        x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)
        x1, y1 = max(0, x1), max(0, y1)
        x2, y2 = min(w, x2), min(h, y2)

        class_name = det.class_name.value if hasattr(det.class_name, "value") else str(det.class_name)
        color = CLASS_COLORS.get(class_name, (255, 255, 255))

        label = f"{class_name}: {det.confidence:.2f}"
        if det.track_id is not None:
            label = f"[{det.track_id}] {label}"

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

    font = cv2.FONT_HERSHEY_SIMPLEX
    font_scale = 0.5
    thickness = 1
    text_size = cv2.getTextSize(label, font, font_scale, thickness)[0]

    label_y1 = max(0, y1 - text_size[1] - 6)
    label_x2 = min(frame.shape[1], x1 + text_size[0] + 4)
    cv2.rectangle(frame, (x1, label_y1), (label_x2, y1), color, -1)
    text_y = max(text_size[1], y1 - 3)
    cv2.putText(frame, label, (x1 + 2, text_y), font, font_scale, (0, 0, 0), thickness)
