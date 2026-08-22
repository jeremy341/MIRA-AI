"""Unit tests for the shared inference engine."""

import time
from unittest.mock import MagicMock, patch

import pytest

from src.config import CAMERA_DEFAULT_CONF, DEFAULT_IMGSZ, DEFAULT_IOU
from src.exceptions import ConfigError
from src.inference_engine import InferenceEngine

@pytest.fixture
def mock_yolo():
    """Mock ultralytics.YOLO so no real model loading occurs."""
    with patch("src.inference_engine.YOLO") as yolo_cls:
        mock_model = MagicMock()
        yolo_cls.return_value = mock_model
        yield yolo_cls, mock_model


@pytest.fixture
def mock_camera():
    """Mock USBCamera so no real hardware is opened."""
    with patch("src.inference_engine.USBCamera") as cam_cls:
        mock_cam = MagicMock()
        cam_cls.return_value = mock_cam
        yield cam_cls, mock_cam


@pytest.fixture
def mock_cv2():
    """Patch cv2 used by the engine to avoid windowing calls."""
    with patch("src.inference_engine.cv2") as cv2_mock:
        yield cv2_mock


@pytest.fixture
def detection_dir(tmp_path):
    """Temporary DETECTION_DIR containing a placeholder .pt model."""
    det_dir = tmp_path / "detection"
    det_dir.mkdir(parents=True)
    (det_dir / "yolo11n.pt").touch()
    return det_dir




class TestConstructor:
    def test_default_conf_and_iou_from_config(self, mock_yolo, mock_camera, detection_dir):
        with patch("src.inference_engine.DETECTION_DIR", detection_dir):
            engine = InferenceEngine("yolo11n.pt")
            assert engine.conf_threshold == CAMERA_DEFAULT_CONF
            assert engine.iou_threshold == DEFAULT_IOU

    def test_explicit_conf_and_iou_override_defaults(self, mock_yolo, mock_camera, detection_dir):
        with patch("src.inference_engine.DETECTION_DIR", detection_dir):
            engine = InferenceEngine("yolo11n.pt", conf_threshold=0.7, iou_threshold=0.3)
            assert engine.conf_threshold == 0.7
            assert engine.iou_threshold == 0.3

    def test_camera_config_and_lifecycle_flags(self, mock_yolo, mock_camera, detection_dir):
        with patch("src.inference_engine.DETECTION_DIR", detection_dir):
            engine = InferenceEngine(
                "yolo11n.pt",
                camera_index=2,
                cam_width=800,
                cam_height=600,
                target_latency_ms=100,
                reject_threshold=0.6,
                enable_tracking=False,
            )
            assert engine.camera_index == 2
            assert engine.cam_width == 800
            assert engine.cam_height == 600
            assert engine.target_latency_ms == 100
            assert engine.reject_threshold == 0.6
            assert engine.enable_tracking is False
            assert engine._stopped is False
            assert engine._released is False
            assert engine.skip_frame is False
            assert engine._current_fps == 0.0
            assert engine.latency_history.maxlen == 30
            assert len(engine.latency_history) == 0

    def test_path_traversal_blocked(self, mock_yolo, mock_camera, detection_dir):
        with patch("src.inference_engine.DETECTION_DIR", detection_dir):
            with pytest.raises(ConfigError, match="path escapes"):
                InferenceEngine("../secret.pt")

    def test_model_not_found_raises_file_not_found_error(self, mock_yolo, mock_camera, detection_dir):
        (detection_dir / "other.pt").touch()
        with patch("src.inference_engine.DETECTION_DIR", detection_dir):
            with pytest.raises(FileNotFoundError, match="not found"):
                InferenceEngine("ghost.pt")

    def test_classifier_model_raises_value_error(self, mock_yolo, mock_camera, detection_dir):
        (detection_dir / "classifier_model.pt").touch()
        with patch("src.inference_engine.DETECTION_DIR", detection_dir):
            with pytest.raises(ValueError, match="classifier"):
                InferenceEngine("classifier_model.pt")

    def test_camera_init_failure_calls_cleanup(self, mock_yolo, detection_dir):
        with patch("src.inference_engine.USBCamera", side_effect=RuntimeError("Camera not accessible")):
            with patch("src.inference_engine.DETECTION_DIR", detection_dir):
                with patch.object(InferenceEngine, "_cleanup") as mock_cleanup:
                    with pytest.raises(RuntimeError, match="Camera not accessible"):
                        InferenceEngine("yolo11n.pt")
                    mock_cleanup.assert_called_once()




