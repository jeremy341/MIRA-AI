"""Tests for persisted dashboard jobs and the public jobs API."""

from __future__ import annotations

import json
import threading
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.dashboard.backend import v1
from src.dashboard.backend.v1.state import get_db, get_jobs


def _wait_for(predicate, timeout: float = 5.0) -> bool:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if predicate():
            return True
        time.sleep(0.01)
    return False


def _test_app() -> FastAPI:
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        await v1.startup()
        yield
        await v1.shutdown()

    app = FastAPI(lifespan=lifespan)
    app.include_router(v1.api_router, prefix="/api/v1")
    return app


def test_persisted_jobs_survive_restart_and_stale_jobs_fail_on_startup():
    app = _test_app()
    now = time.time()
    db = get_db()
    db.executemany(
        "INSERT INTO jobs (id, kind, title, status, progress, message, created_at_ts, result_json)"
        " VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        [
            ("done-job", "batch-images", "Old batch", "completed", 1.0, "Done", now - 2, json.dumps({"n": 2})),
            ("queued-job", "batch-video", "Interrupted queued", "queued", 0.0, "Queued", now - 1, None),
            ("running-job", "batch-video", "Interrupted running", "running", 0.4, "Working", now, None),
        ],
    )

    with TestClient(app) as client:
        listed = client.get("/api/v1/jobs?limit=50")
        assert listed.status_code == 200
        jobs = {job["id"]: job for job in listed.json()["jobs"]}
        assert list(job["id"] for job in listed.json()["jobs"]) == ["running-job", "queued-job", "done-job"]
        assert jobs["done-job"]["result"] == {"n": 2}
        for job_id in ("queued-job", "running-job"):
            assert jobs[job_id]["status"] == "failed"
            assert jobs[job_id]["error"] == "Interrupted by restart"
            assert client.get(f"/api/v1/jobs/{job_id}").json() == jobs[job_id]

    # A second application lifespan reads the completed row from SQLite.
    with TestClient(app) as client:
        persisted = client.get("/api/v1/jobs/done-job")
        assert persisted.status_code == 200
        assert persisted.json()["result"] == {"n": 2}


def test_live_memory_job_takes_precedence_over_its_database_row():
    with TestClient(_test_app()) as client:
        started = threading.Event()

        def wait_for_cancel(ctx):
            started.set()
            while not ctx.cancelled.is_set():
                time.sleep(0.01)
            return {"live": True}

        job = get_jobs().submit("batch-images", wait_for_cancel, title="Live job")
        assert started.wait(5)
        get_db().execute(
            "UPDATE jobs SET status='failed', error='stale copy' WHERE id=?",
            (job.id,),
        )

        response = client.get(f"/api/v1/jobs/{job.id}")
        assert response.status_code == 200
        assert response.json()["status"] == "running"
        assert response.json()["error"] is None

        assert client.post(f"/api/v1/jobs/{job.id}/cancel").status_code == 200
        assert _wait_for(lambda: job.status == "cancelled")


def test_job_cancel_and_unknown_or_finished_job_statuses():
    with TestClient(_test_app()) as client:
        assert client.get("/api/v1/jobs/missing").status_code == 404
        assert client.post("/api/v1/jobs/missing/cancel").status_code == 404

        finished = get_jobs().submit("batch-images", lambda ctx: {"done": True})
        assert _wait_for(lambda: finished.status == "completed")
        response = client.post(f"/api/v1/jobs/{finished.id}/cancel")
        assert response.status_code == 409
        assert response.json()["detail"] == "Job has already finished."
