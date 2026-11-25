"""Tests for the v1 benchmark jobs API without loading real model weights."""

from __future__ import annotations

import asyncio
import json
import threading
import time
from dataclasses import dataclass, field

import pytest
from fastapi.testclient import TestClient

from src.dashboard.backend.main import app, websocket_handler
from src.dashboard.backend.v1.routers import benchmark as benchmark_router
from src.dashboard.backend.v1.state import get_db, get_jobs
from src.pipeline.benchmark import BenchmarkResult, PerClassMetrics


@dataclass
class _Harness:
    calls: list[dict] = field(default_factory=list)
    block_model: str | None = None
    started: threading.Event = field(default_factory=threading.Event)
    release: threading.Event = field(default_factory=threading.Event)
    fail_model: str | None = None


class _FakeRegistry:
    available = {"alpha.pt", "beta.pt"}

    def __init__(self):
        self.names: set[str] = set()

    def discover(self):
        self.names = set(self.available)
        return len(self.names)

    def get_model(self, name):
        if name not in self.names:
            raise KeyError(name)
        return {"path": name}

    def list_models(self):
        return [{"name": name} for name in sorted(self.names)]


class _FakeModelBenchmark:
    harness: _Harness

    def __init__(self, model_name: str):
        self.model_name = model_name

    @classmethod
    def from_registry(cls, model_names, dataset_path, conf, max_images):
        name = model_names[0]
        cls.harness.calls.append(
            {"model_names": model_names, "dataset_path": str(dataset_path), "conf": conf, "max_images": max_images}
        )
        return cls(name)

    def run(self):
        harness = type(self).harness
        if self.model_name == harness.block_model:
            harness.started.set()
            if not harness.release.wait(5):
                raise RuntimeError("test did not release the fake benchmark")
        if self.model_name == harness.fail_model:
            raise RuntimeError("benchmark failed for test")
        return [_result(self.model_name)]


def _result(name: str) -> BenchmarkResult:
    return BenchmarkResult(
        model_name=name,
        model_path=f"weights/{name}",
        model_type="yolo_pt",
        total_images=3,
        per_class={"glass": PerClassMetrics(tp=2, fp=1, fn=1)},
        overall_f1=0.66,
        overall_precision=0.67,
        overall_recall=0.65,
        avg_latency_ms=12.5,
        total_detections=4,
        map50=0.71,
        map50_95=0.49,
        errors=["one unreadable image"],
    )


@pytest.fixture
def api_client(monkeypatch):
    monkeypatch.setattr(websocket_handler, "_broadcast_queue", asyncio.Queue(maxsize=32))
    with TestClient(app) as client:
        yield client


@pytest.fixture
def benchmark_doubles(monkeypatch):
    harness = _Harness()
    _FakeModelBenchmark.harness = harness
    monkeypatch.setattr(benchmark_router, "ModelRegistry", _FakeRegistry, raising=False)
    monkeypatch.setattr(benchmark_router, "ModelBenchmark", _FakeModelBenchmark, raising=False)
    return harness


def _wait_for(predicate, timeout: float = 5.0) -> bool:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if predicate():
            return True
        time.sleep(0.01)
    return False


def _submit(client, dataset: str, models: list[str] | None = None, **extra):
    body = {"models": models or ["alpha.pt", "beta.pt"], "dataset": dataset, **extra}
    return client.post("/api/v1/benchmark/runs", json=body)


def test_benchmark_persists_results_and_maps_pipeline_fields(api_client, benchmark_doubles, tmp_path):
    response = _submit(api_client, str(tmp_path), confidence=0.4, max_images=7)

    assert response.status_code == 202
    run_id, job_id = response.json()["run_id"], response.json()["job_id"]
    assert _wait_for(lambda: get_jobs().get(job_id).status == "completed")

    detail = api_client.get(f"/api/v1/benchmark/runs/{run_id}")
    assert detail.status_code == 200
    payload = detail.json()
    assert payload["status"] == "completed"
    assert payload["job_id"] == job_id
    assert payload["config"] == {
        "models": ["alpha.pt", "beta.pt"],
        "dataset": str(tmp_path),
        "confidence": 0.4,
        "max_images": 7,
    }
    assert [result["model"] for result in payload["results"]] == ["alpha.pt", "beta.pt"]
    first = payload["results"][0]
    assert first == {
        "model": "alpha.pt",
        "map50": 0.71,
        "map50_95": 0.49,
        "precision": 0.67,
        "recall": 0.65,
        "f1": 0.66,
        "avg_latency_ms": 12.5,
        "fps": None,
        "per_class": {
            "glass": {
                "tp": 2,
                "fp": 1,
                "fn": 1,
                "precision": pytest.approx(2 / 3),
                "recall": pytest.approx(2 / 3),
                "f1": pytest.approx(2 / 3),
            }
        },
        "errors": ["one unreadable image"],
    }
    assert [call["model_names"] for call in benchmark_doubles.calls] == [["alpha.pt"], ["beta.pt"]]
    assert [call["conf"] for call in benchmark_doubles.calls] == [0.4, 0.4]
    listed = api_client.get("/api/v1/benchmark/runs?limit=20").json()["runs"]
    assert len(listed) == 1 and listed[0]["id"] == run_id
    row = get_db().query_one(
        "SELECT status, config_json, results_json, job_id FROM benchmark_runs WHERE id=?", (run_id,)
    )
    assert row["status"] == "completed" and row["job_id"] == job_id
    assert json.loads(row["results_json"])[0]["fps"] is None


