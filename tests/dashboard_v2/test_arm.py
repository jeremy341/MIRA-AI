"""Sorting-arm placeholder API tests."""

from __future__ import annotations

import asyncio
import time

import pytest
from fastapi.testclient import TestClient

from src.dashboard.backend import main
from src.dashboard.backend.main import app
from src.dashboard.backend.models import Statistics, WasteClass
from src.dashboard.backend.v1.arm import SimulatedArm, set_arm
from src.dashboard.backend.v1.state import get_db


@pytest.fixture(autouse=True)
def _simulated_arm(monkeypatch):
    monkeypatch.setenv("MIRA_HARDWARE_INTERVAL", "0.5")
    set_arm(SimulatedArm(duration=0.12))


def _wait_for_event(client: TestClient, kind: str, count: int = 1, timeout: float = 3.0) -> dict:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        events = client.get("/api/v1/arm/events", params={"kind": kind}).json()["events"]
        if len(events) >= count:
            return events[0]
        time.sleep(0.01)
    raise AssertionError(f"Timed out waiting for {kind}")


def _reset_app_queue():
    main.websocket_handler._broadcast_queue = asyncio.Queue(maxsize=32)


@pytest.fixture(autouse=True)
def _fresh_video_queue():
    _reset_app_queue()
    yield
    _reset_app_queue()


def test_arm_status_command_validation_and_busy_state():
    with TestClient(app) as client:
        status = client.get("/api/v1/arm/status").json()
        assert status["mode"] == "simulated"
        assert status["connected"] is False
        assert status["state"] == "idle"
        assert client.post("/api/v1/arm/commands", json={"action": "sort"}).status_code == 422
        assert client.post("/api/v1/arm/commands", json={"action": "sort", "class_name": "organic"}).status_code == 422
        assert client.post("/api/v1/arm/commands", json={"action": "fly"}).status_code == 422

        accepted = client.post("/api/v1/arm/commands", json={"action": "sort", "class_name": "glass"})
        assert accepted.status_code == 202
        assert accepted.json()["kind"] == "sort_requested"
        assert client.get("/api/v1/arm/status").json()["state"] == "busy"
        assert client.post("/api/v1/arm/commands", json={"action": "home"}).status_code == 409
        completed = _wait_for_event(client, "sort_completed")
        events = client.get("/api/v1/arm/events", params={"limit": 10}).json()["events"]
        kinds_in_order = [event["kind"] for event in reversed(events)]
        assert kinds_in_order == ["sort_requested", "sort_completed"]
        assert completed["class_name"] == "glass"


def test_home_and_stop_commands_log_requested_then_completed():
    with TestClient(app) as client:
        for action in ("home", "stop"):
            accepted = client.post("/api/v1/arm/commands", json={"action": action})
            assert accepted.status_code == 202
            assert accepted.json()["kind"] == f"{action}_requested"
            _wait_for_event(client, f"{action}_completed")

        kinds = [event["kind"] for event in reversed(client.get("/api/v1/arm/events").json()["events"])]
        assert kinds == ["home_requested", "home_completed", "stop_requested", "stop_completed"]


def test_feedback_last_answer_wins_and_accuracy_counts_feedback_only():
    with TestClient(app) as client:
        first = client.post("/api/v1/arm/commands", json={"action": "sort", "class_name": "metal"})
        assert first.status_code == 202
        completed = _wait_for_event(client, "sort_completed")
        requested_id = first.json()["id"]

        assert client.post(f"/api/v1/arm/events/{requested_id}/feedback", json={"correct": True}).status_code == 409
        first_feedback = client.post(f"/api/v1/arm/events/{completed['id']}/feedback", json={"correct": True})
        assert first_feedback.status_code == 200
        assert first_feedback.json()["correct"] is True
        updated = client.post(f"/api/v1/arm/events/{completed['id']}/feedback", json={"correct": False})
        assert updated.status_code == 200
        assert updated.json()["correct"] is False

        second = client.post("/api/v1/arm/commands", json={"action": "sort", "class_name": "plastic"})
        assert second.status_code == 202
        second_completed = _wait_for_event(client, "sort_completed", count=2)
        assert (
            client.post(f"/api/v1/arm/events/{second_completed['id']}/feedback", json={"correct": True}).status_code
            == 200
        )

        assert client.post("/api/v1/arm/events/9999/feedback", json={"correct": True}).status_code == 404
        assert client.get("/api/v1/arm/accuracy").json() == {"accuracy": 0.5, "correct": 1, "total": 2}
        status = client.get("/api/v1/arm/status").json()
        assert status["accuracy"] == 0.5
        assert status["total_feedback"] == 2


def test_statistics_exposes_arm_feedback_accuracy(monkeypatch):
    monkeypatch.setenv("MIRA_HARDWARE_INTERVAL", "0.5")
    stats = Statistics(
        period_start="2026-01-01T00:00:00+00:00",
        period_end="2026-01-01T00:01:00+00:00",
        total_detections=0,
        class_counts={},
        avg_confidence={},
    )
    monkeypatch.setattr(main.camera_service, "get_statistics", lambda period: stats)
    with TestClient(app) as client:
        without_feedback = client.get("/api/statistics").json()["statistics"]
        assert without_feedback["sorting_accuracy"] is None

        get_db().execute(
            "INSERT INTO arm_events (ts, kind, class_name, payload_json, correct) VALUES (?, ?, ?, '{}', ?)",
            (time.time(), "sort_completed", WasteClass.GLASS.value, 1),
        )
        with_feedback = client.get("/api/statistics").json()["statistics"]
        assert with_feedback["sorting_accuracy"] == 1.0
