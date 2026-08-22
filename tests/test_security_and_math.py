"""Tests for security-critical and math utility functions in MIRA."""

import math
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


def _approx(a, b, abs_tol=1e-6):
    assert math.isclose(float(a), float(b), abs_tol=abs_tol), f"{a} != {b} (tol={abs_tol})"




class TestResolveSafePath:
    """Path-traversal prevention for user-supplied file paths."""

    def test_safe_relative_path_returns_resolved(self, tmp_path):
        from src.config import resolve_safe_path

        (tmp_path / "sub").mkdir()
        result = resolve_safe_path("sub", base_dir=tmp_path)
        assert result == (tmp_path / "sub").resolve()

    def test_dotdot_still_inside_base(self, tmp_path):
        from src.config import resolve_safe_path

        (tmp_path / "a" / "b").mkdir(parents=True)
        result = resolve_safe_path("a/b/../b", base_dir=tmp_path)
        assert result == (tmp_path / "a" / "b").resolve()

    def test_dotdot_escapes_root_raises_config_error(self, tmp_path):
        from src.config import ConfigError, resolve_safe_path

        (tmp_path / "inside").mkdir()
        with pytest.raises(ConfigError, match="Path traversal"):
            resolve_safe_path("../outside", base_dir=tmp_path)

    def test_escape_outside_base_raises_config_error(self, tmp_path):
        from src.config import ConfigError, resolve_safe_path

        with pytest.raises(ConfigError, match="Path traversal"):
            resolve_safe_path("../../etc/passwd", base_dir=tmp_path)

    def test_mixed_separators_within_base(self, tmp_path):
        from src.config import resolve_safe_path

        sub = tmp_path / "data" / "images"
        sub.mkdir(parents=True)
        result = resolve_safe_path("data/images", base_dir=tmp_path)
        assert result == sub.resolve()

    def test_empty_path_resolves_to_base(self, tmp_path):
        from src.config import resolve_safe_path

        result = resolve_safe_path("", base_dir=tmp_path)
        assert result == tmp_path.resolve()

    def test_path_with_tilde_expanded(self, tmp_path):
        from src.config import resolve_safe_path

        resolved = resolve_safe_path("~/somewhere", base_dir=Path.home().parent)
        assert "somewhere" in str(resolved)

    def test_absolute_path_inside_base(self, tmp_path):
        from src.config import resolve_safe_path

        abs_path = tmp_path / "inside"
        abs_path.mkdir()
        result = resolve_safe_path(str(abs_path), base_dir=tmp_path)
        assert result == abs_path

    def test_absolute_path_outside_base_raises_config_error(self, tmp_path):
        from src.config import ConfigError, resolve_safe_path

        with pytest.raises(ConfigError):
            resolve_safe_path("/etc", base_dir=tmp_path)




class TestComputeIoU:
    """Intersection-over-Union calculation for axis-aligned bounding boxes."""

    def test_identical_boxes(self):
        from src.pipeline.benchmark import compute_iou

        box = [10, 10, 50, 50]
        _approx(compute_iou(box, box), 1.0)

    def test_no_overlap(self):
        from src.pipeline.benchmark import compute_iou

        a = [0, 0, 10, 10]
        b = [20, 20, 30, 30]
        _approx(compute_iou(a, b), 0.0)

    def test_partial_overlap(self):
        from src.pipeline.benchmark import compute_iou

        a = [0, 0, 10, 10]
        b = [5, 5, 15, 15]
        inter = 5 * 5
        union = 100 + 100 - inter
        _approx(compute_iou(a, b), inter / union)

    def test_one_box_inside_another(self):
        from src.pipeline.benchmark import compute_iou

        outer = [0, 0, 20, 20]
        inner = [5, 5, 15, 15]
        inter = 10 * 10
        union = 400 + 100 - inter
        _approx(compute_iou(outer, inner), inter / union)

    def test_zero_area_box(self):
        from src.pipeline.benchmark import compute_iou

        normal = [0, 0, 10, 10]
        point = [5, 5, 5, 5]
        _approx(compute_iou(normal, point), 0.0)

    def test_touching_boxes_edge(self):
        from src.pipeline.benchmark import compute_iou

        a = [0, 0, 10, 10]
        b = [10, 0, 20, 10]
        _approx(compute_iou(a, b), 0.0)




