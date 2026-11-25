from io import BytesIO
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import HTTPException, Request
from PIL import Image

from src.dashboard.backend.camera_service import CameraService
from src.dashboard.backend.main import camera_service, detect_image
from src.dashboard.backend.models import ModelConfig


@pytest.fixture
def png():
    buffer = BytesIO()
    Image.new("RGB", (32, 24)).save(buffer, "PNG")
    return buffer.getvalue()


@pytest.mark.asyncio
async def test_still_uses_independent_predictor_without_history(monkeypatch, png):
    service = CameraService()
    service.model = MagicMock()
    config = ModelConfig(name="mock.pt", conf_threshold=0.25, reject_threshold=0.55)
    service.model_config = config
    still_model = MagicMock()
    still_model.predict.return_value = []
    monkeypatch.setattr(service, "_load_model", lambda *_: (still_model, config, False, 640))

    result = await service.detect_image(png, 0.65)

    assert result["detections"] == []
    assert result["image"].startswith("data:image/jpeg;base64,")
    assert still_model.predict.call_args.kwargs["conf"] == 0.65
    assert still_model.predict.call_args.args[0].shape == (24, 32, 3)
    service.model.predict.assert_not_called()
    assert not service.detection_history


@pytest.mark.asyncio
async def test_still_requires_model_and_stopped_stream(png):
    service = CameraService()
    with pytest.raises(RuntimeError, match="Load a model"):
        await service.detect_image(png, 0.55)
    service.is_streaming = True
    with pytest.raises(RuntimeError, match="Stop the camera"):
        await service.detect_image(png, 0.55)


def image_request(content, content_type=None):
    chunks = iter(content)

    async def receive():
        chunk = next(chunks, None)
        return {"type": "http.request", "body": chunk or b"", "more_body": chunk is not None}

    headers = [(b"content-type", content_type.encode())] if content_type else []
    return Request({"type": "http", "headers": headers}, receive=receive)


@pytest.mark.asyncio
async def test_upload_validates_content_and_bounds(monkeypatch, png):
    service = AsyncMock(return_value={"image": "preview", "detections": []})
    monkeypatch.setattr(camera_service, "detect_image", service)

    assert (await detect_image(image_request([png], "image/png"), 0.65))["image"] == "preview"
    service.assert_awaited_once_with(png, 0.65)
    with pytest.raises(HTTPException) as wrong_type:
        await detect_image(image_request([png]), 0.65)
    assert wrong_type.value.status_code == 415
    with pytest.raises(HTTPException) as too_large:
        await detect_image(image_request([b"x" * (4 * 1024 * 1024)] * 2 + [b"x"], "image/png"), 0.65)
    assert too_large.value.status_code == 413
    service.assert_awaited_once()


@pytest.mark.asyncio
async def test_upload_accepts_content_type_with_charset(monkeypatch, png):
    service = AsyncMock(return_value={"image": "preview", "detections": []})
    monkeypatch.setattr(camera_service, "detect_image", service)

    result = await detect_image(image_request([png], "image/png; charset=binary"), 0.55)

    assert result["image"] == "preview"
    service.assert_awaited_once_with(png, 0.55)


@pytest.mark.asyncio
async def test_invalid_image_never_reaches_predictor(monkeypatch):
    service = CameraService()
    service.model = MagicMock()
    service.model_config = ModelConfig(name="mock.pt")
    load = MagicMock()
    monkeypatch.setattr(service, "_load_model", load)

    with pytest.raises(ValueError, match="valid JPEG or PNG"):
        await service.detect_image(b"not an image", 0.55)
    load.assert_not_called()