class TestModelLoading:
    def test_pt_model_img_size_and_not_int8(self, mock_yolo, mock_camera, detection_dir):
        with patch("src.inference_engine.DETECTION_DIR", detection_dir):
            engine = InferenceEngine("yolo11n.pt")
            assert engine.img_size == DEFAULT_IMGSZ
            assert engine.is_tflite_int8 is False

    def test_pt_model_explicit_imgsz_overrides_default(self, mock_yolo, mock_camera, detection_dir):
        with patch("src.inference_engine.DETECTION_DIR", detection_dir):
            engine = InferenceEngine("yolo11n.pt", imgsz=1024)
            assert engine.img_size == 1024

    def test_tflite_model_uses_get_tflite_imgsz(self, mock_yolo, mock_camera, detection_dir):
        (detection_dir / "model.tflite").touch()
        with (
            patch("src.inference_engine.DETECTION_DIR", detection_dir),
            patch("src.inference_engine.get_tflite_imgsz", return_value=320),
        ):
            engine = InferenceEngine("model.tflite")
            assert engine.img_size == 320

    def test_tflite_uses_fixed_model_imgsz(self, mock_yolo, mock_camera, detection_dir):
        (detection_dir / "model.tflite").touch()
        with (
            patch("src.inference_engine.DETECTION_DIR", detection_dir),
            patch("src.inference_engine.get_tflite_imgsz", return_value=320),
        ):
            engine = InferenceEngine("model.tflite", imgsz=512)
            assert engine.img_size == 320

    def test_int8_detected_from_filename(self, mock_yolo, mock_camera, detection_dir):
        (detection_dir / "model_int8.tflite").touch()
        with (
            patch("src.inference_engine.DETECTION_DIR", detection_dir),
            patch("src.inference_engine.get_tflite_imgsz", return_value=320),
        ):
            engine = InferenceEngine("model_int8.tflite")
            assert engine.is_tflite_int8 is True

    def test_int8_in_pt_filename_not_detected(self, mock_yolo, mock_camera, detection_dir):
        (detection_dir / "model_int8.pt").touch()
        with patch("src.inference_engine.DETECTION_DIR", detection_dir):
            engine = InferenceEngine("model_int8.pt")
            assert engine.is_tflite_int8 is False

    def test_yolo_loaded_with_detect_task(self, mock_yolo, mock_camera, detection_dir):
        yolo_cls, _ = mock_yolo
        with patch("src.inference_engine.DETECTION_DIR", detection_dir):
            InferenceEngine("yolo11n.pt")
            _, kwargs = yolo_cls.call_args
            assert kwargs.get("task") == "detect"




class TestInt8Behavior:
    def test_int8_defaults_conf_to_025_and_disables_tracking(self, mock_yolo, mock_camera, detection_dir):
        (detection_dir / "model_int8.tflite").touch()
        with (
            patch("src.inference_engine.DETECTION_DIR", detection_dir),
            patch("src.inference_engine.get_tflite_imgsz", return_value=320),
        ):
            engine = InferenceEngine("model_int8.tflite", enable_tracking=True)
            assert engine.conf_threshold == 0.25
            assert engine.enable_tracking is False

    def test_int8_honors_explicit_confidence_threshold(self, mock_yolo, mock_camera, detection_dir):
        (detection_dir / "model_int8.tflite").touch()
        with (
            patch("src.inference_engine.DETECTION_DIR", detection_dir),
            patch("src.inference_engine.get_tflite_imgsz", return_value=320),
        ):
            engine = InferenceEngine("model_int8.tflite", conf_threshold=0.1)
            assert engine.conf_threshold == 0.1

    def test_non_int8_tflite_also_disables_tracking(self, mock_yolo, mock_camera, detection_dir):
        (detection_dir / "model.tflite").touch()
        with (
            patch("src.inference_engine.DETECTION_DIR", detection_dir),
            patch("src.inference_engine.get_tflite_imgsz", return_value=320),
        ):
            engine = InferenceEngine("model.tflite", enable_tracking=True)
            assert engine.enable_tracking is False

    def test_pt_model_preserves_tracking_flag(self, mock_yolo, mock_camera, detection_dir):
        with patch("src.inference_engine.DETECTION_DIR", detection_dir):
            engine = InferenceEngine("yolo11n.pt", enable_tracking=True)
            assert engine.enable_tracking is True