@pytest.mark.parametrize(
    "body",
    [
        {"models": []},
        {"models": ["alpha.pt"] * 7},
        {"models": ["missing.pt"]},
        {"models": ["alpha.pt"], "confidence": 0.01},
        {"models": ["alpha.pt"], "max_images": 0},
        {"models": ["alpha.pt"], "max_images": 5001},
    ],
)
def test_benchmark_rejects_invalid_configurations(api_client, benchmark_doubles, tmp_path, body):
    response = api_client.post("/api/v1/benchmark/runs", json={"dataset": str(tmp_path), **body})

    assert response.status_code == 422


def test_benchmark_rejects_nonexistent_or_non_yaml_dataset_file(api_client, benchmark_doubles, tmp_path):
    missing = api_client.post(
        "/api/v1/benchmark/runs", json={"models": ["alpha.pt"], "dataset": str(tmp_path / "missing.yaml")}
    )
    invalid_file = tmp_path / "labels.txt"
    invalid_file.write_text("", encoding="utf-8")
    wrong_type = api_client.post("/api/v1/benchmark/runs", json={"models": ["alpha.pt"], "dataset": str(invalid_file)})

    assert missing.status_code == 422
    assert wrong_type.status_code == 422


def test_benchmark_uses_cli_default_dataset_resolution(api_client, benchmark_doubles, monkeypatch, tmp_path):
    default_dataset = tmp_path / "default.yaml"
    default_dataset.write_text("path: .\nval: images/val\n", encoding="utf-8")
    monkeypatch.setattr(
        benchmark_router, "resolve_detection_data_yaml", lambda path=None: default_dataset, raising=False
    )

    response = api_client.post("/api/v1/benchmark/runs", json={"models": ["alpha.pt"]})

    assert response.status_code == 202
    run_id, job_id = response.json()["run_id"], response.json()["job_id"]
    assert _wait_for(lambda: get_jobs().get(job_id).status == "completed")
    assert api_client.get(f"/api/v1/benchmark/runs/{run_id}").json()["config"]["dataset"] == str(default_dataset)


def test_benchmark_reports_per_model_progress(api_client, benchmark_doubles, tmp_path):
    benchmark_doubles.block_model = "beta.pt"
    response = _submit(api_client, str(tmp_path))
    run_id, job_id = response.json()["run_id"], response.json()["job_id"]

    try:
        assert benchmark_doubles.started.wait(5)
        job = get_jobs().get(job_id)
        assert job.progress == pytest.approx(0.5)
        assert api_client.get(f"/api/v1/benchmark/runs/{run_id}").json()["status"] == "running"
    finally:
        benchmark_doubles.release.set()
    assert _wait_for(lambda: get_jobs().get(job_id).status == "completed")


def test_benchmark_cancellation_is_persisted_between_models(api_client, benchmark_doubles, tmp_path):
    benchmark_doubles.block_model = "alpha.pt"
    response = _submit(api_client, str(tmp_path), models=["alpha.pt", "beta.pt"])
    run_id, job_id = response.json()["run_id"], response.json()["job_id"]

    try:
        assert benchmark_doubles.started.wait(5)
        get_jobs().cancel(job_id)
    finally:
        benchmark_doubles.release.set()
    assert _wait_for(lambda: get_jobs().get(job_id).status == "cancelled")
    assert api_client.get(f"/api/v1/benchmark/runs/{run_id}").json()["status"] == "cancelled"
    assert [call["model_names"] for call in benchmark_doubles.calls] == [["alpha.pt"]]


def test_queued_benchmark_cancellation_updates_the_run(api_client, benchmark_doubles, tmp_path):
    jobs = get_jobs()
    release_workers = threading.Event()
    started_workers = [threading.Event(), threading.Event()]

    def occupy_worker(ctx, started):
        started.set()
        release_workers.wait(5)
        return {}

    jobs.submit("test-blocker", lambda ctx: occupy_worker(ctx, started_workers[0]))
    jobs.submit("test-blocker", lambda ctx: occupy_worker(ctx, started_workers[1]))
    assert all(event.wait(5) for event in started_workers)
    response = _submit(api_client, str(tmp_path), models=["alpha.pt"])
    run_id, job_id = response.json()["run_id"], response.json()["job_id"]

    try:
        assert get_jobs().get(job_id).status == "queued"
        get_jobs().cancel(job_id)
    finally:
        release_workers.set()
    assert _wait_for(lambda: get_jobs().get(job_id).status == "cancelled")
    assert _wait_for(lambda: api_client.get(f"/api/v1/benchmark/runs/{run_id}").json()["status"] == "cancelled")


def test_benchmark_failure_is_persisted(api_client, benchmark_doubles, tmp_path):
    benchmark_doubles.fail_model = "alpha.pt"
    response = _submit(api_client, str(tmp_path), models=["alpha.pt"])
    run_id, job_id = response.json()["run_id"], response.json()["job_id"]

    assert _wait_for(lambda: get_jobs().get(job_id).status == "failed")
    assert api_client.get(f"/api/v1/benchmark/runs/{run_id}").json()["status"] == "failed"


def test_benchmark_delete_is_blocked_while_running_and_succeeds_after_completion(
    api_client, benchmark_doubles, tmp_path
):
    benchmark_doubles.block_model = "alpha.pt"
    response = _submit(api_client, str(tmp_path), models=["alpha.pt"])
    run_id, job_id = response.json()["run_id"], response.json()["job_id"]

    try:
        assert benchmark_doubles.started.wait(5)
        assert api_client.delete(f"/api/v1/benchmark/runs/{run_id}").status_code == 409
    finally:
        benchmark_doubles.release.set()
    assert _wait_for(lambda: get_jobs().get(job_id).status == "completed")
    assert api_client.delete(f"/api/v1/benchmark/runs/{run_id}").status_code == 204
    assert api_client.get(f"/api/v1/benchmark/runs/{run_id}").status_code == 404
