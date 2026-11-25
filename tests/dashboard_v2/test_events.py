"""Events WebSocket fan-out contract tests."""

from __future__ import annotations

import asyncio

import pytest
from fastapi.testclient import TestClient

from src.dashboard.backend import main as dashboard_main
from src.dashboard.backend.main import app
from src.dashboard.backend.v1.state import get_events


@pytest.fixture(autouse=True)
def _fresh_video_queue():
    dashboard_main.websocket_handler._broadcast_queue = asyncio.Queue(maxsize=32)
    yield
    dashboard_main.websocket_handler._broadcast_queue = asyncio.Queue(maxsize=32)


def test_events_websocket_hello_and_event_delivery_order(monkeypatch):
    monkeypatch.setenv("MIRA_HARDWARE_INTERVAL", "0.5")
    with TestClient(app) as client:
        with client.websocket_connect("/ws/v1/events") as websocket:
            hello = websocket.receive_json()
            assert hello["type"] == "hello"
            assert hello["data"] == {"version": 1}
            get_events().publish("job_progress", {"step": 1})
            get_events().publish("arm_event", {"step": 2})
            get_events().publish("job_finished", {"step": 3})
            received = [websocket.receive_json() for _ in range(3)]
            assert [event["type"] for event in received] == ["job_progress", "arm_event", "job_finished"]
            assert [event["data"]["step"] for event in received] == [1, 2, 3]
