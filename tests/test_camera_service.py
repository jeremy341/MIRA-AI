# Focused runtime regression tests for the dashboard camera service.

import asyncio
import threading
from unittest.mock import MagicMock, patch

import pytest

from src.dashboard.backend.camera_service import BYTE_TRACK_CONFIG_PATH, CameraService
from src.dashboard.backend.models import CameraConfig, ModelConfig, SystemStatus


def test_initializes_runtime_state():
    service = CameraService()

    assert service.on_detection is None
    assert service.on_metrics is None
    assert service.on_status_change is None
    assert service.on_frame is None
    assert service._disconnect_count == 0
    assert service._streaming_thread is None


def test_history_snapshots_are_available_and_limited():
    service = CameraService()
    service.metrics_history.extend(["metric-1", "metric-2"])
    service.detection_history.extend(["detection-1", "detection-2"])

    assert service.get_metrics_snapshot(1) == ["metric-2"]
    assert service.get_detection_snapshot(1) == ["detection-2"]


@pytest.mark.parametrize("method_name", ["get_metrics_snapshot", "get_detection_snapshot"])
def test_history_snapshots_reject_invalid_limits(method_name):
    service = CameraService()

    with pytest.raises(ValueError, match="between 1 and 1000"):
        getattr(service, method_name)(0)


@pytest.mark.asyncio
async def test_start_streaming_processes_a_frame_without_runtime_state_errors():
    frame_processed = threading.Event()
    camera = MagicMock()
    camera.read.return_value = (True, object())
    model = MagicMock()
    model.predict.return_value = []
    service = CameraService(loop=asyncio.get_running_loop())
    service.camera = camera
    service.model = model
    service.model_config = ModelConfig(name="mock.pt", enable_tracking=False)
    service.on_frame = lambda _frame, _detections: frame_processed.set()

    assert await service.start_streaming() is True
    assert await asyncio.to_thread(frame_processed.wait, 1)
    await service.stop()

    assert service.status == SystemStatus.IDLE
    assert service.latency_history


@pytest.mark.asyncio
async def test_tracking_uses_persistent_tracker_and_frame_callback_runs_on_worker():
    camera = MagicMock()
    camera.read.return_value = (True, object())
    model = MagicMock()
    service = CameraService(loop=asyncio.get_running_loop())
    service.camera = camera
    service.model = model
    service.model_config = ModelConfig(name="mock.pt", enable_tracking=True)
    callback_thread = []
    frame_processed = threading.Event()

    def on_frame(_frame, _detections):
        callback_thread.append(threading.current_thread())
        with service._lock:
            service.is_streaming = False
        frame_processed.set()

    service.on_frame = on_frame

    assert await service.start_streaming() is True
    worker_thread = service._streaming_thread
    assert await asyncio.to_thread(frame_processed.wait, 1)
    await service.stop()

    model.track.assert_called_once()
    model.predict.assert_not_called()
    assert model.track.call_args.kwargs["imgsz"] == service.img_size
    assert model.track.call_args.kwargs["conf"] == service.model_config.conf_threshold
    assert model.track.call_args.kwargs["iou"] == service.model_config.iou_threshold
    assert model.track.call_args.kwargs["persist"] is True
    assert model.track.call_args.kwargs["tracker"] == str(BYTE_TRACK_CONFIG_PATH)
    assert callback_thread == [worker_thread]


@pytest.mark.asyncio
async def test_int8_model_uses_prediction_even_when_tracking_is_enabled():
    camera = MagicMock()
    camera.read.return_value = (True, object())
    model = MagicMock()
    model.predict.return_value = []
    service = CameraService(loop=asyncio.get_running_loop())
    service.camera = camera
    service.model = model
    service.model_config = ModelConfig(name="mock_int8.tflite", enable_tracking=True)
    service.is_tflite_int8 = True
    frame_processed = threading.Event()

    def on_frame(_frame, _detections):
        with service._lock:
            service.is_streaming = False
        frame_processed.set()

    service.on_frame = on_frame

    assert await service.start_streaming() is True
    assert await asyncio.to_thread(frame_processed.wait, 1)
    await service.stop()

    model.track.assert_not_called()
    model.predict.assert_called_once_with(
        camera.read.return_value[1],
        imgsz=service.img_size,
        conf=service.model_config.conf_threshold,
        iou=service.model_config.iou_threshold,
        verbose=False,
    )


