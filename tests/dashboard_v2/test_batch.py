"""Integration tests for video and image batch processing."""

from __future__ import annotations

import io
import threading
import time
from contextlib import asynccontextmanager
from pathlib import Path

import cv2
import numpy as np
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from PIL import Image

from src.dashboard.backend import v1
from src.dashboard.backend.v1 import model_runner
from src.dashboard.backend.v1.state import get_db


class _Boxes:
    def __init__(self, class_id: int):
        self.cls = [class_id]
        self.conf = [0.9]
        self.xyxy = [[1, 2, 8, 9]]
        self.id = None

    def __len__(self):
        return 1


class _Result:
    def __init__(self, class_id: int):
        self.boxes = _Boxes(class_id)


class _FakeModel:
    def predict(self, frame, imgsz, conf, iou, verbose):
        return [_Result(0)]


class _FailingModel:
    def predict(self, frame, imgsz, conf, iou, verbose):
        raise RuntimeError("synthetic video inference failure")


class _PixelModel:
    def predict(self, frame, imgsz, conf, iou, verbose):
        blue, green, red = (int(channel) for channel in frame[0, 0])
        if red > 200:
            raise RuntimeError("synthetic inference failure")
        return [_Result(1 if green > 200 else 0)]


class _BlockingModel:
    def __init__(self, started: threading.Event, release: threading.Event):
        self.started = started
        self.release = release

    def predict(self, frame, imgsz, conf, iou, verbose):
        self.started.set()
        self.release.wait(5)
        return [_Result(0)]


class _EventRecorder:
    def __init__(self):
        self.events: list[tuple[str, dict]] = []

    def publish(self, event_type: str, data: dict):
        self.events.append((event_type, data))


@pytest.fixture
def fake_models(tmp_path, monkeypatch):
    (tmp_path / "demo.pt").write_bytes(b"fake weights")
    monkeypatch.setattr(model_runner, "DETECTION_DIR", tmp_path)
    model_runner.set_model_factory(lambda path, task: _FakeModel())
    yield
    model_runner.set_model_factory(None)


@pytest.fixture
def api_client(fake_models):
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        await v1.startup()
        yield
        await v1.shutdown()

    app = FastAPI(lifespan=lifespan)
    app.include_router(v1.api_router, prefix="/api/v1")
    with TestClient(app) as client:
        yield client


def _wait_for_job(client: TestClient, job_id: str, timeout: float = 10.0) -> dict:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        response = client.get(f"/api/v1/jobs/{job_id}")
        if response.status_code == 200:
            job = response.json()
            if job["status"] in {"completed", "failed", "cancelled"}:
                return job
        time.sleep(0.01)
    raise AssertionError(f"Job {job_id} did not finish")


def _png_bytes(color: tuple[int, int, int] = (0, 0, 255)) -> bytes:
    image = Image.new("RGB", (12, 10), color)
    payload = io.BytesIO()
    image.save(payload, format="PNG")
    return payload.getvalue()


def _make_video(tmp_path: Path, frame_count: int = 8) -> bytes:
    path = tmp_path / "sample.avi"
    writer = cv2.VideoWriter(str(path), cv2.VideoWriter_fourcc(*"MJPG"), 4.0, (24, 16))
    if not writer.isOpened():
        writer.release()
        pytest.skip("OpenCV MJPG AVI encoding is unavailable")
    for index in range(frame_count):
        writer.write(np.full((16, 24, 3), index * 10, dtype=np.uint8))
    writer.release()
    return path.read_bytes()


def _wait_until(predicate, timeout: float = 5.0) -> bool:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if predicate():
            return True
        time.sleep(0.01)
    return False


