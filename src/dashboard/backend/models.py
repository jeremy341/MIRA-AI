# Data models for MIRA Control Center API

from datetime import datetime, timezone
from pydantic import BaseModel, Field
from enum import StrEnum


class WasteClass(StrEnum):
    GLASS = "glass"
    METAL = "metal"
    PAPER = "paper"
    PLASTIC = "plastic"
    TRASH = "trash"


class Detection(BaseModel):
    class_name: WasteClass
    confidence: float = Field(ge=0.0, le=1.0)
    bbox: list[int]  # [x1, y1, x2, y2]
    track_id: int | None = None
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class CameraConfig(BaseModel):
    index: int = Field(0, ge=0)
    width: int = Field(640, gt=0, le=8192)
    height: int = Field(360, gt=0, le=8192)
    fps: int = Field(30, gt=0, le=240)
    autofocus: bool = False
    auto_exposure: bool = True


class ModelConfig(BaseModel):
    name: str = Field(min_length=1)
    conf_threshold: float = Field(0.25, ge=0.0, le=1.0)
    reject_threshold: float = Field(0.25, ge=0.0, le=1.0)
    iou_threshold: float = Field(0.45, ge=0.0, le=1.0)
    enable_tracking: bool = True
    target_latency_ms: int = Field(1000, gt=0)


class SystemMetrics(BaseModel):
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    fps: float
    inference_latency_ms: float
    avg_latency_ms: float
    cpu_percent: float
    memory_percent: float
    temperature_celsius: float | None = None
    detections_per_second: float
    skip_frames: bool


class Statistics(BaseModel):
    period_start: datetime
    period_end: datetime
    total_detections: int
    class_counts: dict[WasteClass, int]
    avg_confidence: dict[WasteClass, float]
    sorting_accuracy: float | None = None  # If robotic arm feedback available


class SystemStatus(StrEnum):
    IDLE = "idle"
    INITIALIZING = "initializing"
    RUNNING = "running"
    PAUSED = "paused"
    ERROR = "error"
