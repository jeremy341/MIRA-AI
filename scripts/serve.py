"""REST API for MIRA-AI model inference.

Provides a FastAPI-based HTTP server for object detection using
Ultralytics YOLO models. Run with::

    python scripts/serve.py
    python scripts/serve.py --port 8080 --model mira_exp015.pt
    MIRA_MODEL=mira_exp015.pt python scripts/serve.py

Endpoints:
    POST /detect  — Upload an image and return detection results.
    GET  /health  — Liveness / readiness probe.
"""

from __future__ import annotations

import argparse
import os
import sys
import tempfile
import time
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Bootstrap sys.path so ``src`` package modules are importable.
# This mirrors the pattern used by every other script in this directory.
# ---------------------------------------------------------------------------
_SCRIPT_DIR = Path(__file__).resolve().parent
_SRC_DIR = _SCRIPT_DIR.parent / "src"
if str(_SRC_DIR) not in sys.path:
    sys.path.insert(0, str(_SRC_DIR))

from config import CLASS_NAMES, DETECTION_DIR  # noqa: E402
from logger import get_logger  # noqa: E402
from pipeline.models import ModelRegistry  # noqa: E402

from fastapi import FastAPI, File, HTTPException, Query, UploadFile  # noqa: E402
from fastapi.middleware.cors import CORSMiddleware  # noqa: E402
from fastapi.responses import JSONResponse  # noqa: E402

logger = get_logger("mira.serve")

# ---------------------------------------------------------------------------
# App factory
# ---------------------------------------------------------------------------

app = FastAPI(
    title="MIRA-AI Detection API",
    description="Object-detection inference server for waste-classification models.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8000", "http://127.0.0.1:8000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Global model registry — lazily populated on first request.
# ---------------------------------------------------------------------------
_registry: ModelRegistry | None = None
_loaded_model_name: str | None = None


def _get_registry() -> ModelRegistry:
    """Return (and cache) a discovered ModelRegistry."""
    global _registry
    if _registry is None:
        _registry = ModelRegistry()
        n = _registry.discover()
        logger.info("Discovered %d model(s) in %s", n, DETECTION_DIR)
    return _registry


def _load_model(name: str) -> Any:
    """Load a model by filename, caching the active one globally.

    If *name* is ``None`` or empty, the first discovered model is used.
    """
    global _loaded_model_name

    registry = _get_registry()

    if not name:
        models = registry.list_models()
        if not models:
            raise HTTPException(
                status_code=503,
                detail="No models found in the models/detection directory.",
            )
        name = models[0]["name"]
        logger.info("No model specified — defaulting to '%s'", name)

    try:
        adapter = registry.load_model(name)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("Failed to load model '%s'", name)
        raise HTTPException(
            status_code=500,
            detail=f"Model loading failed: {exc}",
        ) from exc

    _loaded_model_name = name
    return adapter


# ---------------------------------------------------------------------------
# POST /detect
# ---------------------------------------------------------------------------

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".webp", ".tiff"}
MAX_UPLOAD_BYTES = 20 * 1024 * 1024  # 20 MB


@app.post("/detect")
async def detect(
    file: UploadFile = File(..., description="Image file to run detection on."),  # noqa: B008
    model: str | None = Query(  # noqa: B008
        default=None,
        description="Model filename (e.g. mira_exp015.pt). "
        "Falls back to MIRA_MODEL env var, then the first discovered model.",
    ),
    conf: float = Query(default=0.25, ge=0.0, le=1.0, description="Confidence threshold."),  # noqa: B008
    iou: float = Query(default=0.45, ge=0.0, le=1.0, description="IoU threshold for NMS."),  # noqa: B008
) -> JSONResponse:
    """Run object detection on an uploaded image.

    Returns a JSON object with the list of detections, each containing
    ``class_id``, ``class_name``, ``confidence``, and ``bbox`` (xyxy).
    """
    # --- Validate upload -------------------------------------------------
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided.")

    ext = Path(file.filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported image format '{ext}'. Allowed: {', '.join(sorted(ALLOWED_EXTENSIONS))}",
        )

    contents = await file.read()
    if len(contents) > MAX_UPLOAD_BYTES:
        raise HTTPException(
            status_code=413,
            detail=f"File too large ({len(contents)} bytes). Maximum is {MAX_UPLOAD_BYTES}.",
        )
    if len(contents) == 0:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    # --- Resolve model ---------------------------------------------------
    model_name = model or os.environ.get("MIRA_MODEL", "")
    adapter = _load_model(model_name)

    # --- Run inference via a temp file (YOLO expects a path) -------------
    t0 = time.perf_counter()
    try:
        with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as tmp:
            tmp.write(contents)
            tmp_path = Path(tmp.name)

        result = adapter.predict(str(tmp_path), conf=conf, iou=iou)
    except Exception as exc:
        logger.exception("Inference failed for '%s'", file.filename)
        raise HTTPException(status_code=500, detail=f"Inference failed: {exc}") from exc
    finally:
        tmp_path.unlink(missing_ok=True)

    latency_ms = (time.perf_counter() - t0) * 1000

    detections = [d.to_dict() for d in result.detections]
    logger.info(
        "%d detection(s) in %.1f ms — model=%s file=%s",
        len(detections),
        latency_ms,
        result.model_name,
        file.filename,
    )

    return JSONResponse(
        content={
            "model": result.model_name,
            "file": file.filename,
            "conf_threshold": conf,
            "iou_threshold": iou,
            "num_detections": len(detections),
            "detections": detections,
            "latency_ms": round(latency_ms, 2),
        }
    )


# ---------------------------------------------------------------------------
# GET /health
# ---------------------------------------------------------------------------


@app.get("/health")
async def health() -> dict[str, Any]:
    """Liveness and readiness probe.

    Returns model counts, available class names, and the active model.
    """
    registry = _get_registry()
    models = registry.list_models()

    return {
        "status": "ok",
        "active_model": _loaded_model_name,
        "available_models": [m["name"] for m in models],
        "num_models": len(models),
        "class_names": CLASS_NAMES,
        "num_classes": len(CLASS_NAMES),
    }


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------


def main() -> None:
    """Parse CLI flags and start the uvicorn server."""
    parser = argparse.ArgumentParser(description="MIRA-AI detection REST API")
    parser.add_argument("--host", default="0.0.0.0", help="Bind address (default: 0.0.0.0)")
    parser.add_argument("--port", type=int, default=8000, help="Listen port (default: 8000)")
    parser.add_argument(
        "--model",
        default=os.environ.get("MIRA_MODEL", ""),
        help="Model filename to pre-load (default: first discovered model)",
    )
    parser.add_argument("--workers", type=int, default=1, help="Number of uvicorn workers")
    args = parser.parse_args()

    import uvicorn

    # Pre-load the requested model so the first request is fast.
    if args.model:
        try:
            _load_model(args.model)
            logger.info("Pre-loaded model: %s", args.model)
        except HTTPException:
            logger.warning("Could not pre-load model '%s' — will try at request time.", args.model)

    logger.info("Starting MIRA-AI server on %s:%d", args.host, args.port)
    uvicorn.run(
        app,
        host=args.host,
        port=args.port,
        workers=args.workers,
        log_level="info",
    )


if __name__ == "__main__":
    main()