def test_video_batch_records_sampled_frames_metrics_and_cleans_temp_files(api_client, tmp_path, monkeypatch):
    from src.dashboard.backend.v1.routers import batch
    from src.dashboard.backend.v1 import batch_runner

    monkeypatch.setattr(batch.tempfile, "tempdir", str(tmp_path))
    event_recorder = _EventRecorder()
    monkeypatch.setattr(batch_runner, "get_events", lambda: event_recorder)
    content = _make_video(tmp_path)
    response = api_client.post(
        "/api/v1/batch/video",
        data={"model_name": "demo.pt", "confidence": "0.3", "frame_stride": "2", "name": "Test clip"},
        files={"video": ("sample.avi", content, "video/x-msvideo")},
    )
    assert response.status_code == 202, response.text
    payload = response.json()
    job = _wait_for_job(api_client, payload["job_id"])
    assert job["status"] == "completed"
    assert job["progress"] == 1.0
    assert job["result"]["session_id"] == payload["session_id"]
    assert job["result"]["processed"] == 4
    assert job["result"]["skipped"] == 4
    assert job["result"]["total_detections"] == 4
    assert job["result"]["class_counts"] == {"glass": 4, "metal": 0, "paper": 0, "plastic": 0, "trash": 0}

    db = get_db()
    session = db.query_one("SELECT * FROM sessions WHERE id=?", (payload["session_id"],))
    assert session["source"] == "video" and session["status"] == "completed"
    detections = db.query("SELECT * FROM detections WHERE session_id=? ORDER BY frame_index", (payload["session_id"],))
    assert [row["frame_index"] for row in detections] == [0, 2, 4, 6]
    assert all(abs(row["ts"] - (session["started_at_ts"] + row["frame_index"] / 4)) < 0.01 for row in detections)
    assert len(db.query("SELECT * FROM metrics WHERE session_id=?", (payload["session_id"],))) == 2
    assert not list(tmp_path.glob("mira-batch-*"))
    assert [event[0] for event in event_recorder.events] == ["session_started", "session_stopped"]


def test_video_validation_rejects_bad_model_type_and_undecodable_file(api_client, tmp_path):
    valid_video = _make_video(tmp_path)
    bad_model = api_client.post(
        "/api/v1/batch/video",
        data={"model_name": "missing.pt"},
        files={"video": ("sample.avi", valid_video, "video/x-msvideo")},
    )
    assert bad_model.status_code == 422
    wrong_type = api_client.post(
        "/api/v1/batch/video",
        data={"model_name": "demo.pt"},
        files={"video": ("sample.txt", b"not a movie", "text/plain")},
    )
    assert wrong_type.status_code == 415
    undecodable = api_client.post(
        "/api/v1/batch/video",
        data={"model_name": "demo.pt"},
        files={"video": ("broken.avi", b"not a movie", "video/x-msvideo")},
    )
    assert undecodable.status_code == 422
    bad_stride = api_client.post(
        "/api/v1/batch/video",
        data={"model_name": "demo.pt", "frame_stride": "121"},
        files={"video": ("sample.avi", valid_video, "video/x-msvideo")},
    )
    assert bad_stride.status_code == 422


def test_video_size_cap_rejects_upload_before_creating_a_session(api_client, monkeypatch):
    from src.dashboard.backend.v1.routers import batch

    monkeypatch.setattr(batch, "MAX_VIDEO_BYTES", 8)
    response = api_client.post(
        "/api/v1/batch/video",
        data={"model_name": "demo.pt"},
        files={"video": ("large.avi", b"123456789", "video/x-msvideo")},
    )
    assert response.status_code == 413
    assert get_db().query("SELECT * FROM sessions") == []


def test_video_cancel_marks_session_completed_and_finishes_job_as_cancelled(api_client, tmp_path, monkeypatch):
    from src.dashboard.backend.v1.routers import batch
    from src.dashboard.backend.v1 import batch_runner

    started, release = threading.Event(), threading.Event()
    model_runner.set_model_factory(lambda path, task: _BlockingModel(started, release))
    monkeypatch.setattr(batch.tempfile, "tempdir", str(tmp_path))
    content = _make_video(tmp_path, frame_count=20)
    original_capture = cv2.VideoCapture
    captures = []

    class CaptureSpy:
        def __init__(self, *args, **kwargs):
            self.inner = original_capture(*args, **kwargs)
            self.released = False
            captures.append(self)

        def __getattr__(self, name):
            return getattr(self.inner, name)

        def release(self):
            self.released = True
            self.inner.release()

    monkeypatch.setattr(batch_runner.cv2, "VideoCapture", CaptureSpy)
    response = api_client.post(
        "/api/v1/batch/video",
        data={"model_name": "demo.pt", "frame_stride": "1"},
        files={"video": ("sample.avi", content, "video/x-msvideo")},
    )
    assert response.status_code == 202
    payload = response.json()
    try:
        assert started.wait(5)
        cancelled = api_client.post(f"/api/v1/jobs/{payload['job_id']}/cancel")
        assert cancelled.status_code == 200
    finally:
        release.set()

    job = _wait_for_job(api_client, payload["job_id"])
    assert job["status"] == "cancelled"
    session = get_db().query_one("SELECT status FROM sessions WHERE id=?", (payload["session_id"],))
    assert session["status"] == "completed"
    assert not list(tmp_path.glob("mira-batch-*"))
    assert len(captures) == 2 and all(capture.released for capture in captures)


