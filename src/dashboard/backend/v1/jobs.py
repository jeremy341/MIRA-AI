"""Background jobs with progress and cancellation, mirrored into the `jobs` table."""

from __future__ import annotations

import json
import threading
import time
import uuid
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from .events import EventBus
from .storage import Database


class JobCancelledError(Exception):
    """Raise inside a job function to stop it as `cancelled`."""


@dataclass
class JobContext:
    job_id: str
    cancelled: threading.Event
    _report: Callable[[float, str], None]

    def progress(self, fraction: float, message: str = "") -> None:
        self._report(max(0.0, min(1.0, fraction)), message)

    def raise_if_cancelled(self) -> None:
        if self.cancelled.is_set():
            raise JobCancelledError()


@dataclass
class Job:
    id: str
    kind: str
    title: str
    status: str = "queued"
    progress: float = 0.0
    message: str = ""
    created_at_ts: float = field(default_factory=time.time)
    finished_at_ts: float | None = None
    result: dict[str, Any] | None = None
    error: str | None = None
    _cancel: threading.Event = field(default_factory=threading.Event, repr=False)

    def to_dict(self) -> dict[str, Any]:
        def iso(ts: float | None) -> str | None:
            return datetime.fromtimestamp(ts, timezone.utc).isoformat() if ts else None

        return {
            "id": self.id,
            "kind": self.kind,
            "title": self.title,
            "status": self.status,
            "progress": self.progress,
            "message": self.message,
            "created_at": iso(self.created_at_ts),
            "finished_at": iso(self.finished_at_ts),
            "result": self.result,
            "error": self.error,
        }


class JobManager:
    def __init__(self, db: Database, events: EventBus, max_workers: int = 2):
        self._db = db
        self._events = events
        self._jobs: dict[str, Job] = {}
        self._lock = threading.Lock()
        self._pool = ThreadPoolExecutor(max_workers=max_workers, thread_name_prefix="mira-job")

    def submit(self, kind: str, fn: Callable[[JobContext], dict[str, Any] | None], *, title: str = "") -> Job:
        job = Job(id=uuid.uuid4().hex, kind=kind, title=title or kind)
        with self._lock:
            self._jobs[job.id] = job
        self._persist(job)
        self._pool.submit(self._run, job, fn)
        return job

    def get(self, job_id: str) -> Job | None:
        with self._lock:
            return self._jobs.get(job_id)

    def list(self, limit: int = 50) -> list[Job]:
        with self._lock:
            jobs = sorted(self._jobs.values(), key=lambda j: j.created_at_ts, reverse=True)
        return jobs[:limit]

    def cancel(self, job_id: str) -> Job | None:
        job = self.get(job_id)
        if job is not None and job.status in {"queued", "running"}:
            job._cancel.set()
        return job

    def shutdown(self) -> None:
        for job in self.list(1000):
            job._cancel.set()
        self._pool.shutdown(wait=False, cancel_futures=True)

    def _run(self, job: Job, fn: Callable[[JobContext], dict[str, Any] | None]) -> None:
        if job._cancel.is_set():
            self._finish(job, "cancelled")
            return
        job.status = "running"
        self._persist(job)

        def report(fraction: float, message: str) -> None:
            job.progress, job.message = fraction, message
            self._events.publish("job_progress", {"job_id": job.id, "progress": fraction, "message": message})

        try:
            job.result = fn(JobContext(job.id, job._cancel, report)) or {}
            if job._cancel.is_set():
                self._finish(job, "cancelled")
            else:
                job.progress = 1.0
                self._finish(job, "completed")
        except JobCancelledError:
            self._finish(job, "cancelled")
        except Exception as exc:  # a failing job must never kill the worker thread
            job.error = str(exc) or exc.__class__.__name__
            self._finish(job, "failed")

    def _finish(self, job: Job, status: str) -> None:
        job.status = status
        job.finished_at_ts = time.time()
        self._persist(job)
        self._events.publish("job_finished", {"job_id": job.id, "status": status, "error": job.error})

    def _persist(self, job: Job) -> None:
        self._db.execute(
            "INSERT INTO jobs (id, kind, title, status, progress, message, created_at_ts, finished_at_ts,"
            " result_json, error) VALUES (?,?,?,?,?,?,?,?,?,?) ON CONFLICT(id) DO UPDATE SET"
            " status=excluded.status, progress=excluded.progress, message=excluded.message,"
            " finished_at_ts=excluded.finished_at_ts, result_json=excluded.result_json, error=excluded.error",
            (
                job.id,
                job.kind,
                job.title,
                job.status,
                job.progress,
                job.message,
                job.created_at_ts,
                job.finished_at_ts,
                json.dumps(job.result) if job.result is not None else None,
                job.error,
            ),
        )
