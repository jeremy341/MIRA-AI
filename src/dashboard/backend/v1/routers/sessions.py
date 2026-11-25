"""Session lifecycle, detection history and replay timeline API."""

from __future__ import annotations

import asyncio
import json
import math
import time
import uuid
from datetime import datetime, timezone
from typing import Literal

from fastapi import APIRouter, HTTPException, Query, Response
from pydantic import BaseModel, Field

from ..recorder import recorder, set_camera_service
from ..state import get_db, get_events

router = APIRouter(tags=["Sessions"])

CLASS_NAMES = ("glass", "metal", "paper", "plastic", "trash")
SessionSource = Literal["camera", "image", "video", "batch"]
SessionStatus = Literal["active", "completed", "failed"]


class SessionCreate(BaseModel):
    name: str | None = Field(default=None, max_length=120)
    source: SessionSource
    model_name: str | None = None


class SessionPatch(BaseModel):
    name: str | None = Field(default=None, max_length=120)
    notes: str | None = Field(default=None, max_length=5000)


class SessionSummary(BaseModel):
    id: str
    name: str
    source: SessionSource
    model_name: str | None
    status: SessionStatus
    started_at: str
    ended_at: str | None
    duration_seconds: float
    total_detections: int
    class_counts: dict[str, int]
    avg_confidence: float | None


class SessionDetail(SessionSummary):
    config: dict
    notes: str | None


class SessionListResponse(BaseModel):
    sessions: list[SessionSummary]
    total: int


class DetectionItem(BaseModel):
    ts: str
    offset_seconds: float
    frame_index: int | None
    class_name: str
    confidence: float
    bbox: list[int | None]
    track_id: int | None


class DetectionListResponse(BaseModel):
    detections: list[DetectionItem]
    total: int


class TimelineBucket(BaseModel):
    start_offset: float
    objects: int
    class_counts: dict[str, int]
    avg_confidence: float | None
    fps: float | None
    latency_ms: float | None


class TimelineResponse(BaseModel):
    duration_seconds: float
    bucket_seconds: float
    buckets: list[TimelineBucket]


def _iso(timestamp: float | None) -> str | None:
    return datetime.fromtimestamp(timestamp, timezone.utc).isoformat() if timestamp is not None else None


def _auto_name(timestamp: float | None = None) -> str:
    value = datetime.fromtimestamp(timestamp or time.time(), timezone.utc)
    return value.strftime("Session %Y-%m-%d %H:%M")


def _summary_sql(where_clause: str = "", order_limit: str = "") -> str:
    return (
        "SELECT s.id, s.name, s.source, s.model_name, s.status, s.started_at_ts, s.ended_at_ts,"
        " s.config_json, s.notes, MAX(0.0, COALESCE(s.ended_at_ts, ?) - s.started_at_ts) AS duration_seconds,"
        " (SELECT COUNT(*) FROM detections d WHERE d.session_id=s.id) AS total_detections,"
        " (SELECT AVG(d.confidence) FROM detections d WHERE d.session_id=s.id) AS avg_confidence"
        " FROM sessions s"
        f" {where_clause} {order_limit}"
    )


def _class_counts(session_ids: list[str]) -> dict[str, dict[str, int]]:
    counts = {session_id: {name: 0 for name in CLASS_NAMES} for session_id in session_ids}
    if not session_ids:
        return counts
    placeholders = ",".join("?" for _ in session_ids)
    rows = get_db().query(
        "SELECT session_id, class_name, COUNT(*) AS count FROM detections"
        f" WHERE session_id IN ({placeholders}) GROUP BY session_id, class_name",
        session_ids,
    )
    for row in rows:
        if row["class_name"] in CLASS_NAMES:
            counts[row["session_id"]][row["class_name"]] = int(row["count"])
    return counts