def test_video_failure_marks_session_failed_and_removes_temp_file(api_client, tmp_path, monkeypatch):
    from src.dashboard.backend.v1.routers import batch

    model_runner.set_model_factory(lambda path, task: _FailingModel())
    monkeypatch.setattr(batch.tempfile, "tempdir", str(tmp_path))
    content = _make_video(tmp_path)
    response = api_client.post(
        "/api/v1/batch/video",
        data={"model_name": "demo.pt"},
        files={"video": ("sample.avi", content, "video/x-msvideo")},
    )
    assert response.status_code == 202
    payload = response.json()
    job = _wait_for_job(api_client, payload["job_id"])
    assert job["status"] == "failed"
    assert "synthetic video inference failure" in job["error"]
    session = get_db().query_one("SELECT status FROM sessions WHERE id=?", (payload["session_id"],))
    assert session["status"] == "failed"
    assert not list(tmp_path.glob("mira-batch-*"))


def test_multipart_image_batch_persists_rows_and_cleans_temp_files(api_client, tmp_path, monkeypatch):
    from src.dashboard.backend.v1.routers import batch

    monkeypatch.setattr(batch.tempfile, "tempdir", str(tmp_path))
    response = api_client.post(
        "/api/v1/batch/images",
        data={"model_name": "demo.pt", "name": "Photo set"},
        files=[
            ("images", ("a.png", _png_bytes(), "image/png")),
            ("images", ("b.png", _png_bytes((0, 255, 0)), "image/png")),
        ],
    )
    assert response.status_code == 202, response.text
    payload = response.json()
    job = _wait_for_job(api_client, payload["job_id"])
    assert job["status"] == "completed" and job["progress"] == 1.0
    assert job["result"]["processed"] == 2
    assert job["result"]["skipped"] == 0
    assert job["result"]["total_detections"] == 2
    assert job["result"]["errors"] == []

    db = get_db()
    session = db.query_one("SELECT * FROM sessions WHERE id=?", (payload["session_id"],))
    assert session["source"] == "batch" and session["status"] == "completed"
    rows = db.query("SELECT * FROM detections WHERE session_id=? ORDER BY frame_index", (payload["session_id"],))
    assert [row["frame_index"] for row in rows] == [0, 1]
    assert abs(rows[1]["ts"] - rows[0]["ts"] - 0.001) < 0.00001
    assert not list(tmp_path.glob("mira-batch-*"))


def test_image_inference_failures_are_counted_without_failing_the_job(api_client):
    model_runner.set_model_factory(lambda path, task: _PixelModel())
    response = api_client.post(
        "/api/v1/batch/images",
        data={"model_name": "demo.pt"},
        files=[
            ("images", ("good.png", _png_bytes((0, 255, 0)), "image/png")),
            ("images", ("bad.png", _png_bytes((255, 0, 0)), "image/png")),
        ],
    )
    assert response.status_code == 202
    job = _wait_for_job(api_client, response.json()["job_id"])
    assert job["status"] == "completed"
    assert job["result"]["processed"] == 1
    assert job["result"]["skipped"] == 1
    assert len(job["result"]["errors"]) == 1
    assert "synthetic inference failure" in job["result"]["errors"][0]["error"]


def test_directory_batch_naturally_sorts(api_client, tmp_path):
    model_runner.set_model_factory(lambda path, task: _PixelModel())
    folder = tmp_path / "pictures"
    folder.mkdir()
    (folder / "img10.png").write_bytes(_png_bytes((0, 0, 255)))
    (folder / "img2.png").write_bytes(_png_bytes((0, 255, 0)))
    response = api_client.post(
        "/api/v1/batch/images",
        json={"directory": str(folder), "recursive": False, "model_name": "demo.pt"},
    )
    assert response.status_code == 202, response.text
    job = _wait_for_job(api_client, response.json()["job_id"])
    assert job["status"] == "completed"
    assert job["result"]["processed"] == 2
    rows = get_db().query(
        "SELECT frame_index, class_name FROM detections WHERE session_id=? ORDER BY frame_index",
        (response.json()["session_id"],),
    )
    assert [(row["frame_index"], row["class_name"]) for row in rows] == [(0, "metal"), (1, "glass")]


