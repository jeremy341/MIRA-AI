"""Session API and asynchronous recorder tests with no camera or model required."""

from __future__ import annotations

import asyncio
import time
from datetime import datetime, timezone
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from src.dashboard.backend.models import Detection, SystemMetrics, WasteClass
from src.dashboard.backend.v1.recorder import recorder
from src.dashboard.backend.v1.state import get_db, get_events


@pytest.fixture
def client():
    app, websocket_handler = _app_with_fresh_websocket_queue()

    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        websocket_handler._broadcast_queue = asyncio.Queue(maxsize=32)


def _app_with_fresh_websocket_queue():
    from src.dashboard.backend.main import app, websocket_handler

    # The shared legacy handler binds this queue to its first TestClient lifespan loop.
    websocket_handler._broadcast_queue = asyncio.Queue(maxsize=32)
    return app, websocket_handler


def _insert_detection(session_id: str, ts: float, class_name: str, confidence: float, frame_index: int = 0) -> None:
    get_db().execute(
        "INSERT INTO detections (session_id, ts, frame_index, class_name, confidence, x1, y1, x2, y2, track_id)"
        " VALUES (?, ?, ?, ?, ?, 1, 2, 10, 20, 7)",
        (session_id, ts, frame_index, class_name, confidence),
    )


def test_session_lifecycle_conflicts_and_cascade_delete(client):
    created = client.post("/api/v1/sessions", json={"source": "camera", "name": "  "})
    assert created.status_code == 201
    session = created.json()
    assert session["name"].startswith("Session ")
    assert session["status"] == "active"
    assert session["class_counts"] == {"glass": 0, "metal": 0, "paper": 0, "plastic": 0, "trash": 0}

    assert client.post("/api/v1/sessions", json={"source": "camera"}).status_code == 409
    assert client.delete(f"/api/v1/sessions/{session['id']}").status_code == 409

    _insert_detection(session["id"], time.time(), "glass", 0.9)
    get_db().execute(
        "INSERT INTO metrics (session_id, ts, fps, latency_ms) VALUES (?, ?, ?, ?)",
        (session["id"], time.time(), 12.0, 40.0),
    )
    stopped = client.post(f"/api/v1/sessions/{session['id']}/stop")
    assert stopped.status_code == 200
    assert stopped.json()["status"] == "completed"
    assert stopped.json()["total_detections"] == 1
    assert stopped.json()["class_counts"]["glass"] == 1
    assert stopped.json()["avg_confidence"] == 0.9
    assert client.post(f"/api/v1/sessions/{session['id']}/stop").status_code == 409
    assert client.delete(f"/api/v1/sessions/{session['id']}").status_code == 204
    assert get_db().query_one("SELECT COUNT(*) AS n FROM detections WHERE session_id=?", (session["id"],))["n"] == 0
    assert get_db().query_one("SELECT COUNT(*) AS n FROM metrics WHERE session_id=?", (session["id"],))["n"] == 0


def test_patch_pagination_status_and_detection_filters(client):
    first = client.post("/api/v1/sessions", json={"source": "image", "name": "First"}).json()
    second = client.post("/api/v1/sessions", json={"source": "image", "name": "Second"}).json()
    now = time.time()
    _insert_detection(first["id"], now, "glass", 0.8, 1)
    _insert_detection(first["id"], now + 0.1, "glass", 0.95, 2)
    _insert_detection(first["id"], now + 0.2, "paper", 0.7, 3)

    patched = client.patch(
        f"/api/v1/sessions/{first['id']}",
        json={"name": "Renamed", "notes": "review notes"},
    )
    assert patched.status_code == 200
    assert patched.json()["name"] == "Renamed"
    assert patched.json()["notes"] == "review notes"
    assert patched.json()["config"] == {}

    page = client.get("/api/v1/sessions?limit=1&offset=0&status=active").json()
    assert page["total"] == 2
    assert len(page["sessions"]) == 1
    assert (
        client.get("/api/v1/sessions?limit=1&offset=1&status=active").json()["sessions"][0]["id"]
        != page["sessions"][0]["id"]
    )

    detections = client.get(
        f"/api/v1/sessions/{first['id']}/detections?limit=1&offset=0&class_name=glass&min_confidence=0.9"
    )
    assert detections.status_code == 200
    assert detections.json()["total"] == 1
    item = detections.json()["detections"][0]
    assert item["frame_index"] == 2
    assert item["class_name"] == "glass"
    assert item["bbox"] == [1, 2, 10, 20]
    assert item["track_id"] == 7
    assert client.get("/api/v1/sessions?limit=501").status_code == 422
    assert client.get("/api/v1/sessions?status=").status_code == 200
    assert client.get("/api/v1/sessions?status=unknown").status_code == 422
    assert client.post("/api/v1/sessions", json={"source": "image", "name": "x" * 121}).status_code == 422
    assert client.patch(f"/api/v1/sessions/{second['id']}", json={"notes": "x" * 5001}).status_code == 422