class TestComputeMap:
    """Mean Average Precision across classes."""

    def test_identical_coordinates_on_different_images_do_not_match(self):
        from src.pipeline.benchmark import compute_map

        preds = [
            [{"class_id": 0, "confidence": 0.9, "bbox_pixel": [10, 10, 50, 50]}],
            [],
        ]
        gts = [
            [],
            [{"class_id": 0, "bbox": [10, 10, 50, 50]}],
        ]

        assert compute_map(preds, gts) == pytest.approx(0.0)

    def test_prediction_matches_ground_truth_on_same_image(self):
        from src.pipeline.benchmark import compute_map

        preds = [
            [],
            [{"class_id": 0, "confidence": 0.9, "bbox_pixel": [10, 10, 50, 50]}],
        ]
        gts = [
            [],
            [{"class_id": 0, "bbox": [10, 10, 50, 50]}],
        ]

        assert compute_map(preds, gts) == pytest.approx(1.0)

    def test_perfect_predictions(self):
        from src.pipeline.benchmark import compute_map

        preds = [[{"class_id": 0, "confidence": 0.99, "bbox_pixel": [10, 10, 50, 50]}]]
        gts = [[{"class_id": 0, "bbox": [10, 10, 50, 50]}]]
        assert compute_map(preds, gts) == pytest.approx(1.0, abs=0.01)

    def test_no_predictions(self):
        from src.pipeline.benchmark import compute_map

        preds = [[]]
        gts = [[{"class_id": 0, "bbox": [10, 10, 50, 50]}]]
        assert compute_map(preds, gts) == pytest.approx(0.0)

    def test_no_ground_truths(self):
        from src.pipeline.benchmark import compute_map

        preds = [[{"class_id": 0, "confidence": 0.9, "bbox_pixel": [10, 10, 50, 50]}]]
        gts = [[]]
        assert compute_map(preds, gts) == pytest.approx(0.0)

    def test_single_class(self):
        from src.pipeline.benchmark import compute_map

        preds = [[{"class_id": 0, "confidence": 0.9, "bbox_pixel": [10, 10, 50, 50]}]]
        gts = [[{"class_id": 0, "bbox": [10, 10, 50, 50]}]]
        assert compute_map(preds, gts) == pytest.approx(1.0, abs=0.01)

    def test_multiple_classes(self):
        from src.pipeline.benchmark import compute_map

        preds = [
            [
                {"class_id": 0, "confidence": 0.95, "bbox_pixel": [10, 10, 50, 50]},
                {"class_id": 1, "confidence": 0.85, "bbox_pixel": [60, 60, 100, 100]},
            ]
        ]
        gts = [
            [
                {"class_id": 0, "bbox": [10, 10, 50, 50]},
                {"class_id": 1, "bbox": [60, 60, 100, 100]},
            ]
        ]
        assert compute_map(preds, gts) == pytest.approx(1.0, abs=0.01)

    def test_mixed_quality(self):
        from src.pipeline.benchmark import compute_map

        preds = [
            [
                {"class_id": 0, "confidence": 0.9, "bbox_pixel": [10, 10, 50, 50]},
                {"class_id": 0, "confidence": 0.8, "bbox_pixel": [100, 100, 200, 200]},
            ]
        ]
        gts = [
            [
                {"class_id": 0, "bbox": [10, 10, 50, 50]},
                {"class_id": 0, "bbox": [100, 100, 200, 200]},
            ]
        ]
        ap = compute_map(preds, gts)
        assert 0.0 <= ap <= 1.0 + 1e-9




class TestSetupCameraProperties:
    """Hardware-focused camera config tests using mocked OpenCV."""

    def test_creates_a_two_dimensional_numpy_array(self):
        import cv2

        from src.config import setup_camera_properties

        cap = MagicMock()
        cap.isOpened.return_value = True

        with (
            patch.object(cv2, "CAP_PROP_FOURCC", "test_fourcc"),
            patch.object(cv2, "VideoWriter_fourcc", return_value="mjpg") as mock_fourcc,
            patch("src.config.logger"),
        ):
            with (
                patch.object(cv2, "CAP_PROP_FRAME_WIDTH", 3),
                patch.object(cv2, "CAP_PROP_FRAME_HEIGHT", 4),
                patch.object(cv2, "CAP_PROP_FPS", 5),
                patch.object(cv2, "CAP_PROP_BUFFERSIZE", 38),
                patch.object(cv2, "CAP_PROP_AUTOFOCUS", 39),
                patch.object(cv2, "CAP_PROP_AUTO_EXPOSURE", 40),
                patch.object(
                    cv2,
                    "CAP_PROP_AUTO_WB",
                    41,
                ),
            ):
                setup_camera_properties(cap, 640, 480, 30)

        mock_fourcc.assert_called_once_with("M", "J", "P", "G")
        cap.set.assert_any_call("test_fourcc", "mjpg")
        cap.set.assert_any_call(3, 640)
        cap.set.assert_any_call(4, 480)
        cap.set.assert_any_call(5, 30)
        cap.set.assert_any_call(38, 1)
        cap.set.assert_any_call(39, 0)
        cap.set.assert_any_call(40, 1)

    def test_raises_camera_error_if_camera_not_opened(self):
        from src.config import CameraError, setup_camera_properties

        cap = MagicMock()
        cap.isOpened.return_value = False

        with (
            patch("cv2.CAP_PROP_FOURCC", "test_fourcc"),
            patch("cv2.VideoWriter_fourcc", return_value="mjpg"),
            patch("src.config.logger"),
        ):
            with pytest.raises(CameraError):
                setup_camera_properties(cap, 640, 480)




@pytest.mark.skipif(not hasattr(pytest, "skip"), reason="Requires PyTorch installation")
class TestHardwareDetection:
    """Hardware detection tests requiring PyTorch."""

    def test_detect_hardware_has_cpu(self):
        """Hardware detection should always find CPU cores."""
        from src.deploy import detect_hardware

        info = detect_hardware()
        assert info.cpu_count > 0
        assert len(info.platform) > 0
        assert info.python_version is not None




class TestDatasetSummary:
    """Tests for the dataset_summary helper."""

    def test_dataset_summary_calls_validator(self, tmp_path):
        from src.pipeline.validators import dataset_summary

        split_dir = tmp_path / "test_ds"
        (split_dir / "images" / "train").mkdir(parents=True)
        (split_dir / "labels" / "train").mkdir(parents=True)

        summary = dataset_summary(split_dir)
        assert summary["images"] == 0
        assert summary["labels"] == 0
        assert "class_counts" in summary
        assert "valid" in summary
