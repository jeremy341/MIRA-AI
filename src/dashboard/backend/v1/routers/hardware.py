"""Hardware API. Owner and contract: docs/dashboard-v2/CONTRACT.md."""

from __future__ import annotations

import asyncio
import time
from datetime import datetime, timezone

from fastapi import APIRouter, Query

from ..hardware_sampler import HardwareSampler, read_hardware_metrics
from ..state import get_db

router = APIRouter(tags=["Hardware"])
_sampler: HardwareSampler | None = None


async def on_startup() -> None:
    global _sampler
    _sampler = HardwareSampler()
    await _sampler.start()


async def on_shutdown() -> None:
    global _sampler
    if _sampler is not None:
        await _sampler.stop()
        _sampler = None


@router.get("/hardware/current")
async def hardware_current() -> dict:
    metrics = await asyncio.to_thread(read_hardware_metrics)
    return {"ts": datetime.now(timezone.utc).isoformat(), **metrics}


def _mean(values: list[float | None]) -> float | None:
    valid_values = [float(value) for value in values if value is not None]
    return sum(valid_values) / len(valid_values) if valid_values else None


@router.get("/hardware/history")
def hardware_history(
    minutes: int = Query(default=60, ge=1, le=1440), points: int = Query(default=240, ge=10, le=1000)
) -> dict:
    now = time.time()
    start = now - minutes * 60
    samples = get_db().query(
        "SELECT ts, cpu_percent, memory_percent, temperature_c FROM hardware_samples "
        "WHERE ts >= ? AND ts <= ? ORDER BY ts ASC",
        (start, now),
    )
    buckets: dict[int, list] = {}
    for sample in samples:
        index = min(points - 1, int((sample["ts"] - start) / (minutes * 60) * points))
        buckets.setdefault(index, []).append(sample)

    history_points = []
    for index in sorted(buckets):
        bucket = buckets[index]
        timestamp = sum(row["ts"] for row in bucket) / len(bucket)
        history_points.append(
            {
                "ts": datetime.fromtimestamp(timestamp, timezone.utc).isoformat(),
                "cpu_percent": _mean([row["cpu_percent"] for row in bucket]),
                "memory_percent": _mean([row["memory_percent"] for row in bucket]),
                "temperature_c": _mean([row["temperature_c"] for row in bucket]),
            }
        )
    return {"points": history_points, "minutes": minutes}
