"""Benchmark API. Owner and contract: docs/dashboard-v2/CONTRACT.md."""

from __future__ import annotations

import asyncio
import json
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from starlette.responses import Response

from src.cli.inference import resolve_detection_data_yaml
from src.pipeline.benchmark import ModelBenchmark
from src.pipeline.models import ModelRegistry

from ..events import EventBus
from ..jobs import JobCancelledError, JobContext
from ..state import get_db, get_events, get_jobs

router = APIRouter(tags=["Benchmark"])
_job_events: asyncio.Queue | None = None
_job_event_task: asyncio.Task | None = None
_job_event_bus: EventBus | None = None


async def on_startup() -> None:
    global _job_events, _job_event_task, _job_event_bus
    _job_event_bus = get_events()
    _job_events = _job_event_bus.subscribe()
    _job_event_task = asyncio.create_task(_sync_finished_jobs(_job_events))


async def on_shutdown() -> None:
    global _job_events, _job_event_task, _job_event_bus
    if _job_event_task is not None:
        _job_event_task.cancel()
        try:
            await _job_event_task
        except asyncio.CancelledError:
            pass
    if _job_event_bus is not None and _job_events is not None:
        _job_event_bus.unsubscribe(_job_events)
    _job_events = None
    _job_event_task = None
    _job_event_bus = None


async def _sync_finished_jobs(queue: asyncio.Queue) -> None:
    while True:
        event = await queue.get()
        if event.get("type") != "job_finished":
            continue
        data = event.get("data", {})
        job_id, status = data.get("job_id"), data.get("status")
        if job_id and status in {"completed", "failed", "cancelled"}:
            get_db().execute("UPDATE benchmark_runs SET status=? WHERE job_id=?", (status, job_id))


class BenchmarkRequest(BaseModel):
    models: list[str] = Field(min_length=1, max_length=6)
    dataset: str | None = None
    confidence: float = Field(default=0.25, ge=0.05, le=1)
    max_images: int | None = Field(default=100, ge=1, le=5000)


def _resolve_dataset(dataset: str | None) -> str:
    if dataset is None:
        try:
            resolved = Path(resolve_detection_data_yaml(None)).expanduser().resolve()
        except (FileNotFoundError, OSError, SystemExit) as exc:
            message = str(exc) or "No default YOLO dataset was found."
            raise HTTPException(status_code=422, detail=message) from exc
    else:
        if not dataset.strip():
            raise HTTPException(status_code=422, detail="dataset must be a path to a YOLO dataset YAML or folder.")
        resolved = Path(dataset).expanduser().resolve()

    if not resolved.exists():
        raise HTTPException(status_code=422, detail=f"Dataset path does not exist: {resolved}")
    if resolved.is_file() and resolved.suffix.lower() not in {".yaml", ".yml"}:
        raise HTTPException(status_code=422, detail="Dataset file must be a YAML file.")
    if not resolved.is_file() and not resolved.is_dir():
        raise HTTPException(status_code=422, detail="Dataset path must be a YAML file or folder.")
    return str(resolved)


def _validate_models(names: list[str]) -> None:
    registry = ModelRegistry()
    registry.discover()
    available = {model["name"] for model in registry.list_models()}
    for name in names:
        if not name or name not in available:
            raise HTTPException(status_code=422, detail=f"Unknown benchmark model '{name}'.")


def _result_to_api(result: Any) -> dict[str, Any]:
    return {
        "model": result.model_name,
        "map50": result.map50,
        "map50_95": result.map50_95,
        "precision": result.overall_precision,
        "recall": result.overall_recall,
        "f1": result.overall_f1,
        "avg_latency_ms": result.avg_latency_ms,
        "fps": None,
        "per_class": {name: metrics.to_dict() for name, metrics in result.per_class.items()},
        "errors": list(result.errors),
    }


def _update_run(run_id: str, status: str, results: list[dict[str, Any]] | None) -> None:
    results_json = json.dumps(results) if results is not None else None
    get_db().execute("UPDATE benchmark_runs SET status=?, results_json=? WHERE id=?", (status, results_json, run_id))


