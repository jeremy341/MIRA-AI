from datetime import datetime, timezone

import pytest

from src.dashboard.backend.camera_service import CameraService
from src.dashboard.backend.models import Detection


def test_get_statistics_averages_confidence_per_class():
    service = CameraService()
    now = datetime.now(timezone.utc)
    service.detection_history.extend(
        [
            Detection(class_name="glass", confidence=0.8, bbox=[0, 0, 1, 1], timestamp=now),
            Detection(class_name="glass", confidence=0.6, bbox=[0, 0, 1, 1], timestamp=now),
            Detection(class_name="paper", confidence=0.5, bbox=[0, 0, 1, 1], timestamp=now),
        ]
    )

    stats = service.get_statistics(period_seconds=60)

    assert stats.total_detections == 3
    assert stats.class_counts == {"glass": 2, "paper": 1}
    assert stats.avg_confidence["glass"] == pytest.approx(0.7)
    assert stats.avg_confidence["paper"] == pytest.approx(0.5)
