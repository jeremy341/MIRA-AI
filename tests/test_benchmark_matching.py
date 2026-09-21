from src.pipeline.benchmark import match_predictions
from src.pipeline.models import Detection


def item(class_id, box, confidence=0.9):
    return Detection(class_id, f"class_{class_id}", confidence, tuple(box))


def test_matching_uses_the_supplied_iou():
    prediction = item(0, [0, 0, 10, 10])
    truth = item(0, [0, 0, 6, 10])
    strict = match_predictions([prediction], [truth], 0.7)
    relaxed = match_predictions([prediction], [truth], 0.5)
    assert strict.true_positives == 0
    assert strict.false_positives == 1
    assert strict.false_negatives == 1
    assert relaxed.true_positives == 1