def _summary_payload(row, counts: dict[str, int]) -> dict:
    return {
        "id": row["id"],
        "name": row["name"],
        "source": row["source"],
        "model_name": row["model_name"],
        "status": row["status"],
        "started_at": _iso(row["started_at_ts"]),
        "ended_at": _iso(row["ended_at_ts"]),
        "duration_seconds": round(float(row["duration_seconds"]), 3),
        "total_detections": int(row["total_detections"]),
        "class_counts": counts,
        "avg_confidence": round(float(row["avg_confidence"]), 4) if row["avg_confidence"] is not None else None,
    }


def _get_session_row(session_id: str, now: float | None = None):
    return get_db().query_one(
        _summary_sql("WHERE s.id=?"),
        (time.time() if now is None else now, session_id),
    )


def _require_session(session_id: str, now: float | None = None):
    row = _get_session_row(session_id, now)
    if row is None:
        raise HTTPException(status_code=404, detail="Session not found")
    return row


@router.post("/sessions", response_model=SessionDetail, status_code=201)
def create_session(payload: SessionCreate) -> dict:
    now = time.time()
    session_id = uuid.uuid4().hex
    name = (payload.name or "").strip() or _auto_name(now)
    model_name = (payload.model_name or "").strip() or None
    db = get_db()

    with db.transaction():
        if payload.source == "camera" and db.query_one(
            "SELECT id FROM sessions WHERE source='camera' AND status='active' LIMIT 1"
        ):
            raise HTTPException(status_code=409, detail="A camera session is already active")
        db.execute(
            "INSERT INTO sessions (id, name, source, model_name, status, started_at_ts, config_json, notes)"
            " VALUES (?, ?, ?, ?, 'active', ?, '{}', NULL)",
            (session_id, name, payload.source, model_name, now),
        )

    created = {
        "id": session_id,
        "name": name,
        "source": payload.source,
        "model_name": model_name,
        "started_at": _iso(now),
    }
    if payload.source == "camera":
        recorder.start_session(created)
    else:
        get_events().publish("session_started", created)
    return _detail_payload(_require_session(session_id, now))


def _detail_payload(row) -> dict:
    payload = _summary_payload(row, _class_counts([row["id"]])[row["id"]])
    try:
        config = json.loads(row["config_json"] or "{}")
    except (TypeError, json.JSONDecodeError):
        config = {}
    payload.update({"config": config, "notes": row["notes"]})
    return payload


@router.post("/sessions/{session_id}/stop", response_model=SessionDetail)
def stop_session(session_id: str) -> dict:
    now = time.time()
    db = get_db()
    with db.transaction():
        current = db.query_one("SELECT source, status FROM sessions WHERE id=?", (session_id,))
        if current is None:
            raise HTTPException(status_code=404, detail="Session not found")
        if current["status"] != "active":
            raise HTTPException(status_code=409, detail="Only an active session can be stopped")
        db.execute("UPDATE sessions SET status='completed', ended_at_ts=? WHERE id=?", (now, session_id))

    ended_at = _iso(now)
    if current["source"] == "camera":
        if not recorder.stop_session(session_id, ended_at=ended_at):
            get_events().publish("session_stopped", {"id": session_id, "ended_at": ended_at})
    else:
        get_events().publish("session_stopped", {"id": session_id, "ended_at": ended_at})
    return _detail_payload(_require_session(session_id, now))


@router.get("/sessions", response_model=SessionListResponse)
def list_sessions(
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    status: str | None = None,
) -> dict:
    if status == "":
        status = None
    if status is not None and status not in {"active", "completed", "failed"}:
        raise HTTPException(status_code=422, detail="status must be active, completed or failed")
    now = time.time()
    where_clause = "WHERE s.status=?" if status else ""
    params: list = [now]
    if status:
        params.append(status)
    total_row = get_db().query_one(f"SELECT COUNT(*) AS total FROM sessions s {where_clause}", params[1:])
    rows = get_db().query(
        _summary_sql(where_clause, "ORDER BY s.started_at_ts DESC LIMIT ? OFFSET ?"),
        [*params, limit, offset],
    )
    counts = _class_counts([row["id"] for row in rows])
    items = [_summary_payload(row, counts[row["id"]]) for row in rows]
    return {"sessions": items, "total": int(total_row["total"])}


