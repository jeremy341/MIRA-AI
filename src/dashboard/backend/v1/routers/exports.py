"""Session CSV, JSON, and printable HTML exports."""

from __future__ import annotations

import csv
import io
import re
import unicodedata
from collections.abc import Iterator

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse

from ..reports.html_report import render_report
from ..reports.summary import (
    build_session_summary,
    format_timestamp,
    load_report_aggregates,
)
from ..state import get_db

router = APIRouter(tags=["Export"])
CSV_HEADER = ("ts", "offset_seconds", "frame_index", "class_name", "confidence", "x1", "y1", "x2", "y2", "track_id")
CSV_CHUNK_SIZE = 1000


def _slug(value: str) -> str:
    ascii_value = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")
    slug = re.sub(r"[^a-z0-9]+", "-", ascii_value.lower()).strip("-")
    return slug or "session"


def _attachment_filename(session_name: str, session_id: str, extension: str) -> str:
    safe_id = re.sub(r"[^A-Za-z0-9_-]", "", session_id[:8]) or "session"
    return f"{_slug(session_name)}-{safe_id}.{extension}"


def _csv_text_cell(value: str) -> str:
    if value.startswith(("=", "+", "-", "@")):
        return f"'{value}"
    return value


def _csv_line(values: tuple[object, ...]) -> str:
    buffer = io.StringIO(newline="")
    safe_values = tuple(_csv_text_cell(value) if isinstance(value, str) else value for value in values)
    csv.writer(buffer).writerow(safe_values)
    return buffer.getvalue()


def _stream_detections(session_id: str, started_at_ts: float) -> Iterator[str]:
    yield _csv_line(CSV_HEADER)
    cursor = get_db().execute(
        "SELECT ts, frame_index, class_name, confidence, x1, y1, x2, y2, track_id "
        "FROM detections WHERE session_id=? ORDER BY ts, id",
        (session_id,),
    )
    while rows := cursor.fetchmany(CSV_CHUNK_SIZE):
        for row in rows:
            ts = float(row["ts"])
            values = (
                format_timestamp(ts),
                f"{round(ts - started_at_ts, 3):.3f}",
                row["frame_index"],
                str(row["class_name"]),
                row["confidence"],
                row["x1"],
                row["y1"],
                row["x2"],
                row["y2"],
                row["track_id"],
            )
            yield _csv_line(values)


@router.get("/sessions/{session_id}/export.csv")
def export_csv(session_id: str) -> StreamingResponse:
    session = build_session_summary(get_db(), session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")

    filename = _attachment_filename(session["session"]["name"], session_id, "csv")
    return StreamingResponse(
        _stream_detections(session_id, session["started_at_ts"]),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/sessions/{session_id}/export.json")
def export_json(session_id: str) -> JSONResponse:
    db = get_db()
    summary = build_session_summary(db, session_id)
    if summary is None:
        raise HTTPException(status_code=404, detail="Session not found")

    started_at_ts = summary["started_at_ts"]
    detections = db.query(
        "SELECT ts, frame_index, class_name, confidence, x1, y1, x2, y2, track_id "
        "FROM detections WHERE session_id=? ORDER BY ts, id",
        (session_id,),
    )
    metrics = db.query(
        "SELECT ts, fps, latency_ms, cpu_percent, memory_percent, temperature_c "
        "FROM metrics WHERE session_id=? ORDER BY ts, id",
        (session_id,),
    )

    payload = {
        "session": summary["session"],
        "class_counts": summary["session"]["class_counts"],
        "detections": [
            {
                "ts": format_timestamp(row["ts"]),
                "offset_seconds": round(float(row["ts"]) - started_at_ts, 3),
                "frame_index": row["frame_index"],
                "class_name": row["class_name"],
                "confidence": row["confidence"],
                "bbox": [row["x1"], row["y1"], row["x2"], row["y2"]],
                "track_id": row["track_id"],
            }
            for row in detections
        ],
        "metrics": [
            {
                "ts": format_timestamp(row["ts"]),
                "offset_seconds": round(float(row["ts"]) - started_at_ts, 3),
                "fps": row["fps"],
                "latency_ms": row["latency_ms"],
                "cpu_percent": row["cpu_percent"],
                "memory_percent": row["memory_percent"],
                "temperature_c": row["temperature_c"],
            }
            for row in metrics
        ],
    }
    filename = _attachment_filename(summary["session"]["name"], session_id, "json")
    return JSONResponse(
        payload,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/sessions/{session_id}/report.html", response_class=HTMLResponse)
def export_report(session_id: str, download: int = Query(default=0, ge=0, le=1)) -> HTMLResponse:
    db = get_db()
    summary = build_session_summary(db, session_id)
    if summary is None:
        raise HTTPException(status_code=404, detail="Session not found")

    aggregates = load_report_aggregates(
        db,
        session_id,
        summary["started_at_ts"],
        summary["session"]["duration_seconds"],
    )
    html = render_report(summary["session"], aggregates)
    headers = {}
    if download:
        filename = _attachment_filename(summary["session"]["name"], session_id, "html")
        headers["Content-Disposition"] = f'attachment; filename="{filename}"'
    return HTMLResponse(content=html, headers=headers)
