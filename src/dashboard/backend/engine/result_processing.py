"""Map YOLO results into the dashboard's typed detection records."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from src.dashboard.backend.models import Detection, WasteClass


class ResultProcessor:
    def __init__(self, class_id_to_name: Callable[[int], str]):
        self._class_id_to_name = class_id_to_name

    def process(
        self,
        results: Any,
        conf_threshold: float = 0.5,
        reject_threshold: float | None = None,
    ) -> list[Detection]:
        detections = []
        effective_threshold = max(conf_threshold, reject_threshold or conf_threshold)

        if not results or len(results) == 0:
            return detections

        boxes = results[0].boxes
        if boxes is None or len(boxes) == 0:
            return detections

        for box in boxes:
            if box.conf is None or len(box.conf) == 0 or box.cls is None or len(box.cls) == 0:
                continue
            conf = float(box.conf[0])
            if conf < effective_threshold:
                continue

            cls_id = int(box.cls[0])
            class_name = self._class_id_to_name(cls_id)

            try:
                waste_class = WasteClass(class_name)
            except ValueError:
                continue

            x1, y1, x2, y2 = box.xyxy[0].cpu().numpy().astype(int).tolist()
            track_id = int(box.id[0]) if box.id is not None and len(box.id) > 0 else None
            detections.append(
                Detection(class_name=waste_class, confidence=conf, bbox=[x1, y1, x2, y2], track_id=track_id)
            )

        return detections
