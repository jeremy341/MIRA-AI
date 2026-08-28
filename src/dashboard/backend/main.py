# Fast Api server for MIRA Dashboard

import asyncio
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, FileResponse

from src.dashboard.backend.models import CameraConfig, ModelConfig
from src.dashboard.backend.camera_service import CameraService
from src.dashboard.backend.websocket_handler import WebSocketHandler

camera_service = CameraService()
websocket_handler = WebSocketHandler(camera_service)


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("MIRA Control Center starting up...")
    camera_service._loop = asyncio.get_running_loop()
    websocket_handler._loop = asyncio.get_running_loop()
    await websocket_handler.start()
    yield
    print("Shutting down MIRA Control Center...")
    await websocket_handler.stop()
    await camera_service.shutdown()


app = FastAPI(
    title="MIRA Control Center API",
    description="Control interface for MIRA recycling sorting system",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8000", "http://127.0.0.1:8000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

FRONTEND_DIR = Path(__file__).parent.parent / "frontend"


def _status_payload() -> dict:
    return {**camera_service.get_status_snapshot(), "timestamp": datetime.now(timezone.utc).isoformat()}


def _missing_prerequisites() -> list[str]:
    state = camera_service.get_status_snapshot()
    return [
        name
        for name, ready in (
            ("camera", state["camera_initialized"]),
            ("model", state["model_loaded"]),
        )
        if not ready
    ]


async def _set_camera(config: CameraConfig) -> tuple[bool, str]:
    if camera_service.get_status_snapshot()["streaming"]:
        return False, "Stop the stream before changing camera settings"
    success = await camera_service.initialize_camera(config)
    return success, "Camera config updated" if success else "Failed to update camera config"


async def _set_model(config: ModelConfig) -> tuple[bool, str]:
    if camera_service.get_status_snapshot()["streaming"]:
        return False, "Stop the stream before changing models"
    success = await camera_service.load_model(config.name, config)
    message = f"Model {config.name} loaded" if success else f"Failed to load model {config.name}"
    return success, message


async def _start_stream() -> tuple[bool, str, list[str]]:
    missing = _missing_prerequisites()
    if missing:
        return False, "Configure the camera and load a model before starting the stream.", missing
    success = await camera_service.start_streaming()
    message = "Stream starting; waiting for the first frame" if success else "Failed to start stream"
    return success, message, []


async def _stop_stream() -> tuple[bool, str]:
    success = await camera_service.stop()
    return success, "Stream stopped" if success else "The streaming worker did not stop cleanly"


def _statistics_payload(period: int) -> dict:
    if period < 1:
        raise HTTPException(status_code=400, detail="period must be a positive integer")
    if period > 86400:
        raise HTTPException(status_code=400, detail="period must not exceed 86400 seconds (24 hours)")

    stats = camera_service.get_statistics(period)
    stats_dict = stats.model_dump(mode="json")
    total = sum(stats.class_counts.values())
    if total and stats.avg_confidence:
        stats_dict["average_confidence"] = (
            sum(stats.avg_confidence.get(class_name, 0) * count for class_name, count in stats.class_counts.items())
            / total
        )
    else:
        stats_dict["average_confidence"] = None
    return {"statistics": stats_dict, "period_seconds": period}


@app.get("/", response_class=HTMLResponse)
async def root():
    # Serve the MIRA Control Center dashboard
    dashboard_path = FRONTEND_DIR / "dashboard.html"
    if dashboard_path.exists():
        return FileResponse(dashboard_path, media_type="text/html")
    raise HTTPException(status_code=404, detail="Dashboard not found")


@app.get("/dashboard.css")
async def dashboard_css():
    return FileResponse(FRONTEND_DIR / "dashboard.css", media_type="text/css")


@app.get("/dashboard.js")
async def dashboard_js():
    return FileResponse(FRONTEND_DIR / "dashboard.js", media_type="application/javascript")


@app.get("/api/status")
async def get_status():
    return _status_payload()


@app.get("/api/models")
async def get_models():
    models = camera_service.get_available_models()
    return {"models": models, "count": len(models), "timestamp": datetime.now(timezone.utc).isoformat()}


@app.post("/api/camera/initialize")
async def initialize_camera(config: CameraConfig):
    success, message = await _set_camera(config)

    if success:
        return {"success": True, "message": message, "config": config.model_dump()}
    raise HTTPException(status_code=409 if "Stop" in message else 500, detail=message)


@app.post("/api/model/load")
async def load_model(model_config: ModelConfig):
    success, message = await _set_model(model_config)

    if success:
        return {
            "success": True,
            "message": message,
            "config": model_config.model_dump(),
        }
    raise HTTPException(status_code=409 if "Stop" in message else 500, detail=message)


@app.post("/api/stream/start")
async def start_stream():
    success, message, missing = await _start_stream()
    if missing:
        raise HTTPException(
            status_code=409,
            detail={
                "message": message,
                "missing": missing,
            },
        )

    if success:
        return {
            "success": True,
            "status": camera_service.status.value,
            "message": message,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    raise HTTPException(
        status_code=500, detail="The stream could not be started. Check the camera connection and configuration."
    )


@app.post("/api/stream/stop")
async def stop_stream():
    stopped, message = await _stop_stream()
    if not stopped:
        raise HTTPException(status_code=500, detail=message)

    return {
        "success": True,
        "status": camera_service.status.value,
        "message": message,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@app.get("/api/statistics")
async def get_statistics(period: int = 60):
    return _statistics_payload(period)


@app.get("/api/metrics/history")
async def get_metrics_history(limit: int = 100):
    if limit < 1 or limit > 1000:
        raise HTTPException(status_code=400, detail="limit must be between 1 and 1000")
    history = list(camera_service.metrics_history)[-limit:]

    return {
        "metrics": [m.model_dump() for m in history],
        "count": len(history),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@app.get("/api/detections/recent")
async def get_recent_detections(limit: int = 50):
    if limit < 1 or limit > 1000:
        raise HTTPException(status_code=400, detail="limit must be between 1 and 1000")
    detections = list(camera_service.detection_history)[-limit:]

    return {
        "detections": [d.model_dump() for d in detections],
        "count": len(detections),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@app.websocket("/ws/video")
async def video_stream(websocket: WebSocket):
    await websocket.accept()
    await websocket_handler.handle_video_stream(websocket)


@app.websocket("/ws/control")
async def control_websocket(websocket: WebSocket):
    await websocket.accept()

    try:
        while True:
            data = await websocket.receive_json()

            command = data.get("command")
            params = data.get("params", {})

            if command == "set_camera_config":
                config = CameraConfig(**params)
                success, message = await _set_camera(config)

                await websocket.send_json(
                    {
                        "type": "response",
                        "command": command,
                        "success": success,
                        "message": message,
                    }
                )

            elif command == "load_model":
                config = ModelConfig(**params)
                success, message = await _set_model(config)

                await websocket.send_json(
                    {
                        "type": "response",
                        "command": command,
                        "success": success,
                        "message": message,
                    }
                )

            elif command == "start_stream":
                success, message, missing = await _start_stream()
                if missing:
                    await websocket.send_json(
                        {
                            "type": "error",
                            "message": message,
                            "missing": missing,
                        }
                    )
                else:
                    await websocket.send_json(
                        {
                            "type": "response",
                            "command": command,
                            "success": success,
                            "message": message,
                        }
                    )

            elif command == "stop_stream":
                stopped, message = await _stop_stream()

                await websocket.send_json(
                    {
                        "type": "response",
                        "command": command,
                        "success": stopped,
                        "message": message,
                    }
                )

            elif command == "get_status":
                await websocket.send_json({"type": "status", **_status_payload()})

            elif command == "get_statistics":
                period = params.get("period", 60)
                stats_payload = _statistics_payload(period)
                await websocket.send_json({"type": "statistics", **stats_payload, "period": period})

            else:
                await websocket.send_json({"type": "error", "message": f"Unknown command: {command}"})

    except WebSocketDisconnect:
        print("Control WebSocket disconnected")
    except Exception as e:
        print(f"Control WebSocket error: {e}")
        try:
            await websocket.send_json({"type": "error", "message": f"Error: {str(e)}"})
        except Exception:
            pass


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=False, log_level="info")