@router.get("/sessions/{session_id}", response_model=SessionDetail)
def get_session(session_id: str) -> dict:
    return _detail_payload(_require_session(session_id))


@router.patch("/sessions/{session_id}", response_model=SessionDetail)
def patch_session(session_id: str, payload: SessionPatch) -> dict:
    _require_session(session_id)
    fields = payload.model_fields_set
    updates: list[str] = []
    values: list = []
    if "name" in fields and payload.name is not None:
        updates.append("name=?")
        values.append(payload.name.strip() or _auto_name())
    if "notes" in fields:
        updates.append("notes=?")
        values.append(payload.notes)
    if updates:
        values.append(session_id)
        get_db().execute(f"UPDATE sessions SET {', '.join(updates)} WHERE id=?", values)
    return _detail_payload(_require_session(session_id))


@router.delete("/sessions/{session_id}", status_code=204)
def delete_session(session_id: str) -> Response:
    db = get_db()
    with db.transaction():
        row = db.query_one("SELECT status FROM sessions WHERE id=?", (session_id,))
        if row is None:
            raise HTTPException(status_code=404, detail="Session not found")
        if row["status"] == "active":
            raise HTTPException(status_code=409, detail="Stop the active session before deleting it")
        db.execute("DELETE FROM sessions WHERE id=?", (session_id,))
    return Response(status_code=204)


@router.get("/sessions/{session_id}/detections", response_model=DetectionListResponse)
def list_detections(
    session_id: str,
    limit: int = Query(500, ge=1, le=500),
    offset: int = Query(0, ge=0),
    class_name: str | None = None,
    min_confidence: float | None = Query(None, ge=0.0, le=1.0),
) -> dict:
    session = _require_session(session_id)
    if class_name == "":
        class_name = None
    if class_name is not None and class_name not in CLASS_NAMES:
        raise HTTPException(status_code=422, detail="class_name must be one of glass, metal, paper, plastic or trash")
    filters = ["d.session_id=?"]
    params: list = [session_id]
    if class_name is not None:
        filters.append("d.class_name=?")
        params.append(class_name)
    if min_confidence is not None:
        filters.append("d.confidence>=?")
        params.append(min_confidence)
    where_clause = " AND ".join(filters)
    total = get_db().query_one(f"SELECT COUNT(*) AS total FROM detections d WHERE {where_clause}", params)["total"]
    rows = get_db().query(
        "SELECT d.ts, MAX(0.0, d.ts-?) AS offset_seconds, d.frame_index, d.class_name, d.confidence,"
        " d.x1, d.y1, d.x2, d.y2, d.track_id"
        f" FROM detections d WHERE {where_clause} ORDER BY d.ts, d.id LIMIT ? OFFSET ?",
        [session["started_at_ts"], *params, limit, offset],
    )
    detections = [
        {
            "ts": _iso(row["ts"]),
            "offset_seconds": round(float(row["offset_seconds"]), 3),
            "frame_index": row["frame_index"],
            "class_name": row["class_name"],
            "confidence": float(row["confidence"]),
            "bbox": [row["x1"], row["y1"], row["x2"], row["y2"]],
            "track_id": row["track_id"],
        }
        for row in rows
    ]
    return {"detections": detections, "total": int(total)}


