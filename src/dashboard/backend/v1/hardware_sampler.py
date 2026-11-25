"""Low-overhead Raspberry Pi friendly hardware sampling for the dashboard."""

from __future__ import annotations

import asyncio
import os
import platform
import re
import shutil
import subprocess
import time
from pathlib import Path
from typing import Any

import psutil

from .state import get_db, get_events

DEFAULT_INTERVAL_SECONDS = 2.0
DEFAULT_RETENTION_HOURS = 24.0
PREFERRED_TEMPERATURE_KEYS = ("cpu", "coretemp", "k10temp", "cpu_thermal", "soc_thermal")
THERMAL_ZONE_PATH = Path("/sys/class/thermal/thermal_zone0/temp")
DEVICE_TREE_MODEL_PATH = Path("/proc/device-tree/model")
CPU_INFO_PATH = Path("/proc/cpuinfo")


def _env_float(name: str, default: float, minimum: float | None = None) -> float:
    try:
        value = float(os.environ.get(name, default))
    except (TypeError, ValueError):
        return default
    if minimum is not None and value < minimum:
        return minimum
    return value


def sampling_interval() -> float:
    return _env_float("MIRA_HARDWARE_INTERVAL", DEFAULT_INTERVAL_SECONDS, minimum=0.5)


def retention_hours() -> float:
    return _env_float("MIRA_HARDWARE_RETENTION_HOURS", DEFAULT_RETENTION_HOURS, minimum=0.0)


def read_cpu_percent() -> float | None:
    try:
        return float(psutil.cpu_percent(interval=None))
    except Exception:
        return None


def read_memory() -> dict[str, float | None]:
    try:
        memory = psutil.virtual_memory()
        return {
            "percent": float(memory.percent),
            "used_mb": float(memory.used) / (1024 * 1024),
            "total_mb": float(memory.total) / (1024 * 1024),
        }
    except Exception:
        return {"percent": None, "used_mb": None, "total_mb": None}


def _temperature_from_sensors(sensors: dict[str, Any]) -> float | None:
    def readings_for(key: str) -> list[Any]:
        value = sensors.get(key, [])
        if isinstance(value, list | tuple):
            return list(value)
        return [value]

    keys = list(sensors)
    ordered_keys = sorted(
        keys,
        key=lambda key: next(
            (index for index, preferred in enumerate(PREFERRED_TEMPERATURE_KEYS) if preferred in key.lower()),
            len(PREFERRED_TEMPERATURE_KEYS),
        ),
    )
    for key in ordered_keys:
        for reading in readings_for(key):
            current = reading.get("current") if isinstance(reading, dict) else getattr(reading, "current", None)
            if current is not None:
                try:
                    return float(current)
                except (TypeError, ValueError):
                    continue
    return None


def _read_psutil_temperature() -> float | None:
    sensors = psutil.sensors_temperatures(fahrenheit=False)
    return _temperature_from_sensors(sensors)


def _read_thermal_zone_temperature(path: Path = THERMAL_ZONE_PATH) -> float | None:
    try:
        raw = path.read_text(encoding="ascii").strip()
        return float(raw) / 1000.0
    except (OSError, ValueError):
        return None


def is_raspberry_pi(
    model_path: Path = DEVICE_TREE_MODEL_PATH,
    cpuinfo_path: Path = CPU_INFO_PATH,
) -> bool:
    for path in (model_path, cpuinfo_path):
        try:
            contents = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        if "raspberry pi" in contents.lower():
            return True
    return False


def _read_vcgencmd_temperature() -> float | None:
    if not is_raspberry_pi():
        return None
    executable = shutil.which("vcgencmd")
    if not executable:
        return None
    try:
        result = subprocess.run(
            [executable, "measure_temp"],
            capture_output=True,
            text=True,
            timeout=1.0,
            check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    if result.returncode != 0:
        return None
    match = re.search(r"temp=([-+]?\d+(?:\.\d+)?)\s*'C", result.stdout)
    return float(match.group(1)) if match else None


def read_temperature() -> float | None:
    for reader in (_read_psutil_temperature, _read_thermal_zone_temperature, _read_vcgencmd_temperature):
        try:
            temperature = reader()
        except Exception:
            continue
        if temperature is not None:
            return temperature
    return None


def read_load_1m() -> float | None:
    try:
        return float(os.getloadavg()[0])
    except (AttributeError, OSError):
        return None


def read_cpu_count() -> int | None:
    try:
        return psutil.cpu_count()
    except Exception:
        return None


def read_hardware_metrics() -> dict[str, Any]:
    memory = read_memory()
    return {
        "cpu_percent": read_cpu_percent(),
        "memory_percent": memory["percent"],
        "memory_used_mb": memory["used_mb"],
        "memory_total_mb": memory["total_mb"],
        "temperature_c": read_temperature(),
        "load_1m": read_load_1m(),
        "platform": platform.system(),
        "is_raspberry_pi": is_raspberry_pi(),
        "cpu_count": read_cpu_count(),
    }


def prune_hardware_samples(db, keep_hours: float, now: float | None = None) -> int:
    cutoff = (time.time() if now is None else now) - keep_hours * 3600
    cursor = db.execute("DELETE FROM hardware_samples WHERE ts < ?", (cutoff,))
    return cursor.rowcount


class HardwareSampler:
    def __init__(self, interval: float | None = None, keep_hours: float | None = None):
        self.interval = sampling_interval() if interval is None else max(0.5, interval)
        self.keep_hours = retention_hours() if keep_hours is None else max(0.0, keep_hours)
        self._task: asyncio.Task | None = None
        self._sample_count = 0

    async def start(self) -> None:
        if self._task is None or self._task.done():
            self._task = asyncio.create_task(self._run(), name="mira-hardware-sampler")

    async def stop(self) -> None:
        if self._task is None:
            return
        self._task.cancel()
        try:
            await self._task
        except asyncio.CancelledError:
            pass
        self._task = None

    async def sample_once(self) -> dict[str, Any]:
        metrics = await asyncio.to_thread(read_hardware_metrics)
        ts = time.time()
        get_db().execute(
            "INSERT INTO hardware_samples (ts, cpu_percent, memory_percent, temperature_c, load_1m) "
            "VALUES (?, ?, ?, ?, ?)",
            (ts, metrics["cpu_percent"], metrics["memory_percent"], metrics["temperature_c"], metrics["load_1m"]),
        )
        self._sample_count += 1
        sample = {"ts": ts, **{key: metrics[key] for key in ("cpu_percent", "memory_percent", "temperature_c")}}
        if self._sample_count % 5 == 0:
            get_events().publish("hardware_sample", sample)
        return sample

    async def _run(self) -> None:
        last_prune = time.monotonic()
        while True:
            try:
                await self.sample_once()
                now = time.monotonic()
                if now - last_prune >= 3600:
                    await asyncio.to_thread(prune_hardware_samples, get_db(), self.keep_hours)
                    last_prune = now
                await asyncio.sleep(self.interval)
            except asyncio.CancelledError:
                raise
            except Exception:
                # A transient database or platform failure must not kill the sampler task.
                await asyncio.sleep(self.interval)
