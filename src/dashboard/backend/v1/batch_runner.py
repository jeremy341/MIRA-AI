"""Background workers for video and image batch sessions."""

from __future__ import annotations

import json
import shutil
import threading
import time
import uuid
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import cv2
import numpy as np
from PIL import Image, ImageOps, UnidentifiedImageError

from src.config import CLASS_NAMES

from .model_runner import predict_frame
from .state import get_db, get_events, get_jobs

MAX_IMAGE_PIXELS = 16_000_000
_DB_BATCH_SIZE = 500
_resource_lock = threading.Lock()
_resources: dict[str, _JobResource] = {}


@dataclass
class _JobResource:
    session_id: str
    temporary_path: Path | None
    started: bool = False
    completed: bool = False


class _SessionWriter:
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.processed = 0
        self.skipped = 0
        self.total_detections = 0
        self.class_counts = Counter({name: 0 for name in CLASS_NAMES})
        self._detections: list[tuple[Any, ...]] = []
        self._metrics: list[tuple[Any, ...]] = []

    def add_frame(
        self,
        frame_index: int,
        ts: float,
        detections,
        latency_ms: float,
        fps: float | None = None,
        record_metric: bool = True,
    ) -> None:
        self.processed += 1
        self.total_detections += len(detections)
        for detection in detections:
            self.class_counts[detection.class_name] += 1
            self._detections.append(
                (
                    self.session_id,
                    ts,
                    frame_index,
                    detection.class_name,
                    detection.confidence,
                    *detection.bbox,
                    detection.track_id,
                )
            )
        if record_metric:
            self._metrics.append((self.session_id, ts, fps, latency_ms))
        if len(self._detections) >= _DB_BATCH_SIZE or len(self._metrics) >= _DB_BATCH_SIZE:
            self.flush()

    def flush(self) -> None:
        if not self._detections and not self._metrics:
            return
        db = get_db()
        with db.transaction():
            if self._detections:
                db.executemany(
                    "INSERT INTO detections (session_id, ts, frame_index, class_name, confidence, x1, y1, x2, y2, track_id)"
                    " VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    self._detections,
                )
            if self._metrics:
                db.executemany(
                    "INSERT INTO metrics (session_id, ts, fps, latency_ms) VALUES (?, ?, ?, ?)",
                    self._metrics,
                )
        self._detections.clear()
        self._metrics.clear()

    def result(self, duration_seconds: float, *, errors: list[dict[str, str]] | None = None) -> dict[str, Any]:
        result = {
            "session_id": self.session_id,
            "processed": self.processed,
            "skipped": self.skipped,
            "total_detections": self.total_detections,
            "class_counts": dict(self.class_counts),
            "duration_seconds": round(duration_seconds, 3),
        }
        if errors is not None:
            result["errors"] = errors[:20]
        return result


def decode_image(path: str | Path) -> np.ndarray:
    """Decode a JPEG or PNG, applying EXIF orientation and the 16 MP limit."""
    if Path(path).is_symlink():
        raise ValueError("Symbolic links are not allowed in an image batch.")
    try:
        with Image.open(path) as opened:
            if opened.format not in {"JPEG", "PNG"}:
                raise ValueError("Choose a JPEG or PNG image.")
            image = ImageOps.exif_transpose(opened)
            width, height = image.size
            if width <= 0 or height <= 0 or width * height > MAX_IMAGE_PIXELS:
                raise ValueError("Each image must be 16 megapixels or smaller.")
            image.load()
            rgb = np.asarray(image.convert("RGB"), dtype=np.uint8)
    except (UnidentifiedImageError, OSError, Image.DecompressionBombError) as exc:
        raise ValueError("The image could not be decoded.") from exc
    return cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)


def _create_session(source: str, model_name: str, name: str | None, config: dict[str, Any]) -> tuple[str, float]:
    started_at_ts = time.time()
    session_id = uuid.uuid4().hex
    session_name = (
        name or f"{source.title()} batch {datetime.fromtimestamp(started_at_ts, timezone.utc):%Y-%m-%d %H:%M}"
    )
    get_db().execute(
        "INSERT INTO sessions (id, name, source, model_name, status, started_at_ts, config_json)"
        " VALUES (?, ?, ?, ?, 'active', ?, ?)",
        (session_id, session_name, source, model_name, started_at_ts, json.dumps(config)),
    )
    get_events().publish("session_started", {"session_id": session_id, "source": source, "name": session_name})
    return session_id, started_at_ts


def _finish_session(session_id: str, status: str) -> None:
    ended_at_ts = time.time()
    cursor = get_db().execute(
        "UPDATE sessions SET status=?, ended_at_ts=? WHERE id=? AND status='active'",
        (status, ended_at_ts, session_id),
    )
    if cursor.rowcount:
        get_events().publish("session_stopped", {"session_id": session_id, "status": status})


def _cleanup(path: Path) -> None:
    if path.is_dir():
        shutil.rmtree(path, ignore_errors=True)
    else:
        path.unlink(missing_ok=True)


def _register_resource(job_id: str, job, resource: _JobResource) -> None:
    with _resource_lock:
        if job.status in {"completed", "failed", "cancelled"} or resource.completed:
            return
        _resources[job_id] = resource


def _mark_started(resource: _JobResource) -> None:
    with _resource_lock:
        if resource.completed:
            return
        resource.started = True