class TestContextManager:
    def test_enter_returns_self(self, mock_yolo, mock_camera, detection_dir):
        with patch("src.inference_engine.DETECTION_DIR", detection_dir):
            engine = InferenceEngine("yolo11n.pt")
            assert engine.__enter__() is engine

    def test_cleanup_on_exception_in_with_statement(self, mock_yolo, mock_camera, detection_dir):
        with patch("src.inference_engine.DETECTION_DIR", detection_dir):
            engine = InferenceEngine("yolo11n.pt")
            try:
                with engine:
                    raise RuntimeError("boom")
            except RuntimeError:
                pass
            assert engine._released is True




class TestFrameSkipping:
    def _make_result(self, inference_time: float) -> MagicMock:
        result = MagicMock()
        result.speed = {"inference": inference_time}
        return result

    def test_empty_results_clears_skip_frame(self, mock_yolo, mock_camera, mock_cv2, detection_dir):
        with patch("src.inference_engine.DETECTION_DIR", detection_dir):
            engine = InferenceEngine("yolo11n.pt")
            engine.skip_frame = True
            engine._update_metrics([])
            assert engine.skip_frame is False

    def test_high_avg_latency_sets_skip_frame(self, mock_yolo, mock_camera, mock_cv2, detection_dir):
        with patch("src.inference_engine.DETECTION_DIR", detection_dir):
            engine = InferenceEngine("yolo11n.pt", target_latency_ms=50)
            result = self._make_result(100)
            engine.latency_history.extend([100] * 29)
            engine._update_metrics([result])
            assert engine.skip_frame is True

    def test_low_avg_latency_does_not_set_skip_frame(self, mock_yolo, mock_camera, mock_cv2, detection_dir):
        with patch("src.inference_engine.DETECTION_DIR", detection_dir):
            engine = InferenceEngine("yolo11n.pt", target_latency_ms=50)
            result = self._make_result(30)
            engine.latency_history.extend([30] * 29)
            engine._update_metrics([result])
            assert engine.skip_frame is False

    def test_missing_inference_key_defaults_to_zero(self, mock_yolo, mock_camera, mock_cv2, detection_dir):
        with patch("src.inference_engine.DETECTION_DIR", detection_dir):
            engine = InferenceEngine("yolo11n.pt", target_latency_ms=50)
            result = MagicMock()
            result.speed = {"preprocess": 5}
            engine.latency_history.clear()
            engine.skip_frame = True
            engine._update_metrics([result])
            assert engine.skip_frame is False




class TestLatencyTracking:
    def test_deque_respects_maxlen(self, mock_yolo, mock_camera, mock_cv2, detection_dir):
        with patch("src.inference_engine.DETECTION_DIR", detection_dir):
            engine = InferenceEngine("yolo11n.pt")
            result = MagicMock()
            result.speed = {"inference": 10}
            for _ in range(50):
                engine._update_metrics([result])
            assert len(engine.latency_history) == 30

    def test_fps_positive_after_inference(self, mock_yolo, mock_camera, mock_cv2, detection_dir):
        with patch("src.inference_engine.DETECTION_DIR", detection_dir):
            engine = InferenceEngine("yolo11n.pt")
            engine.prev_time = time.perf_counter() - 0.1
            result = MagicMock()
            result.speed = {"inference": 10}
            engine._update_metrics([result])
            assert engine._current_fps > 0




