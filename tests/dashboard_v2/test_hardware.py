"""Hardware sampler and API coverage without requiring platform sensors."""

from __future__ import annotations

import asyncio
import time
from types import SimpleNamespace

from fastapi.testclient import TestClient
import pytest

from src.dashboard.backend import main as dashboard_main
from src.dashboard.backend.main import app
from src.dashboard.backend.v1 import hardware_sampler
from src.dashboard.backend.v1.routers import hardware
from src.dashboard.backend.v1.state import get_db, get_events


def _disable_sampler_writes(monkeypatch):
    async def sample_without_writing(self):
        return {}

    monkeypatch.setattr(hardware_sampler.HardwareSampler, "sample_once", sample_without_writing)


@pytest.fixture(autouse=True)
def _reset_app_queues():
    # The legacy video handler is a process singleton; each TestClient uses a fresh event loop.
    dashboard_main.websocket_handler._broadcast_queue = asyncio.Queue(maxsize=32)
    yield
    dashboard_main.websocket_handler._broadcast_queue = asyncio.Queue(maxsize=32)


def test_temperature_sensor_preference_and_fallbacks(monkeypatch, tmp_path):
    read_vcgencmd_temperature = hardware_sampler._read_vcgencmd_temperature
    sensors = {
        "acpitz": [SimpleNamespace(current=29.0)],
        "coretemp": [SimpleNamespace(current=51.5)],
    }
    assert hardware_sampler._temperature_from_sensors(sensors) == 51.5

    monkeypatch.setattr(hardware_sampler, "_read_psutil_temperature", lambda: None)
    monkeypatch.setattr(hardware_sampler, "_read_thermal_zone_temperature", lambda: 47.8)
    monkeypatch.setattr(hardware_sampler, "_read_vcgencmd_temperature", lambda: 88.0)
    assert hardware_sampler.read_temperature() == 47.8

    monkeypatch.setattr(hardware_sampler, "_read_thermal_zone_temperature", lambda: None)
    monkeypatch.setattr(hardware_sampler, "is_raspberry_pi", lambda: True)
    monkeypatch.setattr(hardware_sampler.shutil, "which", lambda name: "vcgencmd.exe")
    monkeypatch.setattr(
        hardware_sampler.subprocess,
        "run",
        lambda *args, **kwargs: SimpleNamespace(returncode=0, stdout="temp=62.4'C\n"),
    )
    monkeypatch.setattr(hardware_sampler, "_read_vcgencmd_temperature", read_vcgencmd_temperature)
    assert hardware_sampler.read_temperature() == 62.4


def test_temperature_readers_ignore_sensor_failures(monkeypatch):
    monkeypatch.setattr(hardware_sampler, "_read_psutil_temperature", lambda: (_ for _ in ()).throw(OSError("sensor")))
    monkeypatch.setattr(
        hardware_sampler, "_read_thermal_zone_temperature", lambda: (_ for _ in ()).throw(OSError("zone"))
    )
    monkeypatch.setattr(hardware_sampler, "_read_vcgencmd_temperature", lambda: None)
    assert hardware_sampler.read_temperature() is None


def test_thermal_zone_millidegree_conversion(tmp_path):
    temperature_file = tmp_path / "temp"
    temperature_file.write_text("50375\n", encoding="ascii")
    assert hardware_sampler._read_thermal_zone_temperature(temperature_file) == 50.375


def test_pruning_removes_samples_older_than_retention():
    db = get_db()
    db.executemany(
        "INSERT INTO hardware_samples (ts, cpu_percent, memory_percent) VALUES (?, ?, ?)",
        [(6000.0, 1.0, 2.0), (7000.0, 3.0, 4.0), (9000.0, 5.0, 6.0)],
    )
    assert hardware_sampler.prune_hardware_samples(db, keep_hours=1, now=10000.0) == 1
    assert [row["ts"] for row in db.query("SELECT ts FROM hardware_samples ORDER BY ts")] == [7000.0, 9000.0]


def test_sampler_publishes_every_fifth_sample(monkeypatch):
    monkeypatch.setattr(
        hardware_sampler,
        "read_hardware_metrics",
        lambda: {
            "cpu_percent": 12.0,
            "memory_percent": 34.0,
            "memory_used_mb": 100.0,
            "memory_total_mb": 300.0,
            "temperature_c": None,
            "load_1m": 0.5,
            "platform": "test",
            "is_raspberry_pi": False,
            "cpu_count": 4,
        },
    )

    async def sample_five_times():
        queue = get_events().subscribe()
        sampler = hardware_sampler.HardwareSampler(interval=0.5)
        for _ in range(5):
            await sampler.sample_once()
        await asyncio.sleep(0)
        event = queue.get_nowait()
        get_events().unsubscribe(queue)
        return event

    event = asyncio.run(sample_five_times())
    assert event["type"] == "hardware_sample"
    assert event["data"]["cpu_percent"] == 12.0


def test_current_hardware_shape_and_history_downsampling(monkeypatch):
    monkeypatch.setenv("MIRA_HARDWARE_INTERVAL", "0.5")
    _disable_sampler_writes(monkeypatch)
    metrics = {
        "cpu_percent": 10.0,
        "memory_percent": 20.0,
        "memory_used_mb": 30.0,
        "memory_total_mb": 40.0,
        "temperature_c": None,
        "load_1m": None,
        "platform": "test",
        "is_raspberry_pi": False,
        "cpu_count": 2,
    }
    monkeypatch.setattr(hardware, "read_hardware_metrics", lambda: metrics)
    monkeypatch.setattr(hardware_sampler, "read_hardware_metrics", lambda: metrics)
    now = time.time()
    get_db().executemany(
        "INSERT INTO hardware_samples (ts, cpu_percent, memory_percent, temperature_c, load_1m) VALUES (?, ?, ?, ?, ?)",
        [
            (now - 25, 20.0, 40.0, None, None),
            (now - 15, 40.0, 60.0, 50.0, None),
            (now - 500, 10.0, 30.0, 40.0, None),
        ],
    )
    with TestClient(app) as client:
        current = client.get("/api/v1/hardware/current")
        assert current.status_code == 200
        assert current.json()["memory_total_mb"] == 40.0
        assert current.json()["is_raspberry_pi"] is False

        history = client.get("/api/v1/hardware/history", params={"minutes": 60, "points": 10})
        assert history.status_code == 200
        result = history.json()
        assert result["minutes"] == 60
        assert len(result["points"]) == 2
        newest = max(result["points"], key=lambda point: point["ts"])
        assert newest["cpu_percent"] == 30.0
        assert newest["memory_percent"] == 50.0
        assert newest["temperature_c"] == 50.0


def test_history_empty_window_and_parameter_bounds(monkeypatch):
    monkeypatch.setenv("MIRA_HARDWARE_INTERVAL", "0.5")
    _disable_sampler_writes(monkeypatch)
    with TestClient(app) as client:
        response = client.get("/api/v1/hardware/history", params={"minutes": 1, "points": 10})
        assert response.status_code == 200
        assert response.json() == {"points": [], "minutes": 1}
        assert client.get("/api/v1/hardware/history", params={"minutes": 0}).status_code == 422
        assert client.get("/api/v1/hardware/history", params={"points": 1001}).status_code == 422
