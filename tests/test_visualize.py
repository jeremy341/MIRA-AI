"""Tests for MIRA shared visualization utilities."""

from unittest.mock import MagicMock

import numpy as np
import pytest


@pytest.fixture
def sample_frame():
    """Return a 100x100x3 dummy BGR frame."""
    return np.zeros((100, 100, 3), dtype=np.uint8)


def _make_mock_box(conf, xyxy, cls_id):
    """Create a mock YOLO box with cpu().numpy() chain support.

    The box.xyxy[0] must return a 1D array of 4 values [x1, y1, x2, y2]
    after the .cpu().numpy() chain, matching the real YOLO output.
    """
    box = MagicMock()
    box.conf = np.array([conf])

    xyxy_array = np.array(xyxy)

    class _XYXYProxy(list):
        """List-like proxy so box.xyxy[0] returns a cpu()-chainable mock."""

        def __init__(self, arr):
            super().__init__([arr])

        def __getitem__(self, idx):
            val = super().__getitem__(idx)
            m = MagicMock()
            m.cpu.return_value.numpy.return_value = val
            return m

    box.xyxy = _XYXYProxy(xyxy_array)

    box.cls = np.array([cls_id])
    return box


def _make_mock_results(boxes_list, names=None):
    """Create mock YOLO results with a list of mock boxes."""
    results = MagicMock()

    if names is None:
        names = {0: "glass", 1: "metal", 2: "paper", 3: "plastic", 4: "trash"}

    results.__len__ = lambda self: 1
    results[0].names = names

    if not boxes_list:
        results[0].boxes = None
    else:
        mock_boxes = MagicMock()
        mock_boxes.__iter__ = lambda self: iter(boxes_list)
        mock_boxes.__len__ = lambda self: len(boxes_list)
        results[0].boxes = mock_boxes

    return results


def test_draw_boxes_no_detections_returns_frame_unchanged(sample_frame):
    from src.visualize import draw_boxes

    results = _make_mock_results([])
    result = draw_boxes(sample_frame, results, conf_threshold=0.3)
    np.testing.assert_array_equal(result, sample_frame)


def test_draw_boxes_below_threshold_no_boxes_drawn(sample_frame):
    from src.visualize import draw_boxes

    low_conf_box = _make_mock_box(0.1, [10.0, 10.0, 50.0, 50.0], 0)
    results = _make_mock_results([low_conf_box], names={0: "glass"})

    result = draw_boxes(sample_frame.copy(), results, conf_threshold=0.3)
    np.testing.assert_array_equal(result, sample_frame)


def test_draw_boxes_above_threshold_draws_rectangle(sample_frame):
    from src.visualize import draw_boxes

    box = _make_mock_box(0.85, [10.0, 10.0, 50.0, 50.0], 2)
    results = _make_mock_results([box])

    result = draw_boxes(sample_frame.copy(), results, conf_threshold=0.3)
    assert not np.array_equal(result, sample_frame)


def test_draw_boxes_clips_to_frame_bounds(sample_frame):
    from src.visualize import draw_boxes

    overflow_box = _make_mock_box(0.9, [-10.0, -10.0, 110.0, 110.0], 1)
    results = _make_mock_results([overflow_box], names={1: "metal"})

    result = draw_boxes(sample_frame.copy(), results, conf_threshold=0.3)
    assert result.shape == sample_frame.shape


def test_draw_boxes_multiple_detections(sample_frame):
    from src.visualize import draw_boxes

    box1 = _make_mock_box(0.7, [5.0, 5.0, 30.0, 30.0], 0)
    box2 = _make_mock_box(0.6, [60.0, 60.0, 90.0, 90.0], 3)
    results = _make_mock_results([box1, box2], names={0: "glass", 3: "plastic"})

    result = draw_boxes(sample_frame.copy(), results, conf_threshold=0.3)
    assert not np.array_equal(result, sample_frame)


def test_draw_boxes_reject_tier_unsicher(sample_frame):
    """Detection between conf_threshold and reject_threshold draws yellow 'unsicher'."""
    from src.visualize import draw_boxes

    box = _make_mock_box(0.40, [10.0, 10.0, 50.0, 50.0], 0)
    results = _make_mock_results([box], names={0: "glass"})

    result = draw_boxes(sample_frame.copy(), results, conf_threshold=0.25, reject_threshold=0.55)
    assert not np.array_equal(result, sample_frame)


def test_draw_boxes_reject_tier_confident(sample_frame):
    """Detection above reject_threshold draws green labeled box."""
    from src.visualize import draw_boxes

    box = _make_mock_box(0.90, [10.0, 10.0, 50.0, 50.0], 2)
    results = _make_mock_results([box], names={2: "paper"})

    result = draw_boxes(sample_frame.copy(), results, conf_threshold=0.25, reject_threshold=0.55)
    assert not np.array_equal(result, sample_frame)


def test_draw_boxes_below_conf_threshold_not_drawn(sample_frame):
    """Detection below conf_threshold is not drawn at all."""
    from src.visualize import draw_boxes

    box = _make_mock_box(0.10, [10.0, 10.0, 50.0, 50.0], 4)
    results = _make_mock_results([box], names={4: "trash"})

    result = draw_boxes(sample_frame.copy(), results, conf_threshold=0.25, reject_threshold=0.55)
    np.testing.assert_array_equal(result, sample_frame)


def test_draw_boxes_empty_results(sample_frame):
    """Empty results list returns frame unchanged."""
    from src.visualize import draw_boxes

    results = MagicMock()
    results.__len__ = lambda self: 0

    result = draw_boxes(sample_frame.copy(), results, conf_threshold=0.3, reject_threshold=0.55)
    np.testing.assert_array_equal(result, sample_frame)
