"""Model compare API. Owner and contract: docs/dashboard-v2/CONTRACT.md."""

from __future__ import annotations

import asyncio
import base64
import json
import time
import uuid
from datetime import datetime, timezone
from io import BytesIO
from pathlib import Path
from typing import Annotated, Any

import numpy as np
from fastapi import APIRouter, File, Form, HTTPException, Query, UploadFile
from PIL import Image, ImageDraw, ImageFont, ImageOps
from starlette.responses import Response

from src.config import CLASS_NAMES
from .. import model_runner
from ..state import get_db

router = APIRouter(tags=["Model compare"])

MAX_UPLOAD_BYTES = 8 * 1024 * 1024
MAX_IMAGE_PIXELS = 16_000_000
READ_CHUNK_BYTES = 64 * 1024
CLASS_COLORS = {
    "glass": "#2a7f45",
    "metal": "#66778a",
    "paper": "#2457c5",
    "plastic": "#f2c230",
    "trash": "#3a3a3a",
}


async def _read_upload(upload: UploadFile) -> bytes:
    chunks = []
    size = 0
    while chunk := await upload.read(READ_CHUNK_BYTES):
        size += len(chunk)
        if size > MAX_UPLOAD_BYTES:
            raise HTTPException(status_code=413, detail="Choose an image no larger than 8 MB.")
        chunks.append(chunk)
    return b"".join(chunks)


def _decode_image(payload: bytes) -> tuple[Image.Image, np.ndarray]:
    try:
        with Image.open(BytesIO(payload), formats=["JPEG", "PNG"]) as source:
            if source.width * source.height > MAX_IMAGE_PIXELS:
                raise HTTPException(status_code=422, detail="Choose an image no larger than 16 megapixels.")
            image = ImageOps.exif_transpose(source).convert("RGB")
    except Image.DecompressionBombError as exc:
        raise HTTPException(status_code=422, detail="Choose an image no larger than 16 megapixels.") from exc
    except (OSError, SyntaxError) as exc:
        raise HTTPException(status_code=422, detail="Choose a valid JPEG or PNG image.") from exc

    image.thumbnail((1280, 1280))
    frame_bgr = np.asarray(image)[:, :, ::-1].copy()
    return image, frame_bgr


def _validate_model_names(models: str) -> list[str]:
    names = [name.strip() for name in models.split(",")]
    if any(not name for name in names):
        raise HTTPException(status_code=422, detail="Provide 2 to 4 model names separated by commas.")
    if not 2 <= len(names) <= 4:
        raise HTTPException(status_code=422, detail="Compare requires between 2 and 4 models.")
    if len(set(names)) != len(names):
        duplicate = next(name for name in names if names.count(name) > 1)
        raise HTTPException(status_code=422, detail=f"Duplicate model name: {duplicate}")
    for name in names:
        try:
            model_runner.resolve_model_path(name)
        except (ValueError, FileNotFoundError) as exc:
            raise HTTPException(status_code=422, detail=f"Invalid model '{name}': {exc}") from exc
    return names


def _annotated_preview(image: Image.Image, detections: list[dict[str, Any]]) -> str:
    annotated = image.copy()
    draw = ImageDraw.Draw(annotated)
    font = ImageFont.load_default()
    width, height = annotated.size

    for detection in detections:
        class_name = detection["class_name"]
        color = CLASS_COLORS.get(class_name, "#3a3a3a")
        x1, y1, x2, y2 = detection["bbox"]
        x1 = max(0, min(width - 1, x1))
        y1 = max(0, min(height - 1, y1))
        x2 = max(0, min(width - 1, x2))
        y2 = max(0, min(height - 1, y2))
        draw.rectangle((x1, y1, x2, y2), outline=color, width=3)
        label = f"{class_name} {detection['confidence']:.2f}"
        label_box = draw.textbbox((0, 0), label, font=font)
        label_width = label_box[2] - label_box[0]
        label_height = label_box[3] - label_box[1]
        label_top = max(0, y1 - label_height - 4)
        draw.rectangle((x1, label_top, x1 + label_width + 6, label_top + label_height + 4), fill=color)
        text_color = "#202020" if class_name == "plastic" else "#ffffff"
        draw.text((x1 + 3, label_top + 2), label, fill=text_color, font=font)

    encoded = BytesIO()
    annotated.save(encoded, format="JPEG", quality=85)
    return "data:image/jpeg;base64," + base64.b64encode(encoded.getvalue()).decode("ascii")