def test_directory_batch_ignores_symlink_files(api_client, tmp_path):
    folder = tmp_path / "pictures"
    folder.mkdir()
    (folder / "keep.png").write_bytes(_png_bytes())
    external = tmp_path / "outside.png"
    external.write_bytes(_png_bytes())
    try:
        (folder / "linked.png").symlink_to(external)
    except OSError:
        pytest.skip("File symlinks are unavailable on this platform")

    response = api_client.post(
        "/api/v1/batch/images",
        json={"directory": str(folder), "recursive": True, "model_name": "demo.pt"},
    )
    assert response.status_code == 202, response.text
    job = _wait_for_job(api_client, response.json()["job_id"])
    assert job["status"] == "completed"
    assert job["result"]["processed"] == 1


def test_directory_batch_recurses_into_real_subfolders(api_client, tmp_path):
    folder = tmp_path / "pictures"
    nested = folder / "subfolder"
    nested.mkdir(parents=True)
    (nested / "one.png").write_bytes(_png_bytes())
    response = api_client.post(
        "/api/v1/batch/images",
        json={"directory": str(folder), "recursive": True, "model_name": "demo.pt"},
    )
    assert response.status_code == 202, response.text
    job = _wait_for_job(api_client, response.json()["job_id"])
    assert job["status"] == "completed"
    assert job["result"]["processed"] == 1


def test_directory_validation_rejects_non_directory_and_file_limit(api_client, tmp_path, monkeypatch):
    from src.dashboard.backend.v1.routers import batch

    not_directory = api_client.post(
        "/api/v1/batch/images",
        json={"directory": str(tmp_path / "missing"), "model_name": "demo.pt"},
    )
    assert not_directory.status_code == 422

    folder = tmp_path / "too-many"
    folder.mkdir()
    (folder / "a.png").write_bytes(_png_bytes())
    (folder / "b.jpg").write_bytes(_png_bytes())
    monkeypatch.setattr(batch, "MAX_DIRECTORY_IMAGES", 1)
    too_many = api_client.post(
        "/api/v1/batch/images",
        json={"directory": str(folder), "model_name": "demo.pt"},
    )
    assert too_many.status_code == 413


def test_image_upload_rejects_mode_mixing_type_and_size_caps(api_client, monkeypatch):
    from src.dashboard.backend.v1.routers import batch

    mixed = api_client.post(
        "/api/v1/batch/images",
        data={"model_name": "demo.pt", "directory": "C:/photos"},
        files={"images": ("a.png", _png_bytes(), "image/png")},
    )
    assert mixed.status_code == 422

    wrong_type = api_client.post(
        "/api/v1/batch/images",
        data={"model_name": "demo.pt"},
        files={"images": ("a.gif", _png_bytes(), "image/gif")},
    )
    assert wrong_type.status_code == 415

    monkeypatch.setattr(batch, "MAX_IMAGE_BYTES", 16)
    too_large = api_client.post(
        "/api/v1/batch/images",
        data={"model_name": "demo.pt"},
        files={"images": ("a.png", _png_bytes(), "image/png")},
    )
    assert too_large.status_code == 413

    monkeypatch.setattr(batch, "MAX_MULTIPART_IMAGES", 1)
    too_many_files = api_client.post(
        "/api/v1/batch/images",
        data={"model_name": "demo.pt"},
        files=[
            ("images", ("a.png", _png_bytes(), "image/png")),
            ("images", ("b.png", _png_bytes(), "image/png")),
        ],
    )
    assert too_many_files.status_code == 413


def test_image_validation_rejects_bad_model_invalid_confidence_and_bad_content(api_client):
    bad_model = api_client.post(
        "/api/v1/batch/images",
        data={"model_name": "missing.pt"},
        files={"images": ("a.png", _png_bytes(), "image/png")},
    )
    assert bad_model.status_code == 422
    bad_confidence = api_client.post(
        "/api/v1/batch/images",
        data={"model_name": "demo.pt", "confidence": "1.5"},
        files={"images": ("a.png", _png_bytes(), "image/png")},
    )
    assert bad_confidence.status_code == 422
    bad_content = api_client.post(
        "/api/v1/batch/images",
        data={"model_name": "demo.pt"},
        files={"images": ("a.png", b"not an image", "image/png")},
    )
    assert bad_content.status_code == 422


def test_image_upload_rejects_images_over_16_megapixels(api_client, monkeypatch):
    from src.dashboard.backend.v1 import batch_runner

    monkeypatch.setattr(batch_runner, "MAX_IMAGE_PIXELS", 100)
    response = api_client.post(
        "/api/v1/batch/images",
        data={"model_name": "demo.pt"},
        files={"images": ("a.png", _png_bytes(), "image/png")},
    )
    assert response.status_code == 422
