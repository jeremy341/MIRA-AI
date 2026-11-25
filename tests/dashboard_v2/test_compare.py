"""Tests for the v1 model comparison API."""

from __future__ import annotations

import asyncio
import base64
import json
import threading
from io import BytesIO
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest
from fastapi.testclient import TestClient
from PIL import Image

from src.dashboard.backend.main import app, websocket_handler
from src.dashboard.backend.v1 import model_runner
from src.dashboard.backend.v1.routers import compare as compare_router
from src.dashboard.backend.v1.state import get_db


class _FakeBoxes:
    def __init__(self, class_id: int):
        self.cls = [class_id]
        self.conf = [0.8]
        self.xyxy = [[4, 5, 22, 25]]
        self.id = [17]

    def __len__(self):
        return 1


class _FakeModel:
    def __init__(self, name: str, class_id: int, calls: list[tuple[str, np.ndarray, str]]):
        self.name = name
        self.class_id = class_id
        self.calls = calls

    def predict(self, frame, imgsz, conf, iou, verbose):
        self.calls.append((self.name, frame, threading.current_thread().name))
        return [SimpleNamespace(boxes=_FakeBoxes(self.class_id))]


@pytest.fixture
def api_client(monkeypatch):
    monkeypatch.setattr(websocket_handler, "_broadcast_queue", asyncio.Queue(maxsize=32))
    with TestClient(app) as client:
        yield client


@pytest.fixture
def fake_models(tmp_path, monkeypatch):
    for name in ("alpha.pt", "beta.pt"):
        (tmp_path / name).write_bytes(b"weights")
    monkeypatch.setattr(model_runner, "DETECTION_DIR", tmp_path)
    calls: list[tuple[str, np.ndarray, str]] = []
    model_runner.set_model_factory(
        lambda path, task: _FakeModel(Path(path).name, 0 if Path(path).name == "alpha.pt" else 3, calls)
    )
    yield calls
    model_runner.set_model_factory(None)


def _encoded_image(
    size: tuple[int, int] = (40, 32), image_format: str = "JPEG", orientation: int | None = None
) -> bytes:
    image = Image.new("RGB", size, color=(125, 130, 135))
    payload = BytesIO()
    save_options = {}
    if orientation is not None:
        exif = Image.Exif()
        exif[274] = orientation
        save_options["exif"] = exif
    image.save(payload, format=image_format, **save_options)
    return payload.getvalue()


def _post_compare(client, payload: bytes, content_type: str = "image/jpeg", models: str = "alpha.pt,beta.pt"):
    return client.post(
        "/api/v1/compare",
        files={"image": ("sample.jpg", payload, content_type)},
        data={"models": models, "confidence": "0.3"},
    )


def test_compare_runs_sequentially_on_one_frame_and_persists_without_previews(api_client, fake_models):
    response = _post_compare(api_client, _encoded_image((1300, 1200)))

    assert response.status_code == 200
    payload = response.json()
    assert payload["input_name"] == "sample.jpg"
    assert [model["name"] for model in payload["models"]] == ["alpha.pt", "beta.pt"]
    assert [call[0] for call in fake_models] == ["alpha.pt", "beta.pt"]
    assert all(call[2].startswith("asyncio_") for call in fake_models)
    assert fake_models[0][1] is fake_models[1][1]
    assert max(fake_models[0][1].shape[:2]) == 1280
    assert payload["models"][0]["class_counts"] == {
        "glass": 1,
        "metal": 0,
        "paper": 0,
        "plastic": 0,
        "trash": 0,
    }
    assert payload["models"][1]["class_counts"]["plastic"] == 1
    assert payload["models"][0]["avg_confidence"] == pytest.approx(0.8)
    assert payload["models"][0]["detections"] == [
        {"class_name": "glass", "confidence": 0.8, "bbox": [4, 5, 22, 25], "track_id": 17}
    ]
    assert payload["models"][0]["latency_ms"] >= 0
    preview = payload["models"][0]["annotated_image"]
    assert preview.startswith("data:image/jpeg;base64,")
    assert base64.b64decode(preview.partition(",")[2]).startswith(b"\xff\xd8")
    assert set(payload["winner_hint"]) >= {"fastest_model", "most_objects_model", "highest_avg_confidence_model"}
    assert "accuracy" in payload["winner_hint"]["note"].lower()

    row = get_db().query_one("SELECT models_json, results_json FROM comparisons WHERE id=?", (payload["id"],))
    stored_results = json.loads(row["results_json"])
    assert json.loads(row["models_json"]) == ["alpha.pt", "beta.pt"]
    assert all("annotated_image" not in model for model in stored_results["models"])

    comparison_list = api_client.get("/api/v1/compare?limit=20").json()["comparisons"]
    assert len(comparison_list) == 1
    assert all("annotated_image" not in model for model in comparison_list[0]["models"])
    full_record = api_client.get(f"/api/v1/compare/{payload['id']}")
    assert full_record.status_code == 200
    assert all("annotated_image" not in model for model in full_record.json()["models"])


