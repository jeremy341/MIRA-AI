"""
Data models for MIRA Control Center API
"""

from datetime import datetime
from typing import Any
from pydantic import BaseModel, Field
from enum import StrEnum


class WasteClass(StrEnum):
    GLASS = "glass"
    METAL = "metal"
    PAPER = "paper"
    PLASTIC = "plastic"
    TRASH = "trash"


class Detection(BaseModel):
    """Single detection result"""

    class_name: WasteClass
    confidence: float = Field(ge=0.0, le=1.0)
    bbox: list[int]  # [x1, y1, x2, y2]
    track_id: int | None = None
    timestamp: datetime = Field(default_factory=datetime.now)


class CameraConfig(BaseModel):
    """Camera configuration"""

    index: int = 0
    width: int = 640
    height: int = 360
    fps: int = 30
    autofocus: bool = False
    auto_exposure: bool = True


class ModelConfig(BaseModel):
    """Model inference configuration"""

    name: str
    conf_threshold: float = 0.5
    reject_threshold: float = 0.55
    iou_threshold: float = 0.45
    enable_tracking: bool = True
    target_latency_ms: int = 50


class SystemMetrics(BaseModel):
    """System performance metrics"""

    timestamp: datetime = Field(default_factory=datetime.now)
    fps: float
    inference_latency_ms: float
    avg_latency_ms: float
    cpu_percent: float
    memory_percent: float
    temperature_celsius: float | None = None
    detections_per_second: float
    skip_frames: bool


class Statistics(BaseModel):
    """Detection statistics"""

    period_start: datetime
    period_end: datetime
    total_detections: int
    class_counts: dict[WasteClass, int]
    avg_confidence: dict[WasteClass, float]
    sorting_accuracy: float | None = None  # If robotic arm feedback available


class ModelInfo(BaseModel):
    """Detection model information"""

    name: str
    label: str
    path: str
    model_type: str  # "yolo_pt", "yolo_tflite", "third_party"
    size_mb: float
    is_tflite_int8: bool
    input_size: int
    recommended: bool = False


class SystemStatus(StrEnum):
    IDLE = "idle"
    INITIALIZING = "initializing"
    RUNNING = "running"
    PAUSED = "paused"
    ERROR = "error"


class StatusUpdate(BaseModel):
    """System status update"""

    status: SystemStatus
    message: str
    timestamp: datetime = Field(default_factory=datetime.now)
    details: dict[str, Any] | None = None
