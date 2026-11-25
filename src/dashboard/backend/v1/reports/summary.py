"""SQL-backed session summaries and compact report aggregates."""

from __future__ import annotations

import json
import math
from datetime import datetime, timezone
from typing import Any

from ..storage import Database

CLASS_NAMES = ("glass", "metal", "paper", "plastic", "trash")
MAX_CHART_BUCKETS = 36


def format_timestamp(ts: float | int | None) -> str | None:
    if ts is None:
        return None
    return datetime.fromtimestamp(float(ts), timezone.utc).isoformat()


def _config_value(raw_config: str | None) -> Any:
    if raw_config is None:
        return None
    try:
        return json.loads(raw_config)
    except (json.JSONDecodeError, TypeError):
        return None


def build_session_summary(db: Database, session_id: str) -> dict[str, Any] | None:
    """Return the agreed session shape with counts computed directly from the base tables."""
    row = db.query_one(
        "SELECT id, name, source, model_name, status, started_at_ts, ended_at_ts, config_json, notes "
        "FROM sessions WHERE id=?",
        (session_id,),
    )
    if row is None:
        return None

    started_at_ts = float(row["started_at_ts"])
    ended_at_ts = float(row["ended_at_ts"]) if row["ended_at_ts"] is not None else None
    detection_summary = db.query_one(
        "SELECT COUNT(*) AS total, AVG(confidence) AS avg_confidence, MAX(ts) AS latest_ts "
        "FROM detections WHERE session_id=?",
        (session_id,),
    )
    metric_latest = db.query_one("SELECT MAX(ts) AS latest_ts FROM metrics WHERE session_id=?", (session_id,))
    grouped_counts = db.query(
        "SELECT class_name, COUNT(*) AS count FROM detections WHERE session_id=? GROUP BY class_name",
        (session_id,),
    )
    class_counts = {class_name: 0 for class_name in CLASS_NAMES}
    for count_row in grouped_counts:
        class_name = str(count_row["class_name"])
        if class_name in class_counts:
            class_counts[class_name] = int(count_row["count"])

    latest_values = [
        value for value in (detection_summary["latest_ts"], metric_latest["latest_ts"]) if value is not None
    ]
    active_end_ts = max((float(value) for value in latest_values), default=started_at_ts)
    duration_end_ts = ended_at_ts if ended_at_ts is not None else active_end_ts
    duration_seconds = round(max(0.0, duration_end_ts - started_at_ts), 3)
    total_detections = int(detection_summary["total"])
    avg_confidence = detection_summary["avg_confidence"]
    if avg_confidence is not None:
        avg_confidence = round(float(avg_confidence), 4)

    session = {
        "id": row["id"],
        "name": row["name"],
        "source": row["source"],
        "model_name": row["model_name"],
        "status": row["status"],
        "started_at": format_timestamp(started_at_ts),
        "ended_at": format_timestamp(ended_at_ts),
        "duration_seconds": duration_seconds,
        "total_detections": total_detections,
        "class_counts": class_counts,
        "avg_confidence": avg_confidence,
        "config": _config_value(row["config_json"]),
        "notes": row["notes"],
    }
    return {"session": session, "started_at_ts": started_at_ts, "active_end_ts": active_end_ts}


def load_report_aggregates(
    db: Database, session_id: str, started_at_ts: float, duration_seconds: float
) -> dict[str, Any]:
    """Read per-class confidence and a bounded time series for the report charts."""
    class_rows = db.query(
        "SELECT class_name, COUNT(*) AS count, AVG(confidence) AS avg_confidence "
        "FROM detections WHERE session_id=? GROUP BY class_name",
        (session_id,),
    )
    class_stats = {class_name: {"count": 0, "avg_confidence": None} for class_name in CLASS_NAMES}
    for row in class_rows:
        class_name = str(row["class_name"])
        if class_name in class_stats:
            class_stats[class_name] = {
                "count": int(row["count"]),
                "avg_confidence": float(row["avg_confidence"]),
            }

    bucket_span = max(float(duration_seconds), 1.0)
    bucket_seconds = max(1, math.ceil(bucket_span / MAX_CHART_BUCKETS))
    bucket_count = max(1, math.ceil(bucket_span / bucket_seconds))
    bucket_rows = db.query(
        "SELECT CAST(MAX(0.0, ts - ?) / ? AS INTEGER) AS bucket, COUNT(*) AS count "
        "FROM detections WHERE session_id=? GROUP BY bucket ORDER BY bucket",
        (started_at_ts, bucket_seconds, session_id),
    )
    buckets = [0] * bucket_count
    for row in bucket_rows:
        bucket_index = min(max(0, int(row["bucket"])), bucket_count - 1)
        buckets[bucket_index] += int(row["count"])

    return {
        "class_stats": class_stats,
        "time_buckets": buckets,
        "bucket_seconds": bucket_seconds,
        "duration_seconds": duration_seconds,
    }