@pytest.mark.parametrize(
    ("models", "bad_name"),
    [
        ("alpha.pt", None),
        ("alpha.pt,beta.pt,gamma.pt,delta.pt,epsilon.pt", None),
        ("alpha.pt,alpha.pt", "alpha.pt"),
        ("alpha.pt,missing.pt", "missing.pt"),
    ],
)
def test_compare_rejects_invalid_model_selections(api_client, fake_models, models, bad_name):
    response = _post_compare(api_client, _encoded_image(), models=models)

    assert response.status_code == 422
    if bad_name:
        assert bad_name in response.json()["detail"]


def test_compare_rejects_non_jpeg_png_media_type(api_client, fake_models):
    response = _post_compare(api_client, b"gif data", content_type="image/gif")

    assert response.status_code == 415
    assert "JPEG" in response.json()["detail"] and "PNG" in response.json()["detail"]


def test_compare_rejects_upload_larger_than_eight_megabytes(api_client, fake_models):
    response = _post_compare(api_client, b"x" * (8 * 1024 * 1024 + 1))

    assert response.status_code == 413


def test_compare_rejects_images_larger_than_sixteen_megapixels(api_client, fake_models):
    response = _post_compare(api_client, _encoded_image((4001, 4000)))

    assert response.status_code == 422
    assert "16 megapixels" in response.json()["detail"]


def test_compare_transposes_exif_orientation_before_downscaling(api_client, fake_models):
    response = _post_compare(api_client, _encoded_image((1400, 500), orientation=6))

    assert response.status_code == 200
    assert fake_models[0][1].shape[0] == 1280
    assert fake_models[0][1].shape[1] < 500


def test_compare_maps_pillow_decompression_bomb_errors_to_422(api_client, fake_models, monkeypatch):
    def raise_decompression_error(*args, **kwargs):
        raise Image.DecompressionBombError("too many pixels")

    monkeypatch.setattr(compare_router.Image, "open", raise_decompression_error)
    response = _post_compare(api_client, _encoded_image())

    assert response.status_code == 422
    assert "16 megapixels" in response.json()["detail"]


def test_compare_rejects_invalid_image_bytes(api_client, fake_models):
    response = _post_compare(api_client, b"not actually a JPEG")

    assert response.status_code == 422


def test_compare_validates_confidence(api_client, fake_models):
    response = api_client.post(
        "/api/v1/compare",
        files={"image": ("sample.jpg", _encoded_image(), "image/jpeg")},
        data={"models": "alpha.pt,beta.pt", "confidence": "0.01"},
    )

    assert response.status_code == 422


def test_compare_delete_returns_no_content_and_unknown_ids_return_404(api_client, fake_models):
    response = _post_compare(api_client, _encoded_image())
    comparison_id = response.json()["id"]

    assert api_client.delete(f"/api/v1/compare/{comparison_id}").status_code == 204
    assert api_client.delete(f"/api/v1/compare/{comparison_id}").status_code == 404
