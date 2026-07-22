"""
FastAPI server for MIRA Control Center
"""

import logging
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path

from fastapi import FastAPI, Query, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, FileResponse

from .models import CameraConfig, ModelConfig
from .camera_service import CameraService
from .websocket_handler import WebSocketHandler

log = logging.getLogger(__name__)

# Initialize services
camera_service = CameraService()
websocket_handler = WebSocketHandler(camera_service)


@asynccontextmanager
async def lifespan(application: FastAPI):
    log.info("MIRA Control Center starting up...")
    yield
    log.info("Shutting down MIRA Control Center...")
    await camera_service.stop()


# Initialize FastAPI app
app = FastAPI(
    title="MIRA Control Center API",
    description="Control interface for MIRA recycling sorting system",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8000", "http://127.0.0.1:8000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API Routes
# Serve dashboard frontend
FRONTEND_DIR = Path(__file__).parent / "frontend"


@app.get("/", response_class=HTMLResponse)
async def root():
    """Serve the MIRA Control Center dashboard"""
    dashboard_path = FRONTEND_DIR / "dashboard.html"
    if dashboard_path.exists():
        return FileResponse(dashboard_path, media_type="text/html")
    raise HTTPException(status_code=404, detail="Dashboard not found")


@app.get("/api/status")
async def get_status():
    """Get current system status"""
    return {
        "status": camera_service.status.value,
        "message": camera_service.status_message,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "camera_initialized": camera_service.camera is not None,
        "model_loaded": camera_service.model is not None,
        "streaming": camera_service.is_streaming,
    }


@app.get("/api/models")
async def get_models():
    """Get list of available detection models"""
    models = camera_service.get_available_models()
    return {"models": models, "count": len(models), "timestamp": datetime.now(timezone.utc).isoformat()}


@app.post("/api/camera/initialize")
async def initialize_camera(config: CameraConfig):
    """Initialize camera with configuration"""
    success = await camera_service.initialize_camera(config)

    if success:
        return {"success": True, "message": "Camera initialized successfully", "config": config.model_dump()}
    else:
        raise HTTPException(status_code=500, detail="Failed to initialize camera")


@app.post("/api/model/load")
async def load_model(model_config: ModelConfig):
    """Load detection model"""
    success = await camera_service.load_model(model_config.name, model_config)

    if success:
        return {
            "success": True,
            "message": f"Model {model_config.name} loaded successfully",
            "config": model_config.model_dump(),
        }
    else:
        raise HTTPException(status_code=500, detail=f"Failed to load model {model_config.name}")


@app.post("/api/stream/start")
async def start_stream():
    """Start video streaming and inference"""
    success = await camera_service.start_streaming()

    if success:
        return {"success": True, "message": "Streaming started", "timestamp": datetime.now(timezone.utc).isoformat()}
    else:
        raise HTTPException(status_code=500, detail="Failed to start streaming")


@app.post("/api/stream/stop")
async def stop_stream():
    """Stop video streaming"""
    await camera_service.stop()

    return {"success": True, "message": "Streaming stopped", "timestamp": datetime.now(timezone.utc).isoformat()}


@app.get("/api/statistics")
async def get_statistics(period: int = Query(default=60, ge=1, le=3600)):
    """Get detection statistics for the given period"""
    stats = camera_service.get_statistics(period)

    return {"statistics": stats.model_dump(), "period_seconds": period}


@app.get("/api/metrics/history")
async def get_metrics_history(limit: int = Query(default=100, ge=1, le=1000)):
    """Get historical system metrics"""
    history = list(camera_service.metrics_history)[-limit:]

    return {
        "metrics": [m.model_dump() for m in history],
        "count": len(history),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@app.get("/api/detections/recent")
async def get_recent_detections(limit: int = Query(default=50, ge=1, le=500)):
    """Get recent detections"""
    detections = list(camera_service.detection_history)[-limit:]

    return {
        "detections": [d.model_dump() for d in detections],
        "count": len(detections),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


# WebSocket endpoints
@app.websocket("/ws/video")
async def video_stream(websocket: WebSocket):
    """WebSocket endpoint for video streaming"""
    await websocket.accept()
    await websocket_handler.handle_video_stream(websocket)


@app.websocket("/ws/control")
async def control_websocket(websocket: WebSocket):
    """WebSocket endpoint for control commands"""
    await websocket.accept()

    try:
        while True:
            data = await websocket.receive_json()

            command = data.get("command")
            params = data.get("params", {})

            if command == "set_camera_config":
                config = CameraConfig(**params)
                success = await camera_service.initialize_camera(config)

                await websocket.send_json(
                    {
                        "type": "response",
                        "command": command,
                        "success": success,
                        "message": "Camera config updated" if success else "Failed to update camera config",
                    }
                )

            elif command == "load_model":
                model_config = ModelConfig(**params)
                success = await camera_service.load_model(model_config.name, model_config)

                await websocket.send_json(
                    {
                        "type": "response",
                        "command": command,
                        "success": success,
                        "message": f"Model {model_config.name} loaded"
                        if success
                        else f"Failed to load model {model_config.name}",
                    }
                )

            elif command == "start_stream":
                success = await camera_service.start_streaming()

                await websocket.send_json(
                    {
                        "type": "response",
                        "command": command,
                        "success": success,
                        "message": "Stream started" if success else "Failed to start stream",
                    }
                )

            elif command == "stop_stream":
                await camera_service.stop()

                await websocket.send_json(
                    {"type": "response", "command": command, "success": True, "message": "Stream stopped"}
                )

            elif command == "get_status":
                await websocket.send_json(
                    {
                        "type": "status",
                        "status": camera_service.status.value,
                        "message": camera_service.status_message,
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                    }
                )

            elif command == "get_statistics":
                period = params.get("period", 60)
                stats = camera_service.get_statistics(period)

                await websocket.send_json({"type": "statistics", "statistics": stats.model_dump(), "period": period})

            else:
                await websocket.send_json({"type": "error", "message": f"Unknown command: {command}"})

    except WebSocketDisconnect:
        print("Control WebSocket disconnected")
    except Exception as e:
        await websocket.send_json({"type": "error", "message": f"Error: {str(e)}"})


# Run the server
if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True, log_level="info")