@pytest.mark.asyncio
async def test_frame_skip_discards_one_iteration_before_reading_camera():
    camera = MagicMock()
    camera.read.return_value = (True, object())
    model = MagicMock()
    model.predict.return_value = []
    service = CameraService(loop=asyncio.get_running_loop())
    service.camera = camera
    service.model = model
    service.model_config = ModelConfig(name="mock.pt", enable_tracking=False)
    service.skip_frame = True
    frame_processed = threading.Event()

    def on_frame(_frame, _detections):
        with service._lock:
            service.is_streaming = False
        frame_processed.set()

    service.on_frame = on_frame

    assert await service.start_streaming() is True
    assert await asyncio.to_thread(frame_processed.wait, 1)
    await service.stop()

    camera.read.assert_called_once_with()
    model.predict.assert_called_once()


@pytest.mark.asyncio
async def test_status_callback_failure_does_not_change_camera_initialization_result():
    camera = MagicMock()
    service = CameraService(loop=asyncio.get_running_loop())

    def broken_callback(_status, _message):
        raise RuntimeError("UI callback failed")

    service.on_status_change = broken_callback

    with patch("src.dashboard.backend.camera_service.USBCamera", return_value=camera):
        result = await service.initialize_camera(CameraConfig())

    assert result is True
    assert service.status == SystemStatus.IDLE


@pytest.mark.asyncio
async def test_status_callback_is_scheduled_without_waiting_for_completion():
    callback_started = asyncio.Event()
    allow_callback_to_finish = asyncio.Event()
    camera = MagicMock()
    service = CameraService(loop=asyncio.get_running_loop())

    async def slow_callback(_status, _message):
        callback_started.set()
        await allow_callback_to_finish.wait()

    service.on_status_change = slow_callback

    with patch("src.dashboard.backend.camera_service.USBCamera", return_value=camera):
        result = await asyncio.wait_for(service.initialize_camera(CameraConfig()), timeout=0.5)

    assert result is True
    await asyncio.wait_for(callback_started.wait(), timeout=0.5)
    allow_callback_to_finish.set()


@pytest.mark.asyncio
async def test_failed_camera_initialization_releases_the_capture():
    service = CameraService()

    with patch("src.dashboard.backend.camera_service.USBCamera", side_effect=RuntimeError("camera unavailable")):
        result = await service.initialize_camera(CameraConfig())

    assert result is False
    assert service.status == SystemStatus.ERROR


@pytest.mark.asyncio
async def test_stop_waits_for_streaming_read_before_releasing_camera():
    read_started = threading.Event()
    allow_read_to_finish = threading.Event()
    camera = MagicMock()

    def read():
        read_started.set()
        allow_read_to_finish.wait(1)
        return False, None

    camera.read.side_effect = read
    service = CameraService()
    service.camera = camera
    service.model = MagicMock()
    service.model_config = ModelConfig(name="mock.pt")

    assert await service.start_streaming() is True
    assert await asyncio.to_thread(read_started.wait, 1)

    stop_task = asyncio.create_task(service.shutdown())
    await asyncio.sleep(0.05)
    camera.release.assert_not_called()

    allow_read_to_finish.set()
    await asyncio.wait_for(stop_task, timeout=1)
    camera.release.assert_called_once_with()


@pytest.mark.asyncio
async def test_stop_is_bounded_when_camera_read_does_not_return(caplog):
    read_started = threading.Event()
    allow_test_worker_to_finish = threading.Event()
    camera = MagicMock()

    def blocked_read():
        read_started.set()
        allow_test_worker_to_finish.wait()
        return False, None

    camera.read.side_effect = blocked_read
    service = CameraService()
    service._STOP_JOIN_TIMEOUT_SECONDS = 0.05
    service.camera = camera
    service.model = MagicMock()
    service.model_config = ModelConfig(name="mock.pt")

    assert await service.start_streaming() is True
    assert await asyncio.to_thread(read_started.wait, 1)
    streaming_thread = service._streaming_thread

    stop_task = asyncio.create_task(service.shutdown())
    try:
        await asyncio.sleep(0.2)
        assert stop_task.done()
        assert "did not stop within" in caplog.text
        camera.release.assert_called_once_with()
        assert service.camera is None
        assert service.is_streaming is False
        assert service._streaming_thread is streaming_thread
    finally:
        allow_test_worker_to_finish.set()
        await asyncio.wait_for(stop_task, timeout=1)
        await asyncio.to_thread(streaming_thread.join, 1)