class TestCleanup:
    def test_cleanup_idempotent(self, mock_yolo, mock_camera, mock_cv2, detection_dir):
        with patch("src.inference_engine.DETECTION_DIR", detection_dir):
            engine = InferenceEngine("yolo11n.pt")
            engine._cleanup()
            engine._cleanup()
            assert engine._released is True
            assert engine._stopped is True

    def test_cleanup_releases_camera(self, mock_yolo, mock_camera, mock_cv2, detection_dir):
        _, mock_cam = mock_camera
        with patch("src.inference_engine.DETECTION_DIR", detection_dir):
            engine = InferenceEngine("yolo11n.pt")
            engine._cleanup()
            mock_cam.release.assert_called_once()

    def test_cleanup_destroys_cv2_windows(self, mock_yolo, mock_camera, mock_cv2, detection_dir):
        with patch("src.inference_engine.DETECTION_DIR", detection_dir):
            engine = InferenceEngine("yolo11n.pt")
            engine._cleanup()
            mock_cv2.destroyAllWindows.assert_called_once()

    def test_stop_sets_stopped_flag(self, mock_yolo, mock_camera, detection_dir):
        with patch("src.inference_engine.DETECTION_DIR", detection_dir):
            engine = InferenceEngine("yolo11n.pt")
            engine.stop()
            assert engine._stopped is True

    def test_del_warns_when_not_released(self, mock_yolo, mock_camera, detection_dir):
        with patch("src.inference_engine.DETECTION_DIR", detection_dir):
            with patch("src.inference_engine.warnings") as mock_warnings:
                engine = InferenceEngine("yolo11n.pt")
                engine.__del__()
                mock_warnings.warn.assert_called_once()

    def test_del_silent_when_already_released(self, mock_yolo, mock_camera, detection_dir):
        with patch("src.inference_engine.DETECTION_DIR", detection_dir):
            with patch("src.inference_engine.warnings") as mock_warnings:
                engine = InferenceEngine("yolo11n.pt")
                engine._released = True
                engine.__del__()
                mock_warnings.warn.assert_not_called()




class TestInferRouting:
    def test_int8_model_uses_predict_not_track(
        self,
        mock_yolo,
        mock_camera,
        mock_cv2,
        detection_dir,
    ):
        (detection_dir / "model_int8.tflite").touch()
        with (
            patch("src.inference_engine.DETECTION_DIR", detection_dir),
            patch("src.inference_engine.get_tflite_imgsz", return_value=320),
        ):
            engine = InferenceEngine("model_int8.tflite")
            dummy_frame = MagicMock()
            engine._infer(dummy_frame)
            engine.model.predict.assert_called_once()
            engine.model.track.assert_not_called()

    def test_pt_with_tracking_uses_track(
        self,
        mock_yolo,
        mock_camera,
        mock_cv2,
        detection_dir,
    ):
        with patch("src.inference_engine.DETECTION_DIR", detection_dir):
            engine = InferenceEngine("yolo11n.pt", enable_tracking=True)
            dummy_frame = MagicMock()
            engine._infer(dummy_frame)
            engine.model.track.assert_called_once()

    def test_pt_without_tracking_uses_predict(
        self,
        mock_yolo,
        mock_camera,
        mock_cv2,
        detection_dir,
    ):
        with patch("src.inference_engine.DETECTION_DIR", detection_dir):
            engine = InferenceEngine("yolo11n.pt", enable_tracking=False)
            dummy_frame = MagicMock()
            engine._infer(dummy_frame)
            engine.model.predict.assert_called_once()

    def test_non_int8_tflite_uses_predict(
        self,
        mock_yolo,
        mock_camera,
        mock_cv2,
        detection_dir,
    ):
        (detection_dir / "model.tflite").touch()
        with (
            patch("src.inference_engine.DETECTION_DIR", detection_dir),
            patch("src.inference_engine.get_tflite_imgsz", return_value=320),
        ):
            engine = InferenceEngine("model.tflite")
            dummy_frame = MagicMock()
            engine._infer(dummy_frame)
            engine.model.predict.assert_called_once()
            engine.model.track.assert_not_called()