def _release_resource(job_id: str, resource: _JobResource) -> None:
    with _resource_lock:
        if _resources.get(job_id) is resource:
            _resources.pop(job_id, None)
        resource.completed = True


def cancel_if_not_started(job_id: str) -> bool:
    """Finalize and clean a queued batch cancelled before its worker begins."""
    with _resource_lock:
        resource = _resources.get(job_id)
        if resource is None or resource.started or resource.completed:
            return False
        _resources.pop(job_id, None)
        resource.completed = True
    _finish_session(resource.session_id, "completed")
    if resource.temporary_path is not None:
        _cleanup(resource.temporary_path)
    return True


def submit_video(
    *,
    temporary_path: Path,
    video_path: Path,
    model_name: str,
    confidence: float,
    frame_stride: int,
    name: str | None,
    frame_count: int,
    fps: float,
) -> tuple[Any, str]:
    session_id, session_started_at = _create_session(
        "video", model_name, name, {"confidence": confidence, "frame_stride": frame_stride}
    )
    resource = _JobResource(session_id, temporary_path)

    def work(ctx):
        _mark_started(resource)
        capture = None
        writer = _SessionWriter(session_id)
        started = time.monotonic()
        frames_seen = 0
        last_metric_time = -1.0
        try:
            if ctx.cancelled.is_set():
                _finish_session(session_id, "completed")
                return writer.result(time.monotonic() - started)
            capture = cv2.VideoCapture(str(video_path))
            if not capture.isOpened():
                raise RuntimeError("The video could not be opened for processing.")

            while frames_seen < frame_count:
                if ctx.cancelled.is_set():
                    break
                ok, frame = capture.read()
                if not ok:
                    if not ctx.cancelled.is_set():
                        raise RuntimeError("The video ended before all expected frames could be decoded.")
                    break
                frame_index = frames_seen
                frames_seen += 1
                if frame_index % frame_stride == 0:
                    prediction = predict_frame(model_name, frame, confidence=confidence)
                    frame_time = frame_index / fps
                    frame_ts = session_started_at + frame_time
                    record_metric = last_metric_time < 0 or frame_time - last_metric_time >= 1.0
                    writer.add_frame(
                        frame_index,
                        frame_ts,
                        prediction.detections,
                        prediction.latency_ms,
                        fps=fps,
                        record_metric=record_metric,
                    )
                    if record_metric:
                        last_metric_time = frame_time
                else:
                    writer.skipped += 1
                ctx.progress(frames_seen / frame_count, f"Frame {frames_seen} of {frame_count}")

            writer.skipped = max(writer.skipped, frame_count - writer.processed)
            writer.flush()
            status = "completed"
            _finish_session(session_id, status)
            if not ctx.cancelled.is_set():
                ctx.progress(1.0, f"Processed {writer.processed} frames")
            return writer.result(time.monotonic() - started)
        except Exception:
            _finish_session(session_id, "failed")
            raise
        finally:
            if capture is not None:
                capture.release()
            _cleanup(temporary_path)
            _release_resource(ctx.job_id, resource)

    try:
        job = get_jobs().submit("batch-video", work, title=name or "Video batch")
        _register_resource(job.id, job, resource)
        return job, session_id
    except Exception:
        _finish_session(session_id, "failed")
        _cleanup(temporary_path)
        raise


def submit_images(
    *,
    temporary_path: Path | None,
    image_paths: list[Path],
    model_name: str,
    confidence: float,
    name: str | None,
) -> tuple[Any, str]:
    session_id, session_started_at = _create_session(
        "batch", model_name, name, {"confidence": confidence, "image_count": len(image_paths)}
    )
    resource = _JobResource(session_id, temporary_path)

    def work(ctx):
        _mark_started(resource)
        writer = _SessionWriter(session_id)
        errors: list[dict[str, str]] = []
        started = time.monotonic()
        try:
            total = len(image_paths)
            for frame_index, image_path in enumerate(image_paths):
                if ctx.cancelled.is_set():
                    break
                frame_ts = session_started_at + frame_index * 0.001
                try:
                    frame = decode_image(image_path)
                    prediction = predict_frame(model_name, frame, confidence=confidence)
                    writer.add_frame(frame_index, frame_ts, prediction.detections, prediction.latency_ms)
                except Exception as exc:
                    writer.skipped += 1
                    if len(errors) < 20:
                        errors.append({"file": image_path.name, "error": str(exc) or exc.__class__.__name__})
                ctx.progress((frame_index + 1) / total, f"Image {frame_index + 1} of {total}")

            writer.skipped = max(writer.skipped, total - writer.processed)
            writer.flush()
            _finish_session(session_id, "completed")
            if not ctx.cancelled.is_set():
                ctx.progress(1.0, f"Processed {writer.processed} images")
            return writer.result(time.monotonic() - started, errors=errors)
        except Exception:
            _finish_session(session_id, "failed")
            raise
        finally:
            if temporary_path is not None:
                _cleanup(temporary_path)
            _release_resource(ctx.job_id, resource)

    try:
        job = get_jobs().submit("batch-images", work, title=name or "Image batch")
        _register_resource(job.id, job, resource)
        return job, session_id
    except Exception:
        _finish_session(session_id, "failed")
        if temporary_path is not None:
            _cleanup(temporary_path)
        raise
