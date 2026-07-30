"""Tests for security-critical and math utility functions in MIRA."""

import pathlib
from unittest.mock import MagicMock, patch

import pytest


# ---------------------------------------------------------------------------
# resolve_safe_path  (src/config.py)
# ---------------------------------------------------------------------------


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

    def test_escape_outside_base_raises_config_error(self, tmp_path):
        from src.config import resolve_safe_path
        from src.exceptions import ConfigError

        with pytest.raises(ConfigError, match="Path traversal"):
            resolve_safe_path("../../etc/passwd", base_dir=tmp_path)

    def test_absolute_path_outside_base_raises(self, tmp_path):
        from src.config import resolve_safe_path
        from src.exceptions import ConfigError

        with pytest.raises(ConfigError, match="Path traversal"):
            resolve_safe_path(pathlib.Path("/tmp/evil"), base_dir=tmp_path)

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

        resolved = resolve_safe_path("~/somewhere", base_dir=pathlib.Path.home().parent)
        assert "somewhere" in str(resolved)


# ---------------------------------------------------------------------------
# compute_iou  (src/pipeline/benchmark.py)
# ---------------------------------------------------------------------------


class TestComputeIoU:
    """Intersection-over-Union calculation for axis-aligned bounding boxes."""

    def test_identical_boxes(self):
        from src.pipeline.benchmark import compute_iou

        box = [10, 10, 50, 50]
        assert compute_iou(box, box) == pytest.approx(1.0)

    def test_no_overlap(self):
        from src.pipeline.benchmark import compute_iou

        a = [0, 0, 10, 10]
        b = [20, 20, 30, 30]
        assert compute_iou(a, b) == pytest.approx(0.0)

    def test_partial_overlap(self):
        from src.pipeline.benchmark import compute_iou

        a = [0, 0, 10, 10]
        b = [5, 5, 15, 15]
        inter = 5 * 5
        union = 100 + 100 - inter
        assert compute_iou(a, b) == pytest.approx(inter / union)

    def test_one_box_inside_another(self):
        from src.pipeline.benchmark import compute_iou

        outer = [0, 0, 20, 20]
        inner = [5, 5, 15, 15]
        inter = 10 * 10
        union = 400 + 100 - inter
        assert compute_iou(outer, inner) == pytest.approx(inter / union)

    def test_zero_area_box(self):
        from src.pipeline.benchmark import compute_iou

        normal = [0, 0, 10, 10]
        point = [5, 5, 5, 5]
        assert compute_iou(normal, point) == pytest.approx(0.0)

    def test_touching_boxes_edge(self):
        from src.pipeline.benchmark import compute_iou

        a = [0, 0, 10, 10]
        b = [10, 0, 20, 10]
        assert compute_iou(a, b) == pytest.approx(0.0)


# ---------------------------------------------------------------------------
# compute_map  (src/pipeline/benchmark.py)
# ---------------------------------------------------------------------------


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
        result = compute_map(preds, gts)
        assert result == 0.0

    def test_single_class(self):
        from src.pipeline.benchmark import compute_map

        preds = [
            [{"class_id": 0, "confidence": 0.9, "bbox_pixel": [10, 10, 50, 50]}],
        ]
        gts = [
            [{"class_id": 0, "bbox": [10, 10, 50, 50]}],
        ]
        assert compute_map(preds, gts) == pytest.approx(1.0, abs=0.01)

    def test_multiple_classes(self):
        from src.pipeline.benchmark import compute_map

        preds = [
            [
                {"class_id": 0, "confidence": 0.95, "bbox_pixel": [10, 10, 50, 50]},
                {"class_id": 1, "confidence": 0.85, "bbox_pixel": [60, 60, 100, 100]},
            ],
        ]
        gts = [
            [
                {"class_id": 0, "bbox": [10, 10, 50, 50]},
                {"class_id": 1, "bbox": [60, 60, 100, 100]},
            ],
        ]
        assert compute_map(preds, gts) == pytest.approx(1.0, abs=0.01)

    def test_mixed_quality(self):
        from src.pipeline.benchmark import compute_map

        preds = [
            [
                {"class_id": 0, "confidence": 0.9, "bbox_pixel": [10, 10, 50, 50]},
                {"class_id": 0, "confidence": 0.8, "bbox_pixel": [100, 100, 200, 200]},
            ],
        ]
        gts = [
            [
                {"class_id": 0, "bbox": [10, 10, 50, 50]},
                {"class_id": 0, "bbox": [100, 100, 200, 200]},
            ],
        ]
        ap = compute_map(preds, gts)
        assert 0.0 <= ap <= 1.0 + 1e-9


# ---------------------------------------------------------------------------
# setup_camera_properties  (src/config.py)
# ---------------------------------------------------------------------------


class TestSetupCameraProperties:
    """Camera property initialisation (mocked, no real hardware)."""

    def test_sets_fourcc_and_resolution(self):
        from src.config import setup_camera_properties

        mock_cv2 = MagicMock()
        mock_cv2.CAP_PROP_FOURCC = 6
        mock_cv2.CAP_PROP_FRAME_WIDTH = 3
        mock_cv2.CAP_PROP_FRAME_HEIGHT = 4
        mock_cv2.CAP_PROP_FPS = 5
        mock_cv2.CAP_PROP_BUFFERSIZE = 17
        mock_cv2.CAP_PROP_AUTOFOCUS = 28
        mock_cv2.CAP_PROP_AUTO_EXPOSURE = 21
        mock_cv2.VideoWriter_fourcc.return_value = 0x47504A4D

        cap = MagicMock()
        cap.isOpened.return_value = True

        with patch.dict("sys.modules", {"cv2": mock_cv2}):
            setup_camera_properties(cap, width=1280, height=720, fps=30)

        cap.set.assert_any_call(mock_cv2.CAP_PROP_FRAME_WIDTH, 1280)
        cap.set.assert_any_call(mock_cv2.CAP_PROP_FRAME_HEIGHT, 720)
        cap.set.assert_any_call(mock_cv2.CAP_PROP_FPS, 30)
        cap.set.assert_any_call(mock_cv2.CAP_PROP_BUFFERSIZE, 1)
        cap.set.assert_any_call(mock_cv2.CAP_PROP_AUTOFOCUS, 0)
        cap.set.assert_any_call(mock_cv2.CAP_PROP_AUTO_EXPOSURE, 1)

    def test_raises_when_camera_not_opened(self):
        from src.config import setup_camera_properties
        from src.exceptions import CameraError

        mock_cv2 = MagicMock()
        cap = MagicMock()
        cap.isOpened.return_value = False

        with patch.dict("sys.modules", {"cv2": mock_cv2}):
            with pytest.raises(CameraError, match="not opened"):
                setup_camera_properties(cap, width=640, height=480)