def test_timeline_uses_sql_aggregates_and_includes_empty_buckets(client):
    created = client.post("/api/v1/sessions", json={"source": "video", "name": "Timeline"}).json()
    session_id = created["id"]
    get_db().execute(
        "UPDATE sessions SET started_at_ts=100.0, ended_at_ts=102.5, status='completed' WHERE id=?", (session_id,)
    )
    _insert_detection(session_id, 100.1, "glass", 0.8, 1)
    _insert_detection(session_id, 100.8, "glass", 0.9, 2)
    _insert_detection(session_id, 101.2, "paper", 0.7, 3)
    get_db().executemany(
        "INSERT INTO metrics (session_id, ts, fps, latency_ms) VALUES (?, ?, ?, ?)",
        [(session_id, 100.5, 10.0, 20.0), (session_id, 101.5, 12.0, 30.0)],
    )

    response = client.get(f"/api/v1/sessions/{session_id}/timeline?bucket_seconds=1")
    assert response.status_code == 200
    timeline = response.json()
    assert timeline["duration_seconds"] == 2.5
    assert len(timeline["buckets"]) == 3
    assert timeline["buckets"][0]["objects"] == 2
    assert timeline["buckets"][0]["class_counts"]["glass"] == 2
    assert timeline["buckets"][0]["avg_confidence"] == 0.85
    assert timeline["buckets"][0]["fps"] == 10.0
    assert timeline["buckets"][1]["objects"] == 1
    assert timeline["buckets"][1]["latency_ms"] == 30.0
    assert timeline["buckets"][2]["objects"] == 0


def test_startup_recovers_crashed_sessions_from_last_sample_timestamp():
    db = get_db()
    db.execute(
        "INSERT INTO sessions (id, name, source, status, started_at_ts) VALUES ('crashed', 'Crash', 'camera', 'active', 10)"
    )
    db.execute("INSERT INTO detections (session_id, ts, class_name, confidence) VALUES ('crashed', 11, 'glass', 0.8)")
    db.execute("INSERT INTO metrics (session_id, ts, fps) VALUES ('crashed', 12, 20)")

    app, websocket_handler = _app_with_fresh_websocket_queue()
    try:
        with TestClient(app) as client:
            assert client.get("/api/v1/sessions/crashed").json()["status"] == "completed"
            assert (
                client.get("/api/v1/sessions/crashed").json()["ended_at"]
                == datetime.fromtimestamp(12, timezone.utc).isoformat()
            )
    finally:
        websocket_handler._broadcast_queue = asyncio.Queue(maxsize=32)


def test_recorder_batches_callbacks_off_thread_and_publishes_events(monkeypatch):
    service = SimpleNamespace(on_detection=None, on_metrics=None)
    session_id = "recorder-session"
    now = time.time()
    get_db().execute(
        "INSERT INTO sessions (id, name, source, status, started_at_ts) VALUES (?, 'Recorder', 'camera', 'active', ?)",
        (session_id, now),
    )
    published = []
    monkeypatch.setattr(get_events(), "publish", lambda event_type, data: published.append((event_type, data)))
    recorder.attach(service)
    recorder.start_session(
        {"id": session_id, "name": "Recorder", "source": "camera", "started_at": datetime.now(timezone.utc).isoformat()}
    )

    async def submit_samples():
        await service.on_detection(
            [
                Detection(class_name=WasteClass.GLASS, confidence=0.9, bbox=[1, 2, 3, 4], track_id=11),
                Detection(class_name=WasteClass.PAPER, confidence=0.8, bbox=[5, 6, 7, 8], track_id=None),
            ]
        )
        await service.on_metrics(
            SystemMetrics(
                fps=15,
                inference_latency_ms=22,
                avg_latency_ms=25,
                cpu_percent=30,
                memory_percent=40,
                temperature_celsius=50,
                detections_per_second=2,
                skip_frames=False,
            )
        )

    try:
        asyncio.run(submit_samples())
        assert recorder.flush()
        detections = get_db().query("SELECT * FROM detections WHERE session_id=? ORDER BY id", (session_id,))
        metrics = get_db().query("SELECT * FROM metrics WHERE session_id=?", (session_id,))
        assert len(detections) == 2
        assert {row["frame_index"] for row in detections} == {0}
        assert [row["track_id"] for row in detections] == [11, None]
        assert len(metrics) == 1 and metrics[0]["fps"] == 15
        start_events = [data for kind, data in published if kind == "session_started"]
        assert len(start_events) == 1 and start_events[0]["id"] == session_id
        detection_events = [data for kind, data in published if kind == "detection_batch"]
        assert len(detection_events) == 1
        assert len(detection_events[0]["detections"]) == 2
        assert recorder.stop_session(session_id)
        assert any(kind == "session_stopped" for kind, _ in published)
    finally:
        recorder.shutdown()