def _run_models(names: list[str], image: Image.Image, frame_bgr: np.ndarray, confidence: float) -> list[dict[str, Any]]:
    results = []
    for name in names:
        runner_result = model_runner.predict_frame(name, frame_bgr, confidence=confidence, iou=0.45)
        detections = [detection.to_dict() for detection in runner_result.detections]
        class_counts = {class_name: 0 for class_name in CLASS_NAMES}
        for detection in detections:
            if detection["class_name"] in class_counts:
                class_counts[detection["class_name"]] += 1
        confidences = [detection.confidence for detection in runner_result.detections]
        results.append(
            {
                "name": name,
                "latency_ms": round(runner_result.latency_ms, 3),
                "objects": len(detections),
                "class_counts": class_counts,
                "avg_confidence": round(sum(confidences) / len(confidences), 4) if confidences else None,
                "detections": detections,
                "annotated_image": _annotated_preview(image, detections),
            }
        )
    return results


def _winner_hint(models: list[dict[str, Any]]) -> dict[str, Any]:
    fastest = min(models, key=lambda model: model["latency_ms"])
    most_objects = max(models, key=lambda model: model["objects"])
    confidence_models = [model for model in models if model["avg_confidence"] is not None]
    highest_confidence = (
        max(confidence_models, key=lambda model: model["avg_confidence"]) if confidence_models else None
    )
    return {
        "fastest_model": fastest["name"],
        "most_objects_model": most_objects["name"],
        "highest_avg_confidence_model": highest_confidence["name"] if highest_confidence else None,
        "note": "These are observations for this image only; they do not establish detection accuracy without ground truth.",
    }


def _record_from_row(row) -> dict[str, Any]:
    stored = json.loads(row["results_json"])
    return {
        "id": row["id"],
        "created_at": datetime.fromtimestamp(row["created_at_ts"], timezone.utc).isoformat(),
        "input_name": row["input_name"],
        "models": stored["models"],
        "winner_hint": stored["winner_hint"],
    }


@router.post("/compare")
async def compare_models(
    image: Annotated[UploadFile, File()],
    models: Annotated[str, Form()],
    confidence: Annotated[float, Form(ge=0.05, le=1)] = 0.25,
):
    content_type = (image.content_type or "").split(";", 1)[0].strip().lower()
    if content_type not in {"image/jpeg", "image/png"}:
        raise HTTPException(status_code=415, detail="Choose a JPEG or PNG image.")

    payload = await _read_upload(image)
    names = _validate_model_names(models)
    decoded_image, frame_bgr = _decode_image(payload)
    results = await asyncio.to_thread(_run_models, names, decoded_image, frame_bgr, confidence)
    winner_hint = _winner_hint(results)
    comparison_id = uuid.uuid4().hex
    created_at_ts = time.time()
    input_name = Path(image.filename or "upload").name
    stored_results = {
        "models": [{key: value for key, value in result.items() if key != "annotated_image"} for result in results],
        "winner_hint": winner_hint,
    }
    get_db().execute(
        "INSERT INTO comparisons (id, created_at_ts, input_name, models_json, results_json) VALUES (?,?,?,?,?)",
        (comparison_id, created_at_ts, input_name, json.dumps(names), json.dumps(stored_results)),
    )
    return {
        "id": comparison_id,
        "input_name": input_name,
        "models": results,
        "winner_hint": winner_hint,
    }


@router.get("/compare")
async def list_comparisons(limit: int = Query(20, ge=1, le=100)):
    db = get_db()
    rows = db.query("SELECT * FROM comparisons ORDER BY created_at_ts DESC LIMIT ?", (limit,))
    total = db.query_one("SELECT COUNT(*) AS count FROM comparisons")["count"]
    return {"comparisons": [_record_from_row(row) for row in rows], "total": total}


@router.get("/compare/{comparison_id}")
async def get_comparison(comparison_id: str):
    row = get_db().query_one("SELECT * FROM comparisons WHERE id=?", (comparison_id,))
    if row is None:
        raise HTTPException(status_code=404, detail="Comparison not found.")
    return _record_from_row(row)


@router.delete("/compare/{comparison_id}", status_code=204)
async def delete_comparison(comparison_id: str):
    cursor = get_db().execute("DELETE FROM comparisons WHERE id=?", (comparison_id,))
    if cursor.rowcount == 0:
        raise HTTPException(status_code=404, detail="Comparison not found.")
    return Response(status_code=204)


# Optional lifecycle hooks, discovered by v1/__init__.py:
#   async def on_startup() -> None: ...
#   async def on_shutdown() -> None: ...
