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

            succeeded = await self.camera_service.initialize_camera(config)
            message = "Camera config updated" if succeeded else "Failed to update camera config"
            return CommandResult(command, succeeded, message)

        elif command == "load_model":
            config = ModelConfig(**params)
            if state["streaming"]:
                return CommandResult(command, False, "Stop the stream before changing models")

            succeeded = await self.camera_service.load_model(config.name, config)
            message = f"Model {config.name} loaded" if succeeded else f"Failed to load model {config.name}"
            return CommandResult(command, succeeded, message)

        elif command == "start_stream":
            prerequisites = (
                ("camera", state["camera_initialized"]),
                ("model", state["model_loaded"]),
            )
            missing = tuple(name for name, ready in prerequisites if not ready)
            if missing:
                return CommandResult(
                    command,
                    False,
                    "Configure the camera and load a model before starting the stream.",
                    missing,
                )

            succeeded = await self.camera_service.start_streaming()
            message = "Stream starting; waiting for the first frame" if succeeded else "Failed to start stream"
            return CommandResult(command, succeeded, message)

        elif command == "stop_stream":
            succeeded = await self.camera_service.stop_streaming()
            message = "Stream stopped" if succeeded else "The streaming worker did not stop cleanly"
            return CommandResult(command, succeeded, message)

        return CommandResult(command, False, f"Unknown command {command}")