@router.get("/sessions/{session_id}/timeline", response_model=TimelineResponse)
def get_timeline(
    session_id: str,
    bucket_seconds: float = Query(1.0, gt=0),
) -> dict:
    session = _require_session(session_id)
    duration = float(session["duration_seconds"])
    bucket_count = max(1, math.ceil(duration / bucket_seconds))
    detections = get_db().query(
        "SELECT CAST((d.ts-s.started_at_ts)/? AS INTEGER) AS bucket, COUNT(*) AS objects,"
        " AVG(d.confidence) AS avg_confidence FROM detections d"
        " JOIN sessions s ON s.id=d.session_id WHERE d.session_id=? GROUP BY bucket",
        (bucket_seconds, session_id),
    )
    class_rows = get_db().query(
        "SELECT CAST((d.ts-s.started_at_ts)/? AS INTEGER) AS bucket, d.class_name, COUNT(*) AS count"
        " FROM detections d JOIN sessions s ON s.id=d.session_id WHERE d.session_id=?"
        " GROUP BY bucket, d.class_name",
        (bucket_seconds, session_id),
    )
    metric_rows = get_db().query(
        "SELECT CAST((m.ts-s.started_at_ts)/? AS INTEGER) AS bucket, AVG(m.fps) AS fps,"
        " AVG(m.latency_ms) AS latency_ms FROM metrics m"
        " JOIN sessions s ON s.id=m.session_id WHERE m.session_id=? GROUP BY bucket",
        (bucket_seconds, session_id),
    )
    detection_by_bucket = {int(row["bucket"]): row for row in detections}
    metrics_by_bucket = {int(row["bucket"]): row for row in metric_rows}
    counts_by_bucket: dict[int, dict[str, int]] = {}
    for row in class_rows:
        if row["class_name"] in CLASS_NAMES:
            counts_by_bucket.setdefault(int(row["bucket"]), {name: 0 for name in CLASS_NAMES})[row["class_name"]] = int(
                row["count"]
            )

    buckets = []
    for index in range(bucket_count):
        detection_row = detection_by_bucket.get(index)
        metric_row = metrics_by_bucket.get(index)
        buckets.append(
            {
                "start_offset": round(index * bucket_seconds, 3),
                "objects": int(detection_row["objects"]) if detection_row else 0,
                "class_counts": counts_by_bucket.get(index, {name: 0 for name in CLASS_NAMES}),
                "avg_confidence": round(float(detection_row["avg_confidence"]), 4)
                if detection_row and detection_row["avg_confidence"] is not None
                else None,
                "fps": round(float(metric_row["fps"]), 3) if metric_row and metric_row["fps"] is not None else None,
                "latency_ms": round(float(metric_row["latency_ms"]), 3)
                if metric_row and metric_row["latency_ms"] is not None
                else None,
            }
        )
    return {
        "duration_seconds": round(duration, 3),
        "bucket_seconds": bucket_seconds,
        "buckets": buckets,
    }


async def on_startup() -> None:
    """Recover interrupted sessions and attach the recorder to the legacy camera singleton."""
    db = get_db()
    active_sessions = db.query("SELECT id FROM sessions WHERE status='active'")
    db.execute(
        "UPDATE sessions SET status='completed', ended_at_ts=COALESCE(("
        " SELECT MAX(ts) FROM ("
        "  SELECT ts FROM detections WHERE session_id=sessions.id"
        "  UNION ALL SELECT ts FROM metrics WHERE session_id=sessions.id"
        " )"
        "), started_at_ts) WHERE status='active'"
    )
    for row in active_sessions:
        get_events().publish("session_stopped", {"id": row["id"], "recovered": True})
    try:
        from src.dashboard.backend.main import camera_service
    except ImportError:
        return
    set_camera_service(camera_service)


async def on_shutdown() -> None:
    session_id = recorder.active_session_id
    if session_id:
        now = time.time()
        ended_at = _iso(now)
        get_db().execute(
            "UPDATE sessions SET status='completed', ended_at_ts=? WHERE id=? AND status='active'",
            (now, session_id),
        )
        await asyncio.to_thread(recorder.stop_session, session_id, ended_at=ended_at)
    await asyncio.to_thread(recorder.shutdown)
