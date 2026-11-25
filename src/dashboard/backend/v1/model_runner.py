"""Shared model loading and inference for compare, benchmark and batch.

Coordinator-owned. Use this instead of `camera_service` internals (which are being refactored).
Tests inject a fake model with `set_model_factory(lambda path, task: FakeModel())`; a fake only needs
`predict(frame, imgsz=, conf=, iou=, verbose=)` returning ultralytics-style results.
"""

from __future__ import annotations

import threading
import time
from collections import OrderedDict
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np

from src.config import CLASS_NAMES, DETECTION_DIR, get_tflite_imgsz

MODEL_SUFFIXES = (".pt", ".tflite", ".onnx")
CACHE_SIZE = 2


@dataclass(frozen=True)
class RunnerDetection:
    class_name: str
    confidence: float
    bbox: tuple[int, int, int, int]  # x1, y1, x2, y2 in pixels of the frame given to predict()
    track_id: int | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "class_name": self.class_name,
            "confidence": round(self.confidence, 4),
            "bbox": list(self.bbox),
            "track_id": self.track_id,
        }


@dataclass(frozen=True)
class RunnerResult:
    detections: list[RunnerDetection]
    latency_ms: float


def _default_factory(path: str, task: str) -> Any:
    from ultralytics import YOLO

    return YOLO(path, task=task)


_factory: Callable[[str, str], Any] = _default_factory
_cache: OrderedDict[str, tuple[Any, int]] = OrderedDict()
_lock = threading.RLock()


def set_model_factory(factory: Callable[[str, str], Any] | None) -> None:
    """Replace the YOLO constructor (tests). Pass None to restore the default. Clears the cache."""
    global _factory
    with _lock:
        _factory = factory or _default_factory
        _cache.clear()


def list_models() -> list[dict[str, Any]]:
    """Detector files in the models directory (same names as GET /api/models)."""
    found = []
    if not DETECTION_DIR.exists():
        return found
    for path in sorted(DETECTION_DIR.iterdir()):
        if path.is_file() and path.suffix.lower() in MODEL_SUFFIXES:
            found.append({"name": path.name, "size_mb": round(path.stat().st_size / 1024 / 1024, 2)})
    return found


def resolve_model_path(name: str) -> Path:
    """Map a bare file name to a path inside the detection directory. Raises ValueError/FileNotFoundError."""
    if not name or any(sep in name for sep in ("/", "\\", "..")):
        raise ValueError(f"Invalid model name: {name!r}")
    root = DETECTION_DIR.resolve()
    path = (DETECTION_DIR / name).resolve()
    if path.parent != root or path.suffix.lower() not in MODEL_SUFFIXES:
        raise ValueError(f"Invalid model name: {name!r}")
    if not path.exists():
        raise FileNotFoundError(f"Model not found: {name}")
    return path


def load_model(name: str) -> tuple[Any, int]:
    """Return `(model, imgsz)`, cached (most recent `CACHE_SIZE` models stay loaded)."""
    path = resolve_model_path(name)
    with _lock:
        if name in _cache:
            _cache.move_to_end(name)
            return _cache[name]
        imgsz = get_tflite_imgsz(path) if path.suffix.lower() == ".tflite" else 640
        entry = (_factory(str(path), "detect"), imgsz)
        _cache[name] = entry
        while len(_cache) > CACHE_SIZE:
            _cache.popitem(last=False)
        return entry


def predict_frame(name: str, frame_bgr: np.ndarray, confidence: float = 0.25, iou: float = 0.45) -> RunnerResult:
    """Run one BGR frame through the named model. Inference is serialised per process."""
    model, imgsz = load_model(name)
    start = time.perf_counter()
    with _lock:
        results = model.predict(frame_bgr, imgsz=imgsz, conf=confidence, iou=iou, verbose=False)
    latency_ms = (time.perf_counter() - start) * 1000
    detections: list[RunnerDetection] = []
    for result in results:
        boxes = getattr(result, "boxes", None)
        if boxes is None:
            continue
        for index in range(len(boxes)):
            class_id = int(boxes.cls[index])
            x1, y1, x2, y2 = (int(round(float(v))) for v in boxes.xyxy[index])
            track = None
            if getattr(boxes, "id", None) is not None:
                track = int(boxes.id[index])
            detections.append(
                RunnerDetection(
                    class_name=CLASS_NAMES[class_id] if 0 <= class_id < len(CLASS_NAMES) else f"class_{class_id}",
                    confidence=float(boxes.conf[index]),
                    bbox=(x1, y1, x2, y2),
                    track_id=track,
                )
            )
    return RunnerResult(detections=detections, latency_ms=latency_ms)
