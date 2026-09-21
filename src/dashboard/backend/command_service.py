from dataclasses import dataclass, field
from src.dashboard.backend.models import CameraConfig, ModelConfig

@dataclass(frozen=True)
class CommandResult:
    command: str
    success: bool
    message: str
    missing: tuple[str, ...] = field(default_factory=tuple)

class DashboardCommandService:
    def __init__(self, camera_service):
        self.camera_service = camera_service


    async def execute(self, command: str, params: dict) -> CommandResult:
        state = self.camera_service.get_status_snapshot()
        if command == "set_camera_config":
            config = CameraConfig(**params)
            if state["streaming"]:
                return CommandResult(command, False, "Stop the stream before changing camera settings")
            ok = await self.camera_service.initialize_camera(config)
            return CommandResult(command, ok, "Camera config updated" if ok else "Failed to update camera config")
        if command == "load_model":
            config = ModelConfig(**params)
            if state["streaming"]:
                return CommandResult(command, False, "Stop the stream before changing models")
            ok = await self.camera_service.load_model(config.name, config)
            return CommandResult(command, ok, f"Model {config.name} loaded" if ok else f"Failed to load model {config.name}")
        if command == "start_stream":
            missing = tuple(name for name, ready in (
                ("camera", state["camera_initialized"]),
                ("model", state["model_loaded"]),
            ) if not ready)
            if missing:
                return CommandResult(command, False, "Configure the camera and load a model before starting the stream.", missing)
            ok = await self.camera_service.start_streaming()
            return CommandResult(command, ok, "Stream starting; waiting for the first frame" if ok else "Failed to start stream")
        if command == "stop_stream":
            ok = await self.camera_service.stop_streaming()
            return CommandResult(command, ok, "Stream stopped" if ok else "The streaming worker did not stop cleanly")
        return CommandResult(command, False, f"Unknown command {command}")