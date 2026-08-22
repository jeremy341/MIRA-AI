"""Tests for MIRA dashboard WebSocket handler."""

import sys
from datetime import datetime
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import numpy as np
import pytest

# Add dashboard backend to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src" / "dashboard" / "backend"))

from models import Detection, SystemMetrics, SystemStatus, WasteClass
from websocket_handler import WebSocketHandler


@pytest.fixture
def mock_camera_service():
    svc = MagicMock()
    svc.on_detection = None
    svc.on_metrics = None
    svc.on_status_change = None
    svc.on_frame = None
    return svc


@pytest.fixture
def handler(mock_camera_service):
    return WebSocketHandler(mock_camera_service)


class TestInit:
    def test_registers_callbacks(self, mock_camera_service):
        h = WebSocketHandler(mock_camera_service)
        assert mock_camera_service.on_detection == h._on_detections
        assert mock_camera_service.on_metrics == h._on_metrics
        assert mock_camera_service.on_status_change == h._on_status_change
        assert mock_camera_service.on_frame == h.update_frame

    def test_initial_state(self, handler):
        assert handler.connections == set()
        assert handler.frame_buffer is None
        assert handler.latest_detections == []
        assert handler._broadcast_task is None


class TestOnDetections:
    @pytest.mark.asyncio
    async def test_stores_detections(self, handler):
        det = Detection(class_name=WasteClass.GLASS, confidence=0.9, bbox=[0, 0, 10, 10])
        await handler._on_detections([det])
        assert handler.latest_detections == [det]

    @pytest.mark.asyncio
    async def test_stores_latest_detections_without_separate_frame_event(self, handler):
        det = Detection(class_name=WasteClass.METAL, confidence=0.8, bbox=[5, 5, 20, 20], track_id=1)
        await handler._on_detections([det])
        assert handler.latest_detections == [det]
        assert handler._broadcast_queue.empty()

    @pytest.mark.asyncio
    async def test_detections_are_attached_to_frame_events(self, handler):
        det = Detection(class_name=WasteClass.PAPER, confidence=0.7, bbox=[0, 0, 5, 5])
        frame = np.zeros((8, 8, 3), dtype=np.uint8)
        with patch("cv2.imencode", return_value=(True, np.array([1, 2, 3], dtype=np.uint8))):
            handler.update_frame(frame, [det])
        msg = handler._broadcast_queue.get_nowait()
        assert msg["type"] == "frame"
        assert msg["frame_id"] == 1
        assert msg["detections"][0]["class"] == "paper"
        ts = msg["detections"][0]["timestamp"]
        datetime.fromisoformat(ts)  # Should not raise


class TestOnMetrics:
    @pytest.mark.asyncio
    async def test_queues_metrics_message(self, handler):
        metrics = SystemMetrics(
            fps=25.0,
            inference_latency_ms=12.5,
            avg_latency_ms=15.0,
            cpu_percent=40.0,
            memory_percent=55.0,
            detections_per_second=3.0,
            skip_frames=False,
        )
        await handler._on_metrics(metrics)
        msg = handler._broadcast_queue.get_nowait()
        assert msg["type"] == "metrics"
        assert msg["fps"] == 25.0
        assert msg["skip_frames"] is False

    @pytest.mark.asyncio
    async def test_rounds_values(self, handler):
        metrics = SystemMetrics(
            fps=29.97,
            inference_latency_ms=12.345,
            avg_latency_ms=15.678,
            cpu_percent=40.123,
            memory_percent=55.987,
            detections_per_second=3.456,
            skip_frames=True,
        )
        await handler._on_metrics(metrics)
        msg = handler._broadcast_queue.get_nowait()
        assert msg["fps"] == 30.0
        assert msg["inference_latency_ms"] == 12.3
        assert msg["avg_latency_ms"] == 15.7

    @pytest.mark.asyncio
    async def test_temperature_none_when_missing(self, handler):
        metrics = SystemMetrics(
            fps=30.0,
            inference_latency_ms=10.0,
            avg_latency_ms=12.0,
            cpu_percent=50.0,
            memory_percent=60.0,
            detections_per_second=1.0,
            skip_frames=False,
        )
        await handler._on_metrics(metrics)
        msg = handler._broadcast_queue.get_nowait()
        assert msg["temperature_celsius"] is None


class TestOnStatusChange:
    @pytest.mark.asyncio
    async def test_queues_status_message(self, handler):
        await handler._on_status_change(SystemStatus.RUNNING, "Stream started")
        msg = handler._broadcast_queue.get_nowait()
        assert msg["type"] == "status"
        assert msg["status"] == "running"
        assert msg["message"] == "Stream started"
        assert "timestamp" in msg


class TestUpdateFrame:
    def test_updates_frame_buffer(self, handler):
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        handler.update_frame(frame)
        assert np.array_equal(handler.frame_buffer, frame)

    def test_ignores_none_frame(self, handler):
        handler.update_frame(None)
        assert handler.frame_buffer is None

    @patch("cv2.imencode")
    def test_queues_frame_message(self, mock_imencode, handler):
        mock_imencode.return_value = (True, np.array([1, 2, 3], dtype=np.uint8))
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        handler.update_frame(frame)
        msg = handler._broadcast_queue.get_nowait()
        assert msg["type"] == "frame"
        assert "frame" in msg
        assert "timestamp" in msg
        assert msg["detections"] == []

    @patch("cv2.imencode")
    def test_frame_queue_is_bounded(self, mock_imencode, handler):
        mock_imencode.return_value = (True, np.array([1, 2, 3], dtype=np.uint8))
        frame = np.zeros((8, 8, 3), dtype=np.uint8)

        for _ in range(handler._broadcast_queue.maxsize + 10):
            handler.update_frame(frame)

        assert handler._broadcast_queue.qsize() == handler._broadcast_queue.maxsize
        assert all(item["type"] == "frame" for item in list(handler._broadcast_queue._queue))


class TestSendFrame:
    @pytest.mark.asyncio
    async def test_sends_frame_to_websocket(self, handler):
        mock_ws = AsyncMock()
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        with patch("cv2.imencode", return_value=(True, np.array([1, 2, 3], dtype=np.uint8))):
            await handler._send_frame(mock_ws, frame)
        mock_ws.send_json.assert_called_once()
        sent = mock_ws.send_json.call_args[0][0]
        assert sent["type"] == "frame"

    @pytest.mark.asyncio
    async def test_ignores_none_frame(self, handler):
        mock_ws = AsyncMock()
        await handler._send_frame(mock_ws, None)
        mock_ws.send_json.assert_not_called()


class TestStartStop:
    @pytest.mark.asyncio
    async def test_start_creates_task(self, handler):
        await handler.start()
        assert handler._broadcast_task is not None
        assert not handler._broadcast_task.done()
        await handler.stop()

    @pytest.mark.asyncio
    async def test_stop_cancels_task(self, handler):
        await handler.start()
        await handler.stop()
        assert handler._broadcast_task.cancelled()

    @pytest.mark.asyncio
    async def test_stop_without_start(self, handler):
        await handler.stop()  # Should not raise
