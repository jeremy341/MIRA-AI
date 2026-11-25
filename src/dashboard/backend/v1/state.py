"""Process-wide singletons for the v1 API. Tests reset them with `reset_state()`."""

from __future__ import annotations

import threading

from .events import EventBus
from .jobs import JobManager
from .storage import Database, default_db_path

_lock = threading.RLock()
_db: Database | None = None
_events: EventBus | None = None
_jobs: JobManager | None = None


def get_db() -> Database:
    global _db
    with _lock:
        if _db is None:
            _db = Database(default_db_path())
        return _db


def get_events() -> EventBus:
    global _events
    with _lock:
        if _events is None:
            _events = EventBus()
        return _events


def get_jobs() -> JobManager:
    global _jobs
    with _lock:
        if _jobs is None:
            _jobs = JobManager(get_db(), get_events())
        return _jobs


def reset_state() -> None:
    """Close and forget the singletons (tests call this after changing MIRA_DASHBOARD_DB)."""
    global _db, _events, _jobs
    with _lock:
        if _jobs is not None:
            _jobs.shutdown()
        if _db is not None:
            _db.close()
        _db = _events = _jobs = None
