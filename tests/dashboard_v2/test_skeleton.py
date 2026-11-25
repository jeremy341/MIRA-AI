"""Tests for the shared v1 primitives: storage, jobs, events and router mounting."""

from __future__ import annotations

import asyncio
import threading
import time

from fastapi.testclient import TestClient

from src.dashboard.backend.v1.events import EventBus
from src.dashboard.backend.v1.jobs import JobCancelledError, JobManager
from src.dashboard.backend.v1.state import get_db, get_events, get_jobs
from src.dashboard.backend.v1.storage import Database

EXPECTED_TABLES = {
    "sessions",
    "detections",
    "metrics",
    "hardware_samples",
    "jobs",
    "comparisons",
    "benchmark_runs",
    "arm_events",
}


def wait_for(predicate, timeout=5.0):
    deadline = time.time() + timeout
    while time.time() < deadline:
        if predicate():
            return True
        time.sleep(0.02)
    return False


def test_migrations_create_base_tables_and_are_idempotent(tmp_path):
    db = Database(tmp_path / "t.db")
    tables = {row["name"] for row in db.query("SELECT name FROM sqlite_master WHERE type='table'")}
    assert EXPECTED_TABLES <= tables
    assert db.migrate() == []
    db.close()


def test_transaction_rolls_back_on_error(tmp_path):
    db = Database(tmp_path / "t.db")
    try:
        with db.transaction():
            db.execute("INSERT INTO sessions (id, name, source, started_at_ts) VALUES ('a', 'x', 'camera', 1.0)")
            raise RuntimeError("boom")
    except RuntimeError:
        pass
    assert db.query("SELECT * FROM sessions") == []
    db.close()


def test_deleting_a_session_cascades_to_detections(tmp_path):
    db = Database(tmp_path / "t.db")
    db.execute("INSERT INTO sessions (id, name, source, started_at_ts) VALUES ('a', 'x', 'camera', 1.0)")
    db.execute("INSERT INTO detections (session_id, ts, class_name, confidence) VALUES ('a', 1.0, 'glass', 0.9)")
    db.execute("DELETE FROM sessions WHERE id='a'")
    assert db.query("SELECT * FROM detections") == []
    db.close()


def test_job_runs_reports_progress_and_persists(tmp_path):
    db, events = Database(tmp_path / "t.db"), EventBus()
    jobs = JobManager(db, events)

    def work(ctx):
        ctx.progress(0.5, "half")
        return {"answer": 42}

    job = jobs.submit("demo", work, title="Demo")
    assert wait_for(lambda: job.status == "completed")
    assert job.progress == 1.0 and job.result == {"answer": 42}
    assert db.query_one("SELECT status FROM jobs WHERE id=?", (job.id,))["status"] == "completed"
    jobs.shutdown()


def test_job_failure_and_cancellation(tmp_path):
    db, events = Database(tmp_path / "t.db"), EventBus()
    jobs = JobManager(db, events)

    failing = jobs.submit("demo", lambda ctx: 1 / 0)
    assert wait_for(lambda: failing.status == "failed")
    assert "division" in (failing.error or "")

    started = threading.Event()

    def slow(ctx):
        started.set()
        while True:
            ctx.raise_if_cancelled()
            time.sleep(0.01)

    job = jobs.submit("demo", slow)
    assert started.wait(5)
    jobs.cancel(job.id)
    assert wait_for(lambda: job.status == "cancelled")
    assert issubclass(JobCancelledError, Exception)
    jobs.shutdown()


def test_event_bus_delivers_across_threads_and_drops_for_slow_clients():
    async def scenario():
        bus = EventBus(queue_size=2)
        queue = bus.subscribe()
        threading.Thread(target=lambda: [bus.publish("job_progress", {"n": i}) for i in range(5)]).start()
        await asyncio.sleep(0.2)
        received = []
        while not queue.empty():
            received.append(queue.get_nowait())
        return received

    received = asyncio.run(scenario())
    assert len(received) == 2
    assert received[-1]["data"]["n"] == 4 and received[0]["type"] == "job_progress"


def test_singletons_use_the_isolated_database(tmp_path):
    assert get_db().path.name == "dashboard-test.db"
    assert get_jobs() is get_jobs() and get_events() is get_events()


def test_app_mounts_v1_and_runs_lifespan():
    from src.dashboard.backend.main import app

    with TestClient(app) as client:
        assert client.get("/api/status").status_code == 200
        assert client.get("/openapi.json").status_code == 200
    assert get_db().path.name == "dashboard-test.db"
