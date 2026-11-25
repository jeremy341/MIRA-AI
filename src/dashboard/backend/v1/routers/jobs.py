"""Jobs API. Owner and contract: docs/dashboard-v2/CONTRACT.md."""

from __future__ import annotations

import json
import time
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Query

from ..state import get_db, get_jobs

router = APIRouter(tags=["Jobs"])


def _iso_timestamp(value: float | None) -> str | None:
    if value is None:
        return None
    return datetime.fromtimestamp(value, timezone.utc).isoformat()


def _row_to_job(row) -> tuple[float, dict]:
    try:
        result = json.loads(row["result_json"]) if row["result_json"] is not None else None
    except (json.JSONDecodeError, TypeError):
        result = None
    created_at_ts = float(row["created_at_ts"])
    return created_at_ts, {
        "id": row["id"],
        "kind": row["kind"],
        "title": row["title"] or row["kind"],
        "status": row["status"],
        "progress": float(row["progress"]),
        "message": row["message"] or "",
        "created_at": _iso_timestamp(created_at_ts),
        "finished_at": _iso_timestamp(row["finished_at_ts"]),
        "result": result,
        "error": row["error"],
    }


async def on_startup() -> None:
    """Mark work left active in SQLite by a previous process as interrupted."""
    now = time.time()
    get_db().execute(
        "UPDATE jobs SET status='failed', message=?, finished_at_ts=?, error=? WHERE status IN ('queued', 'running')",
        ("Interrupted by restart", now, "Interrupted by restart"),
    )


@router.get("/jobs")
def list_jobs(limit: int = Query(default=50, ge=1, le=1000)) -> dict:
    persisted = get_db().query(
        "SELECT id, kind, title, status, progress, message, created_at_ts, finished_at_ts, result_json, error "
        "FROM jobs ORDER BY created_at_ts DESC LIMIT ?",
        (limit,),
    )
    merged: dict[str, tuple[float, dict]] = {}
    for row in persisted:
        created_at_ts, payload = _row_to_job(row)
        merged[payload["id"]] = (created_at_ts, payload)

    for job in get_jobs().list(limit=10000):
        merged[job.id] = (job.created_at_ts, job.to_dict())

    ordered = sorted(merged.values(), key=lambda item: item[0], reverse=True)
    return {"jobs": [payload for _, payload in ordered[:limit]]}


@router.get("/jobs/{job_id}")
def get_job(job_id: str) -> dict:
    live_job = get_jobs().get(job_id)
    if live_job is not None:
        return live_job.to_dict()

    row = get_db().query_one(
        "SELECT id, kind, title, status, progress, message, created_at_ts, finished_at_ts, result_json, error "
        "FROM jobs WHERE id=?",
        (job_id,),
    )
    if row is None:
        raise HTTPException(status_code=404, detail="Job not found.")
    return _row_to_job(row)[1]


@router.post("/jobs/{job_id}/cancel")
def cancel_job(job_id: str) -> dict:
    manager = get_jobs()
    job = manager.get(job_id)
    if job is not None:
        if job.status not in {"queued", "running"}:
            raise HTTPException(status_code=409, detail="Job has already finished.")
        was_queued = job.status == "queued"
        manager.cancel(job_id)
        if job.kind in {"batch-video", "batch-images"} and was_queued:
            from ..batch_runner import cancel_if_not_started

            cancel_if_not_started(job_id)
        return job.to_dict()

    row = get_db().query_one("SELECT status FROM jobs WHERE id=?", (job_id,))
    if row is None:
        raise HTTPException(status_code=404, detail="Job not found.")
    if row["status"] not in {"queued", "running"}:
        raise HTTPException(status_code=409, detail="Job has already finished.")
    raise HTTPException(status_code=409, detail="Job is not active in this process.")