def _run_payload(row) -> dict[str, Any]:
    return {
        "id": row["id"],
        "created_at": datetime.fromtimestamp(row["created_at_ts"], timezone.utc).isoformat(),
        "status": row["status"],
        "config": json.loads(row["config_json"]),
        "results": json.loads(row["results_json"]) if row["results_json"] is not None else None,
        "job_id": row["job_id"],
    }


@router.post("/benchmark/runs", status_code=202)
async def start_benchmark_run(request: BenchmarkRequest):
    dataset = _resolve_dataset(request.dataset)
    _validate_models(request.models)
    config = {
        "models": request.models,
        "dataset": dataset,
        "confidence": request.confidence,
        "max_images": request.max_images,
    }
    run_id = uuid.uuid4().hex
    created_at_ts = time.time()
    db = get_db()
    db.execute(
        "INSERT INTO benchmark_runs (id, created_at_ts, status, config_json, results_json, job_id) "
        "VALUES (?, ?, 'queued', ?, NULL, NULL)",
        (run_id, created_at_ts, json.dumps(config)),
    )

    def run(ctx: JobContext) -> dict[str, Any]:
        _update_run(run_id, "running", None)
        results: list[dict[str, Any]] = []
        try:
            for index, model_name in enumerate(request.models):
                ctx.raise_if_cancelled()
                benchmark = ModelBenchmark.from_registry(
                    model_names=[model_name],
                    dataset_path=dataset,
                    conf=request.confidence,
                    max_images=request.max_images,
                )
                model_results = benchmark.run()
                ctx.raise_if_cancelled()
                results.extend(_result_to_api(result) for result in model_results)
                _update_run(run_id, "running", results)
                ctx.progress(
                    (index + 1) / len(request.models), f"Benchmarked {index + 1} of {len(request.models)} models"
                )
            ctx.raise_if_cancelled()
        except JobCancelledError:
            _update_run(run_id, "cancelled", results)
            raise
        except Exception:
            _update_run(run_id, "failed", results)
            raise
        _update_run(run_id, "completed", results)
        return {"run_id": run_id, "results": results}

    try:
        job = get_jobs().submit("benchmark", run, title=f"Benchmark {', '.join(request.models)}")
        db.execute("UPDATE benchmark_runs SET job_id=? WHERE id=?", (job.id, run_id))
        current_job = get_jobs().get(job.id)
        if current_job is not None and current_job.status in {"completed", "failed", "cancelled"}:
            db.execute("UPDATE benchmark_runs SET status=? WHERE id=?", (current_job.status, run_id))
    except Exception as exc:
        db.execute("UPDATE benchmark_runs SET status='failed' WHERE id=?", (run_id,))
        raise HTTPException(status_code=500, detail=f"Could not start benchmark job: {exc}") from exc
    return {"run_id": run_id, "job_id": job.id}


@router.get("/benchmark/runs")
async def list_benchmark_runs(limit: int = Query(20, ge=1, le=100)):
    db = get_db()
    rows = db.query("SELECT * FROM benchmark_runs ORDER BY created_at_ts DESC LIMIT ?", (limit,))
    total = db.query_one("SELECT COUNT(*) AS count FROM benchmark_runs")["count"]
    return {"runs": [_run_payload(row) for row in rows], "total": total}


@router.get("/benchmark/runs/{run_id}")
async def get_benchmark_run(run_id: str):
    row = get_db().query_one("SELECT * FROM benchmark_runs WHERE id=?", (run_id,))
    if row is None:
        raise HTTPException(status_code=404, detail="Benchmark run not found.")
    return _run_payload(row)


@router.delete("/benchmark/runs/{run_id}", status_code=204)
async def delete_benchmark_run(run_id: str):
    db = get_db()
    with db.transaction():
        row = db.query_one("SELECT status FROM benchmark_runs WHERE id=?", (run_id,))
        if row is None:
            raise HTTPException(status_code=404, detail="Benchmark run not found.")
        if row["status"] in {"queued", "running"}:
            raise HTTPException(status_code=409, detail="A queued or running benchmark cannot be deleted.")
        db.execute("DELETE FROM benchmark_runs WHERE id=?", (run_id,))
    return Response(status_code=204)
