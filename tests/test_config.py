"""Tests for MIRA shared configuration."""
import pathlib
from unittest.mock import MagicMock, patch


def test_root_dir_is_pathlib_path():
    from src.config import ROOT_DIR
    assert isinstance(ROOT_DIR, pathlib.Path)


def test_script_dir_is_sub_of_root():
    from src.config import ROOT_DIR, SCRIPT_DIR
    assert SCRIPT_DIR.parent == ROOT_DIR


def test_class_names_has_5_entries():
    from src.config import CLASS_NAMES
    assert CLASS_NAMES == ["glass", "metal", "paper", "plastic", "trash"]
    assert len(CLASS_NAMES) == 5


def test_get_detection_models_returns_sorted_list():
    from src.config import get_detection_models
    result = get_detection_models()
    assert isinstance(result, list)
    assert all(isinstance(m, str) for m in result)
    assert result == sorted(result)


def test_get_detection_models_excludes_classifiers():
    from src.config import get_detection_models
    result = get_detection_models()
    assert not any("classifier" in m.lower() for m in result)


def test_get_detection_models_only_pt_and_tflite():
    from src.config import get_detection_models
    result = get_detection_models()
    for m in result:
        assert m.endswith(".pt") or m.endswith(".tflite"), f"Unexpected suffix: {m}"


def test_get_tflite_imgsz_reads_tensor_shape():
    from src.config import get_tflite_imgsz

    mock_interpreter = MagicMock()
    mock_interpreter.get_input_details.return_value = [{"shape": [1, 320, 320, 3]}]

    with patch("ai_edge_litert.interpreter.Interpreter", return_value=mock_interpreter):
        result = get_tflite_imgsz(pathlib.Path("/fake/model.tflite"))

    assert result == 320


def test_get_tflite_imgsz_max_of_dims():
    from src.config import get_tflite_imgsz

    mock_interpreter = MagicMock()
    mock_interpreter.get_input_details.return_value = [{"shape": [1, 3, 224, 224]}]

    with patch("ai_edge_litert.interpreter.Interpreter", return_value=mock_interpreter):
        result = get_tflite_imgsz(pathlib.Path("/fake/model.tflite"))

    assert result == 224
