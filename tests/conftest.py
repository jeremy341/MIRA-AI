"""Shared test setup: the dashboard database never touches the real home directory."""

from __future__ import annotations

import pytest


@pytest.fixture(autouse=True)
def _isolated_dashboard_db(tmp_path, monkeypatch):
    monkeypatch.setenv("MIRA_DASHBOARD_DB", str(tmp_path / "dashboard-test.db"))
    try:
        from src.dashboard.backend.v1.state import reset_state
    except Exception:  # dashboard dependencies are optional for unrelated tests
        yield
        return
    reset_state()
    yield
    reset_state()
